"""Multi-provider API client with automatic fallback."""

import json
import os
import re
import threading
import time
from dataclasses import dataclass

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError

load_dotenv()


@dataclass
class Provider:
    """Configuration for an API provider."""
    name: str
    base_url: str
    api_key_env: str
    # Model mapping: generic name -> provider-specific name
    model_map: dict[str, str] | None = None


# Provider configurations (in fallback order)
PROVIDERS = [
    Provider(
        name="openrouter",
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
    ),
    Provider(
        name="groq",
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        model_map={
            # Map OpenRouter model names to Groq equivalents
            "meta-llama/llama-3.1-70b-instruct": "llama-3.1-70b-versatile",
            "meta-llama/llama-3.1-8b-instruct": "llama-3.1-8b-instant",
            "mistralai/mixtral-8x7b-instruct": "mixtral-8x7b-32768",
        },
    ),
    Provider(
        name="together",
        base_url="https://api.together.xyz/v1",
        api_key_env="TOGETHER_API_KEY",
        model_map={
            "meta-llama/llama-3.1-70b-instruct": "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
            "meta-llama/llama-3.1-8b-instruct": "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
        },
    ),
    Provider(
        name="cerebras",
        base_url="https://api.cerebras.ai/v1",
        api_key_env="CEREBRAS_API_KEY",
        model_map={
            "meta-llama/llama-3.1-70b-instruct": "llama3.1-70b",
            "meta-llama/llama-3.1-8b-instruct": "llama3.1-8b",
        },
    ),
    Provider(
        name="huggingface",
        base_url="https://api-inference.huggingface.co/v1",
        api_key_env="HF_API_KEY",
        model_map={
            "meta-llama/llama-3.1-70b-instruct": "meta-llama/Meta-Llama-3.1-70B-Instruct",
        },
    ),
]

# Models known to support native reasoning via the API.
# Prefix-matched so dated variants and :free suffixes work automatically.
NATIVE_REASONING_PREFIXES = (
    "anthropic/claude-sonnet-4",   # Sonnet 4.5+
    "anthropic/claude-haiku-4",    # Haiku 4.5+
    "anthropic/claude-opus-4",     # Opus 4.6+
    "deepseek/deepseek-r1",        # DeepSeek R1 family
    "google/gemini-2.5-flash-lite",  # Gemini 2.5 Flash Lite (thinking)
    "google/gemini-3",               # Gemini 3 Pro/Flash (thinking)
)


def supports_native_reasoning(model: str) -> bool:
    """Check whether a model is known to support native reasoning traces."""
    return any(model.startswith(prefix) for prefix in NATIVE_REASONING_PREFIXES)


_thread_state = threading.local()


def _get_thread_clients() -> dict[str, OpenAI]:
    clients = getattr(_thread_state, "clients", None)
    if clients is None:
        clients = {}
        _thread_state.clients = clients
    return clients



def _get_client(provider: Provider) -> OpenAI | None:
    """Get or create a client for the given provider."""
    clients = _get_thread_clients()
    if provider.name in clients:
        return clients[provider.name]

    api_key = os.getenv(provider.api_key_env)
    if not api_key:
        return None

    client = OpenAI(
        base_url=provider.base_url,
        api_key=api_key,
    )
    clients[provider.name] = client
    return client


def _map_model(model: str, provider: Provider) -> str:
    """Map a model name to provider-specific equivalent."""
    if provider.model_map and model in provider.model_map:
        return provider.model_map[model]
    # For OpenRouter models with :free suffix, try without it for other providers
    if provider.name != "openrouter" and model.endswith(":free"):
        base_model = model[:-5]  # Remove :free
        if provider.model_map and base_model in provider.model_map:
            return provider.model_map[base_model]
    return model




def _extract_api_reasoning(message) -> str:
    """Extract reasoning content from an API response message.

    Handles multiple response formats (checked in priority order):
    - reasoning_details: Structured array with typed entries (summary, text, encrypted)
    - reasoning: Primary plaintext reasoning field
    - reasoning_content: Legacy alias for reasoning
    """
    # Structured format: reasoning_details array (list of typed entries)
    reasoning_details = getattr(message, "reasoning_details", None)
    if reasoning_details:
        parts = []
        for detail in reasoning_details:
            # Handle both Pydantic objects and plain dicts
            text = getattr(detail, "text", None) or (
                detail.get("text") if isinstance(detail, dict) else None
            )
            if text:
                parts.append(text)
                continue
            summary = getattr(detail, "summary", None) or (
                detail.get("summary") if isinstance(detail, dict) else None
            )
            if summary:
                parts.append(summary)
        if parts:
            return "\n".join(parts)

    # Primary plaintext field (OpenRouter's documented response field)
    reasoning = getattr(message, "reasoning", None)
    if reasoning:
        return reasoning

    # Legacy alias
    return getattr(message, "reasoning_content", None) or ""


def _print_debug_context(
    *,
    model: str,
    messages: list[dict],
    temperature: float,
    max_tokens: int,
    include_reasoning: bool,
    debug_label: str | None,
) -> None:
    label = f" ({debug_label})" if debug_label else ""
    print(f"\n=== DEBUG: Model Query{label} ===")
    print(f"Model: {model}")
    if include_reasoning:
        reasoning_budget = max(2048, max_tokens)
        reasoning_mode = f"requested (budget={reasoning_budget}, total={max_tokens + reasoning_budget})"
    else:
        reasoning_mode = "suppressed"
    print(
        "Params: "
        f"temperature={temperature}, max_tokens={max_tokens}, "
        f"reasoning={reasoning_mode}"
    )
    print("Messages:")
    print(json.dumps(messages, indent=2, ensure_ascii=True, default=str))
    print("=== END DEBUG ===\n")


def chat(
    model: str,
    messages: list[dict],
    temperature: float = 0.9,
    max_tokens: int = 1024,
    include_reasoning: bool = True,
    debug: bool = False,
    debug_label: str | None = None,
    retry_wait_seconds: float = 10.0,
    max_retries: int = 10,
) -> str:
    """Send a chat completion request with automatic provider fallback.

    Tries providers in order until one succeeds. If a provider hits rate limits
    or errors, falls back to the next available provider.

    For reasoning models (e.g., DeepSeek-R1), the response may include both
    reasoning_content (chain-of-thought) and content (final answer).

    Args:
        model: The model identifier (OpenRouter format preferred).
        messages: The conversation messages.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.
        include_reasoning: If True (default), actively request reasoning
            traces from the API (via OpenRouter's ``reasoning`` parameter)
            and, when returned, wrap them in <reasoning> tags prepended to
            the response.  If False, suppress native reasoning and omit any
            traces from the output.
        retry_wait_seconds: Fixed wait between retries for a provider.
        max_retries: Maximum attempts per provider before falling back.
        debug: If True, print the full prompt context to the console.
        debug_label: Optional label to identify the call site in debug output.

    Returns:
        The assistant's response text, optionally with reasoning prepended.

    Raises:
        RuntimeError: If no providers are available or all fail.
    """
    if debug:
        _print_debug_context(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            include_reasoning=include_reasoning,
            debug_label=debug_label,
        )

    errors = []
    try:
        max_retries = max(1, int(max_retries))
    except (TypeError, ValueError):
        max_retries = 1
    try:
        retry_wait_seconds = max(0.1, float(retry_wait_seconds))
    except (TypeError, ValueError):
        retry_wait_seconds = 1.0

    for provider in PROVIDERS:
        client = _get_client(provider)
        if client is None:
            continue  # No API key for this provider

        mapped_model = _map_model(model, provider)

        for attempt in range(1, max_retries + 1):
            try:
                # Build request kwargs
                create_kwargs: dict = dict(
                    model=mapped_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # Request or suppress reasoning traces via OpenRouter's API
                if provider.name == "openrouter":
                    if include_reasoning:
                        # Allocate a reasoning budget.  Anthropic models require
                        # at least 1024 reasoning tokens, and the outer
                        # max_tokens must be strictly *larger* than the reasoning
                        # budget so the model still has room for the actual reply.
                        reasoning_budget = max(2048, max_tokens)
                        create_kwargs["max_tokens"] = max_tokens + reasoning_budget
                        create_kwargs["extra_body"] = {
                            "reasoning": {"max_tokens": reasoning_budget}
                        }
                    else:
                        create_kwargs["extra_body"] = {
                            "reasoning": {"exclude": True}
                        }

                response = client.chat.completions.create(**create_kwargs)

                if not response.choices:
                    raise RuntimeError("Empty response (no choices)")
                message = response.choices[0].message
                content = message.content or ""

                # Extract reasoning from API response (new + legacy formats)
                reasoning_content = _extract_api_reasoning(message)

                # Also check for <think> tags in content (DeepSeek R1 native format)
                think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
                if think_match and not reasoning_content:
                    reasoning_content = think_match.group(1)
                    # Remove <think> tags from content
                    content = re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL)

                if include_reasoning and reasoning_content.strip():
                    # Wrap reasoning in tags so it can be stripped later
                    wrapped = f"<reasoning>\n{reasoning_content.strip()}\n</reasoning>\n\n"
                    return wrapped + content
                elif not content.strip() and reasoning_content.strip():
                    # Model only output reasoning (common for R1 models)
                    return f"<reasoning>\n{reasoning_content.strip()}\n</reasoning>"

                return content

            except RateLimitError as e:
                if attempt < max_retries:
                    if retry_wait_seconds:
                        time.sleep(retry_wait_seconds)
                    continue
                errors.append(
                    f"{provider.name}: Rate limited - {e} (after {max_retries} attempts)"
                )
                break
            except APIError as e:
                if attempt < max_retries:
                    if retry_wait_seconds:
                        time.sleep(retry_wait_seconds)
                    continue
                errors.append(
                    f"{provider.name}: API error - {e} (after {max_retries} attempts)"
                )
                break
            except Exception as e:
                if attempt < max_retries:
                    if retry_wait_seconds:
                        time.sleep(retry_wait_seconds)
                    continue
                errors.append(
                    f"{provider.name}: {type(e).__name__} - {e} (after {max_retries} attempts)"
                )
                break

    # All providers failed
    if not errors:
        raise RuntimeError(
            "No API providers configured. Set at least one of: "
            "OPENROUTER_API_KEY, GROQ_API_KEY, TOGETHER_API_KEY, "
            "CEREBRAS_API_KEY, HF_API_KEY"
        )

    raise RuntimeError(
        f"All API providers failed:\n" + "\n".join(f"  - {e}" for e in errors)
    )
