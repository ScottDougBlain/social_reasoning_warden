#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────
# Batch run: balance no-dossier profiled adversary conditions
#
# Current data gap: ~120 runs WITH dossier but only ~45 WITHOUT.
# This script adds ~120 no-dossier profiled runs across:
#   - 6 profiles × 5 scenarios × 2 warden conditions × 2 rounds = 120
#
# Uses the dominant model combo (Gemini) for consistency with existing data.
# Tag: dossier_balance (for filtering in analysis)
#
# Usage:
#   bash scripts/run_dossier_balance.sh          # run all
#   bash scripts/run_dossier_balance.sh --dry-run # preview commands only
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
    idealistic
    lonely_isolated
    overconfident
    compliant
    time_pressured
)
declare -A PROFILE_SEEDS=(
    [authority_deferential]=101
    [idealistic]=202
    [lonely_isolated]=303
    [overconfident]=404
    [compliant]=505
    [time_pressured]=606
)

# Scenarios already used for profiled adversary runs (good coverage)
SCENARIOS="ai_containment hiring vote automation_decision upselling"

REQUESTER_MODEL="google/gemini-3-flash-preview"
TARGET_MODEL="google/gemini-2.5-flash-lite"
WARDEN_MODEL="google/gemini-3-flash-preview"

TAG="dossier_balance"
ROUNDS=2
MAX_PARALLEL=3  # concurrent experiments (adjust based on API rate limits)

count=0
pids=()

run_or_print() {
    if $DRY_RUN; then
        echo "$@"
        echo
    else
        echo ">>> Starting: $@"
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

echo "=== Dossier Balance Batch Run ==="
echo "Profiles: ${PROFILES[*]}"
echo "Scenarios: ${SCENARIOS}"
echo "Rounds per condition: ${ROUNDS}"
echo "Models: adv=${REQUESTER_MODEL} tgt=${TARGET_MODEL} war=${WARDEN_MODEL}"
echo "Tag: ${TAG}"
echo

for profile in "${PROFILES[@]}"; do
    echo "--- Profile: ${profile} ---"
    profile_seed="${PROFILE_SEEDS[$profile]}"
    run_or_print python main.py \
        --scenario ${SCENARIOS} \
        --target-profiles yes \
        --adversary-profile-access no \
        --profile-seed "${profile_seed}" \
        --warden both \
        --warden-model "${WARDEN_MODEL}" \
        --requester-type adversary \
        --requester-model "${REQUESTER_MODEL}" \
        --target-model "${TARGET_MODEL}" \
        --experiment-rounds "${ROUNDS}" \
        --tag "${TAG}" \
        -y
done

if ! $DRY_RUN; then
    echo
    echo "Waiting for remaining jobs to finish..."
    wait
    echo
    echo "=== All done! ${count} batch jobs completed ==="
    echo "Filter results: python analysis/run_lme.py --tag ${TAG}"
fi
