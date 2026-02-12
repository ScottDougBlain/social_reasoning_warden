#!/usr/bin/env python3
"""Sentence-level transcript analysis over experiment logs.

This tool:
1) selects logs by filename and/or tag
2) extracts messages for requester/target/warden roles
3) classifies each message sentence-by-sentence with an LLM
4) aggregates label statistics

Taxonomies are loaded from YAML/JSON so they can be extended without code
changes. Each analysis type uses its own taxonomy and few-shot examples.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sys
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from rich.console import Console
from rich.table import Table

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.client import chat

LOGS_DIR = PROJECT_ROOT / "logs"
DEFAULT_TAXONOMY_PATH = (
    Path(__file__).resolve().parent / "taxonomies" / "transcript_taxonomies.yaml"
)
TRANSCRIPT_OUTPUT_DIR = Path(__file__).resolve().parent / "transcript_output"
DEFAULT_MODEL = "google/gemini-2.5-flash-lite-preview-09-2025"
REQUESTED_ANALYSIS_TYPES = {"requester", "target", "warden"}
REQUESTER_SPEAKERS = {"adversary", "benign_agent", "requester"}
WARDEN_LABELABLE_RISK_LEVELS = {"MEDIUM", "HIGH"}
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
console = Console()


@dataclass
class TaxonomyDimension:
    """Single label dimension for sentence classification."""

    name: str
    description: str
    labels: dict[str, str]
    allow_multiple: bool = True


@dataclass
class FewShotExample:
    """One few-shot training example."""

    sentence: str
    labels: dict[str, list[str]]


@dataclass
class Taxonomy:
    """Taxonomy and examples for one analysis type."""

    analysis_type: str
    description: str
    dimensions: list[TaxonomyDimension]
    few_shot_examples: list[FewShotExample] = field(default_factory=list)


@dataclass
class MessageRecord:
    """Message extracted from logs for downstream classification."""

    log_file: str
    scenario: str | None
    tag: str | None
    analysis_type: str
    speaker: str
    turn: int | None
    message: str
    warden_turn: int | None = None
    warden_should_advise: bool | None = None
    warden_risk_level: str | None = None
    warden_content: str | None = None


@dataclass
class SentenceClassification:
    """Labels assigned to one sentence."""

    sentence_index: int
    sentence: str
    labels: dict[str, list[str]]
    label_spans: dict[str, dict[str, list[str]]] = field(default_factory=dict)


@dataclass
class MessageClassification:
    """Sentence-level classification output for one message."""

    message: MessageRecord
    sentences: list[SentenceClassification]


def _parse_repeated_values(values: list[str] | None) -> list[str]:
    if not values:
        return []
    parsed: list[str] = []
    for value in values:
        for part in value.split(","):
            stripped = part.strip()
            if stripped:
                parsed.append(stripped)
    return parsed


def _load_structured_file(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    if suffix == ".json":
        return json.loads(text)
    if suffix in {".yaml", ".yml"}:
        return yaml.safe_load(text)
    raise ValueError(f"Unsupported file type for {path}. Use .json, .yaml, or .yml")


def _parse_labels(raw_labels: Any, *, dimension_name: str) -> dict[str, str]:
    if isinstance(raw_labels, dict):
        labels: dict[str, str] = {}
        for label_name, description in raw_labels.items():
            if not isinstance(label_name, str) or not label_name.strip():
                continue
            labels[label_name.strip()] = (
                description.strip()
                if isinstance(description, str)
                else "No description provided."
            )
        return labels

    if isinstance(raw_labels, list):
        labels = {}
        for entry in raw_labels:
            if not isinstance(entry, dict):
                continue
            label_name = entry.get("name")
            if not isinstance(label_name, str) or not label_name.strip():
                continue
            description = entry.get("description")
            labels[label_name.strip()] = (
                description.strip()
                if isinstance(description, str)
                else "No description provided."
            )
        return labels

    raise ValueError(
        f"Invalid labels for dimension '{dimension_name}'. "
        "Expected mapping or list of {name, description} objects."
    )


def _normalize_example_labels(raw_labels: Any, taxonomy: Taxonomy) -> dict[str, list[str]]:
    if not isinstance(raw_labels, dict):
        return {}

    valid_labels_by_dimension = {
        dimension.name: set(dimension.labels.keys()) for dimension in taxonomy.dimensions
    }
    normalized: dict[str, list[str]] = {}
    for dimension in taxonomy.dimensions:
        value = raw_labels.get(dimension.name, [])
        if isinstance(value, str):
            candidate_labels = [value]
        elif isinstance(value, list):
            candidate_labels = value
        else:
            candidate_labels = []

        cleaned: list[str] = []
        for label in candidate_labels:
            if not isinstance(label, str):
                continue
            trimmed = label.strip()
            if not trimmed:
                continue
            if trimmed not in valid_labels_by_dimension[dimension.name]:
                continue
            if trimmed in cleaned:
                continue
            cleaned.append(trimmed)

        if not dimension.allow_multiple and len(cleaned) > 1:
            cleaned = cleaned[:1]
        normalized[dimension.name] = cleaned
    return normalized


def _parse_few_shot_examples(raw_examples: Any, taxonomy: Taxonomy) -> list[FewShotExample]:
    if raw_examples is None:
        return []
    if not isinstance(raw_examples, list):
        raise ValueError(
            f"few_shot_examples for '{taxonomy.analysis_type}' must be a list."
        )

    parsed_examples: list[FewShotExample] = []
    for entry in raw_examples:
        if not isinstance(entry, dict):
            continue
        sentence = entry.get("sentence")
        if not isinstance(sentence, str) or not sentence.strip():
            continue
        labels = _normalize_example_labels(entry.get("labels", {}), taxonomy)
        parsed_examples.append(FewShotExample(sentence=sentence.strip(), labels=labels))
    return parsed_examples


def load_taxonomies(path: Path) -> dict[str, Taxonomy]:
    """Load taxonomy definitions from YAML/JSON."""
    raw_data = _load_structured_file(path)
    if not isinstance(raw_data, dict):
        raise ValueError("Taxonomy file must define a top-level mapping.")

    raw_types = raw_data.get("analysis_types", raw_data)
    if not isinstance(raw_types, dict):
        raise ValueError("Taxonomy file must contain an 'analysis_types' mapping.")

    taxonomies: dict[str, Taxonomy] = {}
    for analysis_type, payload in raw_types.items():
        if not isinstance(analysis_type, str) or analysis_type not in REQUESTED_ANALYSIS_TYPES:
            continue
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid taxonomy definition for '{analysis_type}'.")

        description = payload.get("description", "")
        if not isinstance(description, str):
            description = ""

        raw_dimensions = payload.get("dimensions", [])
        if not isinstance(raw_dimensions, list) or not raw_dimensions:
            raise ValueError(f"Taxonomy '{analysis_type}' must define at least one dimension.")

        dimensions: list[TaxonomyDimension] = []
        for raw_dimension in raw_dimensions:
            if not isinstance(raw_dimension, dict):
                continue
            name = raw_dimension.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            description_text = raw_dimension.get("description", "")
            if not isinstance(description_text, str):
                description_text = ""
            allow_multiple = bool(raw_dimension.get("allow_multiple", True))
            labels = _parse_labels(raw_dimension.get("labels"), dimension_name=name)
            if not labels:
                raise ValueError(
                    f"Dimension '{name}' in '{analysis_type}' must define labels."
                )
            dimensions.append(
                TaxonomyDimension(
                    name=name.strip(),
                    description=description_text.strip(),
                    labels=labels,
                    allow_multiple=allow_multiple,
                )
            )

        if not dimensions:
            raise ValueError(f"Taxonomy '{analysis_type}' has no valid dimensions.")

        taxonomy = Taxonomy(
            analysis_type=analysis_type,
            description=description.strip(),
            dimensions=dimensions,
        )
        taxonomy.few_shot_examples = _parse_few_shot_examples(
            payload.get("few_shot_examples", []), taxonomy
        )
        taxonomies[analysis_type] = taxonomy

    missing = REQUESTED_ANALYSIS_TYPES - set(taxonomies.keys())
    if missing:
        missing_str = ", ".join(sorted(missing))
        raise ValueError(
            f"Taxonomy file is missing required analysis types: {missing_str}"
        )
    return taxonomies


def load_additional_few_shots(path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load optional few-shot examples to merge into taxonomy definitions."""
    raw_data = _load_structured_file(path)
    if not isinstance(raw_data, dict):
        raise ValueError("Few-shot file must define a top-level mapping.")

    extracted: dict[str, list[dict[str, Any]]] = defaultdict(list)

    if isinstance(raw_data.get("analysis_types"), dict):
        candidate_root = raw_data["analysis_types"]
    else:
        candidate_root = raw_data

    for analysis_type, payload in candidate_root.items():
        if not isinstance(analysis_type, str):
            continue
        if analysis_type not in REQUESTED_ANALYSIS_TYPES and analysis_type != "all":
            continue

        if isinstance(payload, dict):
            raw_examples = payload.get("few_shot_examples", payload.get("examples", []))
        else:
            raw_examples = payload

        if not isinstance(raw_examples, list):
            continue
        for entry in raw_examples:
            if isinstance(entry, dict):
                extracted[analysis_type].append(entry)

    return dict(extracted)


def merge_additional_few_shots(
    taxonomies: dict[str, Taxonomy], extra_examples: dict[str, list[dict[str, Any]]]
) -> None:
    """Merge extra few-shot examples into existing taxonomies."""
    for analysis_type, raw_examples in extra_examples.items():
        targets = sorted(REQUESTED_ANALYSIS_TYPES) if analysis_type == "all" else [analysis_type]
        for target_type in targets:
            if target_type not in taxonomies:
                continue
            taxonomy = taxonomies[target_type]
            parsed = _parse_few_shot_examples(raw_examples, taxonomy)
            taxonomy.few_shot_examples.extend(parsed)


def _matches_file(path: Path, patterns: list[str]) -> bool:
    for pattern in patterns:
        if fnmatch.fnmatch(path.name, pattern) or fnmatch.fnmatch(path.stem, pattern):
            return True
        if pattern in path.name:
            return True
    return False


def load_filtered_logs(
    *,
    file_patterns: list[str],
    tags: set[str],
) -> list[tuple[Path, dict[str, Any]]]:
    """Load logs filtered by filename pattern and/or tag."""
    selected: list[tuple[Path, dict[str, Any]]] = []

    for path in sorted(LOGS_DIR.glob("*.json")):
        if file_patterns and not _matches_file(path, file_patterns):
            continue

        try:
            with path.open(encoding="utf-8") as handle:
                log = json.load(handle)
        except json.JSONDecodeError as exc:
            console.print(f"[yellow]Skipping invalid JSON {path.name}: {exc}[/yellow]")
            continue

        if tags:
            tag_value = log.get("tag")
            if tag_value not in tags:
                continue

        selected.append((path, log))
    return selected


def _extract_turn(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_conversation_message(entry: dict[str, Any]) -> str:
    value = entry.get("message")
    if isinstance(value, str):
        return value.strip()
    value = entry.get("content")
    if isinstance(value, str):
        return value.strip()
    return ""


def _normalize_risk_level(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().upper()
    if not normalized:
        return None
    if normalized in {"LOW", "MEDIUM", "HIGH"}:
        return normalized
    return "UNKNOWN"


def extract_messages(
    logs: list[tuple[Path, dict[str, Any]]], analysis_types: set[str]
) -> list[MessageRecord]:
    """Extract requester/target/warden messages from selected logs."""
    include_requester = "requester" in analysis_types
    include_target = "target" in analysis_types
    include_warden = "warden" in analysis_types

    extracted: list[MessageRecord] = []

    for path, log in logs:
        scenario = log.get("scenario")
        tag = log.get("tag")
        advisory_by_turn: dict[int, dict[str, Any]] = {}
        advisories = log.get("warden_advisories")
        if isinstance(advisories, list):
            for advisory in advisories:
                if not isinstance(advisory, dict):
                    continue
                advisory_turn = _extract_turn(advisory.get("turn"))
                if advisory_turn is None:
                    continue
                should_advise = advisory.get("should_advise")
                advisory_by_turn[advisory_turn] = {
                    "should_advise": should_advise
                    if isinstance(should_advise, bool)
                    else None,
                    "risk_level": _normalize_risk_level(advisory.get("risk_level")),
                    "content": advisory.get("content").strip()
                    if isinstance(advisory.get("content"), str)
                    and advisory.get("content").strip()
                    else None,
                }

        conversation = log.get("conversation")
        if isinstance(conversation, list):
            for item in conversation:
                if not isinstance(item, dict):
                    continue
                speaker = item.get("speaker")
                if not isinstance(speaker, str):
                    continue
                text = _extract_conversation_message(item)
                if not text:
                    continue
                msg_turn = _extract_turn(item.get("turn"))
                if include_requester and speaker in REQUESTER_SPEAKERS:
                    linked_turn = msg_turn + 1 if msg_turn is not None else None
                    linked_advisory = (
                        advisory_by_turn.get(linked_turn)
                        if linked_turn is not None
                        else None
                    )
                    extracted.append(
                        MessageRecord(
                            log_file=path.name,
                            scenario=scenario if isinstance(scenario, str) else None,
                            tag=tag if isinstance(tag, str) else None,
                            analysis_type="requester",
                            speaker=speaker,
                            turn=msg_turn,
                            message=text,
                            warden_turn=linked_turn,
                            warden_should_advise=(
                                linked_advisory.get("should_advise")
                                if linked_advisory
                                else None
                            ),
                            warden_risk_level=(
                                linked_advisory.get("risk_level")
                                if linked_advisory
                                else None
                            ),
                            warden_content=(
                                linked_advisory.get("content")
                                if linked_advisory
                                else None
                            ),
                        )
                    )
                if include_target and speaker == "target":
                    extracted.append(
                        MessageRecord(
                            log_file=path.name,
                            scenario=scenario if isinstance(scenario, str) else None,
                            tag=tag if isinstance(tag, str) else None,
                            analysis_type="target",
                            speaker=speaker,
                            turn=msg_turn,
                            message=text,
                        )
                    )

        if include_warden:
            if not isinstance(advisories, list):
                continue
            for advisory in advisories:
                if not isinstance(advisory, dict):
                    continue
                content = advisory.get("content")
                if not isinstance(content, str) or not content.strip():
                    continue
                risk_level = _normalize_risk_level(advisory.get("risk_level"))
                if risk_level not in WARDEN_LABELABLE_RISK_LEVELS:
                    continue
                extracted.append(
                    MessageRecord(
                        log_file=path.name,
                        scenario=scenario if isinstance(scenario, str) else None,
                        tag=tag if isinstance(tag, str) else None,
                        analysis_type="warden",
                        speaker="warden",
                        turn=_extract_turn(advisory.get("turn")),
                        message=content.strip(),
                        warden_turn=_extract_turn(advisory.get("turn")),
                        warden_should_advise=advisory.get("should_advise")
                        if isinstance(advisory.get("should_advise"), bool)
                        else None,
                        warden_risk_level=risk_level,
                        warden_content=content.strip(),
                    )
                )

    return extracted


def split_sentences(text: str) -> list[str]:
    """Split a message into sentence-like spans."""
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    parts = [part.strip() for part in SENTENCE_SPLIT_RE.split(normalized) if part.strip()]
    if not parts:
        return [normalized]
    return parts


def _build_taxonomy_prompt_block(taxonomy: Taxonomy) -> str:
    lines = [f"Analysis type: {taxonomy.analysis_type}"]
    if taxonomy.description:
        lines.append(f"Description: {taxonomy.description}")
    lines.append("Dimensions and labels:")
    for dimension in taxonomy.dimensions:
        lines.append(f"- {dimension.name}")
        lines.append(f"  description: {dimension.description or 'No description provided.'}")
        lines.append(f"  allow_multiple: {str(dimension.allow_multiple).lower()}")
        lines.append("  labels:")
        for label_name, description in dimension.labels.items():
            lines.append(f"    - {label_name}: {description}")
    return "\n".join(lines)


def _build_classifier_messages(
    *, taxonomy: Taxonomy, sentences: list[str]
) -> list[dict[str, str]]:
    input_payload = [
        {"sentence_index": index, "sentence": sentence}
        for index, sentence in enumerate(sentences)
    ]
    example_payload = [
        {"sentence": example.sentence, "labels": example.labels}
        for example in taxonomy.few_shot_examples
    ]

    output_template = {
        "sentences": [
            {
                "sentence_index": 0,
                "labels": {dimension.name: [] for dimension in taxonomy.dimensions},
                "label_spans": {dimension.name: {} for dimension in taxonomy.dimensions},
            }
        ]
    }

    analysis_specific_rules = ""
    if taxonomy.analysis_type == "warden":
        analysis_specific_rules = (
            "Analysis-type rule for warden:\n"
            "- Labels describe tactics the warden attributes to the requester "
            "or another actor, not tactics performed by the warden.\n"
            "- If a sentence is only advice/mitigation and does not identify "
            "a tactic, return [].\n\n"
        )

    user_prompt = (
        "Classify each sentence independently using the taxonomy.\n"
        "Rules:\n"
        "1) Return valid JSON only (no markdown, no prose).\n"
        "2) Output exactly one entry per input sentence.\n"
        "3) Keep sentence_index unchanged.\n"
        "4) For each dimension, return a list of allowed label names.\n"
        "5) If no label applies in a dimension, return [].\n"
        "6) If allow_multiple is false, return at most one label.\n"
        "7) Return label_spans with exact text spans from the sentence that "
        "justify each selected label.\n"
        "8) label_spans must be a nested mapping: "
        "{dimension: {label: [span, ...]}}.\n"
        "9) For dimensions with no selected labels, set label_spans[dimension] to {}.\n"
        "10) Spans must be verbatim snippets from the sentence.\n\n"
        f"{analysis_specific_rules}"
        f"{_build_taxonomy_prompt_block(taxonomy)}\n\n"
        "Few-shot examples (label targets):\n"
        f"{json.dumps(example_payload, ensure_ascii=True, indent=2)}\n\n"
        "Input sentences:\n"
        f"{json.dumps(input_payload, ensure_ascii=True, indent=2)}\n\n"
        "Return JSON in this shape:\n"
        f"{json.dumps(output_template, ensure_ascii=True, indent=2)}"
    )

    return [
        {
            "role": "system",
            "content": (
                "You are a strict JSON classifier for sentence-level transcript tagging."
            ),
        },
        {"role": "user", "content": user_prompt},
    ]


def _extract_json_payload(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if not stripped:
        raise ValueError("Model returned empty output.")

    fence_match = JSON_FENCE_RE.search(stripped)
    if fence_match:
        candidate = fence_match.group(1).strip()
    else:
        candidate = stripped

    try:
        payload = json.loads(candidate)
        if isinstance(payload, dict):
            return payload
    except json.JSONDecodeError:
        pass

    first_brace = candidate.find("{")
    last_brace = candidate.rfind("}")
    if first_brace == -1 or last_brace == -1 or first_brace >= last_brace:
        raise ValueError("Could not find a JSON object in model output.")

    fallback = candidate[first_brace : last_brace + 1]
    try:
        payload = json.loads(fallback)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON from model: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError("Model output JSON must be an object.")
    return payload


def _normalize_sentence_classifications(
    *,
    payload: dict[str, Any],
    sentences: list[str],
    taxonomy: Taxonomy,
) -> list[SentenceClassification]:
    expected_dimensions = [dimension.name for dimension in taxonomy.dimensions]
    allowed_labels = {
        dimension.name: set(dimension.labels.keys()) for dimension in taxonomy.dimensions
    }
    allow_multiple = {
        dimension.name: dimension.allow_multiple for dimension in taxonomy.dimensions
    }

    raw_sentences = payload.get("sentences")
    if not isinstance(raw_sentences, list):
        raw_sentences = []

    by_index_labels: dict[int, dict[str, list[str]]] = {}
    by_index_spans: dict[int, dict[str, dict[str, list[str]]]] = {}
    for entry in raw_sentences:
        if not isinstance(entry, dict):
            continue
        index = entry.get("sentence_index")
        if isinstance(index, str) and index.isdigit():
            index = int(index)
        if not isinstance(index, int):
            continue
        if index < 0 or index >= len(sentences):
            continue
        labels_blob = entry.get("labels", {})
        if not isinstance(labels_blob, dict):
            labels_blob = {}
        spans_blob = entry.get("label_spans", {})
        if not isinstance(spans_blob, dict):
            spans_blob = {}
        sentence_text = sentences[index]
        sentence_text_lower = sentence_text.lower()

        normalized_labels: dict[str, list[str]] = {}
        normalized_spans: dict[str, dict[str, list[str]]] = {}
        for dimension_name in expected_dimensions:
            raw_label_list = labels_blob.get(dimension_name, [])
            if isinstance(raw_label_list, str):
                candidates = [raw_label_list]
            elif isinstance(raw_label_list, list):
                candidates = raw_label_list
            else:
                candidates = []

            cleaned: list[str] = []
            for label in candidates:
                if not isinstance(label, str):
                    continue
                trimmed = label.strip()
                if not trimmed:
                    continue
                if trimmed not in allowed_labels[dimension_name]:
                    continue
                if trimmed in cleaned:
                    continue
                cleaned.append(trimmed)

            if not allow_multiple[dimension_name] and len(cleaned) > 1:
                cleaned = cleaned[:1]
            normalized_labels[dimension_name] = cleaned
            normalized_spans[dimension_name] = {}

            dimension_span_blob = spans_blob.get(dimension_name, {})
            if not isinstance(dimension_span_blob, dict):
                dimension_span_blob = {}
            for label in cleaned:
                raw_spans = dimension_span_blob.get(label, [])
                if isinstance(raw_spans, str):
                    span_candidates = [raw_spans]
                elif isinstance(raw_spans, list):
                    span_candidates = raw_spans
                else:
                    span_candidates = []

                cleaned_spans: list[str] = []
                for span in span_candidates:
                    if not isinstance(span, str):
                        continue
                    span_trimmed = span.strip()
                    if not span_trimmed:
                        continue
                    if span_trimmed.lower() not in sentence_text_lower:
                        continue
                    if span_trimmed in cleaned_spans:
                        continue
                    cleaned_spans.append(span_trimmed)

                normalized_spans[dimension_name][label] = cleaned_spans

        by_index_labels[index] = normalized_labels
        by_index_spans[index] = normalized_spans

    results: list[SentenceClassification] = []
    for index, sentence in enumerate(sentences):
        labels = by_index_labels.get(index)
        label_spans = by_index_spans.get(index)
        if labels is None:
            labels = {dimension_name: [] for dimension_name in expected_dimensions}
        if label_spans is None:
            label_spans = {dimension_name: {} for dimension_name in expected_dimensions}
        results.append(
            SentenceClassification(
                sentence_index=index,
                sentence=sentence,
                labels=labels,
                label_spans=label_spans,
            )
        )
    return results


def classify_message(
    *,
    message: MessageRecord,
    taxonomy: Taxonomy,
    model: str,
    debug: bool,
) -> MessageClassification:
    """Classify one message sentence-by-sentence using the provided taxonomy."""
    sentences = split_sentences(message.message)
    if not sentences:
        return MessageClassification(message=message, sentences=[])

    prompt_messages = _build_classifier_messages(taxonomy=taxonomy, sentences=sentences)
    max_tokens = max(768, min(4096, 256 + 220 * len(sentences)))
    payload: dict[str, Any] | None = None
    response = ""
    for attempt in range(2):
        response = chat(
            model,
            prompt_messages,
            temperature=0.0,
            max_tokens=max_tokens,
            include_reasoning=False,
            debug=debug,
            debug_label=f"transcript_analysis.{message.analysis_type}",
        )
        try:
            payload = _extract_json_payload(response)
            break
        except ValueError:
            if attempt == 1:
                raise
            prompt_messages = prompt_messages + [
                {"role": "assistant", "content": response},
                {
                    "role": "user",
                    "content": (
                        "Your previous output was invalid. Return ONLY valid JSON "
                        "that matches the required schema."
                    ),
                },
            ]

    if payload is None:
        raise ValueError("Classifier did not produce valid JSON output.")
    normalized = _normalize_sentence_classifications(
        payload=payload,
        sentences=sentences,
        taxonomy=taxonomy,
    )
    return MessageClassification(message=message, sentences=normalized)


def aggregate_classifications(
    classifications: list[MessageClassification], taxonomies: dict[str, Taxonomy]
) -> dict[str, Any]:
    """Aggregate sentence and message label distributions."""
    by_type: dict[str, list[MessageClassification]] = defaultdict(list)
    for classification in classifications:
        by_type[classification.message.analysis_type].append(classification)

    summary: dict[str, Any] = {}
    for analysis_type, items in by_type.items():
        taxonomy = taxonomies[analysis_type]
        message_count = len(items)
        sentence_count = sum(len(item.sentences) for item in items)

        dimensions_summary: dict[str, Any] = {}
        for dimension in taxonomy.dimensions:
            sentence_label_counts: Counter[str] = Counter()
            message_label_counts: Counter[str] = Counter()
            messages_with_any = 0
            sentences_with_any = 0
            message_label_sets: list[set[str]] = []
            message_speakers: list[str] = []
            message_should_advise: list[bool | None] = []
            message_risk_levels: list[str | None] = []

            for item in items:
                message_has_any = False
                labels_seen_in_message: set[str] = set()

                for sentence in item.sentences:
                    labels = sentence.labels.get(dimension.name, [])
                    if labels:
                        sentences_with_any += 1
                        message_has_any = True
                    for label in labels:
                        sentence_label_counts[label] += 1
                        labels_seen_in_message.add(label)

                if message_has_any:
                    messages_with_any += 1
                for label in labels_seen_in_message:
                    message_label_counts[label] += 1

                message_label_sets.append(labels_seen_in_message)
                message_speakers.append(item.message.speaker)
                message_should_advise.append(item.message.warden_should_advise)
                message_risk_levels.append(item.message.warden_risk_level)

            labels_summary: dict[str, Any] = {}
            for label_name in dimension.labels:
                sentence_hits = sentence_label_counts.get(label_name, 0)
                message_hits = message_label_counts.get(label_name, 0)
                labels_summary[label_name] = {
                    "description": dimension.labels[label_name],
                    "sentence_count": sentence_hits,
                    "sentence_pct": (100.0 * sentence_hits / sentence_count)
                    if sentence_count
                    else 0.0,
                    "message_count": message_hits,
                    "message_pct": (100.0 * message_hits / message_count)
                    if message_count
                    else 0.0,
                }

            warden_linkage_summary: dict[str, Any] | None = None
            if analysis_type == "requester":
                labels_warden_summary: dict[str, Any] = {}
                for label_name in dimension.labels:
                    total_messages = 0
                    with_warden_record = 0
                    flagged_messages = 0
                    risk_counts: Counter[str] = Counter()
                    by_speaker: dict[str, dict[str, Any]] = {}
                    for speaker in ("adversary", "benign_agent"):
                        by_speaker[speaker] = {
                            "messages_with_label": 0,
                            "messages_with_warden_record": 0,
                            "flagged_messages": 0,
                            "flagged_pct_of_warden_messages": None,
                            "risk_level_counts": {
                                "LOW": 0,
                                "MEDIUM": 0,
                                "HIGH": 0,
                                "UNKNOWN": 0,
                            },
                        }

                    for labels_seen, speaker, should_advise, risk_level in zip(
                        message_label_sets,
                        message_speakers,
                        message_should_advise,
                        message_risk_levels,
                    ):
                        if label_name not in labels_seen:
                            continue
                        total_messages += 1
                        if speaker in by_speaker:
                            by_speaker[speaker]["messages_with_label"] += 1

                        if should_advise is None:
                            continue

                        with_warden_record += 1
                        if speaker in by_speaker:
                            by_speaker[speaker]["messages_with_warden_record"] += 1

                        normalized_risk = (
                            risk_level
                            if risk_level in {"LOW", "MEDIUM", "HIGH", "UNKNOWN"}
                            else "UNKNOWN"
                        )
                        risk_counts[normalized_risk] += 1
                        if speaker in by_speaker:
                            by_speaker[speaker]["risk_level_counts"][normalized_risk] += 1

                        if should_advise:
                            flagged_messages += 1
                            if speaker in by_speaker:
                                by_speaker[speaker]["flagged_messages"] += 1

                    flagged_pct = (
                        (100.0 * flagged_messages / with_warden_record)
                        if with_warden_record > 0
                        else None
                    )
                    for speaker in ("adversary", "benign_agent"):
                        speaker_counts = by_speaker[speaker]
                        speaker_with_record = speaker_counts["messages_with_warden_record"]
                        speaker_flagged = speaker_counts["flagged_messages"]
                        speaker_counts["flagged_pct_of_warden_messages"] = (
                            (100.0 * speaker_flagged / speaker_with_record)
                            if speaker_with_record > 0
                            else None
                        )

                    adv_pct = by_speaker["adversary"]["flagged_pct_of_warden_messages"]
                    ben_pct = by_speaker["benign_agent"]["flagged_pct_of_warden_messages"]
                    if isinstance(adv_pct, (int, float)) and isinstance(ben_pct, (int, float)):
                        delta_pp = adv_pct - ben_pct
                    else:
                        delta_pp = None

                    labels_warden_summary[label_name] = {
                        "messages_with_label": total_messages,
                        "messages_with_warden_record": with_warden_record,
                        "flagged_messages": flagged_messages,
                        "flagged_pct_of_warden_messages": flagged_pct,
                        "risk_level_counts": {
                            "LOW": risk_counts.get("LOW", 0),
                            "MEDIUM": risk_counts.get("MEDIUM", 0),
                            "HIGH": risk_counts.get("HIGH", 0),
                            "UNKNOWN": risk_counts.get("UNKNOWN", 0),
                        },
                        "by_speaker": by_speaker,
                        "delta_flagged_pct_pp_adversary_minus_benign": delta_pp,
                    }

                total_with_record = sum(
                    1 for should_advise in message_should_advise if should_advise is not None
                )
                total_flagged = sum(
                    1 for should_advise in message_should_advise if should_advise is True
                )
                warden_linkage_summary = {
                    "messages_with_warden_record": total_with_record,
                    "flagged_messages": total_flagged,
                    "flagged_pct_of_warden_messages": (
                        (100.0 * total_flagged / total_with_record)
                        if total_with_record > 0
                        else None
                    ),
                    "labels": labels_warden_summary,
                }

            dimensions_summary[dimension.name] = {
                "description": dimension.description,
                "allow_multiple": dimension.allow_multiple,
                "messages_with_any_label": messages_with_any,
                "messages_with_any_label_pct": (
                    (100.0 * messages_with_any / message_count) if message_count else 0.0
                ),
                "sentences_with_any_label": sentences_with_any,
                "sentences_with_any_label_pct": (
                    (100.0 * sentences_with_any / sentence_count) if sentence_count else 0.0
                ),
                "labels": labels_summary,
            }
            if warden_linkage_summary is not None:
                dimensions_summary[dimension.name]["warden_linkage"] = warden_linkage_summary

        summary[analysis_type] = {
            "message_count": message_count,
            "sentence_count": sentence_count,
            "dimensions": dimensions_summary,
        }

    return summary


def print_summary(summary: dict[str, Any]) -> None:
    """Render aggregated stats in tables."""
    for analysis_type in sorted(summary.keys()):
        type_data = summary[analysis_type]
        console.print()
        console.print(
            f"[bold]{analysis_type.upper()}[/bold] "
            f"(messages={type_data['message_count']}, sentences={type_data['sentence_count']})"
        )

        for dimension_name, dimension_data in type_data["dimensions"].items():
            table = Table(
                title=f"{analysis_type} :: {dimension_name}",
                show_header=True,
            )
            table.add_column("Label", style="magenta")
            table.add_column("Sentence Count", justify="right")
            table.add_column("Sentence %", justify="right")
            table.add_column("Message Count", justify="right")
            table.add_column("Message %", justify="right")

            for label_name, label_stats in dimension_data["labels"].items():
                table.add_row(
                    label_name,
                    str(label_stats["sentence_count"]),
                    f"{label_stats['sentence_pct']:.1f}%",
                    str(label_stats["message_count"]),
                    f"{label_stats['message_pct']:.1f}%",
                )

            table.caption = (
                "messages with any label: "
                f"{dimension_data['messages_with_any_label']} "
                f"({dimension_data['messages_with_any_label_pct']:.1f}%), "
                "sentences with any label: "
                f"{dimension_data['sentences_with_any_label']} "
                f"({dimension_data['sentences_with_any_label_pct']:.1f}%)"
            )
            console.print(table)

            warden_linkage = dimension_data.get("warden_linkage")
            if isinstance(warden_linkage, dict):
                linkage_table = Table(
                    title=f"{analysis_type} :: {dimension_name} :: warden linkage",
                    show_header=True,
                )
                linkage_table.add_column("Label", style="magenta")
                linkage_table.add_column("Flag % (all)", justify="right")
                linkage_table.add_column("Flag % (adv)", justify="right")
                linkage_table.add_column("Flag % (benign)", justify="right")
                linkage_table.add_column("Delta (pp)", justify="right")
                linkage_table.add_column("Risk L/M/H/U", justify="right")

                labels_blob = warden_linkage.get("labels", {})
                if not isinstance(labels_blob, dict):
                    labels_blob = {}

                for label_name, label_stats in labels_blob.items():
                    if not isinstance(label_stats, dict):
                        continue
                    pct_all = label_stats.get("flagged_pct_of_warden_messages")
                    by_speaker = label_stats.get("by_speaker", {})
                    if not isinstance(by_speaker, dict):
                        by_speaker = {}
                    adv_stats = by_speaker.get("adversary", {})
                    ben_stats = by_speaker.get("benign_agent", {})
                    adv_pct = (
                        adv_stats.get("flagged_pct_of_warden_messages")
                        if isinstance(adv_stats, dict)
                        else None
                    )
                    ben_pct = (
                        ben_stats.get("flagged_pct_of_warden_messages")
                        if isinstance(ben_stats, dict)
                        else None
                    )
                    delta = label_stats.get("delta_flagged_pct_pp_adversary_minus_benign")
                    if not isinstance(delta, (int, float)):
                        if isinstance(adv_pct, (int, float)) and isinstance(ben_pct, (int, float)):
                            delta = adv_pct - ben_pct
                        else:
                            delta = None

                    risk_counts = label_stats.get("risk_level_counts", {})
                    if not isinstance(risk_counts, dict):
                        risk_counts = {}
                    risk_str = (
                        f"{risk_counts.get('LOW', 0)}/"
                        f"{risk_counts.get('MEDIUM', 0)}/"
                        f"{risk_counts.get('HIGH', 0)}/"
                        f"{risk_counts.get('UNKNOWN', 0)}"
                    )

                    linkage_table.add_row(
                        label_name,
                        f"{pct_all:.1f}%" if isinstance(pct_all, (int, float)) else "n/a",
                        f"{adv_pct:.1f}%" if isinstance(adv_pct, (int, float)) else "n/a",
                        f"{ben_pct:.1f}%" if isinstance(ben_pct, (int, float)) else "n/a",
                        f"{delta:+.1f} pp" if isinstance(delta, (int, float)) else "n/a",
                        risk_str,
                    )

                linkage_table.caption = (
                    "Flag rates use messages with a linked warden advisory record as denominator."
                )
                console.print(linkage_table)


def _serialize_classifications(classifications: list[MessageClassification]) -> list[dict[str, Any]]:
    serialized: list[dict[str, Any]] = []
    for item in classifications:
        serialized.append(
            {
                "log_file": item.message.log_file,
                "scenario": item.message.scenario,
                "tag": item.message.tag,
                "analysis_type": item.message.analysis_type,
                "speaker": item.message.speaker,
                "turn": item.message.turn,
                "warden_turn": item.message.warden_turn,
                "warden_should_advise": item.message.warden_should_advise,
                "warden_risk_level": item.message.warden_risk_level,
                "warden_content": item.message.warden_content,
                "message": item.message.message,
                "sentences": [
                    {
                        "sentence_index": sentence.sentence_index,
                        "sentence": sentence.sentence,
                        "labels": sentence.labels,
                        "label_spans": sentence.label_spans,
                    }
                    for sentence in item.sentences
                ],
            }
        )
    return serialized


def _format_plan_line(label: str, value: str, width: int = 88) -> str:
    prefix = f"{label:<20}: "
    return textwrap.fill(
        value,
        width=width,
        initial_indent=prefix,
        subsequent_indent=" " * len(prefix),
    )


def _safe_filename_component(value: str) -> str:
    cleaned = SAFE_FILENAME_RE.sub("-", value).strip("-._")
    return cleaned or "selection"


def _resolve_output_json_path(
    output_json_arg: str,
    *,
    analysis_types: set[str],
    file_patterns: list[str],
    tags: set[str],
) -> Path:
    arg = output_json_arg.strip()
    if arg and arg.lower() != "auto":
        candidate_name = Path(arg).name
        if candidate_name and candidate_name.lower().endswith(".json"):
            return TRANSCRIPT_OUTPUT_DIR / candidate_name
        if candidate_name:
            return TRANSCRIPT_OUTPUT_DIR / f"{candidate_name}.json"

    if tags:
        selector = "tags-" + "-".join(_safe_filename_component(tag) for tag in sorted(tags))
    elif file_patterns:
        selector = "files-" + "-".join(
            _safe_filename_component(pattern) for pattern in file_patterns[:3]
        )
    else:
        selector = "selection"
    selector = selector[:90]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    analysis_type_component = "-".join(sorted(analysis_types))
    filename = (
        f"transcript_analysis_{analysis_type_component}_{selector}_{timestamp}.json"
    )
    return TRANSCRIPT_OUTPUT_DIR / filename


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sentence-level taxonomy classification for transcript logs."
    )
    parser.add_argument(
        "--file-name",
        action="append",
        help=(
            "Filename filter(s) for logs. Repeatable. Supports exact names, "
            "substrings, and glob patterns. Also accepts comma-separated values."
        ),
    )
    parser.add_argument(
        "--tag",
        action="append",
        help="Tag filter(s). Repeatable and comma-separated values are supported.",
    )
    parser.add_argument(
        "--analysis-type",
        nargs="+",
        choices=["requester", "target", "warden", "all"],
        default=["all"],
        help=(
            "Which actor messages to analyze. Accepts one or more values "
            "(e.g. --analysis-type requester warden). Default: all."
        ),
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model for classification (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--taxonomy-file",
        type=Path,
        default=DEFAULT_TAXONOMY_PATH,
        help=(
            "YAML/JSON file defining per-analysis-type taxonomies "
            f"(default: {DEFAULT_TAXONOMY_PATH})."
        ),
    )
    parser.add_argument(
        "--few-shot-file",
        type=Path,
        help=(
            "Optional YAML/JSON file with additional few-shot examples "
            "to merge into the taxonomy."
        ),
    )
    parser.add_argument(
        "--max-messages",
        type=int,
        help="Optional cap on extracted messages (useful for quick iteration).",
    )
    parser.add_argument(
        "--output-json",
        nargs="?",
        const="auto",
        help=(
            "Write full classifications + summary JSON to analysis/transcript_output/. "
            "Optionally provide a filename; any directory component is ignored."
        ),
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print full classification prompts via src.client debug mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    file_patterns = _parse_repeated_values(args.file_name)
    tags = set(_parse_repeated_values(args.tag))
    analysis_types = set(args.analysis_type)
    if "all" in analysis_types:
        analysis_types = set(REQUESTED_ANALYSIS_TYPES)
    analysis_types_display = ",".join(sorted(analysis_types))

    if not file_patterns and not tags:
        raise SystemExit("Provide at least one selector: --file-name or --tag")

    taxonomies = load_taxonomies(args.taxonomy_file)
    if args.few_shot_file:
        extra_examples = load_additional_few_shots(args.few_shot_file)
        merge_additional_few_shots(taxonomies, extra_examples)

    logs = load_filtered_logs(file_patterns=file_patterns, tags=tags)
    if not logs:
        console.print("[yellow]No logs matched the provided filters.[/yellow]")
        return

    messages = extract_messages(logs, analysis_types)
    uncapped_message_count = len(messages)
    logs_with_relevant_messages = {message.log_file for message in messages}
    if args.max_messages is not None:
        if args.max_messages <= 0:
            raise SystemExit("--max-messages must be a positive integer")
        messages = messages[: args.max_messages]

    if not messages:
        console.print(
            "[yellow]No messages found for the selected analysis type(s).[/yellow]"
        )
        return

    logs_to_annotate = {message.log_file for message in messages}
    print("\n=== Analysis Plan ===")
    print(_format_plan_line("Matched logs", str(len(logs))))
    print(
        _format_plan_line(
            "Logs with messages",
            (
                f"{len(logs_with_relevant_messages)} "
                f"(analysis_type={analysis_types_display})"
            ),
        )
    )
    print(_format_plan_line("Logs to annotate", str(len(logs_to_annotate))))
    if args.max_messages is not None and uncapped_message_count > len(messages):
        print(
            _format_plan_line(
                "Messages to annotate",
                f"{len(messages)} (capped from {uncapped_message_count} by --max-messages)",
            )
        )
    else:
        print(_format_plan_line("Messages to annotate", str(len(messages))))
    output_json_path: Path | None = None
    if args.output_json:
        output_json_path = _resolve_output_json_path(
            args.output_json,
            analysis_types=analysis_types,
            file_patterns=file_patterns,
            tags=tags,
        )

    print(_format_plan_line("Model", args.model))
    print(_format_plan_line("Taxonomy file", str(args.taxonomy_file)))
    print(
        _format_plan_line(
            "Few-shot file",
            str(args.few_shot_file) if args.few_shot_file else "(none)",
        )
    )
    print(_format_plan_line("Analysis types", analysis_types_display))
    if "warden" in analysis_types:
        print(
            _format_plan_line(
                "Warden labeling",
                "Only advisories with risk_level HIGH or MEDIUM are included.",
            )
        )
    if output_json_path:
        print(_format_plan_line("Output JSON", str(output_json_path)))
    print()
    while True:
        proceed = input("Continue? [y/n]: ").strip().lower()
        if proceed in {"y", "yes"}:
            break
        if proceed in {"n", "no"}:
            print("Aborted.")
            return

    classifications: list[MessageClassification] = []
    for index, message in enumerate(messages, start=1):
        if index == 1 or index % 10 == 0 or index == len(messages):
            console.print(
                f"[dim]Classifying message {index}/{len(messages)} "
                f"({message.analysis_type})[/dim]"
            )
        taxonomy = taxonomies[message.analysis_type]
        classification = classify_message(
            message=message,
            taxonomy=taxonomy,
            model=args.model,
            debug=args.debug,
        )
        classifications.append(classification)

    summary = aggregate_classifications(classifications, taxonomies)
    print_summary(summary)

    if output_json_path:
        payload = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "model": args.model,
            "filters": {
                "file_name": file_patterns,
                "tag": sorted(tags),
                "analysis_type": sorted(analysis_types),
                "max_messages": args.max_messages,
            },
            "taxonomy_file": str(args.taxonomy_file),
            "few_shot_file": str(args.few_shot_file) if args.few_shot_file else None,
            "selected_logs": [path.name for path, _ in logs],
            "summary": summary,
            "classifications": _serialize_classifications(classifications),
        }
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        output_json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
        console.print(f"\n[green]Wrote output to {output_json_path}[/green]")


if __name__ == "__main__":
    main()
