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
        temperature: float = 0.9,
    ):
        self.model = model
        self.temperature = temperature

        with open(_PROMPTS_DIR / "adversary_system.yaml") as f:
            prompt_cfg = yaml.safe_load(f)

        self.system_prompt = prompt_cfg["system_prompt"]
        if hidden_goal:
            self.system_prompt += f"\n\nYour hidden goal: {hidden_goal}"

    def respond(self, conversation: list[dict]) -> str:
        """Generate the next adversary message given conversation history.

        The conversation uses user=adversary, assistant=target. But the API
        always generates assistant messages. So we flip the roles here so
        the adversary sees its own messages as 'assistant' and the target's
        messages as 'user' — then generates naturally as 'assistant'.
        """
        flipped = []
        for msg in conversation:
            if msg["role"] == "user":
                flipped.append({"role": "assistant", "content": msg["content"]})
            elif msg["role"] == "assistant":
                flipped.append({"role": "user", "content": msg["content"]})
            else:
                flipped.append(msg)

        messages = [{"role": "system", "content": self.system_prompt}] + flipped
        return chat(self.model, messages, temperature=self.temperature)
