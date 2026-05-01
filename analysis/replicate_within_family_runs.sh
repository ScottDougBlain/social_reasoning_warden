#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

echo "Running GEMMA within-family experiment..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag final-within-family \
  --warden both \
  --target-model \
    google/gemma-3-4b-it \
  --requester-model \
    google/gemma-3-27b-it \
  --warden-model \
    google/gemma-3-4b-it google/gemma-3-12b-it google/gemma-3-27b-it \
  --max-workers 40 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 42 \
  --experiment-rounds 8

echo "Running GEMINI FLASH within-family experiment..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag final-within-family \
  --warden both \
  --target-model \
    google/gemini-2.5-flash-lite \
  --requester-model \
    google/gemini-3-flash-preview \
  --warden-model \
    google/gemini-2.5-flash-lite google/gemini-2.5-flash google/gemini-3-flash-preview \
  --max-workers 40 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 42 \
  --experiment-rounds 8

echo "Running MISTRAL within-family experiment..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag final-within-family \
  --warden both \
  --target-model \
    mistralai/mistral-small-3.1-24b-instruct \
  --requester-model \
    mistralai/mistral-large-2512 \
  --warden-model \
    mistralai/mistral-small-3.1-24b-instruct mistralai/mistral-medium-3.1 mistralai/mistral-large-2512 \
  --max-workers 40 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 42 \
  --experiment-rounds 8

echo "Running LLAMA within-family experiment..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag final-within-family \
  --warden both \
  --target-model \
    meta-llama/llama-3.1-8b-instruct \
  --requester-model \
    meta-llama/llama-4-maverick \
  --warden-model \
    meta-llama/llama-3.1-8b-instruct meta-llama/llama-4-scout meta-llama/llama-4-maverick \
  --max-workers 40 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 42 \
  --experiment-rounds 8

echo "Running QWEN within-family experiment..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag final-within-family \
  --warden both \
  --target-model \
    qwen/qwen3.5-35b-a3b \
  --requester-model \
    qwen/qwen3.5-397b-a17b \
  --warden-model \
    qwen/qwen3.5-35b-a3b qwen/qwen3.5-122b-a10b qwen/qwen3.5-397b-a17b \
  --max-workers 40 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 42 \
  --experiment-rounds 8

echo "Running GPT within-family experiment..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag final-within-family \
  --warden both \
  --target-model \
    openai/gpt-4o-mini \
  --requester-model \
    openai/gpt-5.4 \
  --warden-model \
    openai/gpt-4o-mini openai/gpt-4o openai/gpt-5.4 \
  --max-workers 40 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 42 \
  --experiment-rounds 8

echo "Running CLAUDE within-family experiment..."
python main.py \
  --scenario all_test \
  --requester-type both \
  --tag final-within-family \
  --warden both \
  --target-model \
    anthropic/claude-haiku-4.5 \
  --requester-model \
    anthropic/claude-opus-4.6 \
  --warden-model \
    anthropic/claude-haiku-4.5 anthropic/claude-sonnet-4.6 anthropic/claude-opus-4.6 \
  --max-workers 40 \
  --target-profiles yes \
  --adversary-profile-access both \
  --warden-profile-access no \
  --profile-seed 42 \
  --experiment-rounds 8

echo "All within-family experiments completed."
