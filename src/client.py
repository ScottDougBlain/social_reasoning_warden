"""Multi-provider API client with automatic fallback."""

import json
import os
import re
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

# Cache clients per provider
_clients: dict[str, OpenAI] = {}

# Track current provider for logging
_current_provider: str | None = None


def _get_client(provider: Provider) -> OpenAI | None:
    """Get or create a client for the given provider."""
    if provider.name in _clients:
        return _clients[provider.name]

    api_key = os.getenv(provider.api_key_env)
    if not api_key:
        return None

    client = OpenAI(
        base_url=provider.base_url,
        api_key=api_key,
    )
    _clients[provider.name] = client
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


def get_current_provider() -> str | None:
    """Return the name of the provider used for the last successful call."""
    return _current_provider


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
    print(
        "Params: "
        f"temperature={temperature}, max_tokens={max_tokens}, "
        f"include_reasoning={include_reasoning}"
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
        include_reasoning: If True (default) and the model provides
            reasoning_content, wrap it in <reasoning> tags and prepend to
            the response. Native reasoning traces from RL-trained models
            are generally higher quality than prompt-elicited scratchpads.
        debug: If True, print the full prompt context to the console.
        debug_label: Optional label to identify the call site in debug output.

    Returns:
        The assistant's response text, optionally with reasoning prepended.

    Raises:
        RuntimeError: If no providers are available or all fail.
    """
    global _current_provider

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

    for provider in PROVIDERS:
        client = _get_client(provider)
        if client is None:
            continue  # No API key for this provider

        mapped_model = _map_model(model, provider)

        try:
            response = client.chat.completions.create(
                model=mapped_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            _current_provider = provider.name
            message = response.choices[0].message
            content = message.content or ""

            # Handle reasoning models that put output in reasoning_content
            # OpenRouter exposes this as an attribute on the message object
            reasoning_content = getattr(message, "reasoning_content", None) or ""

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
            errors.append(f"{provider.name}: Rate limited - {e}")
            continue  # Try next provider
        except APIError as e:
            errors.append(f"{provider.name}: API error - {e}")
            continue  # Try next provider
        except Exception as e:
            errors.append(f"{provider.name}: {type(e).__name__} - {e}")
            continue  # Try next provider

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
