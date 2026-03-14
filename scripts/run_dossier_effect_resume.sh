#!/usr/bin/env bash
# Resume dossier_effect study — picks up remaining families (gemma partial, llama, mistral)
# Also re-runs gemini/gemma gaps (small overlap is fine — extra reps)
set -uo pipefail  # no -e: don't abort on individual run failures

PROFILES=(authority_deferential compliant idealistic time_pressured)
declare -A PROFILE_SEEDS=(
    [authority_deferential]=101
    [compliant]=202
    [idealistic]=303
    [time_pressured]=404
)
SCENARIOS="ai_containment ai_override automation_decision product_launch coding_agent file_access file_access_password hiring model_release upselling vote"
TAG="dossier_effect"
ROUNDS=3
MAX_PARALLEL=4

# Families to run (gemma needs partial, llama+mistral need full)
declare -a ADV_MODELS=(
    "google/gemma-3-27b-it"
    "meta-llama/llama-4-maverick"
    "mistralai/mistral-large-2512"
)
declare -a TGT_MODELS=(
    "google/gemma-3-4b-it"
    "meta-llama/llama-3.1-70b-instruct"
    "mistralai/mistral-small-3.1-24b-instruct"
)
declare -a WARD_MODELS=(
    "google/gemma-3-12b-it"
    "meta-llama/llama-4-scout"
    "mistralai/mistral-medium-3.1"
)

count=0
pids=()

run_bg() {
    echo ">>> Starting: $*"
    "$@" &
    pids+=($!)
    count=$((count + 1))
    if (( ${#pids[@]} >= MAX_PARALLEL )); then
        wait "${pids[0]}"
        pids=("${pids[@]:1}")
    fi
}

NUM_FAMILIES=${#ADV_MODELS[@]}
echo "=== Dossier Effect Study (Resume) ==="
echo "Remaining families: ${NUM_FAMILIES} (gemma, llama, mistral)"
echo

for i in $(seq 0 $((NUM_FAMILIES - 1))); do
    ADV="${ADV_MODELS[$i]}"
    TGT="${TGT_MODELS[$i]}"
    WARD="${WARD_MODELS[$i]}"
    echo "--- Family: adv=${ADV} tgt=${TGT} ward=${WARD} ---"

    for profile in "${PROFILES[@]}"; do
        profile_seed="${PROFILE_SEEDS[$profile]}"
        run_bg python main.py \
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

echo
echo "Waiting for remaining jobs to finish..."
wait
echo
echo "=== All done! ${count} batch jobs completed ==="
echo "Analyze: python analysis/run_lme.py --tag ${TAG} --models 2"
