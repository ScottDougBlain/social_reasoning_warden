# Mixed-Effects Model Results

**Social Reasoning Warden — ERA Project**

**Generated**: 2026-03-04 15:31

**Filters**: tag=dossier_effect

**Data**: 2,259 observations | 2,259 adversary, 0 benign | 11 scenarios | overall SR = 32.4%

**Software**: R lme4 (glmer, binomial) + lmerTest | Wald chi-square tests | Satterthwaite df

---

## Model 1: Warden Effectiveness

**Formula**: `success ~ requester_type * has_warden + (1 + has_warden|scenario) + (1|target_model) + (1|requester_model)`

**Family**: Binomial (logit link)

**N** = 2,259 (2,259 adversary, 0 benign) | 11 scenarios | 4 target models | 4 requester models

**Overall success rate**: 32.4%

**Reference levels**: requester_type=benign_agent, has_warden=0

### Output

```
Loading required package: Matrix
Loading required package: carData
Error in relevel.factor(factor(d$requester_type), ref = "benign_agent") : 
  'ref' must be an existing level
Calls: relevel -> relevel.factor
Execution halted
```


---

## Model 2: Dossier Impact

**Formula**: `success ~ adversary_has_data * has_warden + (1 + has_warden|scenario) + (1|profile_name) + (1|target_model)`

**Family**: Binomial (logit link)

**Data**: Adversary runs with profiled targets only

**N** = 2,259 (1,124 with dossier, 1,135 without) | 11 scenarios | 4 profiles

**Reference levels**: adversary_has_data=0, has_warden=0

### Output

```
--- Data Summary ---
Observations: 2259
With dossier: 1124, Without: 1135

Success by condition:
          0          1
0 0.5129983 0.09856631
1 0.5349233 0.12662942

Cell counts:
                  has_warden
adversary_has_data   0   1
                 0 577 558
                 1 587 537

--- Fitting Model 2: Dossier Impact ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ adversary_has_data * has_warden + (1 + has_warden |  
    scenario) + (1 | profile_name) + (1 | target_model)
   Data: data

     AIC      BIC   logLik deviance df.resid 
  1912.9   1964.4   -947.5   1894.9     2250 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-4.9857 -0.4770 -0.2017  0.4129 10.7608 

Random effects:
 Groups       Name        Variance Std.Dev. Corr
 scenario     (Intercept) 1.66550  1.2905       
              has_warden1 0.35494  0.5958   0.04
 profile_name (Intercept) 0.03843  0.1960       
 target_model (Intercept) 0.66359  0.8146       
Number of obs: 2259, groups:  scenario, 11; profile_name, 4; target_model, 4

Fixed effects:
                                Estimate Std. Error z value Pr(>|z|)    
(Intercept)                      0.06608    0.58072   0.114    0.909    
adversary_has_data1              0.17026    0.14010   1.215    0.224    
has_warden1                     -3.06725    0.30025 -10.216   <2e-16 ***
adversary_has_data1:has_warden1  0.14440    0.25211   0.573    0.567    
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) adv__1 hs_wr1
advrsry_h_1 -0.122              
has_warden1 -0.045  0.232       
advrs__1:_1  0.068 -0.555 -0.449

--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                                 Chisq Df Pr(>Chisq)    
(Intercept)                     0.0129  1     0.9094    
adversary_has_data              1.4768  1     0.2243    
has_warden                    104.3583  1     <2e-16 ***
adversary_has_data:has_warden   0.3281  1     0.5668    
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name        Std.Dev. Corr 
 scenario     (Intercept) 1.29054       
              has_warden1 0.59577  0.036
 profile_name (Intercept) 0.19604       
 target_model (Intercept) 0.81461       

--- Odds Ratios ---
                                      OR   CI_lower   CI_upper
(Intercept)                     1.068310 0.34228687 3.33429609
adversary_has_data1             1.185612 0.90092257 1.56026266
has_warden1                     0.046549 0.02584256 0.08384655
adversary_has_data1:has_warden1 1.155342 0.70488512 1.89366420
Loading required package: Matrix
Loading required package: carData
```


---

## Model 3: Profile Vulnerability

**Formula**: `success ~ profile_name * has_warden + (1 + has_warden|scenario) + (1|target_model)`

**Family**: Binomial (logit link)

**Data**: Adversary runs with profiled targets only

**N** = 2,259 | 11 scenarios | 4 profiles

**Profile counts**:

- Overwhelmed Time-Pressured: 597
- Idealistic True Believer: 582
- Authority-Deferential Follower: 567
- Compliant Agreeable: 513

### Output

```
--- Data Summary ---
Observations: 2259
Profiles: 4, Scenarios: 11
Reference profile: Overwhelmed Time-Pressured

Success rate by profile:
  Idealistic True Believer             36.6%  (n=582)
  Compliant Agreeable                  33.1%  (n=513)
  Authority-Deferential Follower       30.3%  (n=567)
  Overwhelmed Time-Pressured           29.8%  (n=597)

Success by profile x warden:
                                       0          1
Overwhelmed Time-Pressured     0.4715719 0.12416107
Authority-Deferential Follower 0.4778157 0.11678832
Compliant Agreeable            0.5313653 0.10743802
Idealistic True Believer       0.6146179 0.09964413

--- Fitting Model 3: Profile Vulnerability ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ profile_name * has_warden + (1 + has_warden | scenario) +  
    (1 | target_model)
   Data: data

     AIC      BIC   logLik deviance df.resid 
  1902.5   1971.2   -939.3   1878.5     2247 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-4.9901 -0.4692 -0.2058  0.4282  8.6428 

Random effects:
 Groups       Name        Variance Std.Dev. Corr
 scenario     (Intercept) 1.7104   1.308        
              has_warden1 0.3588   0.599    0.00
 target_model (Intercept) 0.6724   0.820        
Number of obs: 2259, groups:  scenario, 11; target_model, 4

Fixed effects:
                                                       Estimate Std. Error
(Intercept)                                            -0.16180    0.58587
profile_nameAuthority-Deferential Follower              0.05237    0.19633
profile_nameCompliant Agreeable                         0.36247    0.20091
profile_nameIdealistic True Believer                    0.85311    0.19858
has_warden1                                            -2.50940    0.33344
profile_nameAuthority-Deferential Follower:has_warden1 -0.16818    0.34313
profile_nameCompliant Agreeable:has_warden1            -0.63650    0.35888
profile_nameIdealistic True Believer:has_warden1       -1.15687    0.35068
                                                       z value Pr(>|z|)    
(Intercept)                                             -0.276 0.782418    
profile_nameAuthority-Deferential Follower               0.267 0.789660    
profile_nameCompliant Agreeable                          1.804 0.071208 .  
profile_nameIdealistic True Believer                     4.296 1.74e-05 ***
has_warden1                                             -7.526 5.24e-14 ***
profile_nameAuthority-Deferential Follower:has_warden1  -0.490 0.624037    
profile_nameCompliant Agreeable:has_warden1             -1.774 0.076134 .  
profile_nameIdealistic True Believer:has_warden1        -3.299 0.000971 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) pr_A-DF prf_CA pr_ITB hs_wr1 p_A-DF: p_CA:_
prfl_nmA-DF -0.166                                            
prfl_nmCmpA -0.163  0.483                                     
prfl_nmIdTB -0.165  0.489   0.484                             
has_warden1 -0.097  0.291   0.283  0.283                      
prf_A-DF:_1  0.094 -0.572  -0.276 -0.281 -0.486               
prfl_nCA:_1  0.090 -0.270  -0.559 -0.273 -0.459  0.456        
prfl_ITB:_1  0.093 -0.277  -0.274 -0.567 -0.468  0.466   0.449

--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                          Chisq Df Pr(>Chisq)    
(Intercept)              0.0763  1   0.782418    
profile_name            23.0293  3  3.982e-05 ***
has_warden              56.6371  1  5.241e-14 ***
profile_name:has_warden 12.8230  3   0.005035 ** 
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name        Std.Dev. Corr 
 scenario     (Intercept) 1.30782       
              has_warden1 0.59897  0.005
 target_model (Intercept) 0.82000       

--- Odds Ratios ---
                                                               OR   CI_lower
(Intercept)                                            0.85061148 0.26979631
profile_nameAuthority-Deferential Follower             1.05376636 0.71718373
profile_nameCompliant Agreeable                        1.43686693 0.96918083
profile_nameIdealistic True Believer                   2.34694326 1.59025772
has_warden1                                            0.08131707 0.04230153
profile_nameAuthority-Deferential Follower:has_warden1 0.84520036 0.43140486
profile_nameCompliant Agreeable:has_warden1            0.52914020 0.26187256
profile_nameIdealistic True Believer:has_warden1       0.31446917 0.15815273
                                                        CI_upper
(Intercept)                                            2.6818005
profile_nameAuthority-Deferential Follower             1.5483111
profile_nameCompliant Agreeable                        2.1302388
profile_nameIdealistic True Believer                   3.4636793
has_warden1                                            0.1563174
profile_nameAuthority-Deferential Follower:has_warden1 1.6559008
profile_nameCompliant Agreeable:has_warden1            1.0691817
profile_nameIdealistic True Believer:has_warden1       0.6252871
Loading required package: Matrix
Loading required package: carData
```


---
