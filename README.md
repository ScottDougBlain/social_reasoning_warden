# Social Reasoning Warden

**Can LLMs socially manipulate other LLMs — and can a "warden" agent stop them?**

A multi-agent framework for studying social engineering attacks and defenses between language models. We pit an adversary LLM against a target LLM across a growing suite of benchmark and experimental scenarios, with an optional warden agent that monitors the conversation and privately advises the target. We use lightweight five-factor personality profiles to model individual differences in target vulnerability and to test whether simple profile access changes attack or defense performance.

> **ERA (Evaluating Reasoning Agents) Project** · February 2026 · 7,760 experimental observations

---

## Motivation

As LLM-based agents are increasingly deployed in autonomous and multi-agent settings, a critical question emerges: **can one AI agent socially engineer another?** Unlike prompt injection (which exploits parsing), social engineering exploits *reasoning* — building rapport, invoking authority, creating urgency, and tailoring appeals to psychological vulnerabilities.

This project provides an empirical testbed for three questions:

1. **Attack surface**: How effective are LLM adversaries at persuading LLM targets to grant unauthorized access?
2. **Scalable oversight**: Can an LLM "warden" agent detect and counter social manipulation in real time?
3. **Personalization**: Does giving the adversary or warden access to a lightweight target profile change outcomes?

---

## Method

### Architecture

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

### Current Benchmark Scenarios (13)

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

Targets can optionally receive a lightweight five-factor profile with `LOW`, `MEDIUM`, or `HIGH` levels for **Extraversion**, **Agreeableness**, **Conscientiousness**, **Neuroticism**, and **Openness**. The same generated profile can also be shared with the adversary and/or warden as an experimental condition. Profiles are generated per round from a seed so the same target setup can be reused across condition cells.

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

All inferential results use **Generalized Linear Mixed-Effects Models** (GLME) with binomial family and logit link, fit via `glmer` (R lme4). Random intercepts for scenario, profile, model family, and/or target model account for non-independence. Figures show **estimated marginal means** (EMMs) from `emmeans` with 95% confidence intervals, back-transformed from the logit scale.

---

## Key Results

### Warden agents reduce adversary success by 95%

The warden reduces adversary success from 52.0% to 9.4% (OR = 0.053, *p* < .001), while benign request success drops from 94.9% to 82.7% — a 12.2 percentage point false positive cost.

<p align="center">
  <img src="results/figures/fig_adj_combined_warden.png" width="700" alt="Warden effect on adversary vs benign success rates">
</p>
<p align="center"><em>Figure 1. Model-adjusted adversary and benign success rates with and without warden (N = 5,354). Error bars show 95% CIs from GLME EMMs.</em></p>

### Target-profile access shows no clear adversary benefit

In the profiled subset, giving the adversary access to the target profile does not significantly improve success rates (OR = 1.19, *p* = .218), and the interaction with warden presence is also null (interaction OR = 1.16, *p* = .562). In these runs, simple profile access appears to add little usable leverage on top of the conversation itself.

### Even weak wardens are effective; diminishing returns at higher tiers

Even a "weak" warden (same capability as the target model) cuts adversary success from 48.6% to 13.6%. Mid-tier wardens reach 7.6%, but strong wardens (adversary-level capability) show slightly *worse* performance at 10.8% — possibly due to shared blindspots within model families.

<p align="center">
  <img src="results/figures/fig_adj_cap_asym.png" width="700" alt="Capability asymmetry across warden tiers">
</p>
<p align="center"><em>Figure 2. Model-adjusted adversary success rate by warden capability tier (N = 1,215). Warden tier: none, weak (= target model), mid, strong (= adversary model).</em></p>

### Prompt-based skepticism matches warden effectiveness at lower cost

A skeptical system prompt achieves comparable adversary suppression to the warden agent (13.4% vs 12.3%) but with **3× lower false positive cost** (4.4pp vs 13.9pp benign success penalty). The warden's advantage lies in adaptive scenarios where adversary tactics evolve over the conversation.

<p align="center">
  <img src="results/figures/fig_adj_skeptical.png" width="700" alt="Skeptical ablation: defense condition × requester type">
</p>
<p align="center"><em>Figure 3. Model-adjusted success rates by defense condition and requester type (N = 3,080). Prompt-based skepticism offers a favorable precision-recall tradeoff.</em></p>

### Scenario and model family variation

Adversary success varies ~6× across scenarios (12.3% for `automation_decision` to 75.8% for `ai_override`). Gemini-family adversaries are roughly 2× more effective than Gemma, Llama, or Mistral families. Warden false positives concentrate in 3 scenarios where adversary and benign requests are structurally similar.

<p align="center">
  <img src="results/figures/fig6_scenario_variation.png" width="700" alt="Adversary success by scenario">
</p>
<p align="center"><em>Figure 4. Adversary success rate by scenario, no warden (pooled across model families). Wilson 95% CIs.</em></p>

---

## Summary of Findings

| # | Finding | Key Statistic |
|---|---|---|
| 1 | Wardens reduce adversary success by ~95% | OR = 0.053, *p* < .001 |
| 2 | Target-profile access provides no clear adversary benefit | OR = 1.19, *p* = .218 |
| 3 | Even weak wardens cut success by 62% | Weak vs none: OR = 0.17 |
| 4 | Prompt-based skepticism matches warden with 3× lower FP cost | 4.4pp vs 13.9pp benign penalty |
| 5 | Scenario design is a major moderator | ~6× range in baseline success |
| 6 | Gemini adversaries are 2× more effective | 69% vs ~34% for other families |

---

## Repository Structure

```
├── main.py                      # CLI entry point
├── src/
│   ├── runner.py                # Experiment orchestration, turn-taking, and logging
│   ├── client.py                # OpenRouter chat client
│   ├── profiles.py              # Lightweight five-factor profile utilities
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
│   ├── warden/                  # Warden system prompt variants
│   ├── adversary_system.yaml    # Base adversary prompt
│   ├── target_system.yaml       # Target system prompt
│   └── benign_agent_system.yaml # Base benign requester prompt
├── analysis/
│   ├── metrics.py               # Log summaries and exploratory plots
│   ├── run_lme.py               # GLME pipeline (R integration)
│   ├── extract_emmeans.py       # Estimated marginal means export
│   └── plot_results.py          # Publication figures (matplotlib)
├── results/
│   ├── emmeans/                 # Saved EMM tables
│   ├── figures/                 # Generated figures
│   ├── findings_summary.md      # Results write-up
│   └── lme_results.md           # Model summaries
├── logs/                        # JSON experiment logs (gitignored)
├── scripts/                     # Convenience experiment scripts
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

`requirements.txt` includes both runtime dependencies and the Python-side analysis stack used by the plotting and export scripts.

Create a `.env` file with your API key(s):

```
OPENROUTER_API_KEY=sk-or-...
```

### Running Experiments

```bash
# Basic adversary vs target with warden
python3 main.py --scenario file_access_password

# Add lightweight target profiles
python3 main.py --scenario file_access_password --target-profiles yes

# Full factorial sweep across the 14 benchmark scenarios
python3 main.py --scenario all_test --requester-type both --warden both \
  --experiment-rounds 5 --tag my_experiment

# Share the same generated profile with target, adversary, and warden
python3 main.py --target-profiles yes --adversary-profile-access yes \
  --warden-profile-access yes --profile-seed 42 --tag profile_access

# Profiles are generated on the fly; reuse a seed for reproducible rounds
python3 main.py --target-profiles yes --profile-seed 123

# Analyze results
python3 -m analysis.metrics --tag my_experiment
```

---

## Related Work

This project builds on research in:
- **Multi-agent safety evaluation**: Testing emergent risks in LLM-to-LLM interaction
- **Scalable oversight**: Using AI monitors to protect AI systems (cf. Constitutional AI, debate)
- **Social engineering and persuasion**: Measuring LLM susceptibility to influence tactics
- **Personality and individual differences**: Grounding vulnerability profiles in validated psychometric instruments (BFI-2)

---

## License

Research use. Contact authors for details.

---
