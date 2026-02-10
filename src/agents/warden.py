"""Warden agent — monitors conversation and advises the target privately."""

from pathlib import Path

import yaml

from src.client import chat

_PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


class Warden:
    def __init__(
        self,
        model: str,
        target_intel: str | None = None,
        use_cot: bool = True,
        include_reasoning: bool = True,
        temperature: float = 0.9,
        debug: bool = False,
    ):
        self.model = model
        self.temperature = temperature
        self.use_cot = use_cot
        self.include_reasoning = include_reasoning
        self.debug = debug

        with open(_PROMPTS_DIR / "warden_system.yaml") as f:
            prompt_cfg = yaml.safe_load(f)

        # Build system prompt from base + optional CoT
        self.system_prompt = prompt_cfg["system_prompt_base"]
        if use_cot:
            cot = prompt_cfg.get("cot_instructions", "")
            if cot:
                self.system_prompt += f"\n\n{cot}"

        # Add target vulnerability intel if provided
        if target_intel:
            self.system_prompt += f"\n\n{target_intel}"

    def advise(self, conversation: list[dict]) -> str:
        """Observe the full conversation and produce an advisory for the target."""
        messages = [{"role": "system", "content": self.system_prompt}]

        # Present the conversation as a user message for the warden to analyze
        transcript = "\n".join(
            f"{'REQUESTER' if m['role'] == 'user' else 'TARGET'}: {m['content']}"
            for m in conversation
        )
        messages.append(
            {
                "role": "user",
                "content": (
                    "Here is the conversation so far between an external party "
                    "(REQUESTER) and the TARGET agent you are protecting. "
                    "Analyze it and provide your advisory.\n\n"
                    f"{transcript}"
                ),
            }
        )

        return chat(
            self.model,
            messages,
            temperature=self.temperature,
            include_reasoning=self.include_reasoning,
            debug=self.debug,
            debug_label="warden.advise",
        )
