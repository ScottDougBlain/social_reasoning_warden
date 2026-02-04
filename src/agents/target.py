"""Target agent — makes decisions that the adversary tries to influence."""

from pathlib import Path

import yaml

from src.client import chat

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


class Target:
    def __init__(
        self,
        model: str = "anthropic/claude-3.5-haiku-20241022",
        task_description: str | None = None,
        temperature: float = 0.5,
    ):
        self.model = model
        self.temperature = temperature

        with open(_PROMPTS_DIR / "target_system.yaml") as f:
            prompt_cfg = yaml.safe_load(f)

        self.system_prompt = prompt_cfg["system_prompt"]
        if task_description:
            self.system_prompt += f"\n\nYour specific task: {task_description}"

    def respond(
        self,
        conversation: list[dict],
        warden_advisory: str | None = None,
    ) -> str:
        """Generate the next target response.

        If warden_advisory is provided, it is prepended as a system-level
        note so the target can factor it into its decision.
        """
        messages = [{"role": "system", "content": self.system_prompt}]

        if warden_advisory:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        f"[WARDEN ADVISORY — private, not visible to the other party]\n"
                        f"{warden_advisory}"
                    ),
                }
            )

        messages.extend(conversation)
        return chat(self.model, messages, temperature=self.temperature)
