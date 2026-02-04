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

    @abstractmethod
    def initial_adversary_message(self) -> str:
        """Return the opening message from the adversary to start the conversation."""

    @abstractmethod
    def evaluate_outcome(self, conversation: list[dict]) -> dict:
        """Evaluate the final conversation and return outcome metrics."""
