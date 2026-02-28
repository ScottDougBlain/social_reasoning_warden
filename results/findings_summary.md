# Social Reasoning Warden — Key Findings Summary

**ERA Project | February 2026**
**Total observations: 7,760 across 3 main studies + exploratory runs**

---

## Study 1: Warden Effectiveness & Dossier Impact (N = 2,274)

**Design**: 2 (dossier: yes/no) x 2 (warden: yes/no) factorial, adversary-only, 11 scenarios, 4 profiles, 4 model families.

| Condition | Adversary SR | 95% CI |
|---|---|---|
| No warden, no dossier | 50.9% | [46.9 - 55.0] |
| No warden, dossier | 53.3% | [49.3 - 57.3] |
| Warden, no dossier | 9.8% | [7.6 - 12.5] |
| Warden, dossier | 12.5% | [10.0 - 15.6] |

**GLME** (binomial logit, random effects for scenario, profile, target model):
- **Warden**: OR = 0.053, p < .001 — reduces adversary success by ~95%
- **Dossier**: OR = 1.19, p = .218 — no significant effect
- **Dossier x Warden interaction**: OR = 1.16, p = .562 — no interaction

**Interpretation**: The warden is overwhelmingly effective. Dossiers, however, show no benefit — models don't spontaneously leverage behavioral information. The bottleneck appears to be instruction-following/attention rather than capability. *(See Fig 1, Fig 2)*

---

## Study 2: Capability Asymmetry (N = 1,215)

**Design**: 4 warden tiers (none / weak=target / mid / strong=adversary), adversary-only, 11 scenarios, 4 model families.

| Warden Tier | Adversary SR | 95% CI |
|---|---|---|
| None (no warden) | 48.4% | [42.8 - 54.0] |
| Weak (= target model) | 18.5% | [14.5 - 23.2] |
| Mid (independent) | 11.5% | [8.4 - 15.6] |
| Strong (= adversary model) | 15.1% | [11.5 - 19.6] |

**GLME** (binomial logit, random effects for scenario, profile, model family):
- **Warden tier (ordered)**: OR = 0.47 per tier step, p < .001
- Weak vs none: OR = 0.17; Mid vs none: OR = 0.09; Strong vs none: OR = 0.13

**Interpretation**: Even a "weak" warden (same capability as the target) cuts adversary success by 62%. Diminishing returns beyond mid-tier. Notably, "strong" wardens (adversary-level) are slightly less effective than mid-tier — possibly because matched-family models share similar blindspots. *(See Fig 3)*

---

## Study 3: Skeptical Ablation (N = 3,080)

**Design**: 3 defense conditions (baseline / skeptical prompt / warden agent) x 2 requester types (adversary / benign), 11 scenarios, 4 profiles, 4 model families.

| Defense | Adversary SR | Benign SR | FP Cost |
|---|---|---|---|
| Baseline (no defense) | 50.5% [46.2 - 54.7] | 92.0% [89.4 - 94.0] | — |
| Skeptical (prompt-based) | 13.4% [10.7 - 16.5] | 87.6% [84.5 - 90.2] | -4.4pp |
| Warden (agent-based) | 12.3% [9.7 - 15.5] | 78.1% [74.3 - 81.6] | -13.9pp |

**Interpretation**: Prompt-based skepticism achieves comparable adversary suppression to the warden agent (13.4% vs 12.3%) but with **3x lower false positive cost** (4.4pp vs 13.9pp benign success penalty). This is the key tradeoff: the warden blocks adversaries well but is trigger-happy with legitimate requests. *(See Fig 4)*

---

## Cross-Cutting Findings

### Model Family Variation (adversary, no warden, pooled)
| Family | SR | 95% CI | N |
|---|---|---|---|
| Gemini | 69.0% | [65.2 - 72.6] | 603 |
| Gemma | 36.6% | [33.2 - 40.2] | 737 |
| Llama | 34.9% | [31.2 - 38.8] | 593 |
| Mistral | 33.6% | [29.9 - 37.4] | 599 |

Gemini-family models are roughly 2x more effective adversaries than other families. *(See Fig 5)*

### Scenario Variation (adversary, no warden, pooled)

Highest SR: ai_override (75.8%), file_access (75.5%)
Lowest SR: automation_decision (12.3%), ai_containment (15.3%)

~6x range in baseline adversary success across scenarios — scenario design is a major moderator. *(See Fig 6)*

### Warden False Positive Analysis

Concentrated in scenarios where adversary and benign requests look similar:
- file_access_password: 77.3% FP rate
- file_access: 50.0% FP rate
- coding_agent: 48.9% FP rate

Frontier wardens (GPT-4o, Claude Sonnet, Gemini Flash Preview) show 0% FP. Mid-tier open models show 10-25% FP. *(See Fig 7)*

---

## Figures

All in `results/figures/`:

| # | File | Content |
|---|---|---|
| 1 | `fig1_warden_effect.png` | Warden effect bar chart (OR = 0.053) |
| 2 | `fig2_dossier_interaction.png` | Dossier x warden 2x2 interaction |
| 3 | `fig3_capability_asymmetry.png` | Adversary SR by warden tier |
| 4 | `fig4_skeptical_ablation.png` | 3 conditions x 2 requester types |
| 5 | `fig5_model_family.png` | Adversary SR by model family |
| 6 | `fig6_scenario_variation.png` | Adversary SR by scenario (horizontal) |
| 7 | `fig7_warden_fp_by_scenario.png` | Warden FP cost paired dot plot |

---

## GLME Model Specifications

All models: binomial family, logit link, fit via `glmer` (lme4). Wald chi-square tests.

| Model | DV | Fixed | Random | Tag |
|---|---|---|---|---|
| Dossier Impact | success | adversary_has_data * has_warden | scenario, profile, target_model | dossier_effect |
| Cap Asymmetry | success | warden_tier (ordered) | scenario, profile, model_family | cap_asym |

---

## Key Takeaways for Write-Up

1. **Wardens work** — 95% reduction in adversary success (OR = 0.053), robust across scenarios and model families.
2. **Dossiers don't help (yet)** — giving adversaries behavioral intel has no effect (OR = 1.19, NS). Models fail to spontaneously use profile information; explicit priming may be needed.
3. **Even weak wardens help** — a target-capability warden still cuts adversary success by 62%. Diminishing returns suggest mid-tier is the cost-effective sweet spot.
4. **Prompt-based defense is competitive** — skepticism instructions match warden effectiveness with 3x lower FP cost. The warden's value-add is in scenarios where adversary tactics are highly adaptive.
5. **Scenario design is a major moderator** — 6x variation in baseline success rates. Hardest to defend: ai_override, file_access. Easiest: ai_containment, automation_decision.
6. **Model family matters** — Gemini adversaries are 2x more effective than Gemma/Llama/Mistral.
7. **Warden FP is concentrated** — 3 scenarios account for most false positives. Frontier-tier wardens show 0% FP; mid-tier open models are the bottleneck.
