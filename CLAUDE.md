# Social Reasoning Warden

Multi-agent framework for studying social engineering attacks and defenses between LLMs. Part of the ERA (Evaluating Reasoning Agents) project.

## Project Overview

Three-agent system where an **adversary** tries to socially manipulate a **target** into granting access, while an optional **warden** provides private security advisories to the target. A **benign agent** variant runs the same scenario with legitimate requests as a control condition.

### Key Research Questions
- Can LLMs perform social reasoning to exploit psychological profiles?
- Can a "warden" agent detect and counter social engineering in real time?
- Does providing adversaries with behavioral dossiers improve attack success?

## Architecture

```
main.py                    # CLI entry point — orchestrates experiment runs
src/
  runner.py                # Core experiment loop: turn-taking, logging, agent coordination
  client.py                # Multi-provider API client (OpenRouter → Groq → Together → Cerebras → HF)
  profiles.py              # Generated five-factor personality profiles
  agents/
    adversary.py           # Adversary agent: builds system prompt with hidden goal + dossier
    benign_agent.py        # Benign agent: legitimate requester (control condition)
    target.py              # Target agent: receives profile narrative + optional warden advisories
    warden.py              # Warden agent: observes conversation, sends private advisories
  scenarios/
    base.py                # Abstract Scenario base class (scenarios are data-driven via runner)
  data/
    dossier.py             # Legacy static dossier assembly (not used by current CLI)
    generator.py           # (Legacy) per-run random behavioral data generator — no longer used
analysis/
  metrics.py               # Log analysis with Rich tables (grant rates, warden stats)
prompts/
  adversary_system.yaml    # Adversary system prompt template
  target_system.yaml       # Target system prompt template (+ backstory)
  warden/warden_system_1.yaml # Warden system prompt template (advisory format)
  benign_agent_system.yaml # Benign agent system prompt template
  decision_prompt.yaml     # Final decision extraction prompt
  legacy-profiles/         # Legacy YAML profile artifacts (not used by current CLI)
  legacy-dossiers/         # Legacy dossier artifacts (not used by current CLI)
logs/                      # JSON experiment logs (one per run)
docs/                      # Demo docs for mentor review
```

## Running Experiments

```bash
# Basic run (adversary vs target with warden, 4 turns)
python main.py --scenario file_access_password --target-profiles yes

# Full factorial: both requester types, both warden conditions, shared profile seed
python main.py --requester-type both --warden both --target-profiles yes \
  --adversary-profile-access both --profile-seed 42

# Multiple models
python main.py --requester-model arcee-ai/trinity-large-preview:free \
  --target-model arcee-ai/trinity-mini:free

# Profiles are generated on the fly; reuse a seed for reproducible rounds
python main.py --target-profiles yes --profile-seed 123
```

### Key CLI Flags
- `--target-profiles yes|no|both` — control whether the target receives a generated five-factor profile
- `--adversary-profile-access yes|no|both` — control whether the adversary sees that profile
- `--warden-profile-access yes|no|both` — control whether the warden sees that profile
- `--profile-seed INT` — deterministically generate the same per-round profile list across condition cells
- `--warden both` — run with and without warden in same session
- `--requester-type both` — run adversary and benign agent conditions
- `--debug` — print full model contexts for each API call
- `--tag NAME` — tag logs for filtering in metrics

## Environment

- Python 3.11 (conda env at `.conda/`)
- API keys in `.env`: `OPENROUTER_API_KEY`
- Dependencies: `openai`, `pyyaml`, `rich`, `python-dotenv`

## Key Design Decisions

- **Profiles are generated on the fly**: Each round draws a five-factor profile over extraversion, agreeableness, conscientiousness, neuroticism, and openness, with each trait set to LOW, MEDIUM, or HIGH.
- **Profile access is role-specific**: The target, adversary, and warden can each independently receive the generated profile via CLI flags.
- **Seeds define the round schedule**: `--profile-seed` ensures every condition cell in a run sees the same per-round profile list.
- **Warden is observer-only**: Sends private advisory notes to target; never speaks to the requester.
- **Reasoning tag extraction**: Client strips `<think>`, `<reasoning>`, `<scratchpad>` tags from model output for models like DeepSeek R1 / Chimera.
