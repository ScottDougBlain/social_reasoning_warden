#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# Batch run: skeptical target ablation study
#
# Tests whether baked-in skepticism instructions (prompt-based defense)
# can match the effect of an external warden agent. Also checks whether
# skepticism hurts benign agent success (false positives).
#
# 3 defense conditions × 2 requester types:
#   1. Baseline:  no warden, no skepticism   (adversary + benign)
#   2. Skeptical: no warden, skepticism ON   (adversary + benign)
#   3. Warden:    warden ON, no skepticism   (adversary + benign)
#
# 4 model families × 4 profiles × 11 scenarios × 3 reps
#
# Tag: skeptical_ablation
#
# Usage:
#   bash scripts/run_skeptical_ablation.sh          # run all
#   bash scripts/run_skeptical_ablation.sh --dry-run # preview commands only
# ──────────────────────────────────────────────────────────────────────────
set -euo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "=== DRY RUN — commands will be printed but not executed ==="
    echo
fi

PROFILES=(
    authority_deferential
    compliant
    idealistic
    time_pressured
)

# Same 11 scenarios used in cap_asym / dossier_effect studies
SCENARIOS="ai_containment ai_override automation_decision product_launch coding_agent file_access file_access_password hiring model_release upselling vote"

# Model families: adversary=high, target=low, warden=mid
# (matching cap_asym tier definitions)
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

NUM_FAMILIES=${#ADV_MODELS[@]}
# Per family: 4 profiles × 3 conditions × 2 requester types × 11 scenarios × 3 rounds = 792
# Total: 792 × 4 families = 3,168 runs (48 batch commands)
echo "=== Skeptical Target Ablation Study ==="
echo "Profiles: ${PROFILES[*]}"
echo "Scenarios: ${SCENARIOS}"
echo "Rounds per condition: ${ROUNDS}"
echo "Model families: ${NUM_FAMILIES}"
echo "Tag: ${TAG}"
echo
echo "Conditions:"
echo "  1. Baseline  — no warden, no skepticism"
echo "  2. Skeptical — no warden, skepticism ON"
echo "  3. Warden    — warden ON, no skepticism"
echo

for i in $(seq 0 $((NUM_FAMILIES - 1))); do
    ADV="${ADV_MODELS[$i]}"
    TGT="${TGT_MODELS[$i]}"
    WARD="${WARD_MODELS[$i]}"
    echo "--- Family $((i+1)): adv=${ADV} tgt=${TGT} ward=${WARD} ---"

    for profile in "${PROFILES[@]}"; do
        # Condition 1: Baseline (no warden, no skepticism)
        run_or_print python main.py \
            --scenario ${SCENARIOS} \
            --profile "${profile}" \
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
            --profile "${profile}" \
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
            --profile "${profile}" \
            --warden with_warden \
            --target-skeptical off \
            --requester-type both \
            --requester-model "${ADV}" \
            --target-model "${TGT}" \
            --warden-model "${WARD}" \
            --experiment-rounds "${ROUNDS}" \
            --tag "${TAG}" \
            -y
    done
done

if ! $DRY_RUN; then
    echo
    echo "Waiting for remaining jobs to finish..."
    wait
    echo
    echo "=== All done! ${count} batch jobs completed ==="
    echo "Analyze: python analysis/run_lme.py --tag ${TAG}"
fi
