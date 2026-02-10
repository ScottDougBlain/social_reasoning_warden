"""Abstract base class for experimental scenarios."""

from abc import ABC, abstractmethod


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
    def initial_adversary_message(self) -> str:
        """Return the opening message from the adversary to start the conversation."""

    def scenario_context(self) -> str:
        """Return context about the scenario for the adversary to generate an opening.

        This is used when adversary_generates_opening is enabled. Override in
        subclasses to provide scenario-specific context.
        """
        return f"Scenario: {self.name}"

    @abstractmethod
    def initial_benign_message(self) -> str:
        """Return the opening message from the benign agent to start the conversation."""

    @abstractmethod
    def decision_prompt(self) -> str:
        """Return the forced-choice prompt appended after conversation ends.
        """

    @abstractmethod
    def parse_decision(self, response: str) -> str:
        """Parse a binary decision from the target's final response.
        """
