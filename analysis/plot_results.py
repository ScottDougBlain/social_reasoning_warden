#!/usr/bin/env python3
"""
Publication-quality figures for Social Reasoning Warden.

Generates key result plots from the three main studies:
  - dossier_effect: dossier × warden factorial
  - cap_asym: warden capability tier
  - skeptical_ablation: baseline vs skeptical vs warden × requester type

Usage:
    python analysis/plot_results.py
    python analysis/plot_results.py --output-dir results/figures
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
import numpy as np
import seaborn as sns

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis.metrics import load_logs

# ── Style ────────────────────────────────────────────────────────────────

sns.set_theme(style="whitegrid", font_scale=1.1)
PALETTE = sns.color_palette("colorblind")
FIG_DPI = 200
BAR_WIDTH = 0.35

# Backward compat: old logs used "chicken" before the rename to "product_launch"
_SCENARIO_ALIASES = {"chicken": "product_launch"}


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

        # Model family
        m = req_model.lower()
        if "gemini" in m:
            family = "Gemini"
        elif "gemma" in m:
            family = "Gemma"
        elif "llama" in m:
            family = "Llama"
        elif "mistral" in m:
            family = "Mistral"
        elif "claude" in m:
            family = "Claude"
        elif "gpt" in m:
            family = "GPT"
        else:
            family = "Other"

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
            "tag": log.get("tag") or "",
        })
    return rows


# ── Figure 1: Warden Effect (dossier_effect study) ──────────────────────


def fig_warden_effect(data: list[dict], output_dir: Path):
    """Bar chart: adversary SR with vs without warden, from dossier_effect."""
    adv = [d for d in data if d["tag"] == "dossier_effect" and d["requester_type"] == "adversary"]
    if not adv:
        print("  [skip] No dossier_effect adversary data")
        return

    with_w = [d for d in adv if d["has_warden"]]
    without_w = [d for d in adv if not d["has_warden"]]

    r_w, lo_w, hi_w, n_w = _rate_and_ci(with_w)
    r_nw, lo_nw, hi_nw, n_nw = _rate_and_ci(without_w)

    fig, ax = plt.subplots(figsize=(5, 5))
    bars = ax.bar(
        [0, 1], [r_nw * 100, r_w * 100],
        yerr=[(r_nw - lo_nw) * 100, (r_w - lo_w) * 100],
        error_kw=dict(capsize=6, capthick=1.5, elinewidth=1.5),
        color=[PALETTE[0], PALETTE[1]], width=0.55, edgecolor="black", linewidth=0.5,
    )
    # Asymmetric error bars
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
    ax.set_title(f"Warden Effect on Adversary Success\n(raw OR = {or_val:.3f})")
    ax.set_ylim(0, 70)

    for i, (r, hi, n) in enumerate([(r_nw, hi_nw, n_nw), (r_w, hi_w, n_w)]):
        ax.text(i, hi * 100 + 3, f"{r*100:.1f}%\nn={n}", ha="center", fontsize=10)

    sns.despine()
    fig.tight_layout()
    fig.savefig(output_dir / "fig1_warden_effect.pdf", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("  [saved] fig1_warden_effect.pdf")


# ── Figure 2: Dossier Effect (2×2 interaction) ──────────────────────────


def fig_dossier_effect(data: list[dict], output_dir: Path):
    """Grouped bar: dossier × warden interaction, adversary only."""
    adv = [d for d in data if d["tag"] == "dossier_effect" and d["requester_type"] == "adversary"]
    if not adv:
        print("  [skip] No dossier_effect data")
        return

    conditions = [
        ("No Dossier\nNo Warden", lambda d: not d["has_dossier"] and not d["has_warden"]),
        ("Dossier\nNo Warden", lambda d: d["has_dossier"] and not d["has_warden"]),
        ("No Dossier\nWith Warden", lambda d: not d["has_dossier"] and d["has_warden"]),
        ("Dossier\nWith Warden", lambda d: d["has_dossier"] and d["has_warden"]),
    ]

    rates, los, his, hi_abs, ns = [], [], [], [], []
    for label, filt in conditions:
        subset = [d for d in adv if filt(d)]
        r, lo, hi, n = _rate_and_ci(subset)
        rates.append(r * 100)
        los.append((r - lo) * 100)
        his.append((hi - r) * 100)
        hi_abs.append(hi * 100)
        ns.append(n)

    fig, ax = plt.subplots(figsize=(7, 5))
    colors = [PALETTE[0], PALETTE[0], PALETTE[1], PALETTE[1]]
    hatches = ["", "///", "", "///"]
    x = np.arange(4)

    bars = ax.bar(x, rates, yerr=[los, his],
                  error_kw=dict(capsize=5, capthick=1.3, elinewidth=1.3),
                  color=colors, width=0.6, edgecolor="black", linewidth=0.5)
    for bar, hatch in zip(bars, hatches):
        bar.set_hatch(hatch)

    # Compute raw ORs
    dossier_yes = [d for d in adv if d["has_dossier"]]
    dossier_no = [d for d in adv if not d["has_dossier"]]
    or_dossier = _raw_odds_ratio(dossier_yes, dossier_no)
    warden_yes = [d for d in adv if d["has_warden"]]
    warden_no = [d for d in adv if not d["has_warden"]]
    or_warden = _raw_odds_ratio(warden_yes, warden_no)

    ax.set_xticks(x)
    ax.set_xticklabels([c[0] for c in conditions], fontsize=9)
    ax.set_ylabel("Adversary Success Rate (%)")
    ax.set_title(f"Dossier × Warden Interaction\n(raw OR: dossier = {or_dossier:.2f}, warden = {or_warden:.3f})")
    ax.set_ylim(0, 70)

    for i, (r, h, n) in enumerate(zip(rates, hi_abs, ns)):
        ax.text(i, h + 2, f"{r:.1f}%\nn={n}", ha="center", fontsize=9)

    sns.despine()
    fig.tight_layout()
    fig.savefig(output_dir / "fig2_dossier_interaction.pdf", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("  [saved] fig2_dossier_interaction.pdf")


# ── Figure 3: Capability Asymmetry (warden tier) ────────────────────────


def fig_capability_asymmetry(data: list[dict], output_dir: Path):
    """Bar chart: adversary SR by warden tier (none/weak/mid/strong)."""
    adv = [d for d in data if d["tag"] == "cap_asym" and d["requester_type"] == "adversary"]
    if not adv:
        print("  [skip] No cap_asym data")
        return

    tiers = ["none", "weak", "mid", "strong"]
    tier_labels = ["None", "Weak\n(= target)", "Mid", "Strong\n(= adversary)"]

    rates, los, his, hi_abs, ns = [], [], [], [], []
    for tier in tiers:
        subset = [d for d in adv if d["warden_tier"] == tier]
        r, lo, hi, n = _rate_and_ci(subset)
        rates.append(r * 100)
        los.append((r - lo) * 100)
        his.append((hi - r) * 100)
        hi_abs.append(hi * 100)
        ns.append(n)

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
    ax.set_title(f"Warden Capability Asymmetry\n(raw OR any-warden vs. none = {or_overall:.3f})")
    ax.set_ylim(0, 65)

    for i, (r, h, n) in enumerate(zip(rates, hi_abs, ns)):
        ax.text(i, h + 2, f"{r:.1f}%\nn={n}", ha="center", fontsize=9)

    sns.despine()
    fig.tight_layout()
    fig.savefig(output_dir / "fig3_capability_asymmetry.pdf", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("  [saved] fig3_capability_asymmetry.pdf")


# ── Figure 4: Skeptical Ablation (3 conditions × 2 requester types) ─────


def fig_skeptical_ablation(data: list[dict], output_dir: Path):
    """Grouped bar: defense condition × requester type."""
    skep = [d for d in data if d["tag"] == "skeptical_ablation"]
    if not skep:
        print("  [skip] No skeptical_ablation data")
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

    fig, ax = plt.subplots(figsize=(7, 5.5))
    x = np.arange(len(conditions))
    width = 0.32

    for j, (rt, rt_label, color) in enumerate([
        ("adversary", "Adversary", PALETTE[3]),
        ("benign_agent", "Benign Agent", PALETTE[0]),
    ]):
        rates, err_lo, err_hi, hi_abs, ns_list = [], [], [], [], []
        for cond in conditions:
            subset = [d for d in skep if d["requester_type"] == rt and _cond(d) == cond]
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
    ax.set_title("Defense Mechanism Comparison\n(Adversary suppression vs. benign false positive cost)")
    ax.set_ylim(0, 110)
    ax.legend(loc="upper right", framealpha=0.9)

    sns.despine()
    fig.tight_layout()
    fig.savefig(output_dir / "fig4_skeptical_ablation.pdf", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("  [saved] fig4_skeptical_ablation.pdf")


# ── Figure 5: Adversary SR by Model Family ───────────────────────────────


def fig_model_family(data: list[dict], output_dir: Path):
    """Bar chart: adversary SR by model family (pooled across main studies)."""
    main_tags = {"dossier_effect", "cap_asym", "skeptical_ablation"}
    adv = [d for d in data if d["tag"] in main_tags and d["requester_type"] == "adversary"
           and not d["has_warden"]]
    if not adv:
        print("  [skip] No adversary data for model family plot")
        return

    families = defaultdict(list)
    for d in adv:
        families[d["model_family"]].append(d)

    # Sort by success rate
    family_data = []
    for fam, items in families.items():
        if len(items) < 10:
            continue
        r, lo, hi, n = _rate_and_ci(items)
        family_data.append((fam, r, lo, hi, n))
    family_data.sort(key=lambda x: -x[1])

    if not family_data:
        print("  [skip] Not enough data for model family plot")
        return

    fig, ax = plt.subplots(figsize=(7, 5))
    fams = [f[0] for f in family_data]
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
    ax.set_title("Adversary Effectiveness by Model Family\n(no warden, pooled across studies)")
    ax.set_ylim(0, 80)

    for i, (r, h, n) in enumerate(zip(rates, hi_abs, ns)):
        ax.text(i, h + 2, f"{r:.1f}%\nn={n}", ha="center", fontsize=9)

    sns.despine()
    fig.tight_layout()
    fig.savefig(output_dir / "fig5_model_family.pdf", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("  [saved] fig5_model_family.pdf")


# ── Figure 6: Adversary SR by Scenario ───────────────────────────────────


def fig_scenario_variation(data: list[dict], output_dir: Path):
    """Horizontal bar: adversary SR by scenario (no warden), pooled."""
    main_tags = {"dossier_effect", "cap_asym", "skeptical_ablation"}
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
    fig.savefig(output_dir / "fig6_scenario_variation.pdf", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("  [saved] fig6_scenario_variation.pdf")


# ── Figure 7: Warden FP by Scenario ─────────────────────────────────────


def fig_warden_fp(data: list[dict], output_dir: Path):
    """Paired dot plot: benign SR with and without warden, by scenario."""
    main_tags = {"skeptical_ablation", "dossier_effect", "cap_asym"}
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
    fig.savefig(output_dir / "fig7_warden_fp_by_scenario.pdf", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("  [saved] fig7_warden_fp_by_scenario.pdf")


# ── Figure 0: Warden Effect — Adversary vs Benign (pooled) ────────────────


def fig_warden_effect_both(data: list[dict], output_dir: Path):
    """Grouped bar: warden effect on adversary AND benign agent success."""
    main_tags = {"dossier_effect", "cap_asym", "skeptical_ablation"}
    main = [d for d in data if d["tag"] in main_tags]
    if not main:
        print("  [skip] No main study data for warden effect (both)")
        return

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
    ax.set_title("Warden Effect: Adversary vs. Benign Agent\n"
                 f"(adversary raw OR = {or_adv:.3f})")
    ax.set_ylim(0, 115)
    ax.legend(loc="upper right", framealpha=0.9)

    sns.despine()
    fig.tight_layout()
    fig.savefig(output_dir / "fig0_warden_effect_both.pdf",
                dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("  [saved] fig0_warden_effect_both.pdf")


# ── Figure 8: Profile Vulnerability × Warden ─────────────────────────────


def fig_profile_vulnerability(data: list[dict], output_dir: Path):
    """Grouped bar: adversary SR by profile × warden condition."""
    main_tags = {"dossier_effect", "cap_asym", "skeptical_ablation"}
    adv = [d for d in data if d["tag"] in main_tags
           and d["requester_type"] == "adversary"]
    if not adv:
        print("  [skip] No adversary data for profile vulnerability plot")
        return

    # Map display names → canonical keys for matching
    profile_map = {
        "Idealistic True Believer": "Idealistic",
        "Compliant Agreeable": "Compliant",
        "Authority-Deferential Follower": "Authority\nDeferential",
        "Authority-Deferential Junior Employee": "Authority\nDeferential",
        "Overwhelmed Time-Pressured": "Time\nPressured",
        "Overwhelmed Time-Pressured Worker": "Time\nPressured",
    }
    profile_order = ["Idealistic", "Compliant",
                     "Authority\nDeferential", "Time\nPressured"]

    # Bucket data by canonical profile label
    bucketed = defaultdict(list)
    for d in adv:
        label = profile_map.get(d["profile"])
        if label:
            bucketed[(label, d["has_warden"])].append(d)

    fig, ax = plt.subplots(figsize=(7, 5.5))
    x = np.arange(len(profile_order))
    width = 0.32

    for j, (has_w, w_label, color) in enumerate([
        (False, "No Warden", PALETTE[3]),
        (True, "With Warden", PALETTE[1]),
    ]):
        rates, err_lo, err_hi, hi_abs, ns_list = [], [], [], [], []
        for prof in profile_order:
            subset = bucketed.get((prof, has_w), [])
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
            ax.text(x[i] + offset, h + 2, f"{r:.1f}%\nn={n}",
                    ha="center", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(profile_order, fontsize=9)
    ax.set_xlabel("Target Vulnerability Profile")
    ax.set_ylabel("Adversary Success Rate (%)")
    ax.set_title("Profile Vulnerability × Warden\n"
                 "(pooled across studies, adversary only)")
    ax.set_ylim(0, 80)
    ax.legend(loc="upper right", framealpha=0.9)

    sns.despine()
    fig.tight_layout()
    fig.savefig(output_dir / "fig8_profile_vulnerability.pdf",
                dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)
    print("  [saved] fig8_profile_vulnerability.pdf")


# ── Main ─────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Generate result figures.")
    parser.add_argument(
        "--output-dir", type=str, default="results/figures",
        help="Directory for output PDFs.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Loading all experiment logs...")
    data = _load_and_flatten()
    print(f"  {len(data)} valid observations loaded")

    # Filter to main studies
    main_tags = {"dossier_effect", "cap_asym", "skeptical_ablation"}
    main_data = [d for d in data if d["tag"] in main_tags]
    print(f"  {len(main_data)} from main studies ({', '.join(main_tags)})")

    print("\nGenerating figures...")
    fig_warden_effect_both(data, output_dir)
    fig_warden_effect(data, output_dir)
    fig_dossier_effect(data, output_dir)
    fig_capability_asymmetry(data, output_dir)
    fig_skeptical_ablation(data, output_dir)
    fig_model_family(data, output_dir)
    fig_scenario_variation(data, output_dir)
    fig_warden_fp(data, output_dir)
    fig_profile_vulnerability(data, output_dir)

    print(f"\nAll figures saved to {output_dir}/")


if __name__ == "__main__":
    main()
