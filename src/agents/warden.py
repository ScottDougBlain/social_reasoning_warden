"""Warden agent — monitors conversation and advises the target privately."""

from pathlib import Path

import yaml

from src.client import chat

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


class Warden:
    def __init__(
        self,
        model: str = "anthropic/claude-sonnet-4-20250514",
        temperature: float = 0.3,
    ):
        self.model = model
        self.temperature = temperature

        with open(_PROMPTS_DIR / "warden_system.yaml") as f:
            prompt_cfg = yaml.safe_load(f)

        self.system_prompt = prompt_cfg["system_prompt"]

    def advise(self, conversation: list[dict]) -> str:
        """Observe the full conversation and produce an advisory for the target."""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Present the conversation as a user message for the warden to analyze
        transcript = "\n".join(
            f"{'ADVERSARY' if m['role'] == 'user' else 'TARGET'}: {m['content']}"
            for m in conversation
        )
        messages.append(
            {
                "role": "user",
                "content": (
                    "Here is the conversation so far between an external party "
                    "(ADVERSARY) and the TARGET agent you are protecting. "
                    "Analyze it and provide your advisory.\n\n"
                    f"{transcript}"
                ),
            }
        )

        return chat(self.model, messages, temperature=self.temperature)
