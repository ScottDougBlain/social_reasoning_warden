# Mixed-Effects Model Results

**Social Reasoning Warden — ERA Project**

**Generated**: 2026-02-19 14:22

**Filters**: tag=cap_asym

**Data**: 1,207 observations | 1,207 adversary, 0 benign | 11 scenarios | overall SR = 23.5%

**Software**: R lme4 (glmer, binomial) + lmerTest | Wald chi-square tests | Satterthwaite df

---

## Model 4: Capability Asymmetry

**Formula**: `success ~ warden_tier + (1|model_family) + (1|scenario) + (1|profile_name)`

**Family**: Binomial (logit link)

**Data**: Adversary runs only (cap_asym study)

**N** = 1,207 | 4 model families | 11 scenarios | 4 profiles

**Reference level**: warden_tier=none

**Warden tier counts**:

- none: 303
- weak: 302
- mid: 302
- strong: 300

### Output

```
--- Data Summary ---
Observations: 1207
Model families: 4
Scenarios: 11, Profiles: 4
Overall success rate: 23.5%

Runs by warden tier:

  none   weak    mid strong 
   303    302    302    300 

Success rate by warden tier:
  none        48.5%  (n=303)
  weak        18.5%  (n=302)
  mid         11.6%  (n=302)
  strong      15.3%  (n=300)

Success rate by model_family x warden_tier:
        none         weak         mid          strong      
gemini  "80% (n=75)" "25% (n=75)" "13% (n=75)" "18% (n=74)"
gemma   "43% (n=76)" "18% (n=76)" "13% (n=76)" "16% (n=76)"
llama   "38% (n=76)" "16% (n=75)" "18% (n=76)" "24% (n=74)"
mistral "33% (n=76)" "14% (n=76)" "1% (n=75)"  "4% (n=76)" 

--- Fitting Model 4: Capability Asymmetry ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ warden_tier + (1 | model_family) + (1 | scenario) +  
    (1 | profile_name)
   Data: data

     AIC      BIC   logLik deviance df.resid 
  1035.7   1071.4   -510.8   1021.7     1200 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-2.9121 -0.4755 -0.2717 -0.0988  7.8130 

Random effects:
 Groups       Name        Variance Std.Dev.
 scenario     (Intercept) 1.256878 1.1211  
 profile_name (Intercept) 0.003894 0.0624  
 model_family (Intercept) 0.362317 0.6019  
Number of obs: 1207, groups:  scenario, 11; profile_name, 4; model_family, 4

Fixed effects:
                  Estimate Std. Error z value Pr(>|z|)    
(Intercept)       -0.05617    0.47307  -0.119    0.905    
warden_tierweak   -1.79102    0.21498  -8.331   <2e-16 ***
warden_tiermid    -2.43823    0.24147 -10.098   <2e-16 ***
warden_tierstrong -2.05346    0.22477  -9.136   <2e-16 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) wrdn_trw wrdn_trm
warden_trwk -0.169                  
warden_trmd -0.151  0.407           
wrdn_trstrn -0.162  0.427    0.396  

--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
               Chisq Df Pr(>Chisq)    
(Intercept)   0.0141  1     0.9055    
warden_tier 142.2762  3     <2e-16 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name        Std.Dev.
 scenario     (Intercept) 1.121106
 profile_name (Intercept) 0.062402
 model_family (Intercept) 0.601928

--- Odds Ratios (exp of fixed effects) ---
                          OR   CI_lower  CI_upper
(Intercept)       0.94537498 0.37404371 2.3893834
warden_tierweak   0.16678922 0.10944038 0.2541899
warden_tiermid    0.08731525 0.05439445 0.1401605
warden_tierstrong 0.12828989 0.08257850 0.1993049

--- Linear Trend Test (ordered warden_tier) ---
Linear slope for warden tier (0=none -> 3=strong):
                  Estimate Std. Error    z value     Pr(>|z|)
(Intercept)      0.3227302 0.46053137  0.7007778 4.834417e-01
warden_tier_ord -0.7638159 0.07640516 -9.9969145 1.572194e-23

OR per tier increase: 0.466
Loading required package: Matrix
Loading required package: carData
```
