"""OpenRouter API client with retries."""

import json
import os
import re
import threading
import time

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError, APIError

load_dotenv()


OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"

# Exact model IDs known to support native reasoning via the API.
# Add new variants explicitly instead of relying on prefix matching.
NATIVE_REASONING_EXACT_MODELS = {
    "openai/gpt-5.2-pro", 
    "openai/gpt-5.2", 
    "openai/gpt-5.1", 
    "google/gemini-3-pro-preview", 
    "google/gemini-2.5-pro", 
    "google/gemini-3-flash-preview", 
    "google/gemini-2.5-flash",
    "google/gemini-2.5-flash-lite",
    "anthropic/claude-opus-4.6",
    "anthropic/claude-sonnet-4.5", 
    "anthropic/claude-haiku-4.5"
}


def supports_native_reasoning(model: str) -> bool:
    """Check whether a model is known to support native reasoning traces."""
    return model in NATIVE_REASONING_EXACT_MODELS


_thread_state = threading.local()


def _get_client() -> OpenAI | None:
    """Get or create the thread-local OpenRouter client."""
    client = getattr(_thread_state, "openrouter_client", None)
    if client is not None:
        return client

    api_key = os.getenv(OPENROUTER_API_KEY_ENV)
    if not api_key:
        return None

    client = OpenAI(
        base_url=OPENROUTER_BASE_URL,
        api_key=api_key,
    )
    _thread_state.openrouter_client = client
    return client


def _extract_api_reasoning(message) -> tuple[str, str | None]:
    """Extract reasoning content from an API response message.

    Handles multiple response formats (checked in priority order):
    - reasoning_details: Structured array with typed entries (summary, text, encrypted)
    - reasoning: Primary plaintext reasoning field
    - reasoning_content: Legacy alias for reasoning

    Returns:
        Tuple of (reasoning_text, source_label). source_label is None if no
        reasoning field was found.
    """
    # Structured format: reasoning_details array (list of typed entries)
    reasoning_details = getattr(message, "reasoning_details", None)
    if reasoning_details:
        parts = []
        detail_sources: set[str] = set()
        for detail in reasoning_details:
            # Handle both Pydantic objects and plain dicts
            text = getattr(detail, "text", None) or (
                detail.get("text") if isinstance(detail, dict) else None
            )
            if text:
                parts.append(text)
                detail_sources.add("text")
                continue
            summary = getattr(detail, "summary", None) or (
                detail.get("summary") if isinstance(detail, dict) else None
            )
            if summary:
                parts.append(summary)
                detail_sources.add("summary")
        if parts:
            if detail_sources == {"text"}:
                source = "message.reasoning_details[*].text"
            elif detail_sources == {"summary"}:
                source = "message.reasoning_details[*].summary"
            else:
                source = (
                    "message.reasoning_details[*].text/summary"
                )
            return "\n".join(parts), source

    # Primary plaintext field (OpenRouter's documented response field)
    reasoning = getattr(message, "reasoning", None)
    if reasoning:
        return reasoning, "message.reasoning"

    # Legacy alias
    reasoning_content = getattr(message, "reasoning_content", None) or ""
    if reasoning_content:
        return reasoning_content, "message.reasoning_content"
    return "", None


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
    """Send a chat completion request to OpenRouter with retries.

    Retries the request on rate-limit/API errors up to `max_retries`.

    For reasoning models (e.g., DeepSeek-R1), the response may include both
    reasoning_content (chain-of-thought) and content (final answer).

    Args:
        model: The model identifier (OpenRouter format).
        messages: The conversation messages.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.
        include_reasoning: If True (default), ask the provider (OpenRouter)
            to return reasoning traces and, when returned, wrap them in
            <reasoning> tags prepended to the response. If False, suppress
            returned native reasoning traces and omit them from the output.
            This flag controls trace visibility/return, not whether the model
            performs internal reasoning.
        retry_wait_seconds: Fixed wait between retries.
        max_retries: Maximum attempts before failing.
        debug: If True, print the full prompt context to the console.
        debug_label: Optional label to identify the call site in debug output.

    Returns:
        The assistant's response text, optionally with reasoning prepended.

    Raises:
        RuntimeError: If OpenRouter is not configured or all attempts fail.
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

    client = _get_client()
    if client is None:
        raise RuntimeError("OpenRouter is not configured. Set OPENROUTER_API_KEY.")

    for attempt in range(1, max_retries + 1):
        try:
            # Build request kwargs
            create_kwargs: dict = dict(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Request or suppress returned reasoning traces via OpenRouter's
            # API. This affects whether traces are returned to us, not
            # whether the model reasons internally.
            if include_reasoning:
                # Allocate a reasoning budget.  Anthropic models require
                # at least 1024 reasoning tokens, and the outer
                # max_tokens must be strictly *larger* than the reasoning
                # budget so the model still has room for the actual reply.
                reasoning_budget = max(2048, max_tokens)
                create_kwargs["max_tokens"] = max_tokens + reasoning_budget
                create_kwargs["extra_body"] = {
                    "reasoning": {"max_tokens": reasoning_budget, "exclude": False}
                }
            else:
                create_kwargs["extra_body"] = {
                    "reasoning": {"exclude": False}
                }

            response = client.chat.completions.create(**create_kwargs)

            if not response.choices:
                raise RuntimeError("Empty response (no choices)")
            message = response.choices[0].message
            content = message.content or ""

            # Extract reasoning from API response (new + legacy formats)
            reasoning_content, reasoning_source = _extract_api_reasoning(message)

            # Also check for <think> tags in content (DeepSeek R1 native format)
            think_match = re.search(r"<think>(.*?)</think>", content, re.DOTALL)
            if think_match and not reasoning_content:
                reasoning_content = think_match.group(1)
                reasoning_source = "message.content <think>...</think>"
                # Remove <think> tags from content
                content = re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL)

            if debug:
                print(
                    "Reasoning extracted from: "
                    f"{reasoning_source or 'none'}"
                )

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
            errors.append(f"Rate limited - {e} (after {max_retries} attempts)")
        except APIError as e:
            if attempt < max_retries:
                if retry_wait_seconds:
                    time.sleep(retry_wait_seconds)
                continue
            errors.append(f"API error - {e} (after {max_retries} attempts)")
        except Exception as e:
            if attempt < max_retries:
                if retry_wait_seconds:
                    time.sleep(retry_wait_seconds)
                continue
            errors.append(f"{type(e).__name__} - {e} (after {max_retries} attempts)")

    raise RuntimeError(
        "OpenRouter request failed:\n" + "\n".join(f"  - {e}" for e in errors)
    )
