#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# Quick study: hiring scenario with/without warden across 4 model families
#
# Purpose: answer Lennart's question about warden behavior in hiring, and
# which adversary model is most effective at swaying the hiring decision.
#
# 4 model families × 4 profiles × 2 warden conditions × 2 requester types × 3 reps
# = 4 × 4 × 2 × 2 × 3 = 192 runs (+ hiring is a single-target scenario, so fast)
#
# Tag: hiring_warden
#
# Usage:
#   bash scripts/run_hiring_warden.sh          # run all
#   bash scripts/run_hiring_warden.sh --dry-run # preview commands only
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

SCENARIO="hiring"

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

TAG="hiring_warden"
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

        if (( ${#pids[@]} >= MAX_PARALLEL )); then
            wait "${pids[0]}"
            pids=("${pids[@]:1}")
        fi
    fi
}

NUM_FAMILIES=${#ADV_MODELS[@]}
TOTAL=$((NUM_FAMILIES * ${#PROFILES[@]} * 2 * 2 * ROUNDS))
echo "=== Hiring Warden Study ==="
echo "Scenario: ${SCENARIO}"
echo "Profiles: ${PROFILES[*]}"
echo "Rounds: ${ROUNDS}"
echo "Model families: ${NUM_FAMILIES}"
echo "Estimated runs: ${TOTAL}"
echo "Tag: ${TAG}"
echo

for i in $(seq 0 $((NUM_FAMILIES - 1))); do
    ADV="${ADV_MODELS[$i]}"
    TGT="${TGT_MODELS[$i]}"
    WARD="${WARD_MODELS[$i]}"
    echo "--- Family $((i+1)): adv=${ADV} tgt=${TGT} ward=${WARD} ---"

    for profile in "${PROFILES[@]}"; do
        # Both warden conditions, both requester types
        run_or_print python main.py \
            --scenario ${SCENARIO} \
            --profile "${profile}" \
            --warden both \
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
    echo "Analyze: python analysis/metrics.py --tag ${TAG}"
fi
