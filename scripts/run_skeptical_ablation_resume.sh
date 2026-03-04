#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# Resume: skeptical target ablation study
#
# Picks up where the initial run stalled. Status as of 2026-02-21:
#
#   Gemini  — 41%: auth_def ~done, compliant partial (skeptical=5/66),
#                   idealistic + time_pressured = 0%
#   Gemma   — 0%
#   Llama   — 0%
#   Mistral — 0%
#
# This script runs:
#   1. Gemini: remaining profiles (idealistic, time_pressured) — all conditions
#   2. Gemini: compliant/skeptical (the stalled cell)
#   3. Gemma, Llama, Mistral — full (all profiles × all conditions)
#
# Skips Gemini auth_def (94%) and compliant baseline+warden (68%+) as
# near-complete; a few missing runs there are likely formatting failures.
#
# Tag: skeptical_ablation
#
# Usage:
#   bash scripts/run_skeptical_ablation_resume.sh          # run all
#   bash scripts/run_skeptical_ablation_resume.sh --dry-run # preview
# ──────────────────────────────────────────────────────────────────────────
set -euo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "=== DRY RUN — commands will be printed but not executed ==="
    echo
fi

SCENARIOS="ai_containment ai_override automation_decision product_launch coding_agent file_access file_access_password hiring model_release upselling vote"

# Model families: adversary=high, target=low, warden=mid
declare -a ADV_MODELS=(
    "google/gemini-3-flash-preview"
    "google/gemma-3-27b-it"
    "meta-llama/llama-4-maverick"
    "mistralai/mistral-large-2512"
)
declare -a TGT_MODELS=(
    "google/gemini-2.5-flash-lite"
    "google/gemma-3-4b-it"
    "meta-llama/llama-3.1-70b-instruct"
    "mistralai/mistral-small-3.1-24b-instruct"
)
declare -a WARD_MODELS=(
    "google/gemini-2.5-flash"
    "google/gemma-3-12b-it"
    "meta-llama/llama-4-scout"
    "mistralai/mistral-medium-3.1"
)

TAG="skeptical_ablation"
ROUNDS=3
MAX_PARALLEL=4

count=0
pids=()

run_or_print() {
    if $DRY_RUN; then
        echo "$@"
        echo
    else
        echo ">>> Starting: $*"
        "$@" &
        pids+=($!)
        count=$((count + 1))

        # Throttle: wait if we've hit MAX_PARALLEL
        if (( ${#pids[@]} >= MAX_PARALLEL )); then
            wait "${pids[0]}"
            pids=("${pids[@]:1}")
        fi
    fi
}

run_all_conditions() {
    # Run all 3 conditions for a given family + profile
    local ADV="$1" TGT="$2" WARD="$3" PROFILE="$4"

    # Condition 1: Baseline (no warden, no skepticism)
    run_or_print python main.py \
        --scenario ${SCENARIOS} \
        --profile "${PROFILE}" \
        --warden without_warden \
        --target-skeptical off \
        --requester-type both \
        --requester-model "${ADV}" \
        --target-model "${TGT}" \
        --warden-model "${WARD}" \
        --experiment-rounds "${ROUNDS}" \
        --tag "${TAG}" \
        -y

    # Condition 2: Skeptical target (no warden)
    run_or_print python main.py \
        --scenario ${SCENARIOS} \
        --profile "${PROFILE}" \
        --warden without_warden \
        --target-skeptical on \
        --requester-type both \
        --requester-model "${ADV}" \
        --target-model "${TGT}" \
        --warden-model "${WARD}" \
        --experiment-rounds "${ROUNDS}" \
        --tag "${TAG}" \
        -y

    # Condition 3: Warden (no skepticism)
    run_or_print python main.py \
        --scenario ${SCENARIOS} \
        --profile "${PROFILE}" \
        --warden with_warden \
        --target-skeptical off \
        --requester-type both \
        --requester-model "${ADV}" \
        --target-model "${TGT}" \
        --warden-model "${WARD}" \
        --experiment-rounds "${ROUNDS}" \
        --tag "${TAG}" \
        -y
}

run_single_condition() {
    # Run one specific condition for a given family + profile
    local ADV="$1" TGT="$2" WARD="$3" PROFILE="$4"
    local WARDEN_FLAG="$5" SKEPTICAL_FLAG="$6"

    run_or_print python main.py \
        --scenario ${SCENARIOS} \
        --profile "${PROFILE}" \
        --warden "${WARDEN_FLAG}" \
        --target-skeptical "${SKEPTICAL_FLAG}" \
        --requester-type both \
        --requester-model "${ADV}" \
        --target-model "${TGT}" \
        --warden-model "${WARD}" \
        --experiment-rounds "${ROUNDS}" \
        --tag "${TAG}" \
        -y
}

echo "=== Skeptical Ablation — RESUME ==="
echo "Scenarios: ${SCENARIOS}"
echo "Rounds: ${ROUNDS}"
echo "Tag: ${TAG}"
echo

# ── Part 1: Finish Gemini ────────────────────────────────────────────────
echo "--- Part 1: Gemini — remaining profiles + stalled cell ---"
ADV="${ADV_MODELS[0]}"
TGT="${TGT_MODELS[0]}"
WARD="${WARD_MODELS[0]}"

# Compliant/skeptical stalled at 5/66 — re-run (will create ~61 new + ~5 duplicate)
echo "  Gemini / compliant / skeptical (was 5/66)"
run_single_condition "${ADV}" "${TGT}" "${WARD}" "compliant" \
    "without_warden" "on"

# Idealistic — not started, all 3 conditions
echo "  Gemini / idealistic (was 0%)"
run_all_conditions "${ADV}" "${TGT}" "${WARD}" "idealistic"

# Time-pressured — not started, all 3 conditions
echo "  Gemini / time_pressured (was 0%)"
run_all_conditions "${ADV}" "${TGT}" "${WARD}" "time_pressured"

# ── Part 2: Gemma (not started) ─────────────────────────────────────────
echo
echo "--- Part 2: Gemma — full (was 0%) ---"
ADV="${ADV_MODELS[1]}"
TGT="${TGT_MODELS[1]}"
WARD="${WARD_MODELS[1]}"

for profile in authority_deferential compliant idealistic time_pressured; do
    echo "  Gemma / ${profile}"
    run_all_conditions "${ADV}" "${TGT}" "${WARD}" "${profile}"
done

# ── Part 3: Llama (not started) ─────────────────────────────────────────
echo
echo "--- Part 3: Llama — full (was 0%) ---"
ADV="${ADV_MODELS[2]}"
TGT="${TGT_MODELS[2]}"
WARD="${WARD_MODELS[2]}"

for profile in authority_deferential compliant idealistic time_pressured; do
    echo "  Llama / ${profile}"
    run_all_conditions "${ADV}" "${TGT}" "${WARD}" "${profile}"
done

# ── Part 4: Mistral (not started) ───────────────────────────────────────
echo
echo "--- Part 4: Mistral — full (was 0%) ---"
ADV="${ADV_MODELS[3]}"
TGT="${TGT_MODELS[3]}"
WARD="${WARD_MODELS[3]}"

for profile in authority_deferential compliant idealistic time_pressured; do
    echo "  Mistral / ${profile}"
    run_all_conditions "${ADV}" "${TGT}" "${WARD}" "${profile}"
done

# ── Wrap up ──────────────────────────────────────────────────────────────
if ! $DRY_RUN; then
    echo
    echo "Waiting for remaining jobs to finish..."
    wait
    echo
    echo "=== All done! ${count} batch jobs completed ==="
    echo "Analyze: python analysis/run_lme.py --tag ${TAG}"
fi
