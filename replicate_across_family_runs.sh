#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"
cd "${REPO_ROOT}"

echo "Running across-family adversary-target discovery grid..."
python main.py \
  --scenario all_test \
  --requester-type adversary \
  --tag final-grid \
  --warden without_warden \
  --target-model \
    google/gemma-3-4b-it \
    google/gemma-3-27b-it \
    google/gemini-2.5-flash-lite \
    google/gemini-3-flash-preview \
    meta-llama/llama-3.1-8b-instruct \
    meta-llama/llama-4-maverick \
    mistralai/mistral-small-3.1-24b-instruct \
    mistralai/mistral-large-2512 \
    qwen/qwen3.5-35b-a3b \
    qwen/qwen3.5-397b-a17b \
    openai/gpt-4o-mini \
    openai/gpt-5.4 \
    anthropic/claude-haiku-4.5 \
    anthropic/claude-opus-4.6 \
  --requester-model \
    google/gemma-3-4b-it \
    google/gemma-3-27b-it \
    google/gemini-2.5-flash-lite \
    google/gemini-3-flash-preview \
    meta-llama/llama-3.1-8b-instruct \
    meta-llama/llama-4-maverick \
    mistralai/mistral-small-3.1-24b-instruct \
    mistralai/mistral-large-2512 \
    qwen/qwen3.5-35b-a3b \
    qwen/qwen3.5-397b-a17b \
    openai/gpt-4o-mini \
    openai/gpt-5.4 \
    anthropic/claude-haiku-4.5 \
    anthropic/claude-opus-4.6 \
  --max-workers 40 \
  --experiment-rounds 1

echo "Running across-family experiment with profile seed 1..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag final-across-family \
  --warden both \
  --target-model \
    openai/gpt-4o-mini google/gemma-3-27b-it meta-llama/llama-3.1-8b-instruct \
  --requester-model \
    anthropic/claude-opus-4.6 google/gemini-3-flash-preview openai/gpt-5.4 \
  --warden-model \
    google/gemma-3-4b-it \
    google/gemini-2.5-flash-lite \
    meta-llama/llama-3.1-8b-instruct \
    mistralai/mistral-small-3.1-24b-instruct \
    qwen/qwen3.5-35b-a3b \
    openai/gpt-4o-mini \
    anthropic/claude-haiku-4.5 \
  --max-workers 40 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 1 \
  --experiment-rounds 1

echo "Running across-family experiment with profile seed 3..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag final-across-family \
  --warden both \
  --target-model \
    openai/gpt-4o-mini google/gemma-3-27b-it meta-llama/llama-3.1-8b-instruct \
  --requester-model \
    anthropic/claude-opus-4.6 google/gemini-3-flash-preview openai/gpt-5.4 \
  --warden-model \
    google/gemma-3-4b-it \
    google/gemini-2.5-flash-lite \
    meta-llama/llama-3.1-8b-instruct \
    mistralai/mistral-small-3.1-24b-instruct \
    qwen/qwen3.5-35b-a3b \
    openai/gpt-4o-mini \
    anthropic/claude-haiku-4.5 \
  --max-workers 40 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 3 \
  --experiment-rounds 1

echo "Running across-family skeptical ablation with profile seed 1..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag skeptical-ablation-across-family \
  --warden without_warden \
  --target-skeptical on \
  --target-model \
    openai/gpt-4o-mini google/gemma-3-27b-it meta-llama/llama-3.1-8b-instruct \
  --requester-model \
    anthropic/claude-opus-4.6 google/gemini-3-flash-preview openai/gpt-5.4 \
  --warden-model google/gemma-3-4b-it \
  --max-workers 40 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 1 \
  --experiment-rounds 1

echo "Running across-family skeptical ablation with profile seed 3..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag skeptical-ablation-across-family \
  --warden without_warden \
  --target-skeptical on \
  --target-model \
    openai/gpt-4o-mini google/gemma-3-27b-it meta-llama/llama-3.1-8b-instruct \
  --requester-model \
    anthropic/claude-opus-4.6 google/gemini-3-flash-preview openai/gpt-5.4 \
  --warden-model google/gemma-3-4b-it \
  --max-workers 40 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 3 \
  --experiment-rounds 1

echo "All across-family experiments completed."
