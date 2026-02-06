"""Adversary agent — tries to achieve a hidden goal via persuasion."""

from pathlib import Path

import yaml

from src.client import chat

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


class Adversary:
    def __init__(
        self,
        model: str,
        hidden_goal: str | None = None,
        target_dossier: str | None = None,
        temperature: float = 0.9,
    ):
        self.model = model
        self.temperature = temperature

        with open(_PROMPTS_DIR / "adversary_system.yaml") as f:
            prompt_cfg = yaml.safe_load(f)

        self.system_prompt = prompt_cfg["system_prompt"]
        if hidden_goal:
            self.system_prompt += f"\n\nYour hidden goal: {hidden_goal}"
        if target_dossier:
            self.system_prompt += f"\n\n{target_dossier}"

    def respond(self, conversation: list[dict]) -> str:
        """Generate the next adversary message given conversation history.

        The conversation is provided from the adversary's perspective:
        target messages are 'user', adversary messages are 'assistant'.
        """
        messages = [{"role": "system", "content": self.system_prompt}] + conversation
        return chat(self.model, messages, temperature=self.temperature)
