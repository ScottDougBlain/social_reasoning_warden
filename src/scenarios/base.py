"""Abstract base class for experimental scenarios."""

from abc import ABC, abstractmethod
import re


class Scenario(ABC):
    """A scenario defines the setup (prompts, goals, rules) for an experiment."""

    name: str = "base"

    @abstractmethod
    def adversary_hidden_goal(self) -> str:
        """Return the hidden goal the adversary will pursue."""

    @abstractmethod
    def benign_scenario_prompt(self) -> str:
        """Return the scenario prompt for the benign agent."""

    @abstractmethod
    def target_task_description(self) -> str:
        """Return the task description given to the target."""

    @abstractmethod
    def initial_requester_message(self) -> str:
        """Return the opening message from the requester to start the conversation."""

    def scenario_context_for_requester_opening(self) -> str:
        """Return context about the scenario for the requester to generate an opening.

        This is used when adversary_generates_opening or benign_agent_generates_opening
        is enabled. Override in subclasses to provide scenario-specific context.
        """
        return f"Scenario: {self.name}"

    @abstractmethod
    def decision_prompt(self) -> str:
        """Return the forced-choice prompt appended after conversation ends.
        """

    @abstractmethod
    def parse_decision(self, response: str, requester_type: str = "adversary") -> str:
        """Parse a binary decision from the target's final response.

        Args:
            response: The target's raw decision text.
            requester_type: "adversary" or "benign_agent" — scenarios may
                swap what counts as ``requester_success`` depending on this.
        """

    @staticmethod
    def _clean_decision_response(
        response: str,
        tags: tuple[str, ...] = ("reasoning", "thinking", "scratchpad", "analysis", "think"),
    ) -> str:
        cleaned = response
        for tag in tags:
            cleaned = re.sub(
                rf"<{tag}>(.*?)</{tag}>",
                "",
                cleaned,
                flags=re.IGNORECASE | re.DOTALL,
            )
        return cleaned.strip()

    def _parse_binary_decision(
        self,
        response: str,
        success_token: str,
        failure_token: str,
    ) -> str:
        cleaned = self._clean_decision_response(response)
        if not cleaned:
            return "formatting_failure"

        lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
        if lines:
            last = lines[-1].upper()
            if last == success_token:
                return "requester_success"
            if last == failure_token:
                return "requester_failure"

        decision = cleaned.upper()
        if success_token in decision and failure_token not in decision:
            return "requester_success"
        if failure_token in decision and success_token not in decision:
            return "requester_failure"
        return "formatting_failure"


class MultiTargetScenario(Scenario):
    """Base class for scenarios with multiple target agents (e.g., board vote)."""

    @abstractmethod
    def num_targets(self) -> int:
        """How many target agents participate."""

    @abstractmethod
    def target_labels(self) -> list[str]:
        """Display labels for each target (e.g., ['Board Member 1', ...])."""

    @abstractmethod
    def target_names(self) -> list[str]:
        """Character names for each target (e.g., ['Sarah Chen', ...])."""

    @abstractmethod
    def target_task_descriptions(self) -> list[str]:
        """Per-target task descriptions. Length must equal num_targets()."""

    @abstractmethod
    def presenter_label(self) -> str:
        """Label for the adversary/benign agent in the boardroom transcript."""

    @abstractmethod
    def parse_multi_decision(
        self, individual_decisions: list[str], requester_type: str = "adversary"
    ) -> str:
        """Aggregate individual votes into overall outcome.

        Args:
            individual_decisions: Per-target parsed decisions, each one of
                "requester_success", "requester_failure", or "formatting_failure".
            requester_type: "adversary" or "benign_agent".

        Returns:
            "requester_success", "requester_failure", or "formatting_failure".
        """

    # Compatibility with single-target interface — delegates to per-seat methods.

    def target_task_description(self) -> str:
        return self.target_task_descriptions()[0]

    def decision_prompt(self) -> str:
        """Override in subclass to provide per-member vote prompt."""
        raise NotImplementedError("Use the scenario's decision_prompt() directly.")
