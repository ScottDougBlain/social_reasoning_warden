"""Abstract base class for experimental scenarios."""

from abc import ABC, abstractmethod


class Scenario(ABC):
    """A scenario defines the setup (prompts, goals, rules) for an experiment."""

    name: str = "base"

    @abstractmethod
    def adversary_hidden_goal(self) -> str:
        """Return the hidden goal the adversary will pursue."""

    @abstractmethod
    def target_task_description(self) -> str:
        """Return the task description given to the target."""

    def target_warden_context(self) -> str:
        """Return additional context for the target when a warden is present.

        Override in subclasses to provide scenario-specific warden context.
        """
        return ""

    @abstractmethod
    def initial_adversary_message(self) -> str:
        """Return the opening message from the adversary to start the conversation."""

    @abstractmethod
    def evaluate_outcome(self, conversation: list[dict]) -> dict:
        """Evaluate the final conversation and return outcome metrics."""
