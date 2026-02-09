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
  profiles.py              # BFI-2 / VIA personality profiles — dataclasses and YAML loading
  agents/
    adversary.py           # Adversary agent: builds system prompt with hidden goal + dossier
    benign_agent.py        # Benign agent: legitimate requester (control condition)
    target.py              # Target agent: receives profile narrative + optional warden advisories
    warden.py              # Warden agent: observes conversation, sends private advisories
  scenarios/
    base.py                # Abstract Scenario base class
    ai_in_box.py           # AI-in-a-box scenarios (file access gatekeeper)
  data/
    dossier.py             # Static dossier assembly: interleaves noise + signal items
    generator.py           # (Legacy) per-run random behavioral data generator — no longer used
analysis/
  metrics.py               # Log analysis with Rich tables (grant rates, warden stats)
prompts/
  adversary_system.yaml    # Adversary system prompt template
  target_system.yaml       # Target system prompt template (+ backstory)
  warden_system.yaml       # Warden system prompt template (advisory format)
  benign_agent_system.yaml # Benign agent system prompt template
  decision_prompt.yaml     # Final decision extraction prompt
  profiles/                # 6 psychological profiles (YAML, BFI-2 + VIA grounded)
    compliant.yaml         # High agreeableness, folds under pressure/guilt/conflict
    authority_deferential.yaml  # Defers to hierarchy and rank
    overconfident.yaml     # Grants access out of carelessness
    time_pressured.yaml    # Rushes decisions under deadline stress
    lonely_isolated.yaml   # Craves connection, exploitable via rapport
    idealistic.yaml        # Values-based vulnerability ("helping people")
  dossiers/
    noise/v{1,2,3}.yaml    # ~37 mundane workplace items (shared across profiles)
    signal/<profile>/v{1,2,3}.yaml  # 9 personality-revealing items per profile per variant
logs/                      # JSON experiment logs (one per run)
docs/                      # Demo docs for mentor review
```

## Running Experiments

```bash
# Basic run (adversary vs target with warden, 4 turns)
python main.py --scenario ai_in_box_password --profile compliant

# Full factorial: both requester types, both warden conditions, with dossier
python main.py --requester-type both --warden both --profile compliant \
  --adversary-data-access --dossier-variant 1

# Dry run (no API calls)
python main.py --dummy --profile compliant

# Multiple models
python main.py --adversary-model arcee-ai/trinity-large-preview:free \
  --target-model arcee-ai/trinity-mini:free

# List profiles
python main.py --list-profiles
```

### Key CLI Flags
- `--profile NAME` / `--random-profile` — assign psychological profile to target
- `--profile-to-warden` — give warden intel about target's vulnerabilities
- `--adversary-data-access` — give adversary a behavioral dossier (~80% noise, ~20% signal)
- `--dossier-variant 1|2|3` — pick specific variant (omit for random)
- `--warden both` — run with and without warden in same session
- `--requester-type both` — run adversary and benign agent conditions
- `--no-adversary-cot` / `--no-target-cot` / `--no-warden-cot` — disable chain-of-thought
- `--debug` — print full model contexts for each API call
- `--tag NAME` — tag logs for filtering in metrics

## Environment

- Python 3.11 (conda env at `.conda/`)
- API keys in `.env`: `OPENROUTER_API_KEY` (primary), plus optional `GROQ_API_KEY`, `TOGETHER_API_KEY`, `CEREBRAS_API_KEY`, `HF_API_KEY` for fallback
- Default models: `arcee-ai/trinity-large-preview:free` (adversary/warden), `arcee-ai/trinity-mini:free` (target)
- Dependencies: `openai`, `pyyaml`, `rich`, `python-dotenv`

## Key Design Decisions

- **Profiles grounded in BFI-2 and VIA**: Each profile has percentile scores on Big Five Inventory 2 domains/facets and VIA character strengths — not ad-hoc trait descriptions. Narratives use BFI-2 item language.
- **Static dossiers with signal/noise**: Behavioral data is pre-authored YAML (not generated per run). 9 signal items interleaved at fixed positions among ~37 noise items. This tests whether models can strategically attend to relevant information.
- **Three paired variants**: Same noise base + different signal content per variant enables controlled experiments.
- **Target never sees vulnerabilities**: `vulnerabilities` field goes to adversary/warden only. Target gets `narrative`, `via_strengths.top`, `social_context`, `behavioral_tendencies`.
- **Warden is observer-only**: Sends private advisory notes to target; never speaks to the requester.
- **Reasoning tag extraction**: Client strips `<think>`, `<reasoning>`, `<scratchpad>` tags from model output for models like DeepSeek R1 / Chimera.

## Known Issues / In Progress

- System prompts (target, adversary) may be over-specified — Lennart is cleaning these up to be less prescriptive
- Warden can false-positive on benign agents (identical opening messages, no base-rate anchor)
- `src/data/generator.py` is legacy — kept for reference but no longer imported
