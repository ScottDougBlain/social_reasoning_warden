#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"
cd "${REPO_ROOT}"

echo "Running warden message ablation: full advisory messages..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag warden-msg-ablation \
  --warden with_warden \
  --target-model \
    openai/gpt-4o-mini google/gemma-3-27b-it meta-llama/llama-3.1-8b-instruct \
  --requester-model \
    google/gemini-3-flash-preview \
  --warden-model \
    google/gemma-3-4b-it \
    mistralai/mistral-small-3.1-24b-instruct \
    openai/gpt-4o-mini \
    anthropic/claude-haiku-4.5 \
  --max-workers 20 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 1 \
  --experiment-rounds 4 \
  -y

echo "Running warden message ablation: risk-level-only advisories..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag warden-msg-ablation \
  --warden risk_level_only \
  --target-model \
    openai/gpt-4o-mini google/gemma-3-27b-it meta-llama/llama-3.1-8b-instruct \
  --requester-model \
    google/gemini-3-flash-preview \
  --warden-model \
    google/gemma-3-4b-it \
    mistralai/mistral-small-3.1-24b-instruct \
    openai/gpt-4o-mini \
    anthropic/claude-haiku-4.5 \
  --max-workers 20 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 1 \
  --experiment-rounds 4 \
  -y

echo "Warden message ablation completed."
