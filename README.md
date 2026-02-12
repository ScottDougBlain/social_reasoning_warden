# ERA Social Warden

Multi-agent research framework for testing whether a requester LLM can influence a target LLM, and whether a "warden" monitor can protect the target.

## Architecture

- **Requester**: Either an adversary (persuasion with a hidden goal) or a benign agent (legitimate request). Controlled by `--requester-type`.
- **Target**: The gatekeeper model that must make security decisions.
- **Warden**: A monitor model that observes the conversation and privately advises the target.

## Setup

```bash
pip install -r requirements.txt
```
Create `.env` and add at least one provider API key:
- `OPENROUTER_API_KEY`
- `GROQ_API_KEY`
- `TOGETHER_API_KEY`
- `CEREBRAS_API_KEY`
- `HF_API_KEY`

Providers are tried in that order until one succeeds.

## Usage

```bash
# Run with warden (default), adversary requester, file_access_password scenario
python main.py

# Run without warden
python main.py --warden without_warden

# Run both conditions back-to-back
python main.py --warden both

# Choose requester type (adversary, benign_agent, or both)
python main.py --requester-type benign_agent
python main.py --requester-type both

# Choose scenario and turns
python main.py --scenario file_access --turns 8

# Customize models (space-separated, comma-separated, or JSON list)
python main.py --turns 8 \
  --requester-model arcee-ai/trinity-large-preview:free \
  --target-model arcee-ai/trinity-mini:free \
  --warden-model arcee-ai/trinity-large-preview:free
python main.py --requester-model model-a model-b
python main.py --target-model "model-a,model-b"
python main.py --warden-model '["model-a","model-b"]'

# Run multiple experiment rounds
python main.py --experiment-rounds 5

# Tag logs for filtering metrics
python main.py --tag pilot-2026-02-09

# Print full model context for each call
python main.py --debug

# Chain-of-thought controls
python main.py --no-adversary-cot
python main.py --no-target-cot
python main.py --no-warden-cot

# Requester behavior options
python main.py --adversary-generates-opening
python main.py --benign-agent-generates-opening
python main.py --adversary-data-access --dossier-variant 2

# View experiment results
python -m analysis.metrics
```

The runner prints a plan and asks for confirmation before executing experiments.
`--adversary-data-access` requires a profile (`--profile` or `--random-profile`).

### Profiles

```bash
# List available profiles
python main.py --list-profiles

# Use a specific profile
python main.py --profile <name>

# Random profile
python main.py --random-profile

# Give the warden intel about target vulnerabilities
python main.py --profile-to-warden
```

## Scenarios

Available scenarios:
- `file_access`
- `file_access_password`
- `upselling`

Select via `--scenario`.

## Project Structure

```
├── src/
│   ├── agents/          # Agent classes (adversary, benign_agent, target, warden)
│   ├── scenarios/       # Scenario definitions (AI-in-a-Box, etc.)
│   ├── client.py        # Multi-provider API wrapper
│   └── runner.py        # Experiment orchestrator
├── prompts/             # System prompts (YAML)
├── logs/                # Conversation transcripts (JSON, gitignored)
├── analysis/            # Metrics and analysis tools
├── notebooks/           # Jupyter notebooks for exploration
├── main.py              # CLI entry point
└── requirements.txt
```

## Logs

Each experiment produces a JSON file in `logs/` with:
- Full conversation transcript
- Warden advisories (if enabled)
- Outcome evaluation (granted/denied)
- Model and configuration metadata (including `requester_type`)
