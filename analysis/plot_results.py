#!/usr/bin/env python3
"""
Publication-quality figures for Social Reasoning Warden.

Generates key result plots from the three main studies:
  - dossier_effect: dossier × warden factorial
  - cap_asym: warden capability tier
  - skeptical_ablation: baseline vs skeptical vs warden × requester type

When emmeans JSON files exist (from extract_emmeans.py), figures use GLME-adjusted
estimated marginal means with asymptotic CIs. Otherwise falls back to raw Wilson CIs.

Usage:
    python analysis/plot_results.py
    python analysis/plot_results.py --output-dir results/figures
    python analysis/plot_results.py --raw   # force raw rates even if emmeans exist
    python analysis/plot_results.py --dossier-tag final-within-family \
        --cap-asym-tag final-within-family \
        --skeptical-tag final-within-family
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import Patch
import numpy as np
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis.model_family import model_family_key, model_family_label
from analysis.metrics import load_logs

# ── Style ────────────────────────────────────────────────────────────────

sns.set_theme(style="whitegrid", font_scale=1.1)
PALETTE = sns.color_palette("colorblind")
FIG_DPI = 200
BAR_WIDTH = 0.35
DEFAULT_TAGS = {
    "dossier": "dossier_effect",
    "cap_asym": "cap_asym",
    "skeptical": "skeptical_ablation",
}


def _save_fig(fig: plt.Figure, output_dir: Path, name: str) -> None:
    """Save figure as PDF."""
    fig.savefig(output_dir / f"{name}.pdf", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {name}.pdf")


def _horizontal_grid_only(ax: plt.Axes) -> None:
    """Keep only horizontal gridlines on a plot."""
    ax.set_axisbelow(True)
    ax.grid(True, axis="y")
    ax.grid(False, axis="x")


def _parse_tag_args(values: list[str] | None, default: str) -> set[str]:
    """Parse repeated/comma-separated tag CLI args into a non-empty set."""
    if not values:
        return {default}

    tags: set[str] = set()
    for value in values:
        for tag in value.split(","):
            tag = tag.strip()
            if tag:
                tags.add(tag)
    return tags or {default}


def _format_tags(tags: set[str]) -> str:
    """Render tags as a stable comma-separated string."""
    return ", ".join(sorted(tags))

# Backward compat: old logs used "chicken" before the rename to "product_launch"
_SCENARIO_ALIASES = {"chicken": "product_launch"}

# ── Emmeans loading ──────────────────────────────────────────────────────

EMMEANS_DIR = Path(__file__).resolve().parents[1] / "results" / "emmeans"


def _load_emmeans(name: str) -> list[dict] | None:
    """Load emmeans JSON if it exists, else return None."""
    path = EMMEANS_DIR / f"{name}.json"
    if not path.exists():
        return None
    with open(path) as f:
        data = json.load(f)
    print(f"  [emmeans] loaded {path.name} ({len(data)} cells)")
    return data


def _wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = z * np.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return (max(0, center - margin), min(1, center + margin))


def _rate_and_ci(items: list[dict], decision_val: str = "requester_success"):
    """Compute success rate and Wilson CI from a list of log dicts."""
    n = len(items)
    k = sum(1 for i in items if i["decision"] == decision_val)
    if n == 0:
        return 0.0, 0.0, 0.0, 0
    rate = k / n
    lo, hi = _wilson_ci(k, n)
    return rate, lo, hi, n


def _raw_odds_ratio(
    exposed: list[dict], unexposed: list[dict],
    decision_val: str = "requester_success",
) -> float:
    """Compute raw odds ratio from two groups (Haldane-corrected for zero cells)."""
    a = sum(1 for d in exposed if d["decision"] == decision_val) + 0.5
    b = sum(1 for d in exposed if d["decision"] != decision_val) + 0.5
    c = sum(1 for d in unexposed if d["decision"] == decision_val) + 0.5
    d = sum(1 for d in unexposed if d["decision"] != decision_val) + 0.5
    return (a * d) / (b * c)


# ── Data loading ─────────────────────────────────────────────────────────


def _load_and_flatten(tags: list[str] | None = None) -> list[dict]:
    """Load logs and flatten to essentials."""
    logs = load_logs(tag=tags)
    rows = []
    for log in logs:
        outcome = log.get("outcome") or {}
        decision = outcome.get("aggregate_decision") or outcome.get("decision")
        if decision not in {"requester_success", "requester_failure"}:
            continue

        models = log.get("models") or {}
        profile = log.get("profile") or {}
        rt = log.get("requester_type", "unknown")
        req_model = models.get("adversary") or models.get("benign_agent") or "unknown"
        req_short = req_model.split("/")[-1].split(":")[0]

        family = model_family_key(req_model)

        # Warden tier
        warden = models.get("warden")
        if not warden:
            tier = "none"
        elif warden == models.get("target"):
            tier = "weak"
        elif warden == (models.get("adversary") or models.get("benign_agent")):
            tier = "strong"
        else:
            tier = "mid"

        target_model = (models.get("target") or "unknown").split("/")[-1].split(":")[0]
        warden_model = (warden or "none").split("/")[-1].split(":")[0] if warden else "none"

        rows.append({
            "decision": decision,
            "requester_type": rt,
            "scenario": _SCENARIO_ALIASES.get(log.get("scenario", "unknown"), log.get("scenario", "unknown")),
            "has_warden": bool(warden),
            "warden_tier": tier,
            "has_dossier": bool(profile.get("adversary_has_data")),
            "target_skeptical": bool(log.get("target_skeptical")),
            "profile": profile.get("name") or "none",
            "model_family": family,
            "req_model": req_short,
            "target_model": target_model,
            "warden_model": warden_model,
            "tag": log.get("tag") or "",
        })
    return rows


# ── Figure 1: Warden Effect (dossier_effect study) ──────────────────────


def fig_warden_effect(
    data: list[dict],
    output_dir: Path,
    dossier_tags: set[str],
    use_raw: bool = False,
):
    """Bar chart: adversary SR with vs without warden, from dossier_effect."""
    adv = [
        d for d in data
        if d["tag"] in dossier_tags and d["requester_type"] == "adversary"
    ]
    if not adv:
        print(f"  [skip] No adversary data for dossier tags: {_format_tags(dossier_tags)}")
        return

    with_w = [d for d in adv if d["has_warden"]]
    without_w = [d for d in adv if not d["has_warden"]]
    n_nw = len(without_w)
    n_w = len(with_w)

    # Try emmeans
    em = None if use_raw else _load_emmeans("fig1_warden_effect")

    if em:
        em_by_w = {int(e["has_warden"]): e for e in em}
        r_nw = em_by_w[0]["prob"]
        lo_nw = em_by_w[0]["asymp.LCL"]
        hi_nw = em_by_w[0]["asymp.UCL"]
        r_w = em_by_w[1]["prob"]
        lo_w = em_by_w[1]["asymp.LCL"]
        hi_w = em_by_w[1]["asymp.UCL"]
        ci_label = "GLME-adjusted"
    else:
        r_nw, lo_nw, hi_nw, _ = _rate_and_ci(without_w)
        r_w, lo_w, hi_w, _ = _rate_and_ci(with_w)
        ci_label = "raw"

    fig, ax = plt.subplots(figsize=(5, 5))

    # Asymmetric error bars
    ax.bar(
        [0, 1], [r_nw * 100, r_w * 100],
        color=[PALETTE[0], PALETTE[1]], width=0.55, edgecolor="black", linewidth=0.5,
    )
    ax.errorbar(
        [0, 1], [r_nw * 100, r_w * 100],
        yerr=[[(r_nw - lo_nw) * 100, (r_w - lo_w) * 100],
              [(hi_nw - r_nw) * 100, (hi_w - r_w) * 100]],
        fmt="none", capsize=6, capthick=1.5, elinewidth=1.5, color="black",
    )

    or_val = _raw_odds_ratio(with_w, without_w)

    ax.set_xticks([0, 1])
    ax.set_xticklabels(["No Warden", "With Warden"])
    ax.set_ylabel("Adversary Success Rate (%)")
    ax.set_title(f"Warden Effect on Adversary Success\n({ci_label}, OR = {or_val:.3f})")
    ax.set_ylim(0, 70)
    _horizontal_grid_only(ax)

    sns.despine()
    fig.tight_layout()
    _save_fig(fig, output_dir, "fig1_warden_effect")


# ── Figure 2: Dossier Effect (2×2 interaction) ──────────────────────────


def fig_dossier_effect(
    data: list[dict],
    output_dir: Path,
    dossier_tags: set[str],
    use_raw: bool = False,
):
    """Grouped bar: dossier × warden interaction, adversary only."""
    adv = [
        d for d in data
        if d["tag"] in dossier_tags and d["requester_type"] == "adversary"
    ]
    if not adv:
        print(f"  [skip] No dossier-tag data found for: {_format_tags(dossier_tags)}")
        return

    conditions = [
        ("No Dossier\nNo Warden", lambda d: not d["has_dossier"] and not d["has_warden"]),
        ("Dossier\nNo Warden", lambda d: d["has_dossier"] and not d["has_warden"]),
        ("No Dossier\nWith Warden", lambda d: not d["has_dossier"] and d["has_warden"]),
        ("Dossier\nWith Warden", lambda d: d["has_dossier"] and d["has_warden"]),
    ]

    # Map emmeans cells to condition order: (dossier, warden) -> index
    em_key_order = [(0, 0), (1, 0), (0, 1), (1, 1)]

    em = None if use_raw else _load_emmeans("fig2_dossier_interaction")

    rates, los, his, hi_abs, ns = [], [], [], [], []
    if em:
        em_lookup = {(int(e["has_dossier"]), int(e["has_warden"])): e for e in em}
        for i, (label, filt) in enumerate(conditions):
            subset = [d for d in adv if filt(d)]
            dk, wk = em_key_order[i]
            e = em_lookup.get((dk, wk))
            if e:
                r, lo, hi = e["prob"], e["asymp.LCL"], e["asymp.UCL"]
            else:
                r, lo, hi, _ = _rate_and_ci(subset)
            rates.append(r * 100)
            los.append((r - lo) * 100)
            his.append((hi - r) * 100)
            hi_abs.append(hi * 100)
            ns.append(len(subset))
        ci_label = "GLME-adjusted"
    else:
        for label, filt in conditions:
            subset = [d for d in adv if filt(d)]
            r, lo, hi, n = _rate_and_ci(subset)
            rates.append(r * 100)
            los.append((r - lo) * 100)
            his.append((hi - r) * 100)
            hi_abs.append(hi * 100)
            ns.append(n)
        ci_label = "raw"

    fig, ax = plt.subplots(figsize=(7, 5))
    colors = [PALETTE[0], PALETTE[0], PALETTE[1], PALETTE[1]]
    hatches = ["", "///", "", "///"]
    x = np.arange(4)

    bars = ax.bar(x, rates, yerr=[los, his],
                  error_kw=dict(capsize=5, capthick=1.3, elinewidth=1.3),
                  color=colors, width=0.6, edgecolor="black", linewidth=0.5)
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)

    # Compute raw ORs (always from data, for reference)
    dossier_yes = [d for d in adv if d["has_dossier"]]
    dossier_no = [d for d in adv if not d["has_dossier"]]
    or_dossier = _raw_odds_ratio(dossier_yes, dossier_no)
    warden_yes = [d for d in adv if d["has_warden"]]
    warden_no = [d for d in adv if not d["has_warden"]]
    or_warden = _raw_odds_ratio(warden_yes, warden_no)

    ax.set_xticks(x)
    ax.set_xticklabels([c[0] for c in conditions], fontsize=9)
    ax.set_ylabel("Adversary Success Rate (%)")
    ax.set_title(f"Dossier × Warden Interaction\n({ci_label} OR: dossier = {or_dossier:.2f}, warden = {or_warden:.3f})")
    ax.set_ylim(0, 70)

    for i, (r, h, n) in enumerate(zip(rates, hi_abs, ns)):
        ax.text(i, h + 2, f"{r:.1f}%\nn={n}", ha="center", fontsize=9)

    legend_handles = [
        Patch(facecolor=PALETTE[0], edgecolor="black", label="No Warden"),
        Patch(facecolor=PALETTE[1], edgecolor="black", label="With Warden"),
        Patch(facecolor="white", edgecolor="black", hatch="", label="No Dossier"),
        Patch(facecolor="white", edgecolor="black", hatch="///", label="Dossier"),
    ]
    ax.legend(
        handles=legend_handles,
        title="Encoding",
        loc="upper right",
        framealpha=0.9,
    )

    _horizontal_grid_only(ax)
    sns.despine()
    fig.tight_layout()
    _save_fig(fig, output_dir, "fig2_dossier_interaction")


# ── Figure 3: Capability Asymmetry (warden tier) ────────────────────────


def fig_capability_asymmetry(
    data: list[dict],
    output_dir: Path,
    cap_asym_tags: set[str],
    use_raw: bool = False,
):
    """Bar chart: adversary SR by warden tier (none/weak/mid/strong)."""
    adv = [
        d for d in data
        if d["tag"] in cap_asym_tags and d["requester_type"] == "adversary"
    ]
    if not adv:
        print(f"  [skip] No cap-asym-tag data found for: {_format_tags(cap_asym_tags)}")
        return

    tiers = ["none", "weak", "mid", "strong"]
    tier_labels = ["None", "Weak\n(= target)", "Mid", "Strong\n(= adversary)"]

    em = None if use_raw else _load_emmeans("fig3_capability_asymmetry")

    rates, los, his, hi_abs, ns = [], [], [], [], []
    if em:
        em_lookup = {e["warden_tier"]: e for e in em}
        for tier in tiers:
            subset = [d for d in adv if d["warden_tier"] == tier]
            e = em_lookup.get(tier)
            if e:
                r, lo, hi = e["prob"], e["asymp.LCL"], e["asymp.UCL"]
            else:
                r, lo, hi, _ = _rate_and_ci(subset)
            rates.append(r * 100)
            los.append((r - lo) * 100)
            his.append((hi - r) * 100)
            hi_abs.append(hi * 100)
            ns.append(len(subset))
        ci_label = "GLME-adjusted"
    else:
        for tier in tiers:
            subset = [d for d in adv if d["warden_tier"] == tier]
            r, lo, hi, n = _rate_and_ci(subset)
            rates.append(r * 100)
            los.append((r - lo) * 100)
            his.append((hi - r) * 100)
            hi_abs.append(hi * 100)
            ns.append(n)
        ci_label = "raw"

    fig, ax = plt.subplots(figsize=(6, 5))
    x = np.arange(4)
    colors = [PALETTE[3], PALETTE[2], PALETTE[1], PALETTE[0]]
    ax.bar(x, rates, yerr=[los, his],
           error_kw=dict(capsize=6, capthick=1.3, elinewidth=1.3),
           color=colors, width=0.6, edgecolor="black", linewidth=0.5)

    # Compute OR for any-warden vs none
    warden_any = [d for d in adv if d["warden_tier"] != "none"]
    warden_none = [d for d in adv if d["warden_tier"] == "none"]
    or_overall = _raw_odds_ratio(warden_any, warden_none)

    ax.set_xticks(x)
    ax.set_xticklabels(tier_labels, fontsize=9)
    ax.set_xlabel("Warden Capability Tier")
    ax.set_ylabel("Adversary Success Rate (%)")
    ax.set_title(f"Warden Capability Asymmetry\n({ci_label}, OR any-warden vs. none = {or_overall:.3f})")
    ax.set_ylim(0, 80)

    for i, (r, h, n) in enumerate(zip(rates, hi_abs, ns)):
        ax.text(i, h + 2, f"{r:.1f}%\nn={n}", ha="center", fontsize=9)

    _horizontal_grid_only(ax)
    sns.despine()
    fig.tight_layout()
    _save_fig(fig, output_dir, "fig3_capability_asymmetry")


# ── Figure 4: Skeptical Ablation (3 conditions × 2 requester types) ─────


def fig_skeptical_ablation(
    data: list[dict],
    output_dir: Path,
    skeptical_tags: set[str],
    use_raw: bool = False,
):
    """Grouped bar: defense condition × requester type."""
    skep = [d for d in data if d["tag"] in skeptical_tags]
    if not skep:
        print(f"  [skip] No skeptical-tag data found for: {_format_tags(skeptical_tags)}")
        return

    def _cond(d):
        if d["target_skeptical"] and d["has_warden"]:
            return "skeptical+warden"
        elif d["target_skeptical"]:
            return "skeptical"
        elif d["has_warden"]:
            return "warden"
        else:
            return "baseline"

    conditions = ["baseline", "skeptical", "warden"]
    cond_labels = ["Baseline\n(no defense)", "Skeptical\n(prompt)", "Warden\n(agent)"]

    em = None if use_raw else _load_emmeans("fig4_skeptical_ablation")
    em_lookup = {}
    if em:
        for e in em:
            em_lookup[(e["defense"], e["requester_type"])] = e

    fig, ax = plt.subplots(figsize=(7, 5.5))
    x = np.arange(len(conditions))
    width = 0.32

    ci_label = "GLME-adjusted" if em else "raw"

    for j, (rt, rt_label, color) in enumerate([
        ("adversary", "Adversary", PALETTE[3]),
        ("benign_agent", "Benign Agent", PALETTE[0]),
    ]):
        rates, err_lo, err_hi, hi_abs, ns_list = [], [], [], [], []
        for cond in conditions:
            subset = [d for d in skep if d["requester_type"] == rt and _cond(d) == cond]
            e = em_lookup.get((cond, rt))
            if e:
                r, lo, hi = e["prob"], e["asymp.LCL"], e["asymp.UCL"]
                n = len(subset)
            else:
                r, lo, hi, n = _rate_and_ci(subset)
            rates.append(r * 100)
            err_lo.append((r - lo) * 100)
            err_hi.append((hi - r) * 100)
            hi_abs.append(hi * 100)
            ns_list.append(n)

        offset = (j - 0.5) * width
        bars = ax.bar(x + offset, rates, width, yerr=[err_lo, err_hi],
                      label=rt_label, color=color,
                      error_kw=dict(capsize=4, capthick=1.2, elinewidth=1.2),
                      edgecolor="black", linewidth=0.5)

        for i, (r, h, n) in enumerate(zip(rates, hi_abs, ns_list)):
            ax.text(x[i] + offset, h + 2, f"{r:.0f}%\nn={n}", ha="center", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(cond_labels, fontsize=9)
    ax.set_ylabel("Success Rate (%)")
    ax.set_title(f"Defense Mechanism Comparison ({ci_label})\n"
                 "(Adversary suppression vs. benign false positive cost)")
    ax.set_ylim(0, 110)
    ax.legend(loc="upper right", framealpha=0.9)

    _horizontal_grid_only(ax)
    sns.despine()
    fig.tight_layout()
    _save_fig(fig, output_dir, "fig4_skeptical_ablation")


# ── Figure 5: Adversary SR by Model Family ───────────────────────────────


def fig_model_family(
    data: list[dict],
    output_dir: Path,
    main_tags: set[str],
    use_raw: bool = False,
):
    """Bar chart: adversary SR by model family (pooled across main studies)."""
    adv = [d for d in data if d["tag"] in main_tags and d["requester_type"] == "adversary"
           and not d["has_warden"]]
    if not adv:
        print("  [skip] No adversary data for model family plot")
        return

    families = defaultdict(list)
    for d in adv:
        families[d["model_family"]].append(d)

    em = None if use_raw else _load_emmeans("fig5_model_family")
    em_lookup = {e["model_family"]: e for e in em} if em else {}

    # Sort by success rate (use emmeans rate if available)
    family_data = []
    for fam, items in families.items():
        if len(items) < 10:
            continue
        e = em_lookup.get(fam)
        if e:
            r, lo, hi = e["prob"], e["asymp.LCL"], e["asymp.UCL"]
        else:
            r, lo, hi, _ = _rate_and_ci(items)
        family_data.append((fam, r, lo, hi, len(items)))
    family_data.sort(key=lambda x: -x[1])

    if not family_data:
        print("  [skip] Not enough data for model family plot")
        return

    ci_label = "GLME-adjusted" if em else "raw"

    fig, ax = plt.subplots(figsize=(7, 5))
    fams = [model_family_label(f[0]) for f in family_data]
    rates = [f[1] * 100 for f in family_data]
    err_lo = [(f[1] - f[2]) * 100 for f in family_data]
    err_hi = [(f[3] - f[1]) * 100 for f in family_data]
    hi_abs = [f[3] * 100 for f in family_data]
    ns = [f[4] for f in family_data]

    x = np.arange(len(fams))
    ax.bar(x, rates, yerr=[err_lo, err_hi],
           error_kw=dict(capsize=5, capthick=1.3, elinewidth=1.3),
           color=PALETTE[:len(fams)], width=0.55, edgecolor="black", linewidth=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels(fams, fontsize=10)
    ax.set_xlabel("Adversary Model Family")
    ax.set_ylabel("Adversary Success Rate (%)")
    ax.set_title(f"Adversary Effectiveness by Model Family ({ci_label})\n"
                 "(no warden, pooled across studies)")
    ax.set_ylim(0, 80)

    for i, (r, h, n) in enumerate(zip(rates, hi_abs, ns)):
        ax.text(i, h + 2, f"{r:.1f}%\nn={n}", ha="center", fontsize=9)

    _horizontal_grid_only(ax)
    sns.despine()
    fig.tight_layout()
    _save_fig(fig, output_dir, "fig5_model_family")


# ── Figure 6: Adversary SR by Scenario ───────────────────────────────────


def fig_scenario_variation(data: list[dict], output_dir: Path, main_tags: set[str]):
    """Horizontal bar: adversary SR by scenario (no warden), pooled."""
    adv = [d for d in data if d["tag"] in main_tags and d["requester_type"] == "adversary"
           and not d["has_warden"]]
    if not adv:
        print("  [skip] No data for scenario plot")
        return

    by_sc = defaultdict(list)
    for d in adv:
        by_sc[d["scenario"]].append(d)

    sc_data = []
    for sc, items in by_sc.items():
        if len(items) < 10:
            continue
        r, lo, hi, n = _rate_and_ci(items)
        sc_data.append((sc, r, lo, hi, n))
    sc_data.sort(key=lambda x: x[1])

    if not sc_data:
        print("  [skip] Not enough data for scenario plot")
        return

    fig, ax = plt.subplots(figsize=(8, 6))
    scenarios = [s[0] for s in sc_data]
    rates = [s[1] * 100 for s in sc_data]
    err_lo = [(s[1] - s[2]) * 100 for s in sc_data]
    err_hi = [(s[3] - s[1]) * 100 for s in sc_data]
    hi_abs = [s[3] * 100 for s in sc_data]
    ns = [s[4] for s in sc_data]

    y = np.arange(len(scenarios))
    ax.barh(y, rates, xerr=[err_lo, err_hi],
            error_kw=dict(capsize=3, capthick=1, elinewidth=1),
            color=PALETTE[0], height=0.6, edgecolor="black", linewidth=0.5)

    ax.set_yticks(y)
    ax.set_yticklabels(scenarios, fontsize=9)
    ax.set_xlabel("Adversary Success Rate (%)")
    ax.set_title("Adversary Success by Scenario\n(no warden, pooled across studies)")
    ax.set_xlim(0, 105)

    for i, (h, r, n) in enumerate(zip(hi_abs, rates, ns)):
        ax.text(h + 2, i, f"{r:.0f}% (n={n})", va="center", fontsize=8)

    sns.despine()
    fig.tight_layout()
    _save_fig(fig, output_dir, "fig6_scenario_variation")


def fig_scenario_variation_contrast(
    data: list[dict], output_dir: Path, main_tags: set[str]
):
    """Horizontal grouped bars: adversary SR by scenario with and without warden."""
    adv = [
        d for d in data
        if d["tag"] in main_tags and d["requester_type"] == "adversary"
    ]
    if not adv:
        print("  [skip] No data for scenario contrast plot")
        return

    by_sc = defaultdict(lambda: {"without": [], "with": []})
    for d in adv:
        key = "with" if d["has_warden"] else "without"
        by_sc[d["scenario"]][key].append(d)

    sc_data = []
    for sc, groups in by_sc.items():
        without_items = groups["without"]
        with_items = groups["with"]
        if len(without_items) < 10 or len(with_items) < 10:
            continue

        r_nw, lo_nw, hi_nw, n_nw = _rate_and_ci(without_items)
        r_w, lo_w, hi_w, n_w = _rate_and_ci(with_items)
        sc_data.append((sc, r_nw, lo_nw, hi_nw, n_nw, r_w, lo_w, hi_w, n_w))

    sc_data.sort(key=lambda x: x[1])

    if not sc_data:
        print("  [skip] Not enough paired adversary data for scenario contrast plot")
        return

    fig, ax = plt.subplots(figsize=(9, 6.5))
    scenarios = [s[0] for s in sc_data]
    no_warden_rates = [s[1] * 100 for s in sc_data]
    no_warden_err_lo = [(s[1] - s[2]) * 100 for s in sc_data]
    no_warden_err_hi = [(s[3] - s[1]) * 100 for s in sc_data]
    no_warden_hi_abs = [s[3] * 100 for s in sc_data]
    no_warden_ns = [s[4] for s in sc_data]
    with_warden_rates = [s[5] * 100 for s in sc_data]
    with_warden_err_lo = [(s[5] - s[6]) * 100 for s in sc_data]
    with_warden_err_hi = [(s[7] - s[5]) * 100 for s in sc_data]
    with_warden_hi_abs = [s[7] * 100 for s in sc_data]
    with_warden_ns = [s[8] for s in sc_data]

    y = np.arange(len(scenarios))
    bar_height = 0.34
    offset = bar_height / 2

    ax.barh(
        y - offset,
        no_warden_rates,
        xerr=[no_warden_err_lo, no_warden_err_hi],
        error_kw=dict(capsize=3, capthick=1, elinewidth=1),
        color=PALETTE[0],
        height=bar_height,
        edgecolor="black",
        linewidth=0.5,
        label="No Warden",
    )
    ax.barh(
        y + offset,
        with_warden_rates,
        xerr=[with_warden_err_lo, with_warden_err_hi],
        error_kw=dict(capsize=3, capthick=1, elinewidth=1),
        color=PALETTE[1],
        height=bar_height,
        edgecolor="black",
        linewidth=0.5,
        label="With Warden",
    )

    ax.set_yticks(y)
    ax.set_yticklabels(scenarios, fontsize=9)
    ax.set_xlabel("Adversary Success Rate (%)")
    ax.set_title("Adversary Success by Scenario\n(with vs. without warden)")
    ax.set_xlim(0, 105)
    ax.legend(loc="lower right", framealpha=0.9)

    for i, (h, r, n) in enumerate(zip(no_warden_hi_abs, no_warden_rates, no_warden_ns)):
        ax.text(h + 2, y[i] - offset, f"{r:.0f}% (n={n})", va="center", fontsize=7.5)
    for i, (h, r, n) in enumerate(zip(with_warden_hi_abs, with_warden_rates, with_warden_ns)):
        ax.text(h + 2, y[i] + offset, f"{r:.0f}% (n={n})", va="center", fontsize=7.5)

    sns.despine()
    fig.tight_layout()
    _save_fig(fig, output_dir, "fig6b_scenario_variation")


# ── Figure 7: Warden FP by Scenario ─────────────────────────────────────


def fig_warden_fp(data: list[dict], output_dir: Path, main_tags: set[str]):
    """Paired dot plot: benign SR with and without warden, by scenario."""
    benign = [d for d in data if d["tag"] in main_tags and d["requester_type"] == "benign_agent"]
    if len(benign) < 20:
        print("  [skip] Not enough benign data for FP plot")
        return

    by_sc = defaultdict(lambda: {"with": [], "without": []})
    for d in benign:
        key = "with" if d["has_warden"] else "without"
        by_sc[d["scenario"]][key].append(d)

    # Only scenarios with both conditions and enough data
    sc_data = []
    for sc, groups in by_sc.items():
        if len(groups["with"]) < 5 or len(groups["without"]) < 5:
            continue
        r_w, lo_w, hi_w, n_w = _rate_and_ci(groups["with"])
        r_nw, lo_nw, hi_nw, n_nw = _rate_and_ci(groups["without"])
        delta = r_nw - r_w  # positive = warden causes more FPs
        sc_data.append((sc, r_nw * 100, r_w * 100, delta * 100, n_w, n_nw))

    if not sc_data:
        print("  [skip] Not enough paired data for FP plot")
        return

    sc_data.sort(key=lambda x: x[3])  # sort by delta

    fig, ax = plt.subplots(figsize=(8, 6))
    scenarios = [s[0] for s in sc_data]
    y = np.arange(len(scenarios))

    for i, (sc, r_nw, r_w, delta, n_w, n_nw) in enumerate(sc_data):
        ax.plot([r_w, r_nw], [i, i], color="gray", linewidth=1, zorder=1)
        ax.scatter(r_nw, i, color=PALETTE[0], s=50, zorder=2, label="No Warden" if i == 0 else None)
        ax.scatter(r_w, i, color=PALETTE[1], s=50, zorder=2, label="With Warden" if i == 0 else None)

    ax.set_yticks(y)
    ax.set_yticklabels(scenarios, fontsize=9)
    ax.set_xlabel("Benign Agent Success Rate (%)")
    ax.set_title("Warden False Positive Cost by Scenario\n(lower = warden rejects legitimate requests)")
    ax.set_xlim(0, 110)
    ax.legend(loc="lower right", framealpha=0.9)

    sns.despine()
    fig.tight_layout()
    _save_fig(fig, output_dir, "fig7_warden_fp_by_scenario")


# ── Figure 0: Warden Effect — Adversary vs Benign (pooled) ────────────────


def fig_warden_effect_both(
    data: list[dict],
    output_dir: Path,
    main_tags: set[str],
    use_raw: bool = False,
):
    """Grouped bar: warden effect on adversary AND benign agent success."""
    main = [d for d in data if d["tag"] in main_tags]
    if not main:
        print("  [skip] No main study data for warden effect (both)")
        return

    em = None if use_raw else _load_emmeans("fig0_warden_effect_both")
    em_lookup = {}
    if em:
        for e in em:
            em_lookup[(e["requester_type"], int(e["has_warden"]))] = e

    ci_label = "GLME-adjusted" if em else "raw"

    fig, ax = plt.subplots(figsize=(6, 5.5))
    x = np.arange(2)  # No Warden, With Warden
    width = 0.32

    for j, (rt, rt_label, color) in enumerate([
        ("adversary", "Adversary", PALETTE[3]),
        ("benign_agent", "Benign Agent", PALETTE[0]),
    ]):
        rates, err_lo, err_hi, hi_abs, ns_list = [], [], [], [], []
        for has_w in [False, True]:
            subset = [d for d in main if d["requester_type"] == rt
                      and d["has_warden"] == has_w]
            e = em_lookup.get((rt, int(has_w)))
            if e:
                r, lo, hi = e["prob"], e["asymp.LCL"], e["asymp.UCL"]
                n = len(subset)
            else:
                r, lo, hi, n = _rate_and_ci(subset)
            rates.append(r * 100)
            err_lo.append((r - lo) * 100)
            err_hi.append((hi - r) * 100)
            hi_abs.append(hi * 100)
            ns_list.append(n)

        offset = (j - 0.5) * width
        ax.bar(x + offset, rates, width, yerr=[err_lo, err_hi],
               label=rt_label, color=color,
               error_kw=dict(capsize=5, capthick=1.3, elinewidth=1.3),
               edgecolor="black", linewidth=0.5)

        for i, (r, h, n) in enumerate(zip(rates, hi_abs, ns_list)):
            ax.text(x[i] + offset, h + 2, f"{r:.1f}%\nn={n}",
                    ha="center", fontsize=9)

    # Compute raw OR for adversary with/without warden
    adv_data = [d for d in main if d["requester_type"] == "adversary"]
    adv_w = [d for d in adv_data if d["has_warden"]]
    adv_nw = [d for d in adv_data if not d["has_warden"]]
    or_adv = _raw_odds_ratio(adv_w, adv_nw)

    ax.set_xticks(x)
    ax.set_xticklabels(["No Warden", "With Warden"], fontsize=10)
    ax.set_ylabel("Success Rate (%)")
    ax.set_title(f"Warden Effect: Adversary vs. Benign Agent ({ci_label})\n"
                 f"(adversary OR = {or_adv:.3f})")
    ax.set_ylim(0, 115)
    ax.legend(loc="upper right", framealpha=0.9)

    _horizontal_grid_only(ax)
    sns.despine()
    fig.tight_layout()
    _save_fig(fig, output_dir, "fig0_warden_effect_both")


# ── Figure 8: Profile Vulnerability × Warden ─────────────────────────────


def fig_profile_vulnerability(
    data: list[dict],
    output_dir: Path,
    main_tags: set[str],
    use_raw: bool = False,
):
    """Grouped bar: adversary SR by profile × warden condition."""
    adv = [d for d in data if d["tag"] in main_tags
           and d["requester_type"] == "adversary"]
    if not adv:
        print("  [skip] No adversary data for profile vulnerability plot")
        return

    def _display_profile_label(profile_name: str) -> str:
        parts = [part.strip() for part in profile_name.split("|")]
        if len(parts) <= 1:
            return profile_name
        lines = []
        for i in range(0, len(parts), 2):
            lines.append(" | ".join(parts[i:i + 2]))
        return "\n".join(lines)

    # Bucket data by the actual profile names present in the logs.
    bucketed = defaultdict(list)
    for d in adv:
        profile_name = d["profile"]
        if profile_name and profile_name != "none":
            bucketed[(profile_name, d["has_warden"])].append(d)

    profile_order = sorted(
        {profile_name for profile_name, _ in bucketed},
        key=lambda profile_name: (
            -_rate_and_ci(bucketed.get((profile_name, False), []))[0],
            profile_name,
        ),
    )
    if not profile_order:
        print("  [skip] No profiled adversary data for profile vulnerability plot")
        return
    profile_labels = [_display_profile_label(profile_name) for profile_name in profile_order]

    em = None if use_raw else _load_emmeans("fig8_profile_vulnerability")
    em_lookup = {}
    if em:
        for e in em:
            em_lookup[(e["profile_name"], int(e["has_warden"]))] = e

    ci_label = "GLME-adjusted" if em else "raw"

    fig_width = max(10.5, len(profile_order) * 1.5)
    fig, ax = plt.subplots(figsize=(fig_width, 6))
    x = np.arange(len(profile_order))
    width = 0.32

    for j, (has_w, w_label, color) in enumerate([
        (False, "No Warden", PALETTE[3]),
        (True, "With Warden", PALETTE[1]),
    ]):
        rates, err_lo, err_hi, hi_abs, ns_list = [], [], [], [], []
        for profile_name in profile_order:
            subset = bucketed.get((profile_name, has_w), [])
            e = em_lookup.get((profile_name, int(has_w)))
            if e:
                r, lo, hi = e["prob"], e["asymp.LCL"], e["asymp.UCL"]
                n = len(subset)
            else:
                r, lo, hi, n = _rate_and_ci(subset)
            rates.append(r * 100)
            err_lo.append((r - lo) * 100)
            err_hi.append((hi - r) * 100)
            hi_abs.append(hi * 100)
            ns_list.append(n)

        offset = (j - 0.5) * width
        ax.bar(x + offset, rates, width, yerr=[err_lo, err_hi],
               label=w_label, color=color,
               error_kw=dict(capsize=4, capthick=1.2, elinewidth=1.2),
               edgecolor="black", linewidth=0.5)

        for i, (r, h, n) in enumerate(zip(rates, hi_abs, ns_list)):
            ax.text(x[i] + offset, h + 2.5, f"{r:.1f}%",
                    ha="center", fontsize=8, fontweight="bold")
            ax.text(x[i] + offset, h + 7, f"n={n}",
                    ha="center", fontsize=7, color="0.35")

    ax.set_xticks(x)
    ax.set_xticklabels(profile_labels, fontsize=8)
    ax.set_xlabel("Target Vulnerability Profile")
    ax.set_ylabel("Adversary Success Rate (%)")
    ax.set_title(f"Profile Vulnerability × Warden ({ci_label})\n"
                 "(pooled across studies, adversary only)")
    ax.set_ylim(0, 90)
    ax.legend(loc="upper right", framealpha=0.9)

    _horizontal_grid_only(ax)
    sns.despine()
    fig.tight_layout()
    _save_fig(fig, output_dir, "fig8_profile_vulnerability")


# ── Figure 9: Success Rate by Model Role ─────────────────────────────────


def fig_model_roles(
    data: list[dict],
    output_dir: Path,
    main_tags: set[str],
    use_raw: bool = False,
):
    """3-panel bar chart: adversary SR by requester model, target model, warden model."""
    adv = [d for d in data if d["tag"] in main_tags and d["requester_type"] == "adversary"]
    if not adv:
        print("  [skip] No adversary data for model roles plot")
        return

    em = None if use_raw else _load_emmeans("fig9_model_roles")
    em_lookup = {}
    if em:
        for e in em:
            em_lookup[(e["role"], e["model"])] = e

    ci_label = "GLME-adjusted" if em else "raw"

    # Role configs: (role_key, data_field, filter, panel_title)
    role_configs = [
        ("requester", "req_model", lambda d: not d["has_warden"],
         "By Requester Model\n(no warden)"),
        ("target", "target_model", lambda d: not d["has_warden"],
         "By Target Model\n(no warden)"),
        ("warden", "warden_model", lambda d: d["has_warden"],
         "By Warden Model\n(warden present)"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))

    for ax, (role, data_field, filt, title) in zip(axes, role_configs):
        subset = [d for d in adv if filt(d)]

        # Group by model
        by_model = defaultdict(list)
        for d in subset:
            model_name = d.get(data_field, "unknown")
            if model_name and model_name != "none":
                by_model[model_name].append(d)

        # Build bars
        model_data = []
        for model_name, items in by_model.items():
            if len(items) < 5:
                continue
            e = em_lookup.get((role, model_name))
            if e:
                r, lo, hi = e["prob"], e["asymp.LCL"], e["asymp.UCL"]
            else:
                r, lo, hi, _ = _rate_and_ci(items)
            model_data.append((model_name, r, lo, hi, len(items)))
        model_data.sort(key=lambda x: -x[1])

        if not model_data:
            ax.set_visible(False)
            continue

        names = [m[0] for m in model_data]
        rates = [m[1] * 100 for m in model_data]
        err_lo = [(m[1] - m[2]) * 100 for m in model_data]
        err_hi = [(m[3] - m[1]) * 100 for m in model_data]
        hi_abs = [m[3] * 100 for m in model_data]
        ns = [m[4] for m in model_data]

        x = np.arange(len(names))
        ax.bar(x, rates, yerr=[err_lo, err_hi],
               error_kw=dict(capsize=4, capthick=1, elinewidth=1),
               color=PALETTE[:len(names)], width=0.6,
               edgecolor="black", linewidth=0.5)

        ax.set_xticks(x)
        ax.set_xticklabels(names, fontsize=7, rotation=30, ha="right")
        ax.set_ylabel("Adversary Success Rate (%)")
        ax.set_title(title, fontsize=10)
        ax.set_ylim(0, min(max(hi_abs) + 20, 110))

        for i, (r, h, n) in enumerate(zip(rates, hi_abs, ns)):
            ax.text(i, h + 1.5, f"{r:.0f}%\nn={n}", ha="center", fontsize=7)

    fig.suptitle(f"Adversary Success by Model Role ({ci_label})", fontsize=13, y=1.02)
    sns.despine()
    fig.tight_layout()
    _save_fig(fig, output_dir, "fig9_model_roles")


# ── Figure 10: Warden Intelligence Scatter ────────────────────────────────

_WARDEN_AI_INDEX = {
    "google/gemma-3-4b-it": 6,
    "google/gemma-3-12b-it": 9,
    "google/gemma-3-27b-it": 10,

    "google/gemini-2.5-flash-lite": 18,  # reasoning
    "google/gemini-2.5-flash": 27,  # reasoning
    "google/gemini-3-flash-preview": 46,  # reasoning
    "google/gemini-pro-1.5": 16,
    "google/gemini-2.5-pro": 35,
    "google/gemini-3.1-pro-preview": 57,

    "meta-llama/llama-3.1-8b-instruct": 12,
    "meta-llama/llama-3.1-70b-instruct": 12,
    "meta-llama/llama-4-scout": 14,
    "meta-llama/llama-4-maverick": 18,

    "mistralai/mistral-small-3.1-24b-instruct": 14,
    "mistralai/mistral-medium-3.1": 21,
    "mistralai/mistral-large-2512": 23,

    "qwen/qwen3.5-35b-a3b": 37,  # reasoning
    "qwen/qwen3.5-122b-a10b": 42,
    "qwen/qwen3.5-397b-a17b": 45,

    "openai/gpt-4o-mini": 13,
    "openai/gpt-4o": 17,
    "openai/gpt-5.4": 57,

    "anthropic/claude-haiku-4.5": 37,  # reasoning
    "anthropic/claude-sonnet-4.6": 52,  # adaptive reasoning (max effort)
    "anthropic/claude-opus-4.6": 53,  # adaptive reasoning (max effort)
}


def fig_warden_intelligence(
    data: list[dict],
    output_dir: Path,
    main_tags: set[str],
    use_raw: bool = False,
):
    """Scatter: warden score vs AI intelligence index.

    The score is the combined metric ((1 − adversary SR) + benign SR) / 2.
    It is only defined for warden models with both adversary data and at
    least 5 benign runs.
    """
    warden_data = [d for d in data if d["tag"] in main_tags and d["has_warden"]
                   and d["warden_model"] in _WARDEN_AI_INDEX]
    if not warden_data:
        print("  [skip] No warden data with AI index scores")
        return

    # Try emmeans for adversary SR by warden model
    em = None if use_raw else _load_emmeans("fig9_model_roles")
    em_warden = {}
    if em:
        for e in em:
            if e["role"] == "warden":
                short = e["model"].split("/")[-1].split(":")[0]
                em_warden[short] = e

    # Aggregate by warden model
    by_warden: dict[str, dict] = {}
    for d in warden_data:
        wm = d["warden_model"]
        if wm not in by_warden:
            by_warden[wm] = {"adv": [], "ben": []}
        if d["requester_type"] == "adversary":
            by_warden[wm]["adv"].append(d)
        elif d["requester_type"] == "benign_agent":
            by_warden[wm]["ben"].append(d)

    points = []
    for wm, groups in by_warden.items():
        if not groups["adv"]:
            continue
        ai_idx = _WARDEN_AI_INDEX[wm]

        # Adversary SR (use emmeans if available)
        e = em_warden.get(wm)
        if e:
            adv_sr = e["prob"]
        else:
            adv_sr = sum(1 for d in groups["adv"]
                         if d["decision"] == "requester_success") / len(groups["adv"])

        has_ben = len(groups["ben"]) >= 5
        if not has_ben:
            continue

        ben_sr = sum(1 for d in groups["ben"]
                     if d["decision"] == "requester_success") / len(groups["ben"])
        score = ((1 - adv_sr) + ben_sr) / 2

        n_total = len(groups["adv"]) + len(groups["ben"])
        points.append((wm, ai_idx, score, adv_sr, ben_sr, n_total, has_ben))

    if not points:
        print("  [skip] No warden models with both adversary data and >=5 benign runs")
        return

    ci_label = "GLME-adjusted adversary SR" if em_warden else "raw"

    fig, ax = plt.subplots(figsize=(9, 5.5))

    ax.scatter([p[1] for p in points],
               [p[2] * 100 for p in points],
               s=90, color=PALETTE[0], edgecolors="white", linewidth=0.8,
               zorder=3, label="Combined score")

    # Label each point with adjustable text to reduce overlap
    all_pts = sorted(points, key=lambda p: (p[1], -p[2]))
    for i, (label, x, y_raw, *_rest) in enumerate(all_pts):
        y = y_raw * 100
        offset = 8 if i % 2 == 0 else -10
        va = "bottom" if i % 2 == 0 else "top"
        ax.annotate(label, (x, y), textcoords="offset points",
                    xytext=(5, offset), ha="left", va=va,
                    fontsize=7.5, color="0.3")

    xs = [p[1] for p in points]
    ys = [p[2] * 100 for p in points]
    y_min = max(0, min(ys) - 5)
    ax.set_ylim(y_min, 100)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.set_xlabel("Model Intelligence Index Score")
    ax.set_ylabel("Warden Score (%)")
    ax.set_title(f"Warden Effectiveness vs. Model Intelligence ({ci_label})")

    ax.set_xticks(sorted(set(xs)))
    x_span = max(xs) - min(xs)
    x_pad = max(2, x_span * 0.10)
    ax.set_xlim(min(xs) - x_pad, max(xs) + x_pad * 1.5)

    ax.legend(loc="lower right", fontsize=8, framealpha=0.9)
    sns.despine()
    fig.tight_layout()
    _save_fig(fig, output_dir, "fig10_warden_intelligence")


# ── (Legacy) Figure 10: Scenario × Profile Heatmap ───────────────────────


def fig_scenario_profile_heatmap(
    data: list[dict],
    output_dir: Path,
    main_tags: set[str],
    use_raw: bool = False,
):
    """Heatmap of adversary SR by scenario × profile."""
    adv = [d for d in data if d["tag"] in main_tags
           and d["requester_type"] == "adversary"
           and d["profile"] != "none"]
    if not adv:
        print("  [skip] No adversary data with profiles for heatmap")
        return

    em = None if use_raw else _load_emmeans("fig10_scenario_profile_heatmap")
    em_lookup = {}
    if em:
        for e in em:
            em_lookup[(e["scenario"], e["profile_name"])] = e

    ci_label = "GLME-adjusted" if em else "raw"

    # Collect unique scenarios and profiles
    scenarios = sorted({d["scenario"] for d in adv})
    profiles = sorted({d["profile"] for d in adv})

    # Build rate matrix
    z = np.full((len(scenarios), len(profiles)), np.nan)
    annotations = [[None] * len(profiles) for _ in range(len(scenarios))]

    for i, sc in enumerate(scenarios):
        for j, prof in enumerate(profiles):
            e = em_lookup.get((sc, prof))
            subset = [d for d in adv if d["scenario"] == sc and d["profile"] == prof]
            n = len(subset)
            if e:
                r = e["prob"]
            elif n > 0:
                r = sum(1 for d in subset if d["decision"] == "requester_success") / n
            else:
                r = np.nan
            z[i, j] = r
            if not np.isnan(r):
                annotations[i][j] = f"{r:.0%}\nn={n}"
            else:
                annotations[i][j] = ""

    fig, ax = plt.subplots(figsize=(max(7, len(profiles) * 1.4 + 2),
                                     max(5, len(scenarios) * 0.7 + 2)))

    im = ax.imshow(z, cmap="RdYlGn_r", vmin=0, vmax=1, aspect="auto")
    cbar = fig.colorbar(im, ax=ax, shrink=0.8)
    cbar.set_label("Adversary Success Rate")
    cbar.ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1))

    ax.set_xticks(np.arange(len(profiles)))
    ax.set_yticks(np.arange(len(scenarios)))
    ax.set_xticklabels(profiles, fontsize=8, rotation=35, ha="right")
    ax.set_yticklabels(scenarios, fontsize=8)
    ax.set_xlabel("Target Profile")
    ax.set_ylabel("Scenario")
    ax.set_title(f"Adversary Success: Scenario × Profile ({ci_label})")

    # Add text annotations
    for i in range(len(scenarios)):
        for j in range(len(profiles)):
            txt = annotations[i][j]
            if txt:
                ax.text(j, i, txt, ha="center", va="center", fontsize=7,
                        color="white" if z[i, j] > 0.6 else "black")

    fig.tight_layout()
    _save_fig(fig, output_dir, "fig10_scenario_profile_heatmap")


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Generate result figures.")
    parser.add_argument(
        "--output-dir", type=str, default="results/figures",
        help="Directory for output PDFs.",
    )
    parser.add_argument(
        "--raw", action="store_true",
        help="Force raw Wilson CIs even if emmeans JSON files exist.",
    )
    parser.add_argument(
        "--dossier-tag",
        dest="dossier_tags",
        nargs="+",
        default=[DEFAULT_TAGS["dossier"]],
        help=(
            "Tag(s) to use for dossier-style figures. Accepts repeated values or "
            "comma-separated tags."
        ),
    )
    parser.add_argument(
        "--cap-asym-tag",
        dest="cap_asym_tags",
        nargs="+",
        default=[DEFAULT_TAGS["cap_asym"]],
        help=(
            "Tag(s) to use for capability-asymmetry figures. Accepts repeated values "
            "or comma-separated tags."
        ),
    )
    parser.add_argument(
        "--skeptical-tag",
        dest="skeptical_tags",
        nargs="+",
        default=[DEFAULT_TAGS["skeptical"]],
        help=(
            "Tag(s) to use for skeptical-ablation figures. Accepts repeated values "
            "or comma-separated tags."
        ),
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    dossier_tags = _parse_tag_args(args.dossier_tags, DEFAULT_TAGS["dossier"])
    cap_asym_tags = _parse_tag_args(args.cap_asym_tags, DEFAULT_TAGS["cap_asym"])
    skeptical_tags = _parse_tag_args(args.skeptical_tags, DEFAULT_TAGS["skeptical"])
    main_tags = dossier_tags | cap_asym_tags | skeptical_tags

    print("Using tag filters:")
    print(f"  dossier figures: {_format_tags(dossier_tags)}")
    print(f"  capability asymmetry: {_format_tags(cap_asym_tags)}")
    print(f"  skeptical ablation: {_format_tags(skeptical_tags)}")

    if args.raw:
        print("(--raw: using raw Wilson CIs, ignoring emmeans)")
    else:
        using_custom_tags = (
            dossier_tags != {DEFAULT_TAGS["dossier"]}
            or cap_asym_tags != {DEFAULT_TAGS["cap_asym"]}
            or skeptical_tags != {DEFAULT_TAGS["skeptical"]}
        )
        if using_custom_tags:
            print(
                "Custom tags detected: existing results/emmeans JSON files may not "
                "match these tag filters."
            )
            print("  Use --raw or regenerate emmeans for the same logs/tag subset.")
        if EMMEANS_DIR.exists():
            em_files = list(EMMEANS_DIR.glob("*.json"))
            print(f"Found {len(em_files)} emmeans JSON files in {EMMEANS_DIR}/")
            if not em_files:
                print("  (no emmeans found — will use raw Wilson CIs)")
                print("  Run `python analysis/extract_emmeans.py` to generate them.")
        else:
            print("No emmeans directory found — will use raw Wilson CIs.")
            print("  Run `python analysis/extract_emmeans.py` to generate GLME-adjusted estimates.")

    print("\nLoading all experiment logs...")
    data = _load_and_flatten(tags=main_tags)
    print(f"  {len(data)} valid observations loaded")

    main_data = [d for d in data if d["tag"] in main_tags]
    print(f"  {len(main_data)} from main studies ({', '.join(main_tags)})")

    use_raw = args.raw

    print("\nGenerating figures...")
    fig_warden_effect_both(data, output_dir, main_tags, use_raw=use_raw)
    fig_warden_effect(data, output_dir, dossier_tags, use_raw=use_raw)
    fig_dossier_effect(data, output_dir, dossier_tags, use_raw=use_raw)
    fig_capability_asymmetry(data, output_dir, cap_asym_tags, use_raw=use_raw)
    fig_skeptical_ablation(data, output_dir, skeptical_tags, use_raw=use_raw)
    fig_model_family(data, output_dir, main_tags, use_raw=use_raw)
    fig_scenario_variation(data, output_dir, main_tags)
    fig_scenario_variation_contrast(data, output_dir, main_tags)
    fig_warden_fp(data, output_dir, main_tags)
    fig_profile_vulnerability(data, output_dir, main_tags, use_raw=use_raw)
    fig_model_roles(data, output_dir, main_tags, use_raw=use_raw)
    fig_warden_intelligence(data, output_dir, main_tags, use_raw=use_raw)

    print(f"\nAll figures saved to {output_dir}/")


if __name__ == "__main__":
    main()
