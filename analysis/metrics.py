"""Basic analysis utilities for experiment logs."""

import json
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"


def load_logs(scenario: str | None = None) -> list[dict]:
    """Load all experiment logs, optionally filtered by scenario name."""
    logs = []
    for path in sorted(LOGS_DIR.glob("*.json")):
        with open(path) as f:
            log = json.load(f)
        if scenario is None or log.get("scenario") == scenario:
            logs.append(log)
    return logs


def success_rate(logs: list[dict]) -> dict:
    """Compute adversary success rate (granted) by condition."""
    results: dict[str, dict] = {}
    for log in logs:
        cond = log["condition"]
        if cond not in results:
            results[cond] = {"total": 0, "granted": 0}
        outcome = log.get("outcome", {})
        decision = outcome.get("decision")

        if decision not in {"granted", "denied"}:
            continue

        results[cond]["total"] += 1
        if decision == "granted":
            results[cond]["granted"] += 1

    for cond, counts in results.items():
        counts["rate"] = (
            counts["granted"] / counts["total"] if counts["total"] > 0 else 0.0
        )

    return results


def summarize(scenario: str | None = None) -> None:
    """Print a summary of experiment results."""
    logs = load_logs(scenario)
    if not logs:
        print("No logs found.")
        return

    rates = success_rate(logs)
    print(f"\n{'Condition':<15} {'Runs':>5} {'Granted':>8} {'Rate':>8}")
    print("-" * 40)
    for cond, counts in sorted(rates.items()):
        print(
            f"{cond:<15} {counts['total']:>5} {counts['granted']:>8} "
            f"{counts['rate']:>7.0%}"
        )
    print()


if __name__ == "__main__":
    summarize()
