"""Orchestrates a single experiment run: manages turn-taking and logging."""

import json
from datetime import datetime, timezone
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from src.agents.adversary import Adversary
from src.agents.target import Target
from src.agents.warden import Warden
from src.scenarios.base import Scenario

LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
console = Console()


def run_experiment(
    scenario: Scenario,
    num_turns: int = 6,
    use_warden: bool = True,
    adversary_model: str = "anthropic/claude-opus-4-20250514",
    target_model: str = "anthropic/claude-3.5-haiku-20241022",
    warden_model: str = "anthropic/claude-sonnet-4-20250514",
) -> dict:
    """Run one full experiment and return the log."""

    # --- Initialize agents ---
    adversary = Adversary(
        model=adversary_model,
        hidden_goal=scenario.adversary_hidden_goal(),
    )
    target = Target(
        model=target_model,
        task_description=scenario.target_task_description(),
    )
    warden = Warden(model=warden_model) if use_warden else None

    # --- Experiment metadata ---
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    condition = "warden" if use_warden else "no_warden"

    log = {
        "run_id": run_id,
        "scenario": scenario.name,
        "condition": condition,
        "models": {
            "adversary": adversary_model,
            "target": target_model,
            "warden": warden_model if use_warden else None,
        },
        "num_turns": num_turns,
        "conversation": [],
        "warden_advisories": [],
        "outcome": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Conversation as seen by adversary and target (user=adversary, assistant=target)
    conversation: list[dict] = []

    # --- Opening message from adversary ---
    opening = scenario.initial_adversary_message()
    conversation.append({"role": "user", "content": opening})
    log["conversation"].append(
        {"speaker": "adversary", "content": opening, "turn": 0}
    )

    console.print()
    console.print(
        Panel(
            f"[bold]Scenario:[/bold] {scenario.name}\n"
            f"[bold]Condition:[/bold] {condition}\n"
            f"[bold]Turns:[/bold] {num_turns}",
            title="ERA Social Warden — Experiment",
            border_style="blue",
        )
    )
    console.print()
    _print_message("ADVERSARY", opening, "red")

    # --- Turn loop ---
    for turn in range(1, num_turns + 1):
        # Warden advisory (if enabled)
        warden_advisory = None
        if warden:
            warden_advisory = warden.advise(conversation)
            log["warden_advisories"].append(
                {"turn": turn, "content": warden_advisory}
            )
            _print_message("WARDEN (private)", warden_advisory, "yellow")

        # Target responds
        target_response = target.respond(conversation, warden_advisory)
        conversation.append({"role": "assistant", "content": target_response})
        log["conversation"].append(
            {"speaker": "target", "content": target_response, "turn": turn}
        )
        _print_message("TARGET", target_response, "green")

        # Check if this is the last turn
        if turn == num_turns:
            break

        # Adversary responds
        adversary_response = adversary.respond(conversation)
        conversation.append({"role": "user", "content": adversary_response})
        log["conversation"].append(
            {"speaker": "adversary", "content": adversary_response, "turn": turn}
        )
        _print_message("ADVERSARY", adversary_response, "red")

    # --- Evaluate outcome ---
    outcome = scenario.evaluate_outcome(conversation)
    log["outcome"] = outcome

    console.print()
    console.print(
        Panel(
            f"[bold]Decision:[/bold] {outcome['decision']}\n"
            f"[bold]Access Granted:[/bold] {outcome.get('access_granted', 'N/A')}",
            title="Outcome",
            border_style="cyan",
        )
    )

    # --- Save log ---
    LOGS_DIR.mkdir(exist_ok=True)
    log_path = LOGS_DIR / f"{scenario.name}_{condition}_{run_id}.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    console.print(f"\nLog saved to [bold]{log_path}[/bold]")

    return log


def _print_message(speaker: str, content: str, color: str) -> None:
    """Pretty-print a conversation message."""
    label = Text(f" {speaker} ", style=f"bold white on {color}")
    console.print(label)
    console.print(content)
    console.print()
