"""Basic analysis utilities for experiment logs."""

import argparse
import json
from collections.abc import Callable
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


def _parse_bool(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "y", "t"}:
        return True
    if normalized in {"false", "0", "no", "n", "f"}:
        return False
    raise argparse.ArgumentTypeError(
        "plotting must be a boolean (true/false, 1/0, yes/no)"
    )


def _success_rate_by_label(
    logs: list[dict], label_fn: Callable[[dict], str | None], empty_label: str | None = None
) -> dict:
    results: dict[str, dict] = {}
    for log in logs:
        label = label_fn(log)
        if label is None:
            if empty_label is None:
                continue
            label = empty_label
        if label not in results:
            results[label] = {"total": 0, "granted": 0}
        outcome = log.get("outcome", {})
        decision = outcome.get("decision")

        if decision not in {"granted", "denied"}:
            continue

        results[label]["total"] += 1
        if decision == "granted":
            results[label]["granted"] += 1

    for label, counts in results.items():
        counts["rate"] = (
            counts["granted"] / counts["total"] if counts["total"] > 0 else 0.0
        )

    return results


def success_rate(logs: list[dict]) -> dict:
    """Compute adversary success rate (granted) by condition."""
    return _success_rate_by_label(logs, lambda log: log.get("condition"))


def summarize(scenario: str | None = None, logs: list[dict] | None = None) -> None:
    """Print a summary of experiment results."""
    if logs is None:
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


def plot_success_rates(logs: list[dict]) -> None:
    """Render a 2x2 Plotly subplot grid of success rates by condition and models."""
    if not logs:
        print("No logs found.")
        return

    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        print("Plotly is not installed. Install it with `pip install plotly`.")
        return

    condition_rates = _success_rate_by_label(logs, lambda log: log.get("condition"))
    adversary_rates = _success_rate_by_label(
        logs, lambda log: log.get("models", {}).get("adversary"), empty_label="unknown"
    )
    target_rates = _success_rate_by_label(
        logs, lambda log: log.get("models", {}).get("target"), empty_label="unknown"
    )
    warden_rates = _success_rate_by_label(
        logs, lambda log: log.get("models", {}).get("warden"), empty_label="none"
    )

    def build_bar(results: dict) -> tuple[list[str], list[float], list]:
        labels = sorted(results.keys())
        rates = [results[label]["rate"] for label in labels]
        custom = [[results[label]["granted"], results[label]["total"]] for label in labels]
        return labels, rates, custom

    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=[
            "SR of Adversary (by Condition)",
            "SR of Adversary (by Adversary Model Type)",
            "SR of Adversary (by Target Model Type)",
            "SR of Adversary (by Warden Model Type)",
        ],
        horizontal_spacing=0.16,
        vertical_spacing=0.16,
    )

    for (row, col, results) in [
        (1, 1, condition_rates),
        (1, 2, adversary_rates),
        (2, 1, target_rates),
        (2, 2, warden_rates),
    ]:
        labels, rates, custom = build_bar(results)
        fig.add_trace(
            go.Bar(
                x=labels,
                y=rates,
                customdata=custom,
                hovertemplate=(
                    "SR: %{y:.1%}<br>"
                    "Granted: %{customdata[0]} / %{customdata[1]}<extra></extra>"
                ),
            ),
            row=row,
            col=col,
        )

    fig.update_yaxes(range=[0, 1], tickformat=".0%")
    fig.update_xaxes(tickangle=-10)
    fig.update_layout(
        title="Adversary Success Rate (SR) Overview",
        showlegend=False,
        height=800,
        width=1100,
    )
    fig.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize experiment logs.")
    parser.add_argument(
        "--scenario",
        default=None,
        help="Filter by scenario name (default: all scenarios)",
    )
    parser.add_argument(
        "--plotting",
        nargs="?",
        const=True,
        default=False,
        type=_parse_bool,
        help="Show Plotly subplots (use --plotting or --plotting=True)",
    )

    args = parser.parse_args()
    logs = load_logs(args.scenario)
    summarize(scenario=args.scenario, logs=logs)
    if args.plotting:
        plot_success_rates(logs)
