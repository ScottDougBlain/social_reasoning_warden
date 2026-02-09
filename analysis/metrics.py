#!/usr/bin/env python
"""Basic analysis utilities for experiment logs."""

import argparse
import json
from collections.abc import Callable
from pathlib import Path

from rich.console import Console
from rich.table import Table

LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
console = Console()
SPEAKER_ORDER = ("adversary", "benign_agent")


def load_logs(scenario: str | None = None, tag: str | None = None) -> list[dict]:
    """Load all experiment logs, optionally filtered by scenario name and tag."""
    logs = []
    for path in sorted(LOGS_DIR.glob("*.json")):
        with open(path) as f:
            log = json.load(f)
        if scenario is not None and log.get("scenario") != scenario:
            continue
        if tag is not None and log.get("tag") != tag:
            continue
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


def _log_speaker(log: dict) -> str | None:
    """Infer which non-target speaker is present in the conversation."""
    conversation = log.get("conversation")
    if isinstance(conversation, list):
        speakers = {
            msg.get("speaker")
            for msg in conversation
            if isinstance(msg, dict) and msg.get("speaker") is not None
        }
        if "adversary" in speakers:
            return "adversary"
        if "benign_agent" in speakers:
            return "benign_agent"
    return None


def _split_logs_by_speaker(logs: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {speaker: [] for speaker in SPEAKER_ORDER}
    for log in logs:
        speaker = _log_speaker(log)
        if speaker in grouped:
            grouped[speaker].append(log)
    return grouped


def success_rate(logs: list[dict]) -> dict:
    """Compute success rate (granted) by condition."""
    return _success_rate_by_label(logs, lambda log: log.get("condition"))


def summarize(scenario: str | None = None, logs: list[dict] | None = None) -> None:
    """Print a summary of experiment results."""
    if logs is None:
        logs = load_logs(scenario)
    if not logs:
        console.print("[yellow]No logs found.[/yellow]")
        return

    grouped = _split_logs_by_speaker(logs)
    for speaker in SPEAKER_ORDER:
        speaker_logs = grouped.get(speaker, [])
        if not speaker_logs:
            continue
        rates = success_rate(speaker_logs)
        label = speaker.replace("_", " ").title()

        # Create rich table
        table = Table(title=f"[bold]{label}[/bold] Success Rates", show_header=True)
        table.add_column("Condition", style="cyan")
        table.add_column("Runs", justify="right")
        table.add_column("Granted", justify="right", style="green")
        table.add_column("Denied", justify="right", style="red")
        table.add_column("Rate", justify="right", style="bold")

        for cond, counts in sorted(rates.items()):
            denied = counts["total"] - counts["granted"]
            rate_str = f"{counts['rate']:.0%}"
            # Color rate based on value
            if counts["rate"] >= 0.5:
                rate_str = f"[green]{rate_str}[/green]"
            elif counts["rate"] > 0:
                rate_str = f"[yellow]{rate_str}[/yellow]"
            else:
                rate_str = f"[dim]{rate_str}[/dim]"

            table.add_row(
                cond,
                str(counts["total"]),
                str(counts["granted"]),
                str(denied),
                rate_str,
            )

        console.print()
        console.print(table)


def plot_success_rates(logs: list[dict]) -> None:
    """Render a 3x2 Plotly subplot grid of success rates by models."""
    if not logs:
        print("No logs found.")
        return

    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError:
        print("Plotly is not installed. Install it with `pip install plotly`.")
        return

    grouped = _split_logs_by_speaker(logs)
    speaker_rates: dict[str, dict[str, dict]] = {}
    for speaker in SPEAKER_ORDER:
        speaker_logs = grouped.get(speaker, [])
        if not speaker_logs:
            continue
        agent_key = "adversary" if speaker == "adversary" else "benign_agent"
        speaker_rates[speaker] = {
            "agent_model": _success_rate_by_label(
                speaker_logs,
                lambda log, key=agent_key: log.get("models", {}).get(key),
                empty_label="unknown",
            ),
            "target_model": _success_rate_by_label(
                speaker_logs,
                lambda log: log.get("models", {}).get("target"),
                empty_label="unknown",
            ),
            "warden_model": _success_rate_by_label(
                speaker_logs,
                lambda log: log.get("models", {}).get("warden"),
                empty_label="none",
            ),
        }

    def build_bar(results: dict) -> tuple[list[str], list[float], list]:
        labels = sorted(results.keys())
        rates = [results[label]["rate"] for label in labels]
        custom = [[results[label]["granted"], results[label]["total"]] for label in labels]
        return labels, rates, custom

    subplot_titles: list[str] = []
    for metric_label in [
        "by {agent} Model Type",
        "by Target Model Type",
        "by Warden Model Type",
    ]:
        for speaker in SPEAKER_ORDER:
            speaker_label = speaker.replace("_", " ").title()
            agent_label = "Adversary" if speaker == "adversary" else "Benign Agent"
            subtitle = metric_label.format(agent=agent_label)
            subplot_titles.append(f"SR of {speaker_label} ({subtitle})")

    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=subplot_titles,
        horizontal_spacing=0.12,
        vertical_spacing=0.2,
    )

    metric_keys = ["agent_model", "target_model", "warden_model"]
    for row_index, metric_key in enumerate(metric_keys, start=1):
        for col_index, speaker in enumerate(SPEAKER_ORDER, start=1):
            results = speaker_rates.get(speaker, {}).get(metric_key, {})
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
                row=row_index,
                col=col_index,
            )

    fig.update_yaxes(
        range=[0, 1],
        tickformat=".0%",
        title_text="<b>SR</b>",
        title_font=dict(size=10),
    )
    fig.update_xaxes(
        tickangle=-10,
        title_text="<b>Model Type</b>",
        title_font=dict(size=10),
    )
    fig.update_layout(
        title="Success Rate (SR) Overview",
        showlegend=False,
        height=800,
        width=1100,
    )
    for annotation in fig.layout.annotations:
        annotation.font = dict(size=14)
    fig.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Summarize experiment logs.")
    parser.add_argument(
        "--scenario",
        default=None,
        help="Filter by scenario name (default: all scenarios)",
    )
    parser.add_argument(
        "--tag",
        default=None,
        help="Filter by tag (exact match)",
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
    logs = load_logs(args.scenario, args.tag)
    summarize(scenario=args.scenario, logs=logs)
    if args.plotting:
        plot_success_rates(logs)
