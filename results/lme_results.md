# Mixed-Effects Model Results

**Social Reasoning Warden — ERA Project**

**Generated**: 2026-02-24 11:05

**Filters**: tag=skeptical_ablation

**Data**: 3,058 observations | 1,539 adversary, 1,519 benign | 11 scenarios | overall SR = 56.0%

**Software**: R lme4 (glmer, binomial) + lmerTest | Wald chi-square tests | Satterthwaite df

---

## Model 2: Dossier Impact

**Formula**: `success ~ adversary_has_data * has_warden + (1|scenario) + (1|profile_name) + (1|target_model)`

**Family**: Binomial (logit link)

**Data**: Adversary runs with profiled targets only

**N** = 1,539 (0 with dossier, 1,539 without) | 11 scenarios | 4 profiles

**Reference levels**: adversary_has_data=0, has_warden=0

### Output

```
--- Data Summary ---
Observations: 1539
With dossier: 0, Without: 1539

Success by condition:
          0         1
0 0.3209524 0.1247444

Cell counts:
                  has_warden
adversary_has_data    0    1
                 0 1050  489

--- Fitting Model 2: Dossier Impact ---
  [Model 2] Error: contrasts can be applied only to factors with 2 or more levels
Loading required package: Matrix
Loading required package: carData
```


---
