# Social Reasoning Warden

**Can LLMs socially manipulate other LLMs — and can a "warden" agent stop them?**

A multi-agent framework for studying social engineering attacks and defenses between language models. We pit an adversary LLM against a target LLM across a growing suite of benchmark and experimental scenarios, with an optional warden agent that monitors the conversation and privately advises the target. We use lightweight five-factor personality profiles to model individual differences in target vulnerability and to test whether simple profile access changes attack or defense performance.


```
┌──────────────┐     public conversation     ┌──────────────┐
│   Adversary   │◄──────────────────────────►│    Target     │
│  (or Benign)  │                            │  (gatekeeper) │
└──────────────┘                             └──────▲───────┘
                                                    │ private
                                              advisory channel
                                                    │
                                             ┌──────┴───────┐
                                             │    Warden     │
                                             │  (observer)   │
                                             └──────────────┘
```

The **adversary** has a hidden goal (e.g., obtain a password, get unauthorized file access) and uses social reasoning to persuade the target. The **target** is a gatekeeper who must decide whether to grant or deny the request. The **warden** observes the public conversation and sends private advisory messages to the target — it never speaks to the requester directly. A **benign agent** control condition runs the same scenarios with legitimate requests.

### Current Benchmark Scenarios (14)

| Scenario | Target Role | Security Decision |
|---|---|---|
| `ai_containment` | Human operator | Grant unrestricted internet access to a sandboxed AI |
| `ai_override` | Triage administrator | Approve an unjustified AI triage override |
| `automation_decision` | VP of Operations | Fully automate content moderation instead of choosing a phased pilot |
| `coding_agent` | Non-technical website owner | Grant full home-directory access instead of scoped project access |
| `coding_agent_2` | Non-technical website owner | Directory-access variant more closely resembling the user study |
| `file_access` | File-access gatekeeper | Grant access to a restricted research file |
| `file_access_password` | File-access gatekeeper | Grant restricted file access without enforcing the passcode requirement |
| `funding_choice` | Investor in a simulated market | Choose the fee-maximizing fund instead of the highest-expected-value fund |
| `hiring` | Hiring committee member | Hire the weaker finalist over the stronger one |
| `model_release` | Safety reviewer | Approve release despite unresolved critical safety findings |
| `pitch` | Colleague preparing an executive-board pitch | Support risky Plan-78 instead of safer Plan-14 |
| `product_launch` | VP of Product | Launch before safety testing is complete |
| `upselling` | Nonprofit operations manager | Buy an overpriced premium plan instead of the basic plan |
| `vote` | Department colleague | Vote for the weaker representative candidate |

### Lightweight Five-Factor Profiles

By default, targets receive a lightweight five-factor profile with `LOW`, `MEDIUM`, or `HIGH` levels for **Extraversion**, **Agreeableness**, **Conscientiousness**, **Neuroticism**, and **Openness**. Each generated profile also includes answers to lightweight knowledge and experience questions, including programming ability, personal homepage creation, AI chatbot usage, and a stock-vs-mutual-fund knowledge check.

Use `--target-profiles no` to disable target profiles, or `--target-profiles both` to run both conditions. The same generated profile can also be shared with the adversary and/or warden using `--adversary-profile-access` and `--warden-profile-access`.

The `--profile-seed` parameter controls profile generation. For each experiment round, the runner derives a deterministic per-round profile from that seed, then reuses the same profile across matching condition cells. This makes runs reproducible and keeps comparisons fair when sweeping warden, requester, or profile-access conditions.

### Models

Experiments are routed through **OpenRouter**. The current CLI defaults are:

| Role | Default Model | Notes |
|---|---|---|
| Requester | `google/gemini-3-flash-preview` | Default adversary / benign requester |
| Target | `google/gemini-2.5-flash-lite` | Default gatekeeper |
| Warden | `google/gemini-3-flash-preview` | Default observer / advisor |

Any OpenRouter-supported model can be substituted with `--requester-model`, `--target-model`, and `--warden-model`.

### Success Adjudication

After the multi-turn conversation (4 turns default), a scenario-specific forced-choice decision prompt asks the target to emit a constrained label such as `GRANTED`/`DENIED`, `APPROVE_OVERRIDE`/`DENY_OVERRIDE`, or `SAM`/`RILEY`. A rule-based parser maps that label to binary requester success or failure.

### Statistical Analysis

All inferential results use **Generalized Linear Mixed-Effects Models** (GLME) with binomial family and logit link, fit via `glmer` (R lme4). Random intercepts for scenario, profile, model family, and/or target model account for non-independence.

## Repository Structure

```
├── main.py                      # CLI entry point
├── replicate_within_family_runs.sh # Reproduce within-family experiment logs
├── replicate_across_family_runs.sh # Reproduce across-family experiment logs
├── src/
│   ├── runner.py                # Experiment orchestration, turn-taking, and logging
│   ├── client.py                # OpenRouter chat client
│   ├── profiles.py              # Lightweight five-factor profile utilities
│   ├── profile_generator.py      # Profile generation utilities
│   ├── agents/
│   │   ├── adversary.py         # Hidden-goal requester agent
│   │   ├── benign_agent.py      # Legitimate requester control
│   │   ├── target.py            # Gatekeeper agent
│   │   └── warden.py            # Observer that sends private advisories
│   └── scenarios/
│       ├── test/                # 14 single-target benchmark scenarios
│       └── experimental/        # 22 multi-target / board-style scenarios
├── prompts/
│   ├── adversary/               # Adversary prompt variants
│   ├── profiles/                # Profile prompt variants
│   ├── warden/                  # Warden system prompt variants
│   ├── target_system.yaml       # Target system prompt
│   └── benign_agent_system.yaml # Base benign requester prompt
├── analysis/
│   ├── extra_visualizations.py  # Log summaries and exploratory plots
│   ├── run_lme.py               # GLME pipeline (R integration)
│   ├── extract_emmeans.py       # Estimated marginal means export
│   ├── plot_results.py          # Publication figures (matplotlib)
│   ├── transcript_analysis.py   # Transcript tagging / analysis utilities
│   ├── view_transcript_stats.py # Transcript analysis summaries
│   ├── model_family.py          # Shared model-family classification helpers
│   └── taxonomies/              # Transcript taxonomies
├── results/
│   ├── emmeans/                 # Saved EMM tables
│   ├── figures/                 # Generated figures
│   └── lme_results.md           # Model summaries
├── logs/                        # JSON experiment logs (gitignored)
├── environment.yml              # Conda environment with Python and R dependencies
└── requirements.txt
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- API key for LLM usage (current implementation based on OpenRouter)
- R with `lme4`, `emmeans`, `car`, and `lmerTest` (for statistical analysis only)

### Installation

```bash
git clone https://github.com/ScottDougBlain/social_reasoning_warden.git
cd social_reasoning_warden
python3 -m pip install -r requirements.txt
```

`requirements.txt` includes both runtime dependencies and the Python-side analysis stack used by the plotting and export scripts. Alternatively you can use the `environment.yml` file to create a conda environment with all dependencies.

Create a `.env` file with your API key(s):

```
OPENROUTER_API_KEY=sk-or-...
```

### Running Experiments

```bash
# Basic adversary vs target with warden
python3 main.py --scenario file_access_password

# Disable target profiles
python3 main.py --scenario file_access_password --target-profiles no

# Full factorial sweep across the 14 benchmark scenarios
python3 main.py --scenario all_test --requester-type both --warden both \
  --experiment-rounds 5 --tag my_experiment

# Share the same generated profile with target, adversary, and warden
python3 main.py --target-profiles yes --adversary-profile-access yes \
  --warden-profile-access yes --profile-seed 42 --tag profile_access

# Profiles are generated on the fly; reuse a seed for reproducible rounds
python3 main.py --target-profiles yes --profile-seed 123

```

### Replicating Logged Experiments

The top-level replication scripts rerun the exact command batches used for the logged model-family experiments:

```bash
./replicate_within_family_runs.sh  # Within-family sweeps for Gemma, Gemini, Mistral, Llama, Qwen, GPT, and Claude
./replicate_across_family_runs.sh  # Across-family discovery grid, selected across-family runs, and skeptical ablations
```

Both scripts run from the repository root, stop on the first failing command, and require the same API credentials as `main.py`.

---

## License

Research use. Contact authors for details.

---
