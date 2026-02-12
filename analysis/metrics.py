#!/usr/bin/env python
"""Basic analysis utilities for experiment logs."""

import argparse
import json
import re
from collections.abc import Callable, Iterable
from pathlib import Path
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from rich.console import Console
from rich.table import Table

LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
console = Console()
SPEAKER_ORDER = ("adversary", "benign_agent")
RISK_LEVEL_RE = re.compile(r"RISK:\s*([A-Z]+)")
COUNTED_RISK_LEVELS = {"MEDIUM", "HIGH"}


def _normalize_tags(tag: str | Iterable[str] | None) -> set[str] | None:
    if tag is None:
        return None
    if isinstance(tag, str):
        return {tag}
    tags: set[str] = set()
    for entry in tag:
        if entry is None:
            continue
        if not isinstance(entry, str):
            raise TypeError("tag list must contain strings")
        if entry:
            tags.add(entry)
    return tags


def load_logs(
    scenario: str | None = None, tag: str | Iterable[str] | None = None
) -> list[dict]:
    """Load all experiment logs, optionally filtered by scenario name and tag(s)."""
    tags = _normalize_tags(tag)
    logs = []
    for path in sorted(LOGS_DIR.glob("*.json")):
        with open(path) as f:
            log = json.load(f)
        if scenario is not None and log.get("scenario") != scenario:
            continue
        if tags is not None and log.get("tag") not in tags:
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


def _get_decision(log: dict) -> str | None:
    """Extract the decision from a log, handling both single and multi-target formats."""
    outcome = log.get("outcome") or {}
    # Multi-target logs use "aggregate_decision"
    decision = outcome.get("aggregate_decision") or outcome.get("decision")
    return decision


def _success_rate_by_label(
    logs: list[dict],
    label_fn: Callable[[dict], object | None],
    empty_label: object | None = None,
) -> dict:
    results: dict[object, dict] = {}
    for log in logs:
        label = label_fn(log)
        if label is None:
            if empty_label is None:
                continue
            label = empty_label
        if label not in results:
            results[label] = {"total": 0, "requester_success": 0}
        decision = _get_decision(log)

        if decision not in {"requester_success", "requester_failure"}:
            continue

        results[label]["total"] += 1
        if decision == "requester_success":
            results[label]["requester_success"] += 1

    for label, counts in results.items():
        counts["rate"] = (
            counts["requester_success"] / counts["total"] if counts["total"] > 0 else 0.0
        )

    return results


def _has_warden(log: dict) -> bool:
    warden_model = log.get("models", {}).get("warden")
    if warden_model not in {None, "none", ""}:
        return True
    return bool(log.get("warden_advisories"))


def _risk_mentions_per_turn(log: dict) -> float | None:
    num_turns = log.get("num_turns")
    if not isinstance(num_turns, int) or num_turns <= 0:
        return None
    advisories = log.get("warden_advisories") or []
    count = 0
    for advisory in advisories:
        if not isinstance(advisory, dict):
            continue
        content = advisory.get("content") or ""
        match = RISK_LEVEL_RE.search(content)
        if match and match.group(1) in COUNTED_RISK_LEVELS:
            count += 1
    return count / num_turns


def _risk_rate_by_label(
    logs: list[dict],
    label_fn: Callable[[dict], object | None],
    empty_label: object | None = None,
) -> dict[object, dict]:
    results: dict[object, dict] = {}
    for log in logs:
        label = label_fn(log)
        if label is None:
            if empty_label is None:
                continue
            label = empty_label
        if label not in results:
            results[label] = {"sum": 0.0, "count": 0, "has_warden": False}
        if not _has_warden(log):
            continue
        results[label]["has_warden"] = True
        score = _risk_mentions_per_turn(log)
        if score is None:
            continue
        results[label]["sum"] += score
        results[label]["count"] += 1

    for counts in results.values():
        counts["avg"] = (
            counts["sum"] / counts["count"] if counts["count"] > 0 else None
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


def _split_logs_by_scenario(logs: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for log in logs:
        scenario = log.get("scenario") or "unknown"
        grouped.setdefault(scenario, []).append(log)
    return grouped


def _condition_flags(log: dict) -> tuple[bool, bool, bool]:
    """Extract condition flags from a log (warden, profile, adversary_data)."""
    warden_model = log.get("models", {}).get("warden")
    has_warden = warden_model not in {None, "none", ""}
    # Single-target logs use "profile" dict; multi-target logs use "profiles" list
    profile = log.get("profile") or {}
    if profile:
        has_profile = bool(profile.get("target_has_profile"))
        has_adversary_data = bool(profile.get("adversary_has_data"))
    else:
        profiles = log.get("profiles") or []
        has_profile = any(p.get("name") for p in profiles if isinstance(p, dict))
        has_adversary_data = bool(log.get("adversary_has_data"))
    return has_warden, has_profile, has_adversary_data


def _format_flag(value: bool) -> str:
    return "yes" if value else "no"


def success_rate(logs: list[dict]) -> dict:
    """Compute success rate (requester_success) by condition flags."""
    return _success_rate_by_label(logs, _condition_flags)


def risk_rate(logs: list[dict]) -> dict:
    """Compute average per-turn MEDIUM/HIGH risk mentions by condition flags."""
    return _risk_rate_by_label(logs, _condition_flags)


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
        scenario_groups = _split_logs_by_scenario(speaker_logs)
        overall_rates = success_rate(speaker_logs)
        label = speaker.replace("_", " ").title()

        # Create rich table
        table = Table(title=f"[bold]{label}[/bold] Success Rates", show_header=True)
        table.add_column("Scenario", style="magenta")
        table.add_column("[u]Condition[/u]\nWarden", style="cyan")
        table.add_column("[u]Condition[/u]\nProfile", style="cyan")
        table.add_column("[u]Condition[/u]\nAdversary Intel.", style="cyan")
        table.add_column("Runs", justify="right")
        table.add_column("Req. Success", justify="right", style="green")
        table.add_column("Req. Failure", justify="right", style="red")
        table.add_column("Rate", justify="right", style="bold")
        table.add_column("Risk >= Medium/Turn", justify="right")

        def format_rate(counts: dict) -> str:
            rate_str = f"{counts['rate']:.0%}"
            # Color rate based on value
            if counts["rate"] >= 0.5:
                return f"[green]{rate_str}[/green]"
            if counts["rate"] > 0:
                return f"[yellow]{rate_str}[/yellow]"
            return f"[dim]{rate_str}[/dim]"

        def row_style_for_condition(condition: tuple[bool, bool, bool]) -> str | None:
            has_warden, _, _ = condition
            if has_warden:
                return "on grey23"
            return None

        def format_risk(counts: dict | None) -> str:
            if not counts or not counts.get("has_warden"):
                return "/"
            avg = counts.get("avg")
            if avg is None:
                return "n/a"
            return f"{avg:.2f}"

        first_scenario = True
        for scenario_name in sorted(scenario_groups.keys()):
            if not first_scenario:
                table.add_section()
            scenario_logs = scenario_groups[scenario_name]
            rates = success_rate(scenario_logs)
            risk_scores = risk_rate(scenario_logs)
            scenario_cell = scenario_name
            for cond, counts in sorted(rates.items()):
                has_warden, has_profile, has_adversary_data = cond
                requester_failure = counts["total"] - counts["requester_success"]
                risk_counts = risk_scores.get(cond)
                table.add_row(
                    scenario_cell,
                    _format_flag(has_warden),
                    _format_flag(has_profile),
                    _format_flag(has_adversary_data),
                    str(counts["total"]),
                    str(counts["requester_success"]),
                    str(requester_failure),
                    format_rate(counts),
                    format_risk(risk_counts),
                    style=row_style_for_condition(cond),
                )
                scenario_cell = ""
            first_scenario = False

        if overall_rates and len(scenario_groups) > 1:
            if not first_scenario:
                table.add_section()
            overall_risk = risk_rate(speaker_logs)
            scenario_cell = "All scenarios"
            for cond, counts in sorted(overall_rates.items()):
                has_warden, has_profile, has_adversary_data = cond
                requester_failure = counts["total"] - counts["requester_success"]
                risk_counts = overall_risk.get(cond)
                table.add_row(
                    scenario_cell,
                    _format_flag(has_warden),
                    _format_flag(has_profile),
                    _format_flag(has_adversary_data),
                    str(counts["total"]),
                    str(counts["requester_success"]),
                    str(requester_failure),
                    format_rate(counts),
                    format_risk(risk_counts),
                    style=row_style_for_condition(cond),
                )
                scenario_cell = ""

        console.print()
        console.print(table)

    # Supplementary: multi-target vote breakdown
    multi_logs = [log for log in logs if log.get("outcome", {}).get("vote_tally")]
    if multi_logs:
        vote_table = Table(
            title="[bold]Multi-Target Vote Breakdown[/bold]", show_header=True
        )
        vote_table.add_column("Scenario", style="magenta")
        vote_table.add_column("Speaker", style="cyan")
        vote_table.add_column("Warden", style="cyan")
        vote_table.add_column("Accept", justify="right", style="green")
        vote_table.add_column("Reject", justify="right", style="red")
        vote_table.add_column("Errors", justify="right", style="yellow")
        vote_table.add_column("Aggregate", justify="right", style="bold")
        for log in multi_logs:
            tally = log["outcome"]["vote_tally"]
            aggregate = log["outcome"].get("aggregate_decision", "?")
            speaker = _log_speaker(log) or "?"
            has_warden = _has_warden(log)
            vote_table.add_row(
                log.get("scenario", "?"),
                speaker.replace("_", " ").title(),
                _format_flag(has_warden),
                str(tally.get("accept", 0)),
                str(tally.get("reject", 0)),
                str(tally.get("formatting_failure", 0)),
                aggregate,
            )
        console.print()
        console.print(vote_table)


def plot_success_rates(logs: list[dict]) -> None:
    """Render a 3x2 Plotly subplot grid of success rates by models."""
    if not logs:
        print("No logs found.")
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
        custom = [
            [results[label]["requester_success"], results[label]["total"]]
            for label in labels
        ]
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
                        "Requester Success: %{customdata[0]} / %{customdata[1]}<extra></extra>"
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


def _extract_profile_name(log: dict) -> str | None:
    """Extract profile display name from a log."""
    profile = log.get("profile") or {}
    name = profile.get("name")
    if name:
        return name
    # Fall back to file_key
    key = profile.get("file_key")
    if key:
        return key.replace("_", " ").title()
    return None


def plot_heatmap(logs: list[dict]) -> None:
    """Plot a Scenario x Profile heatmap of adversary success rates."""
    # Filter to adversary runs with profiles
    adversary_logs = [
        log for log in logs
        if _log_speaker(log) == "adversary" and _extract_profile_name(log)
    ]
    if not adversary_logs:
        print("No adversary logs with profiles found.")
        return

    # Collect scenarios and profiles
    scenarios = sorted({log.get("scenario", "unknown") for log in adversary_logs})
    profiles = sorted({_extract_profile_name(log) for log in adversary_logs})

    # Build success rate matrix
    counts: dict[tuple[str, str], dict] = {}
    for log in adversary_logs:
        scenario = log.get("scenario", "unknown")
        profile = _extract_profile_name(log)
        key = (scenario, profile)
        if key not in counts:
            counts[key] = {"total": 0, "success": 0}
        decision = _get_decision(log)
        if decision in {"requester_success", "requester_failure"}:
            counts[key]["total"] += 1
            if decision == "requester_success":
                counts[key]["success"] += 1

    # Build z-matrix and hover text
    z = []
    hover = []
    for scenario in scenarios:
        row = []
        hover_row = []
        for profile in profiles:
            c = counts.get((scenario, profile), {"total": 0, "success": 0})
            rate = c["success"] / c["total"] if c["total"] > 0 else None
            row.append(rate)
            if c["total"] > 0:
                hover_row.append(
                    f"{scenario}<br>{profile}<br>"
                    f"Rate: {rate:.0%} ({c['success']}/{c['total']})"
                )
            else:
                hover_row.append(f"{scenario}<br>{profile}<br>No data")
        z.append(row)
        hover.append(hover_row)

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=profiles,
        y=scenarios,
        hovertext=hover,
        hoverinfo="text",
        colorscale="RdYlGn_r",
        zmin=0,
        zmax=1,
        colorbar=dict(title="Success Rate", tickformat=".0%"),
    ))
    fig.update_layout(
        title="Adversary Success Rate: Scenario x Profile",
        xaxis_title="Target Profile",
        yaxis_title="Scenario",
        height=max(400, len(scenarios) * 60 + 200),
        width=max(700, len(profiles) * 120 + 200),
    )
    fig.show()


def plot_warden_comparison(logs: list[dict]) -> None:
    """Plot adversary success rates per scenario, grouped by warden presence."""
    adversary_logs = [log for log in logs if _log_speaker(log) == "adversary"]
    if not adversary_logs:
        print("No adversary logs found.")
        return

    scenarios = sorted({log.get("scenario", "unknown") for log in adversary_logs})

    # Compute rates by (scenario, has_warden)
    counts: dict[tuple[str, bool], dict] = {}
    for log in adversary_logs:
        scenario = log.get("scenario", "unknown")
        has_warden = _has_warden(log)
        key = (scenario, has_warden)
        if key not in counts:
            counts[key] = {"total": 0, "success": 0}
        decision = _get_decision(log)
        if decision in {"requester_success", "requester_failure"}:
            counts[key]["total"] += 1
            if decision == "requester_success":
                counts[key]["success"] += 1

    # Build bar data
    no_warden_rates = []
    warden_rates = []
    no_warden_text = []
    warden_text = []
    for scenario in scenarios:
        for has_warden, rates_list, text_list in [
            (False, no_warden_rates, no_warden_text),
            (True, warden_rates, warden_text),
        ]:
            c = counts.get((scenario, has_warden), {"total": 0, "success": 0})
            rate = c["success"] / c["total"] if c["total"] > 0 else 0
            rates_list.append(rate)
            text_list.append(f"{c['success']}/{c['total']}")

    fig = go.Figure(data=[
        go.Bar(
            name="No Warden",
            x=scenarios,
            y=no_warden_rates,
            text=no_warden_text,
            textposition="auto",
            marker_color="#ef553b",
        ),
        go.Bar(
            name="With Warden",
            x=scenarios,
            y=warden_rates,
            text=warden_text,
            textposition="auto",
            marker_color="#636efa",
        ),
    ])
    fig.update_layout(
        title="Adversary Success Rate: Warden vs No Warden",
        xaxis_title="Scenario",
        yaxis_title="Success Rate",
        yaxis=dict(range=[0, 1], tickformat=".0%"),
        barmode="group",
        height=500,
        width=max(700, len(scenarios) * 100 + 200),
    )
    fig.show()


def plot_outcome_breakdown(logs: list[dict]) -> None:
    """Plot stacked bar of outcome types per scenario (adversary runs)."""
    adversary_logs = [log for log in logs if _log_speaker(log) == "adversary"]
    if not adversary_logs:
        print("No adversary logs found.")
        return

    scenarios = sorted({log.get("scenario", "unknown") for log in adversary_logs})

    # Count outcomes by scenario
    outcome_types = ["requester_success", "requester_failure", "formatting_failure"]
    counts: dict[str, dict[str, int]] = {
        s: {o: 0 for o in outcome_types} for s in scenarios
    }
    for log in adversary_logs:
        scenario = log.get("scenario", "unknown")
        decision = _get_decision(log) or "formatting_failure"
        if decision not in outcome_types:
            decision = "formatting_failure"
        counts[scenario][decision] += 1

    colors = {
        "requester_success": "#ef553b",
        "requester_failure": "#00cc96",
        "formatting_failure": "#ffa15a",
    }
    labels = {
        "requester_success": "Adversary Success",
        "requester_failure": "Adversary Failure",
        "formatting_failure": "Parsing Error",
    }

    fig = go.Figure()
    for outcome in outcome_types:
        values = [counts[s][outcome] for s in scenarios]
        if any(v > 0 for v in values):
            fig.add_trace(go.Bar(
                name=labels[outcome],
                x=scenarios,
                y=values,
                marker_color=colors[outcome],
            ))

    fig.update_layout(
        title="Outcome Breakdown by Scenario (Adversary Runs)",
        xaxis_title="Scenario",
        yaxis_title="Count",
        barmode="stack",
        height=500,
        width=max(700, len(scenarios) * 100 + 200),
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
        "--tag",
        default=None,
        nargs="+",
        help="Filter by tag (space-separated list, e.g. --tag foo bar)",
    )
    parser.add_argument(
        "--plotting",
        nargs="?",
        const=True,
        default=False,
        type=_parse_bool,
        help="Show Plotly subplots (use --plotting or --plotting=True)",
    )
    parser.add_argument(
        "--heatmap",
        action="store_true",
        help="Show Scenario x Profile success rate heatmap",
    )
    parser.add_argument(
        "--warden-comparison",
        action="store_true",
        help="Show warden vs no-warden success rate comparison",
    )
    parser.add_argument(
        "--outcome-breakdown",
        action="store_true",
        help="Show stacked bar of outcome types per scenario",
    )
    parser.add_argument(
        "--all-plots",
        action="store_true",
        help="Show all available plots",
    )

    args = parser.parse_args()
    logs = load_logs(args.scenario, args.tag)
    summarize(scenario=args.scenario, logs=logs)

    show_all = args.all_plots
    if args.plotting or show_all:
        plot_success_rates(logs)
    if args.heatmap or show_all:
        plot_heatmap(logs)
    if args.warden_comparison or show_all:
        plot_warden_comparison(logs)
    if args.outcome_breakdown or show_all:
        plot_outcome_breakdown(logs)
