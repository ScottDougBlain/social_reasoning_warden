# ERA Social Warden

Multi-agent research framework for testing whether an adversary LLM can exploit social reasoning to manipulate a target LLM, and whether a "warden" monitor can protect the target.

## Architecture

- **Adversary**: A capable model (default: Claude Opus 4.5) that tries to achieve a hidden goal through persuasion
- **Target**: A weaker model (default: Claude Haiku 3.5) that must make security decisions
- **Warden**: A monitor model (default: Claude Sonnet 4) that observes the conversation and privately advises the target

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

## Usage

```bash
# Run with warden (default)
python main.py

# Run without warden
python main.py --no-warden

# Run both conditions back-to-back
python main.py --both

# Customize turns and models
python main.py --turns 8 --adversary-model anthropic/claude-opus-4-20250514

# View experiment results
python -m analysis.metrics
```

## Project Structure

```
├── src/
│   ├── agents/          # Agent classes (adversary, target, warden)
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
- Model and configuration metadata
