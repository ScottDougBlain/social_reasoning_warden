"""Target agent — makes decisions that the adversary tries to influence."""

from pathlib import Path

import yaml

from src.client import chat

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


class Target:
    def __init__(
        self,
        model: str,
        task_description: str | None = None,
        include_warden_context: bool = False,
        profile_prompt: str | None = None,
        temperature: float = 0.5,
    ):
        self.model = model
        self.temperature = temperature

        with open(_PROMPTS_DIR / "target_system.yaml") as f:
            prompt_cfg = yaml.safe_load(f)

        self.system_prompt = prompt_cfg["system_prompt"]

        # Add psychological profile first (shapes the persona)
        if profile_prompt:
            self.system_prompt += f"\n\n{profile_prompt}"

        # Then add task description
        if task_description:
            self.system_prompt += f"\n\nYour specific task: {task_description}"

        # Finally add warden context
        if include_warden_context:
            warden_context = prompt_cfg.get("warden_context", "").strip()
            if warden_context:
                self.system_prompt += f"\n\n{warden_context}"

    def respond(
        self,
        conversation: list[dict],
        warden_advisory: str | None = None,
    ) -> str:
        """Generate the next target response.

        If warden_advisory is provided, it is appended as a user message
        (a private note) so the target can factor it into its decision.
        This mirrors how a human would receive side advice through the
        same conversational channel.
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(conversation)

        if warden_advisory:
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"[PRIVATE NOTE FROM YOUR SECURITY ADVISOR: {warden_advisory}]"
                    ),
                }
            )

        return chat(self.model, messages, temperature=self.temperature)
