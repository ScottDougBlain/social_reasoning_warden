#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# Batch run: dossier effectiveness study
#
# Tests whether adversary access to behavioral dossiers improves attack
# success rate. Factorial design:
#
#   4 model families × 4 profiles × 11 scenarios × 2 dossier × 2 warden × 3 reps
#   = 2,112 runs total (528 per model family)
#
# Fixed capability tier: adversary=high, target=low, warden=mid
# (same model families as cap_asym study, but tier held constant)
#
# Tag: dossier_effect (for filtering in analysis)
#
# Usage:
#   bash scripts/run_dossier_effect.sh          # run all
#   bash scripts/run_dossier_effect.sh --dry-run # preview commands only
# ──────────────────────────────────────────────────────────────────────────
set -euo pipefail

DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "=== DRY RUN — commands will be printed but not executed ==="
    echo
fi

# Same 4 profiles used in cap_asym
PROFILES=(
    authority_deferential
    compliant
    idealistic
    time_pressured
)
declare -A PROFILE_SEEDS=(
    [authority_deferential]=101
    [compliant]=202
    [idealistic]=303
    [time_pressured]=404
)

# Same 11 scenarios used in cap_asym
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

TAG="dossier_effect"
ROUNDS=3
MAX_PARALLEL=4  # one per model family

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
RUNS_PER_FAMILY=$(( ${#PROFILES[@]} * 11 * 2 * 2 * ROUNDS ))  # profiles × scenarios × dossier × warden × rounds
TOTAL_RUNS=$(( RUNS_PER_FAMILY * NUM_FAMILIES ))

echo "=== Dossier Effect Study ==="
echo "Profiles: ${PROFILES[*]}"
echo "Scenarios: ${SCENARIOS}"
echo "Rounds per condition: ${ROUNDS}"
echo "Model families: ${NUM_FAMILIES}"
echo "Runs per family: ${RUNS_PER_FAMILY}"
echo "Total runs: ${TOTAL_RUNS}"
echo "Tag: ${TAG}"
echo

for i in $(seq 0 $((NUM_FAMILIES - 1))); do
    ADV="${ADV_MODELS[$i]}"
    TGT="${TGT_MODELS[$i]}"
    WARD="${WARD_MODELS[$i]}"
    echo "--- Family $((i+1)): adv=${ADV} tgt=${TGT} ward=${WARD} ---"

    for profile in "${PROFILES[@]}"; do
        profile_seed="${PROFILE_SEEDS[$profile]}"
        run_or_print python main.py \
            --scenario ${SCENARIOS} \
            --target-profiles yes \
            --adversary-profile-access both \
            --profile-seed "${profile_seed}" \
            --warden both \
            --warden-model "${WARD}" \
            --requester-type adversary \
            --requester-model "${ADV}" \
            --target-model "${TGT}" \
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
    echo "Analyze: python analysis/run_lme.py --tag ${TAG} --models 2"
fi
