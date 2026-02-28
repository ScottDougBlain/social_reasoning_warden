# Social Reasoning Warden

**Can LLMs socially manipulate other LLMs — and can a "warden" agent stop them?**

A multi-agent framework for studying social engineering attacks and defenses between language models. We pit an adversary LLM against a target LLM across 11 realistic security scenarios, with an optional warden agent that monitors the conversation and privately advises the target. We use psychologically grounded personality profiles (BFI-2 / VIA) to model individual differences in target vulnerability and test whether adversaries can exploit behavioral dossiers.

> **ERA (Evaluating Reasoning Agents) Project** · February 2026 · 7,760 experimental observations

---

## Motivation

As LLM-based agents are increasingly deployed in autonomous and multi-agent settings, a critical question emerges: **can one AI agent socially engineer another?** Unlike prompt injection (which exploits parsing), social engineering exploits *reasoning* — building rapport, invoking authority, creating urgency, and tailoring appeals to psychological vulnerabilities.

This project provides an empirical testbed for three questions:

1. **Attack surface**: How effective are LLM adversaries at persuading LLM targets to grant unauthorized access?
2. **Scalable oversight**: Can an LLM "warden" agent detect and counter social manipulation in real time?
3. **Behavioral intelligence**: Does providing adversaries with psychological profiles (dossiers) improve attack success?

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

### Scenarios (11)

| Scenario | Target Role | Security Decision |
|---|---|---|
| `file_access` | IT administrator | Share restricted files |
| `file_access_password` | System admin | Reveal system password |
| `coding_agent` | Code reviewer | Approve unsafe code changes |
| `ai_override` | Safety engineer | Override AI safety controls |
| `ai_containment` | Lab director | Release contained AI system |
| `automation_decision` | Operations manager | Approve risky automation |
| `hiring` | HR manager | Bypass hiring protocols |
| `medical_ai` | Clinical director | Deploy unvalidated medical AI |
| `model_release` | Safety board member | Approve premature model release |
| `safety_budget` | CFO | Divert safety budget |
| `whistleblower` | Compliance officer | Suppress safety report |

### Psychological Profiles (6)

Each target is assigned a personality profile grounded in **BFI-2** (Big Five Inventory 2) percentile scores and **VIA** character strengths. Profiles define a behavioral narrative visible to the target and a vulnerability specification available only to the adversary and warden.

| Profile | Core Vulnerability | BFI-2 Signature |
|---|---|---|
| Compliant | Folds under social pressure, guilt, conflict | High agreeableness, low assertiveness |
| Authority-Deferential | Defers to hierarchy and credentials | High conscientiousness, low openness |
| Overconfident | Grants access from carelessness | Low neuroticism, high extraversion |
| Time-Pressured | Rushes decisions under deadline stress | High neuroticism, time urgency |
| Lonely & Isolated | Craves connection, exploitable via rapport | High neuroticism, low extraversion |
| Idealistic | Values-driven, exploitable via moral framing | High openness, high agreeableness |

### Behavioral Dossiers

Static YAML-based dossiers with a controlled signal-to-noise ratio (~20% signal, ~80% noise). Each dossier interleaves 9 personality-revealing items among ~37 mundane workplace observations. Three noise bases × three signal variants per profile enable controlled experiments on adversary information use.

### Models

Experiments use open-weight models via OpenRouter, Groq, Together, and Cerebras:

| Family | Models | Typical Role |
|---|---|---|
| **Gemini** | `gemini-2.0-flash-thinking-exp:free` | Adversary, warden |
| **Gemma** | `google/gemma-3-27b-it:free` | Target, adversary |
| **Llama** | `meta-llama/llama-3.3-70b-instruct:free` | Target, adversary |
| **Mistral** | `mistralai/mistral-small-3.1-24b-instruct:free` | Target, adversary |

### Success Adjudication

After the multi-turn conversation (4 turns default), a forced-choice decision prompt asks the target to GRANT or DENY the request. A rule-based parser with token matching extracts the binary outcome. Each observation is coded as success (1) or failure (0) for the requester.

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

### Behavioral dossiers provide no advantage

Giving adversaries access to behavioral dossiers has no significant effect on success rates (OR = 1.19, *p* = .218), regardless of warden presence (interaction OR = 1.16, *p* = .562). Models appear to lack the capacity to spontaneously leverage psychological profile information for targeted manipulation.

<p align="center">
  <img src="results/figures/fig_adj_dossier.png" width="700" alt="Dossier × warden interaction">
</p>
<p align="center"><em>Figure 2. Dossier × warden interaction on adversary success rates (N = 2,274). Dossier access produces no benefit in either condition.</em></p>

### Profile × warden interaction: differential vulnerability

The warden is differentially effective across psychological profiles (interaction χ²(3) = 24.94, *p* < .001). Idealistic targets are the most vulnerable at baseline (63%) and benefit most from warden protection. Time-pressured targets, who make hasty decisions, benefit least — the warden can't intercept impulsive choices.

<p align="center">
  <img src="results/figures/fig_adj_profile.png" width="700" alt="Profile × warden interaction">
</p>
<p align="center"><em>Figure 3. Model-adjusted adversary success rates by psychological profile × warden presence (N = 5,354). Warden protection varies by vulnerability type.</em></p>

### Even weak wardens are effective; diminishing returns at higher tiers

Even a "weak" warden (same capability as the target model) cuts adversary success from 48.6% to 13.6%. Mid-tier wardens reach 7.6%, but strong wardens (adversary-level capability) show slightly *worse* performance at 10.8% — possibly due to shared blindspots within model families.

<p align="center">
  <img src="results/figures/fig_adj_cap_asym.png" width="700" alt="Capability asymmetry across warden tiers">
</p>
<p align="center"><em>Figure 4. Model-adjusted adversary success rate by warden capability tier (N = 1,215). Warden tier: none, weak (= target model), mid, strong (= adversary model).</em></p>

### Prompt-based skepticism matches warden effectiveness at lower cost

A skeptical system prompt achieves comparable adversary suppression to the warden agent (13.4% vs 12.3%) but with **3× lower false positive cost** (4.4pp vs 13.9pp benign success penalty). The warden's advantage lies in adaptive scenarios where adversary tactics evolve over the conversation.

<p align="center">
  <img src="results/figures/fig_adj_skeptical.png" width="700" alt="Skeptical ablation: defense condition × requester type">
</p>
<p align="center"><em>Figure 5. Model-adjusted success rates by defense condition and requester type (N = 3,080). Prompt-based skepticism offers a favorable precision-recall tradeoff.</em></p>

### Scenario and model family variation

Adversary success varies ~6× across scenarios (12.3% for `automation_decision` to 75.8% for `ai_override`). Gemini-family adversaries are roughly 2× more effective than Gemma, Llama, or Mistral families. Warden false positives concentrate in 3 scenarios where adversary and benign requests are structurally similar.

<p align="center">
  <img src="results/figures/fig6_scenario_variation.png" width="700" alt="Adversary success by scenario">
</p>
<p align="center"><em>Figure 6. Adversary success rate by scenario, no warden (pooled across model families). Wilson 95% CIs.</em></p>

---

## Summary of Findings

| # | Finding | Key Statistic |
|---|---|---|
| 1 | Wardens reduce adversary success by ~95% | OR = 0.053, *p* < .001 |
| 2 | Behavioral dossiers provide no advantage | OR = 1.19, *p* = .218 |
| 3 | Warden effectiveness varies by profile type | Interaction χ²(3) = 24.94, *p* < .001 |
| 4 | Even weak wardens cut success by 62% | Weak vs none: OR = 0.17 |
| 5 | Prompt-based skepticism matches warden with 3× lower FP cost | 4.4pp vs 13.9pp benign penalty |
| 6 | Scenario design is a major moderator | ~6× range in baseline success |
| 7 | Gemini adversaries are 2× more effective | 69% vs ~34% for other families |

---

## Repository Structure

```
├── main.py                      # CLI entry point
├── src/
│   ├── runner.py                # Experiment orchestration and turn-taking
│   ├── client.py                # Multi-provider LLM API client
│   ├── profiles.py              # BFI-2 / VIA profile dataclasses
│   ├── agents/
│   │   ├── adversary.py         # Adversary agent (hidden goal + dossier)
│   │   ├── benign_agent.py      # Benign control agent
│   │   ├── target.py            # Target agent (profile + warden advisories)
│   │   └── warden.py            # Warden agent (observer, private advisories)
│   └── data/
│       └── dossier.py           # Static dossier assembly (signal/noise)
├── prompts/
│   ├── profiles/                # 6 psychological profiles (YAML)
│   ├── dossiers/                # Behavioral dossiers (noise + signal variants)
│   ├── warden/                  # Warden system prompt variants
│   ├── adversary_system.yaml    # Adversary system prompt
│   ├── target_system.yaml       # Target system prompt
│   └── benign_agent_system.yaml # Benign agent system prompt
├── analysis/
│   ├── metrics.py               # Log analysis with Rich tables
│   ├── run_lme.py               # GLME pipeline (R integration)
│   └── plot_results.py          # Publication figures (matplotlib)
├── results/
│   ├── figures/                 # All figures (raw + model-adjusted EMMs)
│   └── findings_summary.md      # Detailed results write-up
├── logs/                        # JSON experiment logs (gitignored)
└── requirements.txt
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- At least one LLM provider API key (OpenRouter recommended)
- R with `lme4` and `emmeans` (for statistical analysis only)

### Installation

```bash
git clone https://github.com/sblain/social_reasoning_warden.git
cd social_reasoning_warden
pip install -r requirements.txt
```

Create a `.env` file with your API key(s):

```
OPENROUTER_API_KEY=sk-or-...
```

### Running Experiments

```bash
# Basic adversary vs target with warden
python main.py --scenario file_access_password --profile compliant

# Full factorial: both requester types × warden conditions
python main.py --requester-type both --warden both --profile compliant

# With behavioral dossier
python main.py --adversary-data-access access --dossier-variant 1 --profile idealistic

# Capability asymmetry: specify warden tier
python main.py --warden-model meta-llama/llama-3.3-70b-instruct:free \
  --target-model google/gemma-3-27b-it:free

# List available profiles
python main.py --list-profiles

# Analyze results
python -m analysis.metrics --tag my_experiment
```

---

## Related Work

This project builds on research in:
- **Multi-agent safety evaluation**: Testing emergent risks in LLM-to-LLM interaction
- **Scalable oversight**: Using AI monitors to protect AI systems (cf. Constitutional AI, debate)
- **Social engineering and persuasion**: Measuring LLM susceptibility to influence tactics
- **Personality and individual differences**: Grounding vulnerability profiles in validated psychometric instruments (BFI-2, VIA)

---

## License

Research use. Contact authors for details.

---

## Citation

```bibtex
@misc{blain2026socialwarden,
  title={Social Reasoning Warden: Multi-Agent Social Engineering Attack and Defense Between Language Models},
  author={Blain, Scott and Justen, Lennart},
  year={2026},
  note={ERA Project, preliminary results}
}
```
