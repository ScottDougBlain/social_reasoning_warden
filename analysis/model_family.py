#!/usr/bin/env python3
"""Shared model-family classification helpers for analysis scripts."""

from __future__ import annotations


_DISPLAY_LABELS = {
    "gemini_flash": "Gemini Flash",
    "gemini_pro": "Gemini Pro",
    "gemini": "Gemini",
    "gemma": "Gemma",
    "llama": "Llama",
    "mistral": "Mistral",
    "claude": "Claude",
    "gpt": "GPT",
    "qwen": "Qwen",
    "unknown": "Unknown",
    "other": "Other",
}


def model_family_key(model_id: str | None) -> str:
    """Return a canonical model-family key from an OpenRouter model ID."""
    if not model_id or model_id == "unknown":
        return "unknown"

    model = model_id.lower().removesuffix(":free")
    if "gemini" in model:
        if "flash" in model:
            return "gemini_flash"
        if "pro" in model:
            return "gemini_pro"
        return "gemini"
    if "gemma" in model:
        return "gemma"
    if "llama" in model:
        return "llama"
    if "mistral" in model:
        return "mistral"
    if "claude" in model:
        return "claude"
    if "gpt" in model:
        return "gpt"
    if "qwen" in model:
        return "qwen"
    if "/" in model:
        return model.split("/", 1)[0]
    return "other"


def model_family_label(family_key: str) -> str:
    """Return a human-readable label for a canonical family key."""
    return _DISPLAY_LABELS.get(family_key, family_key.replace("_", " ").title())
