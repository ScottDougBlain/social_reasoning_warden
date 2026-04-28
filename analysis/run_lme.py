#!/usr/bin/env python3
"""
Mixed-effects models for Social Reasoning Warden experiments.

Runs confirmatory GLME models using R's lme4 + lmerTest:
  Model 1: Warden Effectiveness — requester_type × has_warden
  Model 2: Dossier Impact — adversary_has_data × has_warden (adversary only)
  Model 3: Profile Vulnerability — profile_name × has_warden (adversary + profiled)
  Model 4: Capability Asymmetry — warden_tier (none/weak/mid/strong)
  Model 5: CB5T Detection × Resistance × Warden (adversary + CB5T profiled)
  Model 6: Profile Family × Warden (adversary + CB5T profiled)

Outputs: results/lme_results.md (formatted summary)

Usage:
    python analysis/run_lme.py
    python analysis/run_lme.py --tag claude-series --models 1 2
    python analysis/run_lme.py --tag cap_asym --models 4
    python analysis/run_lme.py --scenario ai_containment
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import warnings
from pathlib import Path

import pandas as pd

# Allow importing from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from analysis.model_family import model_family_key
from analysis.metrics import load_logs

warnings.filterwarnings("ignore")

RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"


# ── Data loading ──────────────────────────────────────────────────────────


def _warden_tier(models: dict) -> str:
    """Classify warden capability tier relative to target and adversary.

    Returns: 'none', 'weak' (= target), 'mid', or 'strong' (= adversary).
    """
    warden = models.get("warden")
    if not warden or warden == "none":
        return "none"
    target = models.get("target", "")
    adversary = models.get("adversary") or models.get("benign_agent") or ""
    # Strip :free suffix for comparison
    def _base(m: str) -> str:
        return m.removesuffix(":free") if m else ""
    if _base(warden) == _base(target):
        return "weak"
    if _base(warden) == _base(adversary):
        return "strong"
    return "mid"


def _has_warden(log: dict) -> bool:
    warden_model = (log.get("models") or {}).get("warden")
    return warden_model not in {None, "none", ""}


def _get_decision(log: dict) -> str | None:
    outcome = log.get("outcome") or {}
    return outcome.get("aggregate_decision") or outcome.get("decision")


def logs_to_dataframe(logs: list[dict]) -> pd.DataFrame:
    """Flatten JSON experiment logs into a pandas DataFrame for LME analysis.

    Each row = one experiment run. Multi-target (board) logs use the
    aggregate decision. Formatting failures are excluded.
    """
    rows = []
    for log in logs:
        decision = _get_decision(log)
        if decision not in {"requester_success", "requester_failure"}:
            continue

        profile = log.get("profile") or {}
        models = log.get("models") or {}
        requester_type = log.get("requester_type", "unknown")

        # Determine requester model
        if requester_type == "adversary":
            requester_model = models.get("adversary")
        elif requester_type == "benign_agent":
            requester_model = models.get("benign_agent")
        else:
            requester_model = models.get("adversary") or models.get("benign_agent")

        rows.append(
            {
                "run_id": log.get("run_id", ""),
                "scenario": log.get("scenario", "unknown"),
                "scenario_type": log.get("scenario_type", "single"),
                "condition": log.get("condition", ""),
                "requester_type": requester_type,
                "has_warden": int(_has_warden(log)),
                "profile_name": profile.get("name") or "none",
                "has_profile": int(bool(profile.get("target_has_profile"))),
                "adversary_has_data": int(bool(profile.get("adversary_has_data"))),
                "warden_has_intel": int(bool(profile.get("warden_has_intel"))),
                "dossier_variant": profile.get("dossier_variant"),
                "requester_model": requester_model or "unknown",
                "target_model": models.get("target", "unknown"),
                "warden_model": models.get("warden") or "none",
                "warden_tier": _warden_tier(models),
                "model_family": model_family_key(requester_model or "unknown"),
                "target_skeptical": int(bool(log.get("target_skeptical"))),
                "num_turns": log.get("num_turns", 0),
                "success": int(decision == "requester_success"),
                "tag": log.get("tag"),
                # CB5T-derived properties
                "detection_capacity": profile.get("detection_capacity") or "unknown",
                "resistance_capacity": profile.get("resistance_capacity") or "unknown",
                "profile_family": profile.get("profile_family") or "unknown",
                "primary_attack_surface": profile.get("primary_attack_surface") or "unknown",
                "warden_value": profile.get("warden_value") or "unknown",
                # BFI-2 domain scores (grid profiles)
                "E": profile.get("E"),
                "A": profile.get("A"),
                "C": profile.get("C"),
                "N": profile.get("N"),
                "O": profile.get("O"),
                "cluster": profile.get("cluster") or "none",
                "profile_type": profile.get("profile_type") or "none",
            }
        )

    df = pd.DataFrame(rows)
    return df


# ── R execution ──────────────────────────────────────────────────────────


def run_r_glmer(csv_path: str, r_script: str, label: str) -> str:
    """Write data to CSV, run R script via subprocess, return cleaned output."""
    print(f"\n{'=' * 70}")
    print(f"  {label}")
    print(f"{'=' * 70}")

    result = subprocess.run(
        ["R", "--vanilla", "--quiet", "-e", r_script],
        capture_output=True,
        text=True,
        timeout=300,
    )

    output = result.stdout + result.stderr
    # Clean R prompt lines
    lines = []
    for line in output.split("\n"):
        if line.startswith(">") or line.startswith("+"):
            continue
        lines.append(line)
    clean = "\n".join(lines).strip()
    print(clean)
    return clean


# ── Convergence-safe fitting ──────────────────────────────────────────────

GLMER_FIT_BLOCK = """
fit_glmer <- function(formula, data, label="model") {
    # Try default optimizer first
    m <- tryCatch(
        glmer(formula, data=data, family=binomial),
        warning = function(w) {
            if (grepl("converge|singular", w$message, ignore.case=TRUE)) {
                cat(sprintf("  [%s] Default optimizer warning: %s\\n", label, w$message))
                cat(sprintf("  [%s] Retrying with bobyqa...\\n", label))
                suppressWarnings(
                    glmer(formula, data=data, family=binomial,
                          control=glmerControl(optimizer="bobyqa", optCtrl=list(maxfun=1e5)))
                )
            } else {
                warning(w)
                glmer(formula, data=data, family=binomial)
            }
        },
        error = function(e) {
            cat(sprintf("  [%s] Error: %s\\n", label, e$message))
            NULL
        }
    )
    m
}
"""


# ── Models ────────────────────────────────────────────────────────────────


def run_model_1(df: pd.DataFrame, output_lines: list) -> str | None:
    """Model 1: Warden Effectiveness — requester_type × has_warden."""
    data = df.copy()

    n_obs = len(data)
    n_adv = (data["requester_type"] == "adversary").sum()
    n_ben = (data["requester_type"] == "benign_agent").sum()
    n_scenarios = data["scenario"].nunique()
    n_profiles = data["profile_name"].nunique()
    n_tgt_models = data["target_model"].nunique()
    n_req_models = data["requester_model"].nunique()
    sr_overall = data["success"].mean()

    csv_path = "/tmp/lme_warden_m1.csv"
    data.to_csv(csv_path, index=False)

    r_script = f"""
library(lme4)
library(car)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d$requester_type <- relevel(factor(d$requester_type), ref="benign_agent")
d$has_warden <- factor(d$has_warden)
d$scenario <- factor(d$scenario)
d$profile_name <- factor(d$profile_name)
d$target_model <- factor(d$target_model)
d$requester_model <- factor(d$requester_model)

cat("\\n--- Data Summary ---\\n")
cat(sprintf("Observations: %d\\n", nrow(d)))
cat(sprintf("Success rate: %.1f%%\\n", mean(d$success) * 100))
cat("\\nSuccess by condition:\\n")
print(with(d, tapply(success, list(requester_type, has_warden), mean)))
cat("\\nCell counts:\\n")
print(with(d, table(requester_type, has_warden)))

cat("\\n--- Fitting Model 1: Warden Effectiveness ---\\n")
m1 <- fit_glmer(
    success ~ requester_type * has_warden
        + (1 + has_warden|scenario) + (1|profile_name) + (1|target_model) + (1|requester_model),
    data=d, label="Model 1"
)

if (!is.null(m1)) {{
    cat("\\n--- Fixed Effects ---\\n")
    print(summary(m1))

    cat("\\n--- Type III Wald Chi-Square Tests ---\\n")
    print(Anova(m1, type="III"))

    cat("\\n--- Random Effects ---\\n")
    print(VarCorr(m1))

    cat("\\n--- Odds Ratios (exp of fixed effects) ---\\n")
    fe <- fixef(m1)
    ci <- confint(m1, parm="beta_", method="Wald")
    or_table <- data.frame(
        OR = exp(fe),
        CI_lower = exp(ci[,1]),
        CI_upper = exp(ci[,2])
    )
    print(or_table)
}}
"""

    output = run_r_glmer(
        csv_path, r_script,
        "MODEL 1: Warden Effectiveness (requester_type x has_warden)"
    )

    output_lines.append("## Model 1: Warden Effectiveness\n")
    output_lines.append(
        "**Formula**: `success ~ requester_type * has_warden "
        "+ (1 + has_warden|scenario) + (1|profile_name) + (1|target_model) + (1|requester_model)`\n"
    )
    output_lines.append(f"**Family**: Binomial (logit link)\n")
    output_lines.append(
        f"**N** = {n_obs:,} ({n_adv:,} adversary, {n_ben:,} benign) | "
        f"{n_scenarios} scenarios | {n_profiles} profiles | {n_tgt_models} target models | "
        f"{n_req_models} requester models\n"
    )
    output_lines.append(
        f"**Overall success rate**: {sr_overall:.1%}\n"
    )
    output_lines.append(
        "**Reference levels**: requester_type=benign_agent, has_warden=0\n"
    )
    output_lines.append("### Output\n")
    output_lines.append("```")
    output_lines.append(output)
    output_lines.append("```\n")

    return output


def run_model_2(df: pd.DataFrame, output_lines: list) -> str | None:
    """Model 2: Dossier Impact — adversary_has_data × has_warden.

    Subset: adversary runs with profiled targets only.
    """
    data = df[
        (df["requester_type"] == "adversary") & (df["has_profile"] == 1)
    ].copy()

    if len(data) < 20:
        msg = f"Model 2 skipped: only {len(data)} adversary+profiled observations."
        print(f"\n  {msg}")
        output_lines.append(f"## Model 2: Dossier Impact\n\n*{msg}*\n")
        return None

    n_obs = len(data)
    n_with_data = (data["adversary_has_data"] == 1).sum()
    n_without = (data["adversary_has_data"] == 0).sum()
    n_scenarios = data["scenario"].nunique()
    n_profiles = data["profile_name"].nunique()

    csv_path = "/tmp/lme_dossier_m2.csv"
    data.to_csv(csv_path, index=False)

    r_script = f"""
library(lme4)
library(car)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d$adversary_has_data <- factor(d$adversary_has_data)
d$has_warden <- factor(d$has_warden)
d$scenario <- factor(d$scenario)
d$profile_name <- factor(d$profile_name)
d$target_model <- factor(d$target_model)

cat("\\n--- Data Summary ---\\n")
cat(sprintf("Observations: %d\\n", nrow(d)))
cat(sprintf("With dossier: %d, Without: %d\\n",
    sum(d$adversary_has_data == "1"), sum(d$adversary_has_data == "0")))
cat("\\nSuccess by condition:\\n")
print(with(d, tapply(success, list(adversary_has_data, has_warden), mean)))
cat("\\nCell counts:\\n")
print(with(d, table(adversary_has_data, has_warden)))

cat("\\n--- Fitting Model 2: Dossier Impact ---\\n")
m2 <- fit_glmer(
    success ~ adversary_has_data * has_warden
        + (1 + has_warden|scenario) + (1|profile_name) + (1|target_model),
    data=d, label="Model 2"
)

if (!is.null(m2)) {{
    cat("\\n--- Fixed Effects ---\\n")
    print(summary(m2))

    cat("\\n--- Type III Wald Chi-Square Tests ---\\n")
    print(Anova(m2, type="III"))

    cat("\\n--- Random Effects ---\\n")
    print(VarCorr(m2))

    cat("\\n--- Odds Ratios ---\\n")
    fe <- fixef(m2)
    ci <- confint(m2, parm="beta_", method="Wald")
    or_table <- data.frame(
        OR = exp(fe),
        CI_lower = exp(ci[,1]),
        CI_upper = exp(ci[,2])
    )
    print(or_table)
}}
"""

    output = run_r_glmer(
        csv_path, r_script,
        "MODEL 2: Dossier Impact (adversary_has_data x has_warden)"
    )

    output_lines.append("## Model 2: Dossier Impact\n")
    output_lines.append(
        "**Formula**: `success ~ adversary_has_data * has_warden "
        "+ (1 + has_warden|scenario) + (1|profile_name) + (1|target_model)`\n"
    )
    output_lines.append(f"**Family**: Binomial (logit link)\n")
    output_lines.append(
        f"**Data**: Adversary runs with profiled targets only\n"
    )
    output_lines.append(
        f"**N** = {n_obs:,} ({n_with_data:,} with dossier, "
        f"{n_without:,} without) | {n_scenarios} scenarios | "
        f"{n_profiles} profiles\n"
    )
    output_lines.append(
        "**Reference levels**: adversary_has_data=0, has_warden=0\n"
    )
    output_lines.append("### Output\n")
    output_lines.append("```")
    output_lines.append(output)
    output_lines.append("```\n")

    return output


def run_model_3(df: pd.DataFrame, output_lines: list) -> str | None:
    """Model 3: Profile Vulnerability — profile_name × has_warden.

    Subset: adversary runs with profiled targets only.
    """
    data = df[
        (df["requester_type"] == "adversary") & (df["has_profile"] == 1)
    ].copy()

    if len(data) < 20:
        msg = f"Model 3 skipped: only {len(data)} adversary+profiled observations."
        print(f"\n  {msg}")
        output_lines.append(f"## Model 3: Profile Vulnerability\n\n*{msg}*\n")
        return None

    n_obs = len(data)
    n_scenarios = data["scenario"].nunique()
    n_profiles = data["profile_name"].nunique()
    profile_counts = data["profile_name"].value_counts()

    csv_path = "/tmp/lme_profile_m3.csv"
    data.to_csv(csv_path, index=False)

    r_script = f"""
library(lme4)
library(car)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d$has_warden <- factor(d$has_warden)
d$scenario <- factor(d$scenario)
d$target_model <- factor(d$target_model)

# Set reference to most common profile for stability
profile_tab <- sort(table(d$profile_name), decreasing=TRUE)
ref_profile <- names(profile_tab)[1]
d$profile_name <- relevel(factor(d$profile_name), ref=ref_profile)

cat("\\n--- Data Summary ---\\n")
cat(sprintf("Observations: %d\\n", nrow(d)))
cat(sprintf("Profiles: %d, Scenarios: %d\\n",
    length(unique(d$profile_name)), length(unique(d$scenario))))
cat(sprintf("Reference profile: %s\\n", ref_profile))

cat("\\nSuccess rate by profile:\\n")
sr_profile <- tapply(d$success, d$profile_name, mean)
sr_n <- tapply(d$success, d$profile_name, length)
for (p in names(sort(sr_profile, decreasing=TRUE))) {{
    cat(sprintf("  %-35s  %.1f%%  (n=%d)\\n", p, sr_profile[p]*100, sr_n[p]))
}}

cat("\\nSuccess by profile x warden:\\n")
print(with(d, tapply(success, list(profile_name, has_warden), mean)))

cat("\\n--- Fitting Model 3: Profile Vulnerability ---\\n")
m3 <- fit_glmer(
    success ~ profile_name * has_warden
        + (1 + has_warden|scenario) + (1|target_model),
    data=d, label="Model 3"
)

if (!is.null(m3)) {{
    cat("\\n--- Fixed Effects ---\\n")
    print(summary(m3))

    cat("\\n--- Type III Wald Chi-Square Tests ---\\n")
    print(Anova(m3, type="III"))

    cat("\\n--- Random Effects ---\\n")
    print(VarCorr(m3))

    cat("\\n--- Odds Ratios ---\\n")
    fe <- fixef(m3)
    ci <- tryCatch(
        confint(m3, parm="beta_", method="Wald"),
        error = function(e) {{
            cat("  CI computation failed:", e$message, "\\n")
            NULL
        }}
    )
    if (!is.null(ci)) {{
        or_table <- data.frame(
            OR = exp(fe),
            CI_lower = exp(ci[,1]),
            CI_upper = exp(ci[,2])
        )
        print(or_table)
    }} else {{
        cat("Odds ratios (no CI):\\n")
        print(data.frame(OR = exp(fe)))
    }}
}}
"""

    output = run_r_glmer(
        csv_path, r_script,
        "MODEL 3: Profile Vulnerability (profile_name x has_warden)"
    )

    output_lines.append("## Model 3: Profile Vulnerability\n")
    output_lines.append(
        "**Formula**: `success ~ profile_name * has_warden "
        "+ (1 + has_warden|scenario) + (1|target_model)`\n"
    )
    output_lines.append(f"**Family**: Binomial (logit link)\n")
    output_lines.append(
        f"**Data**: Adversary runs with profiled targets only\n"
    )
    output_lines.append(
        f"**N** = {n_obs:,} | {n_scenarios} scenarios | "
        f"{n_profiles} profiles\n"
    )
    output_lines.append("**Profile counts**:\n")
    for name, count in profile_counts.items():
        output_lines.append(f"- {name}: {count}")
    output_lines.append("")
    output_lines.append("### Output\n")
    output_lines.append("```")
    output_lines.append(output)
    output_lines.append("```\n")

    return output


def run_model_4(df: pd.DataFrame, output_lines: list) -> str | None:
    """Model 4: Capability Asymmetry — warden_tier effect on adversary success.

    Tests whether stronger warden models (relative to adversary) reduce
    adversary success rate. Warden tier is an ordered factor:
    none < weak (= target) < mid < strong (= adversary).

    Random effects: model_family, scenario, profile_name.
    """
    data = df[df["requester_type"] == "adversary"].copy()

    if len(data) < 20:
        msg = f"Model 4 skipped: only {len(data)} adversary observations."
        print(f"\n  {msg}")
        output_lines.append(f"## Model 4: Capability Asymmetry\n\n*{msg}*\n")
        return None

    n_obs = len(data)
    n_families = data["model_family"].nunique()
    n_scenarios = data["scenario"].nunique()
    n_profiles = data["profile_name"].nunique()
    tier_counts = data["warden_tier"].value_counts()

    csv_path = "/tmp/lme_cap_asym_m4.csv"
    data.to_csv(csv_path, index=False)

    r_script = f"""
library(lme4)
library(car)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d$warden_tier <- factor(d$warden_tier, levels=c("none", "weak", "mid", "strong"), ordered=FALSE)
d$warden_tier <- relevel(d$warden_tier, ref="none")
d$model_family <- factor(d$model_family)
d$scenario <- factor(d$scenario)
d$profile_name <- factor(d$profile_name)

cat("\\n--- Data Summary ---\\n")
cat(sprintf("Observations: %d\\n", nrow(d)))
cat(sprintf("Model families: %d\\n", length(unique(d$model_family))))
cat(sprintf("Scenarios: %d, Profiles: %d\\n",
    length(unique(d$scenario)), length(unique(d$profile_name))))
cat(sprintf("Overall success rate: %.1f%%\\n", mean(d$success) * 100))

cat("\\nRuns by warden tier:\\n")
print(table(d$warden_tier))

cat("\\nSuccess rate by warden tier:\\n")
sr <- tapply(d$success, d$warden_tier, mean)
n_tier <- tapply(d$success, d$warden_tier, length)
for (t in c("none", "weak", "mid", "strong")) {{
    if (!is.na(sr[t])) {{
        cat(sprintf("  %-10s  %.1f%%  (n=%d)\\n", t, sr[t]*100, n_tier[t]))
    }}
}}

cat("\\nSuccess rate by model_family x warden_tier:\\n")
print(with(d, tapply(success, list(model_family, warden_tier), function(x) sprintf("%.0f%% (n=%d)", mean(x)*100, length(x)))))

cat("\\n--- Fitting Model 4: Capability Asymmetry ---\\n")
m4 <- fit_glmer(
    success ~ warden_tier + (1|model_family) + (1 + warden_tier|scenario) + (1|profile_name),
    data=d, label="Model 4"
)

if (!is.null(m4)) {{
    cat("\\n--- Fixed Effects ---\\n")
    print(summary(m4))

    cat("\\n--- Type III Wald Chi-Square Tests ---\\n")
    print(Anova(m4, type="III"))

    cat("\\n--- Random Effects ---\\n")
    print(VarCorr(m4))

    cat("\\n--- Odds Ratios (exp of fixed effects) ---\\n")
    fe <- fixef(m4)
    ci <- tryCatch(
        confint(m4, parm="beta_", method="Wald"),
        error = function(e) {{
            cat("  CI computation failed:", e$message, "\\n")
            NULL
        }}
    )
    if (!is.null(ci)) {{
        or_table <- data.frame(
            OR = exp(fe),
            CI_lower = exp(ci[,1]),
            CI_upper = exp(ci[,2])
        )
        print(or_table)
    }} else {{
        cat("Odds ratios (no CI):\\n")
        print(data.frame(OR = exp(fe)))
    }}
}}
"""

    output = run_r_glmer(
        csv_path, r_script,
        "MODEL 4: Capability Asymmetry (warden_tier)"
    )

    output_lines.append("## Model 4: Capability Asymmetry\n")
    output_lines.append(
        "**Formula**: `success ~ warden_tier "
        "+ (1|model_family) + (1 + warden_tier|scenario) + (1|profile_name)`\n"
    )
    output_lines.append("**Family**: Binomial (logit link)\n")
    output_lines.append(
        "**Data**: Adversary runs only (cap_asym study)\n"
    )
    output_lines.append(
        f"**N** = {n_obs:,} | {n_families} model families | "
        f"{n_scenarios} scenarios | {n_profiles} profiles\n"
    )
    output_lines.append(
        "**Reference level**: warden_tier=none\n"
    )
    output_lines.append("**Warden tier counts**:\n")
    for tier in ["none", "weak", "mid", "strong"]:
        count = tier_counts.get(tier, 0)
        output_lines.append(f"- {tier}: {count}")
    output_lines.append("")
    output_lines.append("### Output\n")
    output_lines.append("```")
    output_lines.append(output)
    output_lines.append("```\n")

    return output


def run_model_5(df: pd.DataFrame, output_lines: list) -> str | None:
    """Model 5: Detection × Resistance × Warden interaction.

    Tests the CB5T-derived capacity model: whether detection_capacity and
    resistance_capacity interact with warden presence to predict success.
    Subset: adversary runs with profiled targets that have CB5T data.
    """
    data = df[
        (df["requester_type"] == "adversary")
        & (df["has_profile"] == 1)
        & (df["detection_capacity"] != "unknown")
    ].copy()

    if len(data) < 20:
        msg = f"Model 5 skipped: only {len(data)} adversary+CB5T observations."
        print(f"\n  {msg}")
        output_lines.append(f"## Model 5: Detection × Resistance × Warden\n\n*{msg}*\n")
        return None

    n_obs = len(data)
    n_scenarios = data["scenario"].nunique()

    csv_path = "/tmp/lme_cb5t_m5.csv"
    data.to_csv(csv_path, index=False)

    r_script = f"""
library(lme4)
library(car)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d$detection_capacity <- factor(d$detection_capacity, levels=c("LOW", "MODERATE", "HIGH"))
d$resistance_capacity <- factor(d$resistance_capacity, levels=c("LOW", "MODERATE", "HIGH"))
d$has_warden <- factor(d$has_warden)
d$scenario <- factor(d$scenario)
d$target_model <- factor(d$target_model)

cat("\\n--- Data Summary ---\\n")
cat(sprintf("Observations: %d\\n", nrow(d)))
cat("\\nDetection × Resistance counts:\\n")
print(table(d$detection_capacity, d$resistance_capacity))
cat("\\nSuccess by detection × resistance × warden:\\n")
print(with(d, tapply(success, list(detection_capacity, resistance_capacity, has_warden), mean)))

cat("\\n--- Fitting Model 5: Detection x Resistance x Warden ---\\n")
m5 <- fit_glmer(
    success ~ detection_capacity * resistance_capacity * has_warden
        + (1|scenario) + (1|target_model),
    data=d, label="Model 5"
)

if (!is.null(m5)) {{
    cat("\\n--- Fixed Effects ---\\n")
    print(summary(m5))

    cat("\\n--- Type III Wald Chi-Square Tests ---\\n")
    print(Anova(m5, type="III"))

    cat("\\n--- Random Effects ---\\n")
    print(VarCorr(m5))

    cat("\\n--- Odds Ratios ---\\n")
    fe <- fixef(m5)
    ci <- tryCatch(
        confint(m5, parm="beta_", method="Wald"),
        error = function(e) {{
            cat("  CI computation failed:", e$message, "\\n")
            NULL
        }}
    )
    if (!is.null(ci)) {{
        or_table <- data.frame(
            OR = exp(fe),
            CI_lower = exp(ci[,1]),
            CI_upper = exp(ci[,2])
        )
        print(or_table)
    }} else {{
        cat("Odds ratios (no CI):\\n")
        print(data.frame(OR = exp(fe)))
    }}
}}
"""

    output = run_r_glmer(
        csv_path, r_script,
        "MODEL 5: Detection × Resistance × Warden"
    )

    output_lines.append("## Model 5: Detection × Resistance × Warden\n")
    output_lines.append(
        "**Formula**: `success ~ detection_capacity * resistance_capacity * has_warden "
        "+ (1|scenario) + (1|target_model)`\n"
    )
    output_lines.append("**Family**: Binomial (logit link)\n")
    output_lines.append(
        "**Data**: Adversary runs with CB5T-profiled targets\n"
    )
    output_lines.append(f"**N** = {n_obs:,} | {n_scenarios} scenarios\n")
    output_lines.append(
        "**Reference levels**: detection=LOW, resistance=LOW, has_warden=0\n"
    )
    output_lines.append("### Output\n")
    output_lines.append("```")
    output_lines.append(output)
    output_lines.append("```\n")

    return output


def run_model_6(df: pd.DataFrame, output_lines: list) -> str | None:
    """Model 6: Profile Family × Warden.

    Tests whether warden effectiveness varies by profile family as predicted
    by CB5T theory. The warden should help most for 'sitting_duck' and
    'sees_cant_act' families and least for 'fortress'.
    Subset: adversary runs with profiled targets that have CB5T data.
    """
    data = df[
        (df["requester_type"] == "adversary")
        & (df["has_profile"] == 1)
        & (df["profile_family"] != "unknown")
    ].copy()

    if len(data) < 20:
        msg = f"Model 6 skipped: only {len(data)} adversary+family observations."
        print(f"\n  {msg}")
        output_lines.append(f"## Model 6: Profile Family × Warden\n\n*{msg}*\n")
        return None

    n_obs = len(data)
    n_scenarios = data["scenario"].nunique()
    n_families = data["profile_family"].nunique()
    family_counts = data["profile_family"].value_counts()

    csv_path = "/tmp/lme_family_m6.csv"
    data.to_csv(csv_path, index=False)

    r_script = f"""
library(lme4)
library(car)

{GLMER_FIT_BLOCK}

d <- read.csv("{csv_path}")
d$profile_family <- relevel(factor(d$profile_family), ref="sitting_duck")
d$has_warden <- factor(d$has_warden)
d$scenario <- factor(d$scenario)
d$target_model <- factor(d$target_model)

cat("\\n--- Data Summary ---\\n")
cat(sprintf("Observations: %d\\n", nrow(d)))
cat("\\nProfile family counts:\\n")
print(table(d$profile_family))

cat("\\nSuccess rate by family:\\n")
sr_fam <- tapply(d$success, d$profile_family, mean)
n_fam <- tapply(d$success, d$profile_family, length)
for (f in names(sort(sr_fam, decreasing=TRUE))) {{
    cat(sprintf("  %-30s  %.1f%%  (n=%d)\\n", f, sr_fam[f]*100, n_fam[f]))
}}

cat("\\nSuccess by family x warden:\\n")
print(with(d, tapply(success, list(profile_family, has_warden), mean)))

cat("\\n--- Fitting Model 6: Profile Family x Warden ---\\n")
m6 <- fit_glmer(
    success ~ profile_family * has_warden
        + (1|scenario) + (1|target_model),
    data=d, label="Model 6"
)

if (!is.null(m6)) {{
    cat("\\n--- Fixed Effects ---\\n")
    print(summary(m6))

    cat("\\n--- Type III Wald Chi-Square Tests ---\\n")
    print(Anova(m6, type="III"))

    cat("\\n--- Random Effects ---\\n")
    print(VarCorr(m6))

    cat("\\n--- Odds Ratios ---\\n")
    fe <- fixef(m6)
    ci <- tryCatch(
        confint(m6, parm="beta_", method="Wald"),
        error = function(e) {{
            cat("  CI computation failed:", e$message, "\\n")
            NULL
        }}
    )
    if (!is.null(ci)) {{
        or_table <- data.frame(
            OR = exp(fe),
            CI_lower = exp(ci[,1]),
            CI_upper = exp(ci[,2])
        )
        print(or_table)
    }} else {{
        cat("Odds ratios (no CI):\\n")
        print(data.frame(OR = exp(fe)))
    }}
}}
"""

    output = run_r_glmer(
        csv_path, r_script,
        "MODEL 6: Profile Family × Warden"
    )

    output_lines.append("## Model 6: Profile Family × Warden\n")
    output_lines.append(
        "**Formula**: `success ~ profile_family * has_warden "
        "+ (1|scenario) + (1|target_model)`\n"
    )
    output_lines.append("**Family**: Binomial (logit link)\n")
    output_lines.append(
        "**Data**: Adversary runs with CB5T-profiled targets\n"
    )
    output_lines.append(
        f"**N** = {n_obs:,} | {n_scenarios} scenarios | "
        f"{n_families} profile families\n"
    )
    output_lines.append(
        "**Reference level**: profile_family=sitting_duck, has_warden=0\n"
    )
    output_lines.append("**Family counts**:\n")
    for fam, count in family_counts.items():
        output_lines.append(f"- {fam}: {count}")
    output_lines.append("")
    output_lines.append("### Output\n")
    output_lines.append("```")
    output_lines.append(output)
    output_lines.append("```\n")

    return output


# ── CLI ───────────────────────────────────────────────────────────────────


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run mixed-effects models on experiment logs."
    )
    parser.add_argument(
        "--tag",
        type=str,
        nargs="+",
        action="append",
        default=None,
        help=(
            "Filter logs by tag (repeatable; space/comma-separated, e.g. "
            "--tag foo bar or --tag foo,bar --tag baz)."
        ),
    )
    parser.add_argument(
        "--scenario", type=str, default=None,
        help="Filter logs by scenario name.",
    )
    parser.add_argument(
        "--requester-model", type=str, default=None,
        help="Filter by requester model.",
    )
    parser.add_argument(
        "--target-model", type=str, default=None,
        help="Filter by target model.",
    )
    parser.add_argument(
        "--models", type=int, nargs="+", default=[1, 2, 3],
        choices=[1, 2, 3, 4, 5, 6],
        help="Which models to run (default: 1 2 3). 4=capability asymmetry, 5=detection×resistance×warden, 6=profile_family×warden.",
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output markdown path (default: results/lme_results.md).",
    )
    return parser.parse_args()


# ── Main ──────────────────────────────────────────────────────────────────


def parse_tag_filter(tag_args: list[list[str]] | None) -> list[str] | None:
    """Normalize tag CLI args into a flat list, supporting comma-separated entries."""
    if not tag_args:
        return None

    tags: list[str] = []
    for group in tag_args:
        for entry in group:
            for candidate in entry.split(","):
                value = candidate.strip()
                if value:
                    tags.append(value)
    return tags or None


def main():
    args = parse_args()

    print("=" * 70)
    print("  Mixed-Effects Models for Social Reasoning Warden")
    print("=" * 70)

    # Parse tag filter
    tag_filter = parse_tag_filter(args.tag)

    print("\nLoading experiment logs...")
    logs = load_logs(
        scenario=args.scenario,
        tag=tag_filter,
        requester_model=args.requester_model,
        target_model=args.target_model,
    )
    print(f"  Loaded {len(logs)} logs")

    if not logs:
        print("No logs found. Check filters.")
        sys.exit(1)

    print("Building analysis dataframe...")
    df = logs_to_dataframe(logs)
    print(f"  Valid observations: {len(df)} (after excluding formatting failures)")

    if len(df) == 0:
        print("No valid observations. All logs may have formatting failures.")
        sys.exit(1)

    # Summary stats
    n_adversary = (df["requester_type"] == "adversary").sum()
    n_benign = (df["requester_type"] == "benign_agent").sum()
    n_warden = (df["has_warden"] == 1).sum()
    n_profiled = (df["has_profile"] == 1).sum()
    n_dossier = (df["adversary_has_data"] == 1).sum()
    n_scenarios = df["scenario"].nunique()

    print(f"  Adversary: {n_adversary}, Benign: {n_benign}")
    print(f"  With warden: {n_warden}, Profiled: {n_profiled}, Dossier: {n_dossier}")
    print(f"  Scenarios: {n_scenarios}")
    print(f"  Overall success rate: {df['success'].mean():.1%}")

    # Build results markdown
    output_lines = [
        "# Mixed-Effects Model Results\n",
        "**Social Reasoning Warden — ERA Project**\n",
        f"**Generated**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}\n",
    ]

    # Filters applied
    filters = []
    if tag_filter:
        filters.append(f"tag={','.join(tag_filter)}")
    if args.scenario:
        filters.append(f"scenario={args.scenario}")
    if args.requester_model:
        filters.append(f"requester_model={args.requester_model}")
    if args.target_model:
        filters.append(f"target_model={args.target_model}")
    if filters:
        output_lines.append(f"**Filters**: {', '.join(filters)}\n")

    output_lines.append(
        f"**Data**: {len(df):,} observations | "
        f"{n_adversary:,} adversary, {n_benign:,} benign | "
        f"{n_scenarios} scenarios | "
        f"overall SR = {df['success'].mean():.1%}\n"
    )
    output_lines.append(
        "**Software**: R lme4 (glmer, binomial) + lmerTest | "
        "Wald chi-square tests | Satterthwaite df\n"
    )
    output_lines.append("---\n")

    # Run selected models
    if 1 in args.models:
        run_model_1(df, output_lines)
        output_lines.append("\n---\n")

    if 2 in args.models:
        run_model_2(df, output_lines)
        output_lines.append("\n---\n")

    if 3 in args.models:
        run_model_3(df, output_lines)
        output_lines.append("\n---\n")

    if 4 in args.models:
        run_model_4(df, output_lines)
        output_lines.append("\n---\n")

    if 5 in args.models:
        run_model_5(df, output_lines)
        output_lines.append("\n---\n")

    if 6 in args.models:
        run_model_6(df, output_lines)

    # Write results
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output) if args.output else RESULTS_DIR / "lme_results.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        f.write("\n".join(output_lines))

    print(f"\n{'=' * 70}")
    print(f"  Results written to {output_path}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
