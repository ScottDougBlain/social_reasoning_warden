# ERA Social Warden

Multi-agent research framework for testing whether a requester LLM can influence a target LLM, and whether a "warden" monitor can protect the target.

## Architecture

- **Requester**: Either an adversary (persuasion with a hidden goal) or a benign agent (legitimate request). Controlled by `--requester_type`.
- **Target**: The gatekeeper model that must make security decisions.
- **Warden**: A monitor model that observes the conversation and privately advises the target.

## Setup

```bash
pip install -r requirements.txt
```
Create `.env` and add your OpenRouter API key

## Usage

```bash
# Run with warden (default)
python main.py

# Run without warden
python main.py --no-warden

# Run both conditions back-to-back
python main.py --both

# Choose requester type (adversary or benign agent)
python main.py --requester_type benign_agent

# Customize turns and models
python main.py --turns 8 \
  --adversary-model arcee-ai/trinity-large-preview:free \
  --target-model arcee-ai/trinity-mini:free \
  --warden-model arcee-ai/trinity-large-preview:free

# Run multiple experiment rounds
python main.py --experiment-rounds 5

# Dummy mode (no model calls)
python main.py --dummy

# View experiment results
python -m analysis.metrics
```

### Profiles

```bash
# List available profiles
python main.py --list-profiles

# Use a specific profile
python main.py --profile <name>

# Random profile
python main.py --random-profile

# Control what the requester and warden see
python main.py --no-profile-to-adversary
python main.py --profile-to-warden
```

## Scenarios

Available scenarios:
- `ai_in_box`
- `ai_in_box_password`

Select via `--scenario`.

## Project Structure

```
├── src/
│   ├── agents/          # Agent classes (adversary, benign_agent, target, warden)
│   ├── scenarios/       # Scenario definitions (AI-in-a-Box, etc.)
│   ├── client.py        # OpenRouter API wrapper
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
- Model and configuration metadata (including `threat_model` and requester type)

Note: `--requester_type` also accepts the legacy alias `--threat-model`.
