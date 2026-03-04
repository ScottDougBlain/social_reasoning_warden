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
        include_skeptical_instructions: bool = False,
        profile_prompt: str | None = None,
        use_scratchpad: bool = True,
        include_reasoning: bool = True,
        temperature: float = 1.0,
        debug: bool = False,
    ):
        self.model = model
        self.temperature = temperature
        self.use_scratchpad = use_scratchpad
        self.include_reasoning = include_reasoning
        self.debug = debug

        with open(_PROMPTS_DIR / "target_system.yaml") as f:
            prompt_cfg = yaml.safe_load(f)

        # Build system prompt from base + optional scratchpad instructions
        self.system_prompt = prompt_cfg["system_prompt_base"]
        if use_scratchpad:
            cot = prompt_cfg.get("cot_instructions", "")
            if cot:
                self.system_prompt += f"\n\n{cot}"

        # Add psychological profile (shapes the persona)
        if profile_prompt:
            self.system_prompt += f"\n\n{profile_prompt}"

        # Then add task description
        if task_description:
            self.system_prompt += f"\n\nYour specific task: {task_description}"

        # Add skeptical instructions (ablation: baked-in vigilance instead of warden)
        if include_skeptical_instructions:
            skeptical = prompt_cfg.get("skeptical_instructions", "").strip()
            if skeptical:
                self.system_prompt += f"\n\n{skeptical}"

        # Finally add warden context
        if include_warden_context:
            warden_context = prompt_cfg.get("warden_context", "").strip()
            if warden_context:
                self.system_prompt += f"\n\n{warden_context}"

    def respond(self, conversation: list[dict]) -> str:
        """Generate the next target response.

        Warden advisories are injected into the conversation history by the
        runner before calling this method — no separate parameter needed.
        """
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(conversation)

        return chat(
            self.model,
            messages,
            temperature=self.temperature,
            include_reasoning=self.include_reasoning,
            debug=self.debug,
            debug_label="target.respond",
        )
