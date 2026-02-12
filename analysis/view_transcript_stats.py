#!/usr/bin/env python3
"""Re-render saved transcript analysis outputs as rich tables.

This script loads a JSON artifact produced by `analysis.transcript_analysis`,
prints the original summary tables, and additionally prints requester-only
tables split by requester type (`adversary` / `benign_agent`). It can also
optionally split all outputs by scenario.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from analysis.transcript_analysis import (
    DEFAULT_TAXONOMY_PATH,
    MessageClassification,
    MessageRecord,
    SentenceClassification,
    aggregate_classifications,
    load_taxonomies,
    print_summary,
)

REQUESTER_TYPES = ("adversary", "benign_agent")
UNKNOWN_SCENARIO_LABEL = "(no_scenario)"
console = Console()


def _coerce_path(path_str: str | None) -> Path:
    if not path_str:
        return DEFAULT_TAXONOMY_PATH
    path = Path(path_str)
    if path.exists():
        return path
    project_relative = PROJECT_ROOT / path
    if project_relative.exists():
        return project_relative
    return DEFAULT_TAXONOMY_PATH


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _deserialize_classifications(
    raw_items: Any,
) -> list[MessageClassification]:
    if not isinstance(raw_items, list):
        return []

    parsed: list[MessageClassification] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue

        message_text = item.get("message")
        if not isinstance(message_text, str):
            message_text = ""
        message = MessageRecord(
            log_file=str(item.get("log_file", "")),
            scenario=item.get("scenario")
            if isinstance(item.get("scenario"), str)
            else None,
            tag=item.get("tag") if isinstance(item.get("tag"), str) else None,
            analysis_type=str(item.get("analysis_type", "")),
            speaker=str(item.get("speaker", "")),
            turn=_safe_int(item.get("turn"), default=0),
            message=message_text,
            warden_turn=_safe_int(item.get("warden_turn"), default=0)
            if item.get("warden_turn") is not None
            else None,
            warden_should_advise=item.get("warden_should_advise")
            if isinstance(item.get("warden_should_advise"), bool)
            else None,
            warden_risk_level=item.get("warden_risk_level")
            if isinstance(item.get("warden_risk_level"), str)
            else None,
            warden_content=item.get("warden_content")
            if isinstance(item.get("warden_content"), str)
            else None,
        )

        sentences: list[SentenceClassification] = []
        raw_sentences = item.get("sentences")
        if isinstance(raw_sentences, list):
            for raw_sentence in raw_sentences:
                if not isinstance(raw_sentence, dict):
                    continue
                sentence_text = raw_sentence.get("sentence")
                if not isinstance(sentence_text, str):
                    sentence_text = ""

                raw_labels = raw_sentence.get("labels")
                labels: dict[str, list[str]] = {}
                if isinstance(raw_labels, dict):
                    for key, value in raw_labels.items():
                        if not isinstance(key, str):
                            continue
                        if isinstance(value, list):
                            cleaned = [entry for entry in value if isinstance(entry, str)]
                        elif isinstance(value, str):
                            cleaned = [value]
                        else:
                            cleaned = []
                        labels[key] = cleaned

                raw_label_spans = raw_sentence.get("label_spans")
                label_spans: dict[str, dict[str, list[str]]] = {}
                if isinstance(raw_label_spans, dict):
                    for dimension_name, raw_dimension_spans in raw_label_spans.items():
                        if not isinstance(dimension_name, str):
                            continue
                        if not isinstance(raw_dimension_spans, dict):
                            continue
                        parsed_dimension_spans: dict[str, list[str]] = {}
                        for label_name, raw_spans in raw_dimension_spans.items():
                            if not isinstance(label_name, str):
                                continue
                            if isinstance(raw_spans, list):
                                spans = [span for span in raw_spans if isinstance(span, str)]
                            elif isinstance(raw_spans, str):
                                spans = [raw_spans]
                            else:
                                spans = []
                            parsed_dimension_spans[label_name] = spans
                        label_spans[dimension_name] = parsed_dimension_spans

                sentences.append(
                    SentenceClassification(
                        sentence_index=_safe_int(raw_sentence.get("sentence_index"), default=0),
                        sentence=sentence_text,
                        labels=labels,
                        label_spans=label_spans,
                    )
                )

        parsed.append(MessageClassification(message=message, sentences=sentences))

    return parsed


def _print_requester_split(
    classifications: list[MessageClassification],
    taxonomies: dict[str, Any],
    *,
    show_examples: bool = False,
) -> None:
    requester_items = [
        item for item in classifications if item.message.analysis_type == "requester"
    ]
    if not requester_items:
        console.print("\n[yellow]No requester classifications found to split.[/yellow]")
        return

    split_items_by_type = {
        requester_type: [
            item for item in requester_items if item.message.speaker == requester_type
        ]
        for requester_type in REQUESTER_TYPES
    }
    split_summary_by_type = {
        requester_type: aggregate_classifications(items, taxonomies).get("requester", {})
        for requester_type, items in split_items_by_type.items()
        if items
    }
    combined_summary = aggregate_classifications(requester_items, taxonomies).get(
        "requester", {}
    )

    console.print("\n[bold]Requester-Type Split (Message %)[/bold]")
    taxonomy = taxonomies.get("requester")
    if taxonomy is None:
        console.print("[yellow]No requester taxonomy found.[/yellow]")
        return

    adv_n = len(split_items_by_type.get("adversary", []))
    ben_n = len(split_items_by_type.get("benign_agent", []))

    def _format_rate_with_counts(label_stats: dict[str, Any]) -> str:
        pct = label_stats.get("flagged_pct_of_warden_messages")
        flagged = label_stats.get("flagged_messages", 0)
        denominator = label_stats.get("messages_with_warden_record", 0)
        if isinstance(pct, (int, float)):
            return f"{pct:.1f}% ({flagged}/{denominator})"
        return f"n/a ({flagged}/{denominator})"

    def _format_risk_counts(label_stats: dict[str, Any]) -> str:
        risk_counts = label_stats.get("risk_level_counts", {})
        if not isinstance(risk_counts, dict):
            return "n/a"
        total = sum(
            value for value in risk_counts.values() if isinstance(value, int) and value >= 0
        )
        if total == 0:
            return "n/a"
        low = risk_counts.get("LOW", 0)
        medium = risk_counts.get("MEDIUM", 0)
        high = risk_counts.get("HIGH", 0)
        unknown = risk_counts.get("UNKNOWN", 0)
        return f"L:{low} M:{medium} H:{high} U:{unknown}"

    for dimension in taxonomy.dimensions:
        examples_by_type: dict[str, dict[str, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for requester_type, items in split_items_by_type.items():
            for item in items:
                for sentence in item.sentences:
                    labels = sentence.labels.get(dimension.name, [])
                    if not labels:
                        continue
                    for label_name in labels:
                        spans = (
                            sentence.label_spans.get(dimension.name, {}).get(label_name, [])
                            if isinstance(sentence.label_spans, dict)
                            else []
                        )
                        for span in spans:
                            if isinstance(span, str) and span.strip():
                                examples_by_type[requester_type][label_name].append(span.strip())

        adv_labels = (
            split_summary_by_type.get("adversary", {})
            .get("dimensions", {})
            .get(dimension.name, {})
            .get("labels", {})
        )
        ben_labels = (
            split_summary_by_type.get("benign_agent", {})
            .get("dimensions", {})
            .get(dimension.name, {})
            .get("labels", {})
        )

        table = Table(
            title=f"requester :: {dimension.name}",
            show_header=True,
        )
        table.add_column("Label", style="magenta")
        table.add_column("Adversary %", justify="right")
        table.add_column("Benign %", justify="right")
        table.add_column("Delta (pp)", justify="right")

        for label_name in dimension.labels:
            adv_pct = adv_labels.get(label_name, {}).get("message_pct")
            ben_pct = ben_labels.get(label_name, {}).get("message_pct")
            if isinstance(adv_pct, (int, float)):
                adv_display = f"{adv_pct:.1f}%"
            else:
                adv_display = "n/a"
            if isinstance(ben_pct, (int, float)):
                ben_display = f"{ben_pct:.1f}%"
            else:
                ben_display = "n/a"

            if isinstance(adv_pct, (int, float)) and isinstance(ben_pct, (int, float)):
                delta = adv_pct - ben_pct
                delta_display = f"{delta:+.1f} pp"
            else:
                delta_display = "n/a"

            table.add_row(
                label_name,
                adv_display,
                ben_display,
                delta_display,
            )

        table.caption = (
            "Message-level percentages. "
            f"adversary messages={adv_n}, benign messages={ben_n}"
        )
        console.print(table)

        adv_warden_labels = (
            split_summary_by_type.get("adversary", {})
            .get("dimensions", {})
            .get(dimension.name, {})
            .get("warden_linkage", {})
            .get("labels", {})
        )
        ben_warden_labels = (
            split_summary_by_type.get("benign_agent", {})
            .get("dimensions", {})
            .get(dimension.name, {})
            .get("warden_linkage", {})
            .get("labels", {})
        )
        all_warden = (
            combined_summary.get("dimensions", {})
            .get(dimension.name, {})
            .get("warden_linkage", {})
        )
        if all_warden:
            warden_table = Table(
                title=f"requester :: {dimension.name} :: warden linkage",
                show_header=True,
            )
            warden_table.add_column("Label", style="magenta")
            warden_table.add_column("Adversary Flag %", justify="right")
            warden_table.add_column("Benign Flag %", justify="right")
            warden_table.add_column("Delta (pp)", justify="right")
            warden_table.add_column("Adv Risk", justify="right")
            warden_table.add_column("Ben Risk", justify="right")

            for label_name in dimension.labels:
                adv_link = adv_warden_labels.get(label_name, {})
                ben_link = ben_warden_labels.get(label_name, {})
                delta = (
                    adv_link.get("delta_flagged_pct_pp_adversary_minus_benign")
                    if isinstance(adv_link, dict)
                    else None
                )
                if not isinstance(delta, (int, float)):
                    adv_pct = adv_link.get("flagged_pct_of_warden_messages")
                    ben_pct = ben_link.get("flagged_pct_of_warden_messages")
                    if isinstance(adv_pct, (int, float)) and isinstance(ben_pct, (int, float)):
                        delta = adv_pct - ben_pct

                warden_table.add_row(
                    label_name,
                    _format_rate_with_counts(adv_link if isinstance(adv_link, dict) else {}),
                    _format_rate_with_counts(ben_link if isinstance(ben_link, dict) else {}),
                    f"{delta:+.1f} pp" if isinstance(delta, (int, float)) else "n/a",
                    _format_risk_counts(adv_link if isinstance(adv_link, dict) else {}),
                    _format_risk_counts(ben_link if isinstance(ben_link, dict) else {}),
                )

            warden_table.caption = (
                "Flag rate denominator is requester messages with a linked warden record. "
                f"overall linked messages={all_warden.get('messages_with_warden_record', 0)}, "
                f"overall flagged={all_warden.get('flagged_messages', 0)}"
            )
            console.print(warden_table)

        if show_examples:
            console.print(f"[bold]Spans :: requester :: {dimension.name}[/bold]")
            for label_name in dimension.labels:
                adv_examples = examples_by_type.get("adversary", {}).get(label_name, [])
                ben_examples = examples_by_type.get("benign_agent", {}).get(label_name, [])
                if not adv_examples and not ben_examples:
                    continue

                console.print(f"[cyan]{label_name}[/cyan]")
                if adv_examples:
                    console.print(f"  adversary ({len(adv_examples)}):")
                    for idx, entry in enumerate(adv_examples, start=1):
                        console.print(f"    {idx}. {entry}")
                else:
                    console.print("  adversary (0)")

                if ben_examples:
                    console.print(f"  benign_agent ({len(ben_examples)}):")
                    for idx, entry in enumerate(ben_examples, start=1):
                        console.print(f"    {idx}. {entry}")
                else:
                    console.print("  benign_agent (0)")
            console.print()


def _scenario_label(classification: MessageClassification) -> str:
    scenario = classification.message.scenario
    if isinstance(scenario, str):
        cleaned = scenario.strip()
        if cleaned:
            return cleaned
    return UNKNOWN_SCENARIO_LABEL


def _print_scenario_split(
    classifications: list[MessageClassification],
    taxonomies: dict[str, Any],
    *,
    show_examples: bool = False,
) -> None:
    if not classifications:
        console.print("\n[yellow]No classifications available for scenario split.[/yellow]")
        return

    by_scenario: dict[str, list[MessageClassification]] = defaultdict(list)
    for classification in classifications:
        by_scenario[_scenario_label(classification)].append(classification)

    console.print("\n[bold]Scenario Split[/bold]")
    for scenario in sorted(by_scenario.keys()):
        items = by_scenario[scenario]
        console.print(
            f"\n[bold]Scenario:[/bold] {scenario} "
            f"(messages={len(items)}, sentences={sum(len(i.sentences) for i in items)})"
        )
        scenario_summary = aggregate_classifications(items, taxonomies)
        if scenario_summary:
            print_summary(scenario_summary)
        else:
            console.print("[yellow]No summary rows for this scenario.[/yellow]")
        _print_requester_split(
            items,
            taxonomies,
            show_examples=show_examples,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Render transcript analysis output JSON as rich tables, including "
            "split-by-requester-type views."
        )
    )
    parser.add_argument(
        "artifact",
        type=Path,
        help="Path to a JSON artifact generated by analysis.transcript_analysis.",
    )
    parser.add_argument(
        "--show-examples",
        action="store_true",
        help=(
            "Print captured evidence spans assigned to each requester category label, "
            "split by adversary vs benign_agent."
        ),
    )
    parser.add_argument(
        "--split-by-scenario",
        action="store_true",
        help=(
            "Also print per-scenario summaries and requester splits. "
            "Requires classifications in the artifact."
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.artifact.exists():
        raise SystemExit(f"Artifact not found: {args.artifact}")

    payload = json.loads(args.artifact.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit("Artifact root must be a JSON object.")

    taxonomies = load_taxonomies(_coerce_path(payload.get("taxonomy_file")))
    classifications = _deserialize_classifications(payload.get("classifications"))

    if not classifications and not payload.get("summary"):
        raise SystemExit("Artifact has neither classifications nor summary.")

    summary = payload.get("summary")
    console.print(f"[bold]Artifact:[/bold] {args.artifact}")
    if isinstance(summary, dict) and summary:
        console.print("[bold]Original Summary[/bold]")
        print_summary(summary)
    else:
        console.print("[yellow]No summary found; recomputing from classifications.[/yellow]")
        recomputed = aggregate_classifications(classifications, taxonomies)
        print_summary(recomputed)

    _print_requester_split(
        classifications,
        taxonomies,
        show_examples=args.show_examples,
    )
    if args.split_by_scenario:
        _print_scenario_split(
            classifications,
            taxonomies,
            show_examples=args.show_examples,
        )


if __name__ == "__main__":
    main()
