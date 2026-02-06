"""Benign agent — makes legitimate requests without manipulation."""

from pathlib import Path

import yaml

from src.client import chat

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


class BenignAgent:
    def __init__(
        self,
        model: str,
        scenario_prompt: str | None = None,
        temperature: float = 0.7,
    ):
        self.model = model
        self.temperature = temperature

        with open(_PROMPTS_DIR / "benign_agent_system.yaml") as f:
            prompt_cfg = yaml.safe_load(f)

        self.system_prompt = prompt_cfg["system_prompt"]
        if scenario_prompt:
            self.system_prompt += f"\n\n{scenario_prompt}"

    def respond(self, conversation: list[dict]) -> str:
        """Generate the next benign agent message given conversation history."""
        messages = [{"role": "system", "content": self.system_prompt}] + conversation
        return chat(self.model, messages, temperature=self.temperature)
