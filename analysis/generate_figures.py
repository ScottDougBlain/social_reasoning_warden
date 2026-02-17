#!/usr/bin/env python
"""Generate publication-ready figures from experiment logs."""

import json
from collections import Counter
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from analysis.metrics import (
    _get_decision,
    _has_warden,
    _log_speaker,
    _success_rate_by_label,
    load_logs,
)

FIGURES_DIR = Path(__file__).resolve().parents[1] / "figures"
FIGURES_DIR.mkdir(exist_ok=True)

# Color palette
C_ADV_NO_WARDEN = "#ef553b"  # red — adversary without warden
C_ADV_WARDEN = "#636efa"     # blue — adversary with warden
C_BENIGN_NO_WARDEN = "#ffa15a"  # orange — benign without warden
C_BENIGN_WARDEN = "#00cc96"  # green — benign with warden
C_SUCCESS = "#ef553b"
C_FAILURE = "#00cc96"
C_ERROR = "#ffa15a"


def _save(fig: go.Figure, name: str) -> None:
    png_path = FIGURES_DIR / f"{name}.png"
    html_path = FIGURES_DIR / f"{name}.html"
    fig.write_image(str(png_path), scale=2)
    fig.write_html(str(html_path), include_plotlyjs="cdn")
    print(f"  Saved {png_path.name} + {html_path.name}")


def _compute_rates(
    logs: list[dict], by_fn, speaker_filter: str | None = None
) -> dict:
    filtered = logs
    if speaker_filter:
        filtered = [log for log in logs if _log_speaker(log) == speaker_filter]
    return _success_rate_by_label(filtered, by_fn)


# ---------------------------------------------------------------------------
# Figure 1: Warden effect — adversary SR with vs without warden, by scenario
# ---------------------------------------------------------------------------
def fig_warden_effect(logs: list[dict]) -> None:
    print("Fig 1: Warden effect on adversary success rate...")
    adv_logs = [log for log in logs if _log_speaker(log) == "adversary"]

    scenarios = sorted({log.get("scenario", "?") for log in adv_logs})

    counts: dict[tuple[str, bool], dict] = {}
    for log in adv_logs:
        scenario = log.get("scenario", "?")
        has_w = _has_warden(log)
        key = (scenario, has_w)
        if key not in counts:
            counts[key] = {"total": 0, "success": 0}
        decision = _get_decision(log)
        if decision in {"requester_success", "requester_failure"}:
            counts[key]["total"] += 1
            if decision == "requester_success":
                counts[key]["success"] += 1

    # Filter to scenarios with data in both conditions
    both = [s for s in scenarios
            if counts.get((s, False), {}).get("total", 0) > 0
            and counts.get((s, True), {}).get("total", 0) > 0]

    # Sort by no-warden SR descending
    both.sort(key=lambda s: -(counts[(s, False)]["success"] / counts[(s, False)]["total"]))

    no_w_rates = []
    w_rates = []
    no_w_text = []
    w_text = []
    for s in both:
        c_nw = counts[(s, False)]
        c_w = counts[(s, True)]
        r_nw = c_nw["success"] / c_nw["total"] if c_nw["total"] else 0
        r_w = c_w["success"] / c_w["total"] if c_w["total"] else 0
        no_w_rates.append(r_nw)
        w_rates.append(r_w)
        no_w_text.append(f"{c_nw['success']}/{c_nw['total']}")
        w_text.append(f"{c_w['success']}/{c_w['total']}")

    fig = go.Figure(data=[
        go.Bar(
            name="No Warden", x=both, y=no_w_rates,
            text=no_w_text, textposition="outside", textfont=dict(size=9),
            marker_color=C_ADV_NO_WARDEN,
        ),
        go.Bar(
            name="With Warden", x=both, y=w_rates,
            text=w_text, textposition="outside", textfont=dict(size=9),
            marker_color=C_ADV_WARDEN,
        ),
    ])
    fig.update_layout(
        title=dict(text="Adversary Success Rate: Warden vs No Warden", font=dict(size=18)),
        xaxis_title="Scenario",
        yaxis=dict(title="Success Rate", range=[0, 1.12], tickformat=".0%"),
        barmode="group",
        height=550,
        width=max(900, len(both) * 65 + 200),
        legend=dict(x=0.85, y=0.98),
        xaxis_tickangle=-35,
        margin=dict(b=120),
    )
    _save(fig, "01_warden_effect")


# ---------------------------------------------------------------------------
# Figure 2: Adversary vs Benign overall success rates by condition
# ---------------------------------------------------------------------------
def fig_adversary_vs_benign(logs: list[dict]) -> None:
    print("Fig 2: Adversary vs Benign success rates by condition...")

    def condition_label(log: dict) -> str | None:
        has_w = _has_warden(log)
        condition = log.get("condition", "")
        has_data = "adversary_data" in condition or bool(log.get("adversary_has_data"))
        parts = []
        parts.append("Warden" if has_w else "No Warden")
        if has_data:
            parts.append("+ Intel")
        return " ".join(parts)

    conditions = ["No Warden", "No Warden + Intel", "Warden", "Warden + Intel"]
    colors = {
        "adversary": {
            "No Warden": C_ADV_NO_WARDEN,
            "No Warden + Intel": "#c62828",
            "Warden": C_ADV_WARDEN,
            "Warden + Intel": "#283593",
        },
        "benign_agent": {
            "No Warden": C_BENIGN_NO_WARDEN,
            "No Warden + Intel": "#e65100",
            "Warden": C_BENIGN_WARDEN,
            "Warden + Intel": "#00796b",
        },
    }

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["<b>Adversary</b>", "<b>Benign Agent</b>"],
        horizontal_spacing=0.12,
    )

    for col, speaker in enumerate(["adversary", "benign_agent"], 1):
        speaker_logs = [log for log in logs if _log_speaker(log) == speaker]
        rates = _success_rate_by_label(speaker_logs, condition_label)
        present = [c for c in conditions if c in rates]
        vals = [rates[c]["rate"] for c in present]
        texts = [f"{rates[c]['requester_success']}/{rates[c]['total']}" for c in present]
        bar_colors = [colors[speaker].get(c, "#999") for c in present]

        fig.add_trace(go.Bar(
            x=present, y=vals, text=texts,
            textposition="outside", textfont=dict(size=11),
            marker_color=bar_colors,
            showlegend=False,
        ), row=1, col=col)

    fig.update_yaxes(range=[0, 1.12], tickformat=".0%", title_text="Success Rate")
    fig.update_layout(
        title=dict(text="Success Rates by Condition", font=dict(size=18)),
        height=450, width=850,
        margin=dict(t=100),
    )
    _save(fig, "02_adversary_vs_benign")


# ---------------------------------------------------------------------------
# Figure 3: Scenario x Profile heatmap (adversary only)
# ---------------------------------------------------------------------------
def fig_scenario_profile_heatmap(logs: list[dict]) -> None:
    print("Fig 3: Scenario x Profile heatmap...")

    def extract_profile(log: dict) -> str | None:
        profile = log.get("profile") or {}
        if isinstance(profile, dict):
            return profile.get("name")
        return None

    adv_profiled = [
        log for log in logs
        if _log_speaker(log) == "adversary" and extract_profile(log)
    ]
    if not adv_profiled:
        # Multi-target: try profiles list
        adv_profiled = [
            log for log in logs
            if _log_speaker(log) == "adversary"
            and log.get("profiles")
            and any(p.get("name") for p in log.get("profiles", []) if isinstance(p, dict))
        ]

    if not adv_profiled:
        print("  Skipping — no profiled adversary logs.")
        return

    scenarios = sorted({log.get("scenario", "?") for log in adv_profiled})
    profiles = sorted({extract_profile(log) for log in adv_profiled if extract_profile(log)})

    if not profiles:
        print("  Skipping — no profile names found.")
        return

    counts: dict[tuple[str, str], dict] = {}
    for log in adv_profiled:
        s = log.get("scenario", "?")
        p = extract_profile(log)
        if not p:
            continue
        key = (s, p)
        if key not in counts:
            counts[key] = {"total": 0, "success": 0}
        decision = _get_decision(log)
        if decision in {"requester_success", "requester_failure"}:
            counts[key]["total"] += 1
            if decision == "requester_success":
                counts[key]["success"] += 1

    z = []
    hover = []
    for s in scenarios:
        row = []
        hover_row = []
        for p in profiles:
            c = counts.get((s, p), {"total": 0, "success": 0})
            rate = c["success"] / c["total"] if c["total"] > 0 else None
            row.append(rate)
            if c["total"] > 0:
                hover_row.append(f"{s}<br>{p}<br>{rate:.0%} ({c['success']}/{c['total']})")
            else:
                hover_row.append(f"{s}<br>{p}<br>No data")
        z.append(row)
        hover.append(hover_row)

    fig = go.Figure(data=go.Heatmap(
        z=z, x=profiles, y=scenarios,
        hovertext=hover, hoverinfo="text",
        colorscale="RdYlGn_r", zmin=0, zmax=1,
        colorbar=dict(title="Adversary SR", tickformat=".0%"),
    ))
    fig.update_layout(
        title=dict(text="Adversary Success Rate: Scenario x Profile", font=dict(size=18)),
        xaxis_title="Target Profile",
        yaxis_title="Scenario",
        height=max(500, len(scenarios) * 40 + 200),
        width=max(700, len(profiles) * 130 + 200),
        margin=dict(l=180),
    )
    _save(fig, "03_scenario_profile_heatmap")


# ---------------------------------------------------------------------------
# Figure 4: Success rate by requester model
# ---------------------------------------------------------------------------
def fig_by_model(logs: list[dict]) -> None:
    print("Fig 4: Success rate by requester model...")

    def requester_model(log: dict) -> str | None:
        models = log.get("models", {})
        m = models.get("adversary") or models.get("benign_agent")
        if m:
            return m.split("/")[-1] if "/" in m else m
        return None

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["<b>Adversary SR by Model</b>", "<b>Benign Agent SR by Model</b>"],
        horizontal_spacing=0.15,
    )

    for col, speaker in enumerate(["adversary", "benign_agent"], 1):
        speaker_logs = [log for log in logs if _log_speaker(log) == speaker]
        rates = _success_rate_by_label(speaker_logs, requester_model)
        # Filter to models with >= 3 runs
        models = sorted(
            [m for m, c in rates.items() if c["total"] >= 3],
            key=lambda m: -rates[m]["rate"],
        )
        vals = [rates[m]["rate"] for m in models]
        texts = [f"{rates[m]['requester_success']}/{rates[m]['total']}" for m in models]

        fig.add_trace(go.Bar(
            x=models, y=vals, text=texts,
            textposition="outside", textfont=dict(size=9),
            marker_color=C_ADV_NO_WARDEN if speaker == "adversary" else C_BENIGN_NO_WARDEN,
            showlegend=False,
        ), row=1, col=col)

    fig.update_yaxes(range=[0, 1.15], tickformat=".0%", title_text="Success Rate")
    fig.update_xaxes(tickangle=-35)
    fig.update_layout(
        title=dict(text="Success Rate by Requester Model (n >= 3)", font=dict(size=18)),
        height=500, width=1100,
        margin=dict(b=130, t=100),
    )
    _save(fig, "04_by_model")


# ---------------------------------------------------------------------------
# Figure 5: Outcome distribution by scenario (adversary runs)
# ---------------------------------------------------------------------------
def fig_outcome_breakdown(logs: list[dict]) -> None:
    print("Fig 5: Outcome breakdown by scenario...")
    adv_logs = [log for log in logs if _log_speaker(log) == "adversary"]
    scenarios = sorted({log.get("scenario", "?") for log in adv_logs})

    outcome_types = ["requester_success", "requester_failure", "formatting_failure"]
    counts: dict[str, Counter] = {s: Counter() for s in scenarios}
    for log in adv_logs:
        s = log.get("scenario", "?")
        d = _get_decision(log) or "formatting_failure"
        if d not in outcome_types:
            d = "formatting_failure"
        counts[s][d] += 1

    colors = {"requester_success": C_SUCCESS, "requester_failure": C_FAILURE,
              "formatting_failure": C_ERROR}
    labels = {"requester_success": "Adversary Success", "requester_failure": "Target Resisted",
              "formatting_failure": "Parse Error"}

    fig = go.Figure()
    for o in outcome_types:
        vals = [counts[s][o] for s in scenarios]
        if any(v > 0 for v in vals):
            fig.add_trace(go.Bar(name=labels[o], x=scenarios, y=vals, marker_color=colors[o]))

    fig.update_layout(
        title=dict(text="Outcome Distribution (Adversary Runs)", font=dict(size=18)),
        xaxis_title="Scenario", yaxis_title="Count",
        barmode="stack",
        height=500, width=max(900, len(scenarios) * 55 + 200),
        xaxis_tickangle=-35,
        margin=dict(b=120),
        legend=dict(x=0.01, y=0.98),
    )
    _save(fig, "05_outcome_breakdown")


# ---------------------------------------------------------------------------
# Figure 6: Warden SR difference (no_warden SR - warden SR) per scenario
# ---------------------------------------------------------------------------
def fig_warden_delta(logs: list[dict]) -> None:
    print("Fig 6: Warden SR delta by scenario...")
    adv_logs = [log for log in logs if _log_speaker(log) == "adversary"]

    counts: dict[tuple[str, bool], dict] = {}
    for log in adv_logs:
        s = log.get("scenario", "?")
        w = _has_warden(log)
        key = (s, w)
        if key not in counts:
            counts[key] = {"total": 0, "success": 0}
        d = _get_decision(log)
        if d in {"requester_success", "requester_failure"}:
            counts[key]["total"] += 1
            if d == "requester_success":
                counts[key]["success"] += 1

    scenarios = sorted({s for s, _ in counts.keys()})
    both = [s for s in scenarios
            if counts.get((s, False), {}).get("total", 0) >= 2
            and counts.get((s, True), {}).get("total", 0) >= 2]

    deltas = []
    for s in both:
        nw = counts[(s, False)]
        w = counts[(s, True)]
        r_nw = nw["success"] / nw["total"]
        r_w = w["success"] / w["total"]
        deltas.append((s, r_nw - r_w, r_nw, r_w))

    deltas.sort(key=lambda x: -x[1])
    names = [d[0] for d in deltas]
    vals = [d[1] for d in deltas]
    colors = ["#00cc96" if v > 0 else "#ef553b" for v in vals]
    hover = [f"{d[0]}<br>No warden: {d[2]:.0%}<br>Warden: {d[3]:.0%}<br>Delta: {d[1]:+.0%}"
             for d in deltas]

    fig = go.Figure(go.Bar(
        x=names, y=vals,
        marker_color=colors,
        hovertext=hover, hoverinfo="text",
        text=[f"{v:+.0%}" for v in vals],
        textposition="outside", textfont=dict(size=9),
    ))
    fig.update_layout(
        title=dict(text="Warden Effect: SR Reduction per Scenario<br>"
                        "<sup>(positive = warden helped target resist)</sup>",
                   font=dict(size=16)),
        xaxis_title="Scenario",
        yaxis=dict(title="SR(no warden) - SR(warden)", tickformat="+.0%",
                   zeroline=True, zerolinewidth=2, zerolinecolor="black"),
        height=500,
        width=max(900, len(names) * 55 + 200),
        xaxis_tickangle=-35,
        margin=dict(b=120),
    )
    _save(fig, "06_warden_delta")


# ---------------------------------------------------------------------------
# Figure 7: Multi-target vote distributions
# ---------------------------------------------------------------------------
def fig_multi_target_votes(logs: list[dict]) -> None:
    print("Fig 7: Multi-target vote distributions...")
    multi_adv = [
        log for log in logs
        if _log_speaker(log) == "adversary"
        and log.get("scenario_type") == "multi_target"
        and log.get("outcome", {}).get("vote_tally")
    ]
    if not multi_adv:
        print("  Skipping — no multi-target adversary logs with vote tallies.")
        return

    scenarios = sorted({log.get("scenario", "?") for log in multi_adv})

    # Average vote counts per scenario
    avg_votes: dict[str, dict] = {}
    for s in scenarios:
        s_logs = [log for log in multi_adv if log.get("scenario") == s]
        accepts = [log["outcome"]["vote_tally"].get("accept", 0) for log in s_logs]
        rejects = [log["outcome"]["vote_tally"].get("reject", 0) for log in s_logs]
        errors = [log["outcome"]["vote_tally"].get("formatting_failure", 0) for log in s_logs]
        n = len(s_logs)
        avg_votes[s] = {
            "accept": sum(accepts) / n,
            "reject": sum(rejects) / n,
            "error": sum(errors) / n,
            "n": n,
        }

    scenarios.sort(key=lambda s: -avg_votes[s]["accept"])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Votes for Adversary",
        x=scenarios,
        y=[avg_votes[s]["accept"] for s in scenarios],
        marker_color=C_SUCCESS,
    ))
    fig.add_trace(go.Bar(
        name="Votes Against",
        x=scenarios,
        y=[avg_votes[s]["reject"] for s in scenarios],
        marker_color=C_FAILURE,
    ))

    fig.update_layout(
        title=dict(text="Multi-Target: Average Vote Split (Adversary Runs)",
                   font=dict(size=18)),
        xaxis_title="Scenario",
        yaxis_title="Avg Votes (of 5)",
        barmode="stack",
        height=500,
        width=max(900, len(scenarios) * 55 + 200),
        xaxis_tickangle=-35,
        margin=dict(b=120),
        legend=dict(x=0.01, y=0.98),
    )
    _save(fig, "07_multi_target_votes")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print(f"Loading logs...")
    logs = load_logs()
    print(f"Loaded {len(logs)} logs.\n")

    fig_warden_effect(logs)
    fig_adversary_vs_benign(logs)
    fig_scenario_profile_heatmap(logs)
    fig_by_model(logs)
    fig_outcome_breakdown(logs)
    fig_warden_delta(logs)
    fig_multi_target_votes(logs)

    print(f"\nAll figures saved to {FIGURES_DIR}/")


if __name__ == "__main__":
    main()
