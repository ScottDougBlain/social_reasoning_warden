#!/usr/bin/env python3
"""Extract model-adjusted estimated marginal means (emmeans) from GLMEs.

Fits the same GLME models as run_lme.py, then uses R's emmeans package to
compute predicted marginal means (on the response/probability scale) with
profile-likelihood or delta-method CIs.  Results are saved as JSON files
under results/emmeans/ for consumption by plot_results.py.

Usage:
    python analysis/extract_emmeans.py
    python analysis/extract_emmeans.py --figures 1 2 3 5 8
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis.metrics import load_logs
from analysis.run_lme import (
    GLMER_FIT_BLOCK,
    logs_to_dataframe,
)

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
EMMEANS_DIR = RESULTS_DIR / "emmeans"


def _run_r(r_script: str, label: str) -> str:
    """Execute an R script and return stdout."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")

    result = subprocess.run(
        ["R", "--vanilla", "--quiet", "-e", r_script],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0:
        print(f"  R stderr:\n{result.stderr}")
    # Strip R prompt lines
    lines = [
        line for line in result.stdout.split("\n")
        if not line.startswith(">") and not line.startswith("+")
    ]
    clean = "\n".join(lines).strip()
    print(clean)
    return result.stdout


def _save_emmeans(data: list[dict], name: str) -> Path:
    """Write emmeans to JSON file."""
    EMMEANS_DIR.mkdir(parents=True, exist_ok=True)
    path = EMMEANS_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  -> Saved {path}")
    return path


def _dataframe_to_json_records(df: pd.DataFrame) -> list[dict]:
    """Convert a dataframe to JSON-safe row dictionaries."""
    records: list[dict] = []
    for _, row in df.iterrows():
        record = {}
        for key, value in row.items():
            if pd.isna(value):
                record[key] = None
            elif hasattr(value, "item"):
                record[key] = value.item()
            else:
                record[key] = value
        records.append(record)
    return records


def _save_contrast_csv(csv_path: str, name: str) -> list[dict] | None:
    """Read an R-written contrast CSV and save it as JSON."""
    try:
        contrast_df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"  [error] {name} contrast CSV not found")
        return None

    contrast_records = _dataframe_to_json_records(contrast_df)
    _save_emmeans(contrast_records, name)
    return contrast_records


# ── Figure 1: Warden Effect (has_warden, adversary only) ─────────────────

def extract_fig1(df: pd.DataFrame) -> list[dict] | None:
    """Emmeans for warden effect: marginal means of has_warden, adversary only."""
    data = df[
        (df["requester_type"] == "adversary")
    ].copy()

    if len(data) < 20:
        print("  [skip] Not enough adversary data for fig1 emmeans")
        return None

    csv_path = "/tmp/emmeans_fig1.csv"
    out_path = "/tmp/emmeans_fig1_out.csv"
    contrast_out_path = "/tmp/emmeans_fig1_contrasts.csv"
    data.to_csv(csv_path, index=False)

    r_script = f"""
library(lme4)
library(emmeans)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d$has_warden <- factor(d$has_warden)
d$scenario <- factor(d$scenario)
d$profile_name <- factor(d$profile_name)
d$target_model <- factor(d$target_model)
d$requester_model <- factor(d$requester_model)

m <- fit_glmer(
    success ~ has_warden
        + (1 + has_warden|scenario) + (1|profile_name) + (1|target_model) + (1|requester_model),
    data=d, label="fig1"
)

if (!is.null(m)) {{
    em <- emmeans(m, ~ has_warden, type="response")
    cat("\\nEmmeans (response scale):\\n")
    print(summary(em))

    em_contrasts <- pairs(em, type="response", reverse=TRUE, adjust="none")
    contrast_df <- as.data.frame(summary(em_contrasts))
    contrast_df$contrast_family <- "warden_effect_adversary_only"
    contrast_df$p.value.raw <- contrast_df$p.value
    contrast_df$p.value <- p.adjust(contrast_df$p.value.raw, method="BH")

    cat("\\nPairwise contrasts (odds ratio):\\n")
    print(contrast_df)

    em_df <- as.data.frame(summary(em))
    write.csv(em_df, "{out_path}", row.names=FALSE)
    write.csv(contrast_df, "{contrast_out_path}", row.names=FALSE)
}}
"""

    _run_r(r_script, "Fig 1: Warden Effect emmeans")

    try:
        em_df = pd.read_csv(out_path)
    except FileNotFoundError:
        print("  [error] emmeans output CSV not found — model may have failed")
        return None

    records = []
    for _, row in em_df.iterrows():
        records.append({
            "has_warden": int(row["has_warden"]),
            "prob": float(row["prob"]),
            "asymp.LCL": float(row["asymp.LCL"]),
            "asymp.UCL": float(row["asymp.UCL"]),
        })
    _save_emmeans(records, "fig1_warden_effect")
    _save_contrast_csv(contrast_out_path, "fig1_warden_effect_contrasts")
    return records


# ── Figure 2: Dossier × Warden Interaction ───────────────────────────────

def extract_fig2(df: pd.DataFrame) -> list[dict] | None:
    """Emmeans for dossier × warden factorial, adversary + profiled."""
    data = df[
        (df["requester_type"] == "adversary") & (df["has_profile"] == 1)
    ].copy()

    if len(data) < 20:
        print("  [skip] Not enough data for fig2 emmeans")
        return None

    csv_path = "/tmp/emmeans_fig2.csv"
    out_path = "/tmp/emmeans_fig2_out.csv"
    contrast_out_path = "/tmp/emmeans_fig2_contrasts.csv"
    data.to_csv(csv_path, index=False)

    r_script = f"""
library(lme4)
library(emmeans)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d$adversary_has_data <- factor(d$adversary_has_data)
d$has_warden <- factor(d$has_warden)
d$scenario <- factor(d$scenario)
d$profile_name <- factor(d$profile_name)
d$target_model <- factor(d$target_model)

m <- fit_glmer(
    success ~ adversary_has_data * has_warden
        + (1 + has_warden|scenario) + (1|profile_name) + (1|target_model),
    data=d, label="fig2"
)

if (!is.null(m)) {{
    em <- emmeans(m, ~ adversary_has_data * has_warden, type="response")
    em_link <- emmeans(m, ~ adversary_has_data * has_warden)
    cat("\\nEmmeans (response scale):\\n")
    print(summary(em))

    dossier_contrasts <- pairs(
        emmeans(m, ~ adversary_has_data | has_warden),
        type="response", reverse=TRUE, adjust="none"
    )
    dossier_df <- as.data.frame(summary(dossier_contrasts))
    dossier_df$contrast_family <- "dossier_vs_no_dossier_within_warden"

    warden_contrasts <- pairs(
        emmeans(m, ~ has_warden | adversary_has_data),
        type="response", reverse=TRUE, adjust="none"
    )
    warden_df <- as.data.frame(summary(warden_contrasts))
    warden_df$contrast_family <- "warden_vs_no_warden_within_dossier"

    grid_df <- as.data.frame(em_link)
    interaction_coef <- ifelse(
        grid_df$adversary_has_data == "1" & grid_df$has_warden == "1", 1,
        ifelse(
            grid_df$adversary_has_data == "0" & grid_df$has_warden == "1", -1,
            ifelse(
                grid_df$adversary_has_data == "1" & grid_df$has_warden == "0", -1,
                ifelse(grid_df$adversary_has_data == "0" & grid_df$has_warden == "0", 1, 0)
            )
        )
    )
    interaction_contrast <- contrast(
        em_link,
        list("dossier_effect_with_warden_minus_without_warden" = interaction_coef),
        adjust="none"
    )
    interaction_df <- as.data.frame(summary(interaction_contrast, type="response"))
    interaction_df$contrast_family <- "dossier_x_warden_interaction"

    all_cols <- Reduce(union, list(names(dossier_df), names(warden_df), names(interaction_df)))
    for (nm in setdiff(all_cols, names(dossier_df))) dossier_df[[nm]] <- NA
    for (nm in setdiff(all_cols, names(warden_df))) warden_df[[nm]] <- NA
    for (nm in setdiff(all_cols, names(interaction_df))) interaction_df[[nm]] <- NA
    contrast_df <- rbind(dossier_df[all_cols], warden_df[all_cols], interaction_df[all_cols])
    contrast_df$p.value.raw <- contrast_df$p.value
    contrast_df$p.value <- p.adjust(contrast_df$p.value.raw, method="BH")

    cat("\\nPairwise contrasts and interaction contrast (BH-adjusted):\\n")
    print(contrast_df)

    em_df <- as.data.frame(summary(em))
    write.csv(em_df, "{out_path}", row.names=FALSE)
    write.csv(contrast_df, "{contrast_out_path}", row.names=FALSE)
}}
"""

    _run_r(r_script, "Fig 2: Dossier × Warden emmeans")

    try:
        em_df = pd.read_csv(out_path)
    except FileNotFoundError:
        print("  [error] emmeans output CSV not found")
        return None

    records = []
    for _, row in em_df.iterrows():
        records.append({
            "has_dossier": int(row["adversary_has_data"]),
            "has_warden": int(row["has_warden"]),
            "prob": float(row["prob"]),
            "asymp.LCL": float(row["asymp.LCL"]),
            "asymp.UCL": float(row["asymp.UCL"]),
        })
    _save_emmeans(records, "fig2_dossier_interaction")
    _save_contrast_csv(contrast_out_path, "fig2_dossier_interaction_contrasts")
    return records


# ── Figure 3: Capability Asymmetry (warden_tier) ─────────────────────────

def extract_fig3(df: pd.DataFrame) -> list[dict] | None:
    """Emmeans for warden capability tier (none/weak/mid/strong)."""
    data = df[df["requester_type"] == "adversary"].copy()

    if len(data) < 20:
        print("  [skip] Not enough data for fig3 emmeans")
        return None

    csv_path = "/tmp/emmeans_fig3.csv"
    out_path = "/tmp/emmeans_fig3_out.csv"
    contrast_out_path = "/tmp/emmeans_fig3_contrasts.csv"
    data.to_csv(csv_path, index=False)

    r_script = f"""
library(lme4)
library(emmeans)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d$warden_tier <- factor(d$warden_tier, levels=c("none", "weak", "mid", "strong"))
d$warden_tier <- relevel(d$warden_tier, ref="none")
d$model_family <- factor(d$model_family)
d$scenario <- factor(d$scenario)
d$profile_name <- factor(d$profile_name)

m <- fit_glmer(
    success ~ warden_tier + (1|model_family) + (1 + warden_tier|scenario) + (1|profile_name),
    data=d, label="fig3"
)

if (!is.null(m)) {{
    em <- emmeans(m, ~ warden_tier, type="response")
    cat("\\nEmmeans (response scale):\\n")
    print(summary(em))

    em_contrasts <- pairs(em, type="response", reverse=TRUE, adjust="BH")
    cat("\\nPairwise contrasts (odds ratio):\\n")
    print(em_contrasts)

    em_df <- as.data.frame(summary(em))
    write.csv(em_df, "{out_path}", row.names=FALSE)

    contrast_df <- as.data.frame(summary(em_contrasts))
    write.csv(contrast_df, "{contrast_out_path}", row.names=FALSE)
}}
"""

    _run_r(r_script, "Fig 3: Capability Asymmetry emmeans")

    try:
        em_df = pd.read_csv(out_path)
    except FileNotFoundError:
        print("  [error] emmeans output CSV not found")
        return None

    records = []
    for _, row in em_df.iterrows():
        records.append({
            "warden_tier": row["warden_tier"],
            "prob": float(row["prob"]),
            "asymp.LCL": float(row["asymp.LCL"]),
            "asymp.UCL": float(row["asymp.UCL"]),
        })
    _save_emmeans(records, "fig3_capability_asymmetry")

    try:
        contrast_df = pd.read_csv(contrast_out_path)
    except FileNotFoundError:
        print("  [error] fig3 pairwise contrast CSV not found")
    else:
        contrast_records = _dataframe_to_json_records(contrast_df)
        _save_emmeans(contrast_records, "fig3_capability_asymmetry_contrasts")

    return records


# ── Figure 0: Warden Effect — Both requester types ───────────────────────

def extract_fig0(df: pd.DataFrame) -> list[dict] | None:
    """Emmeans for warden × requester_type (pooled across studies)."""
    data = df.copy()

    if len(data) < 20:
        print("  [skip] Not enough data for fig0 emmeans")
        return None

    csv_path = "/tmp/emmeans_fig0.csv"
    out_path = "/tmp/emmeans_fig0_out.csv"
    contrast_out_path = "/tmp/emmeans_fig0_contrasts.csv"
    data.to_csv(csv_path, index=False)

    r_script = f"""
library(lme4)
library(emmeans)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d$requester_type <- relevel(factor(d$requester_type), ref="benign_agent")
d$has_warden <- factor(d$has_warden)
d$scenario <- factor(d$scenario)
d$profile_name <- factor(d$profile_name)
d$target_model <- factor(d$target_model)
d$requester_model <- factor(d$requester_model)

m <- fit_glmer(
    success ~ requester_type * has_warden
        + (1 + has_warden|scenario) + (1|profile_name) + (1|target_model) + (1|requester_model),
    data=d, label="fig0"
)

if (!is.null(m)) {{
    em <- emmeans(m, ~ requester_type * has_warden, type="response")
    em_link <- emmeans(m, ~ requester_type * has_warden)
    cat("\\nEmmeans (response scale):\\n")
    print(summary(em))

    warden_contrasts <- pairs(
        emmeans(m, ~ has_warden | requester_type),
        type="response", reverse=TRUE, adjust="none"
    )
    warden_df <- as.data.frame(summary(warden_contrasts))
    warden_df$contrast_family <- "warden_vs_no_warden_within_requester"

    grid_df <- as.data.frame(em_link)
    did_coef <- ifelse(
        grid_df$requester_type == "adversary" & grid_df$has_warden == "1", 1,
        ifelse(
            grid_df$requester_type == "adversary" & grid_df$has_warden == "0", -1,
            ifelse(
                grid_df$requester_type == "benign_agent" & grid_df$has_warden == "1", -1,
                ifelse(grid_df$requester_type == "benign_agent" & grid_df$has_warden == "0", 1, 0)
            )
        )
    )
    did_contrast <- contrast(
        em_link,
        list("adversary_warden_effect_minus_benign_warden_effect" = did_coef),
        adjust="none"
    )
    did_df <- as.data.frame(summary(did_contrast, type="response"))
    did_df$contrast_family <- "requester_type_x_warden_interaction"

    all_cols <- union(names(warden_df), names(did_df))
    for (nm in setdiff(all_cols, names(warden_df))) warden_df[[nm]] <- NA
    for (nm in setdiff(all_cols, names(did_df))) did_df[[nm]] <- NA
    contrast_df <- rbind(warden_df[all_cols], did_df[all_cols])
    contrast_df$p.value.raw <- contrast_df$p.value
    contrast_df$p.value <- p.adjust(contrast_df$p.value.raw, method="BH")

    cat("\\nPairwise contrasts and interaction contrast (BH-adjusted):\\n")
    print(contrast_df)

    em_df <- as.data.frame(summary(em))
    write.csv(em_df, "{out_path}", row.names=FALSE)
    write.csv(contrast_df, "{contrast_out_path}", row.names=FALSE)
}}
"""

    _run_r(r_script, "Fig 0: Warden Effect (both requester types) emmeans")

    try:
        em_df = pd.read_csv(out_path)
    except FileNotFoundError:
        print("  [error] emmeans output CSV not found")
        return None

    records = []
    for _, row in em_df.iterrows():
        records.append({
            "requester_type": row["requester_type"],
            "has_warden": int(row["has_warden"]),
            "prob": float(row["prob"]),
            "asymp.LCL": float(row["asymp.LCL"]),
            "asymp.UCL": float(row["asymp.UCL"]),
        })
    _save_emmeans(records, "fig0_warden_effect_both")
    _save_contrast_csv(contrast_out_path, "fig0_warden_effect_both_contrasts")
    return records


# ── Figure 8: Profile Vulnerability × Warden ─────────────────────────────

def extract_fig8(df: pd.DataFrame) -> list[dict] | None:
    """Emmeans for profile × warden interaction, adversary only."""
    data = df[
        (df["requester_type"] == "adversary") & (df["has_profile"] == 1)
    ].copy()

    if len(data) < 20:
        print("  [skip] Not enough data for fig8 emmeans")
        return None

    csv_path = "/tmp/emmeans_fig8.csv"
    out_path = "/tmp/emmeans_fig8_out.csv"
    data.to_csv(csv_path, index=False)

    r_script = f"""
library(lme4)
library(emmeans)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d$has_warden <- factor(d$has_warden)
d$scenario <- factor(d$scenario)
d$target_model <- factor(d$target_model)
d$profile_name <- factor(d$profile_name)

m <- fit_glmer(
    success ~ profile_name * has_warden
        + (1 + has_warden|scenario) + (1|target_model),
    data=d, label="fig8"
)

if (!is.null(m)) {{
    em <- emmeans(m, ~ profile_name * has_warden, type="response")
    cat("\\nEmmeans (response scale):\\n")
    print(summary(em))

    em_df <- as.data.frame(summary(em))
    write.csv(em_df, "{out_path}", row.names=FALSE)
}}
"""

    _run_r(r_script, "Fig 8: Profile Vulnerability × Warden emmeans")

    try:
        em_df = pd.read_csv(out_path)
    except FileNotFoundError:
        print("  [error] emmeans output CSV not found")
        return None

    records = []
    for _, row in em_df.iterrows():
        records.append({
            "profile_name": row["profile_name"],
            "has_warden": int(row["has_warden"]),
            "prob": float(row["prob"]),
            "asymp.LCL": float(row["asymp.LCL"]),
            "asymp.UCL": float(row["asymp.UCL"]),
        })
    _save_emmeans(records, "fig8_profile_vulnerability")
    return records


# ── Figure 5: Model Family ───────────────────────────────────────────────

def extract_fig5(df: pd.DataFrame) -> list[dict] | None:
    """Emmeans for adversary SR by model family (no warden, pooled)."""
    data = df[
        (df["requester_type"] == "adversary") & (df["has_warden"] == 0)
    ].copy()

    if len(data) < 20:
        print("  [skip] Not enough data for fig5 emmeans")
        return None

    # Only families with >= 10 obs
    family_counts = data["model_family"].value_counts()
    keep = family_counts[family_counts >= 10].index.tolist()
    data = data[data["model_family"].isin(keep)].copy()

    if len(data) < 20:
        print("  [skip] Not enough data after filtering model families")
        return None

    csv_path = "/tmp/emmeans_fig5.csv"
    out_path = "/tmp/emmeans_fig5_out.csv"
    data.to_csv(csv_path, index=False)

    r_script = f"""
library(lme4)
library(emmeans)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d$model_family <- factor(d$model_family)
d$scenario <- factor(d$scenario)
d$profile_name <- factor(d$profile_name)
d$target_model <- factor(d$target_model)

m <- fit_glmer(
    success ~ model_family + (1|scenario) + (1|profile_name) + (1|target_model),
    data=d, label="fig5"
)

if (!is.null(m)) {{
    em <- emmeans(m, ~ model_family, type="response")
    cat("\\nEmmeans (response scale):\\n")
    print(summary(em))

    em_df <- as.data.frame(summary(em))
    write.csv(em_df, "{out_path}", row.names=FALSE)
}}
"""

    _run_r(r_script, "Fig 5: Model Family emmeans")

    try:
        em_df = pd.read_csv(out_path)
    except FileNotFoundError:
        print("  [error] emmeans output CSV not found")
        return None

    records = []
    for _, row in em_df.iterrows():
        records.append({
            "model_family": row["model_family"],
            "prob": float(row["prob"]),
            "asymp.LCL": float(row["asymp.LCL"]),
            "asymp.UCL": float(row["asymp.UCL"]),
        })
    _save_emmeans(records, "fig5_model_family")
    return records


# ── Figure 9: Model Roles (requester / target / warden) ────────────────

def extract_fig9(df: pd.DataFrame) -> list[dict] | None:
    """Emmeans for adversary SR by each model role (requester, target, warden)."""
    all_records: list[dict] = []

    # --- Sub-model configs: (role, filter, formula, emmeans_var, random_effects) ---
    sub_models = [
        (
            "requester",
            lambda d: d[(d["requester_type"] == "adversary") & (d["has_warden"] == 0)],
            "success ~ requester_model + (1|scenario) + (1|target_model)",
            "requester_model",
        ),
        (
            "target",
            lambda d: d[(d["requester_type"] == "adversary") & (d["has_warden"] == 0)],
            "success ~ target_model + (1|scenario) + (1|requester_model)",
            "target_model",
        ),
        (
            "warden",
            lambda d: d[(d["requester_type"] == "adversary") & (d["has_warden"] == 1)],
            "success ~ warden_model + (1|scenario) + (1|target_model)",
            "warden_model",
        ),
    ]

    for role, filter_fn, formula, emm_var in sub_models:
        data = filter_fn(df).copy()

        # Only keep models with >= 10 observations
        model_counts = data[emm_var].value_counts()
        keep = model_counts[model_counts >= 10].index.tolist()
        data = data[data[emm_var].isin(keep)].copy()

        if len(data) < 20:
            print(f"  [skip] Not enough data for fig9 sub-model: {role}")
            continue

        csv_path = f"/tmp/emmeans_fig9_{role}.csv"
        out_path = f"/tmp/emmeans_fig9_{role}_out.csv"
        data.to_csv(csv_path, index=False)

        r_script = f"""
library(lme4)
library(emmeans)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d${emm_var} <- factor(d${emm_var})
d$scenario <- factor(d$scenario)
{"d$target_model <- factor(d$target_model)" if emm_var != "target_model" else "d$requester_model <- factor(d$requester_model)"}
{"d$requester_model <- factor(d$requester_model)" if emm_var == "target_model" else ""}

m <- fit_glmer(
    {formula},
    data=d, label="fig9_{role}"
)

if (!is.null(m)) {{
    em <- emmeans(m, ~ {emm_var}, type="response")
    cat("\\nEmmeans (response scale):\\n")
    print(summary(em))

    em_df <- as.data.frame(summary(em))
    write.csv(em_df, "{out_path}", row.names=FALSE)
}}
"""

        _run_r(r_script, f"Fig 9: Model Roles — {role}")

        try:
            em_df = pd.read_csv(out_path)
        except FileNotFoundError:
            print(f"  [error] emmeans output CSV not found for {role}")
            continue

        for _, row in em_df.iterrows():
            all_records.append({
                "role": role,
                "model": row[emm_var],
                "prob": float(row["prob"]),
                "asymp.LCL": float(row["asymp.LCL"]),
                "asymp.UCL": float(row["asymp.UCL"]),
            })

    if not all_records:
        print("  [skip] No sub-models produced results for fig9")
        return None

    _save_emmeans(all_records, "fig9_model_roles")
    return all_records


# ── Main ─────────────────────────────────────────────────────────────────

ALL_FIGURES = [0, 1, 2, 3, 5, 8, 9]

EXTRACTORS = {
    0: ("Fig 0: Warden Effect (both)", extract_fig0),
    1: ("Fig 1: Warden Effect (adversary)", extract_fig1),
    2: ("Fig 2: Dossier × Warden", extract_fig2),
    3: ("Fig 3: Capability Asymmetry", extract_fig3),
    5: ("Fig 5: Model Family", extract_fig5),
    8: ("Fig 8: Profile Vulnerability", extract_fig8),
    9: ("Fig 9: Model Roles", extract_fig9),
}


def main():
    parser = argparse.ArgumentParser(
        description="Extract emmeans from GLMEs for figure generation."
    )
    parser.add_argument(
        "--figures",
        type=int,
        nargs="+",
        default=ALL_FIGURES,
        choices=ALL_FIGURES,
        help=f"Which figures to extract emmeans for (default: all = {ALL_FIGURES}).",
    )
    parser.add_argument(
        "--tag",
        type=str,
        nargs="+",
        default=None,
        help="Filter logs by tag (space/comma-separated).",
    )
    args = parser.parse_args()

    # Parse tags
    tag_filter = None
    if args.tag:
        tag_filter = []
        for entry in args.tag:
            for t in entry.split(","):
                t = t.strip()
                if t:
                    tag_filter.append(t)

    print("=" * 60)
    print("  Extracting GLME Emmeans for Figures")
    print("=" * 60)

    print("\nLoading experiment logs...")
    logs = load_logs(tag=tag_filter)
    print(f"  Loaded {len(logs)} logs")

    if not logs:
        print("No logs found.")
        sys.exit(1)

    print("Building analysis dataframe...")
    df = logs_to_dataframe(logs)
    print(f"  Valid observations: {len(df)}")

    if len(df) == 0:
        print("No valid observations.")
        sys.exit(1)

    print(f"  Adversary: {(df['requester_type'] == 'adversary').sum()}")
    print(f"  Benign: {(df['requester_type'] == 'benign_agent').sum()}")
    print(f"  Overall SR: {df['success'].mean():.1%}")

    EMMEANS_DIR.mkdir(parents=True, exist_ok=True)

    for fig_num in args.figures:
        label, fn = EXTRACTORS[fig_num]
        print(f"\n--- {label} ---")
        fn(df)

    print(f"\n{'=' * 60}")
    print(f"  All emmeans saved to {EMMEANS_DIR}/")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
