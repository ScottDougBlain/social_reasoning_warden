# Mixed-Effects Model Results

**Social Reasoning Warden — ERA Project**

**Generated**: 2026-03-04 11:02

**Data**: 7,670 observations | 5,756 adversary, 1,914 benign | 38 scenarios | overall SR = 42.7%

**Software**: R lme4 (glmer, binomial) + lmerTest | Wald chi-square tests | Satterthwaite df

---

## Model 1: Warden Effectiveness

**Formula**: `success ~ requester_type * has_warden + (1 + has_warden|scenario) + (1|target_model) + (1|requester_model)`

**Family**: Binomial (logit link)

**N** = 7,670 (5,756 adversary, 1,914 benign) | 38 scenarios | 14 target models | 14 requester models

**Overall success rate**: 42.7%

**Reference levels**: requester_type=benign_agent, has_warden=0

### Output

```
--- Data Summary ---
Observations: 7670
Success rate: 42.7%

Success by condition:
                     0         1
benign_agent 0.8676352 0.7718519
adversary    0.4498103 0.1316066

Cell counts:
              has_warden
requester_type    0    1
  benign_agent 1239  675
  adversary    2899 2857

--- Fitting Model 1: Warden Effectiveness ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ requester_type * has_warden + (1 + has_warden | scenario) +  
    (1 | target_model) + (1 | requester_model)
   Data: data

     AIC      BIC   logLik deviance df.resid 
  7266.8   7329.3  -3624.4   7248.8     7661 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-6.5669 -0.5522 -0.2140  0.5487  8.6677 

Random effects:
 Groups          Name        Variance Std.Dev. Corr
 scenario        (Intercept) 0.37375  0.6114       
                 has_warden1 0.25804  0.5080   0.14
 target_model    (Intercept) 0.08718  0.2953       
 requester_model (Intercept) 0.04827  0.2197       
Number of obs: 7670, groups:  
scenario, 38; target_model, 14; requester_model, 14

Fixed effects:
                                    Estimate Std. Error z value Pr(>|z|)    
(Intercept)                          1.71908    0.19972   8.607  < 2e-16 ***
requester_typeadversary             -2.33027    0.09834 -23.696  < 2e-16 ***
has_warden1                         -0.76935    0.17362  -4.431 9.37e-06 ***
requester_typeadversary:has_warden1 -1.29741    0.16265  -7.977 1.50e-15 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) rqstr_ hs_wr1
rqstr_typdv -0.366              
has_warden1 -0.246  0.436       
rqstr_ty:_1  0.237 -0.590 -0.583

--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                            Chisq Df Pr(>Chisq)    
(Intercept)                74.087  1  < 2.2e-16 ***
requester_type            561.478  1  < 2.2e-16 ***
has_warden                 19.637  1  9.365e-06 ***
requester_type:has_warden  63.626  1  1.504e-15 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups          Name        Std.Dev. Corr 
 scenario        (Intercept) 0.61135       
                 has_warden1 0.50797  0.143
 target_model    (Intercept) 0.29527       
 requester_model (Intercept) 0.21970       

--- Odds Ratios (exp of fixed effects) ---
                                            OR  CI_lower  CI_upper
(Intercept)                         5.57940034 3.7721093 8.2525997
requester_typeadversary             0.09726946 0.0802172 0.1179466
has_warden1                         0.46331368 0.3296803 0.6511144
requester_typeadversary:has_warden1 0.27323972 0.1986526 0.3758317
Loading required package: Matrix
Loading required package: carData
```


---

## Model 2: Dossier Impact

**Formula**: `success ~ adversary_has_data * has_warden + (1 + has_warden|scenario) + (1|profile_name) + (1|target_model)`

**Family**: Binomial (logit link)

**Data**: Adversary runs with profiled targets only

**N** = 5,383 (1,257 with dossier, 4,126 without) | 14 scenarios | 9 profiles

**Reference levels**: adversary_has_data=0, has_warden=0

### Output

```
--- Data Summary ---
Observations: 5383
With dossier: 1257, Without: 4126

Success by condition:
          0         1
0 0.4115066 0.1296386
1 0.5259146 0.1198003

Cell counts:
                  has_warden
adversary_has_data    0    1
                 0 2051 2075
                 1  656  601

--- Fitting Model 2: Dossier Impact ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ adversary_has_data * has_warden + (1 + has_warden |  
    scenario) + (1 | profile_name) + (1 | target_model)
   Data: data

     AIC      BIC   logLik deviance df.resid 
  4780.2   4839.5  -2381.1   4762.2     5374 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-3.9685 -0.5090 -0.2750  0.4872 15.0903 

Random effects:
 Groups       Name        Variance Std.Dev. Corr
 scenario     (Intercept) 1.1621   1.0780       
              has_warden1 0.2754   0.5248   0.53
 profile_name (Intercept) 0.2360   0.4858       
 target_model (Intercept) 0.3775   0.6144       
Number of obs: 5383, groups:  scenario, 14; profile_name, 9; target_model, 9

Fixed effects:
                                Estimate Std. Error z value Pr(>|z|)    
(Intercept)                      -0.9599     0.4661  -2.059   0.0395 *  
adversary_has_data1               0.6492     0.1050   6.183 6.31e-10 ***
has_warden1                      -2.1119     0.1984 -10.645  < 2e-16 ***
adversary_has_data1:has_warden1  -0.7537     0.1858  -4.056 5.00e-05 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) adv__1 hs_wr1
advrsry_h_1 -0.109              
has_warden1  0.216  0.123       
advrs__1:_1  0.041 -0.557 -0.219

--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                                 Chisq Df Pr(>Chisq)    
(Intercept)                     4.2411  1    0.03946 *  
adversary_has_data             38.2246  1  6.305e-10 ***
has_warden                    113.3182  1  < 2.2e-16 ***
adversary_has_data:has_warden  16.4482  1  5.000e-05 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name        Std.Dev. Corr 
 scenario     (Intercept) 1.07801       
              has_warden1 0.52479  0.528
 profile_name (Intercept) 0.48578       
 target_model (Intercept) 0.61442       

--- Odds Ratios ---
                                       OR   CI_lower  CI_upper
(Intercept)                     0.3829380 0.15359766 0.9547120
adversary_has_data1             1.9140172 1.55799274 2.3513985
has_warden1                     0.1210084 0.08202468 0.1785198
adversary_has_data1:has_warden1 0.4706095 0.32693969 0.6774134
Loading required package: Matrix
Loading required package: carData
```


---

## Model 3: Profile Vulnerability

**Formula**: `success ~ profile_name * has_warden + (1 + has_warden|scenario) + (1|target_model)`

**Family**: Binomial (logit link)

**Data**: Adversary runs with profiled targets only

**N** = 5,383 | 14 scenarios | 9 profiles

**Profile counts**:

- Authority-Deferential Follower: 1434
- Overwhelmed Time-Pressured: 1426
- Idealistic True Believer: 1220
- Compliant Agreeable: 1169
- Overwhelmed Time-Pressured Worker: 45
- Overconfident Veteran: 39
- Lonely Isolated: 20
- Authority-Deferential Junior Employee: 15
- Lonely Isolated Worker: 15

### Output

```
--- Data Summary ---
Observations: 5383
Profiles: 9, Scenarios: 14
Reference profile: Authority-Deferential Follower

Success rate by profile:
  Idealistic True Believer             31.2%  (n=1220)
  Compliant Agreeable                  29.4%  (n=1169)
  Authority-Deferential Follower       27.9%  (n=1434)
  Authority-Deferential Junior Employee  26.7%  (n=15)
  Overwhelmed Time-Pressured           26.2%  (n=1426)
  Lonely Isolated                      25.0%  (n=20)
  Overwhelmed Time-Pressured Worker    24.4%  (n=45)
  Overconfident Veteran                23.1%  (n=39)
  Lonely Isolated Worker               20.0%  (n=15)

Success by profile x warden:
                                              0          1
Authority-Deferential Follower        0.4327485 0.13866667
Authority-Deferential Junior Employee 0.4444444 0.00000000
Compliant Agreeable                   0.4552846 0.11552347
Idealistic True Believer              0.4899225 0.11304348
Lonely Isolated                       0.5000000 0.00000000
Lonely Isolated Worker                0.2727273 0.00000000
Overconfident Veteran                 0.3500000 0.10526316
Overwhelmed Time-Pressured            0.3889695 0.14246947
Overwhelmed Time-Pressured Worker     0.4166667 0.04761905

--- Fitting Model 3: Profile Vulnerability ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ profile_name * has_warden + (1 + has_warden | scenario) +  
    (1 | target_model)
   Data: data

     AIC      BIC   logLik deviance df.resid 
  4797.8   4942.8  -2376.9   4753.8     5361 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-3.3637 -0.5046 -0.2774  0.5267 13.6561 

Random effects:
 Groups       Name        Variance Std.Dev. Corr
 scenario     (Intercept) 1.1326   1.0642       
              has_warden1 0.3148   0.5610   0.53
 target_model (Intercept) 0.3880   0.6229       
Number of obs: 5383, groups:  scenario, 14; target_model, 9

Fixed effects:
                                                               Estimate
(Intercept)                                                    -0.39881
profile_nameAuthority-Deferential Junior Employee               0.04056
profile_nameCompliant Agreeable                                 0.09315
profile_nameIdealistic True Believer                            0.27426
profile_nameLonely Isolated                                    -0.20518
profile_nameLonely Isolated Worker                             -1.60430
profile_nameOverconfident Veteran                              -0.76134
profile_nameOverwhelmed Time-Pressured                         -0.24875
profile_nameOverwhelmed Time-Pressured Worker                  -0.80963
has_warden1                                                    -2.12879
profile_nameAuthority-Deferential Junior Employee:has_warden1 -13.31853
profile_nameCompliant Agreeable:has_warden1                    -0.41233
profile_nameIdealistic True Believer:has_warden1               -0.58963
profile_nameLonely Isolated:has_warden1                       -13.76692
profile_nameLonely Isolated Worker:has_warden1                -11.18902
profile_nameOverconfident Veteran:has_warden1                  -0.08361
profile_nameOverwhelmed Time-Pressured:has_warden1              0.24305
profile_nameOverwhelmed Time-Pressured Worker:has_warden1      -1.49341
                                                              Std. Error
(Intercept)                                                      0.41659
profile_nameAuthority-Deferential Junior Employee                0.78763
profile_nameCompliant Agreeable                                  0.12724
profile_nameIdealistic True Believer                             0.12567
profile_nameLonely Isolated                                      0.70196
profile_nameLonely Isolated Worker                               0.76669
profile_nameOverconfident Veteran                                0.53863
profile_nameOverwhelmed Time-Pressured                           0.12470
profile_nameOverwhelmed Time-Pressured Worker                    0.46380
has_warden1                                                      0.23538
profile_nameAuthority-Deferential Junior Employee:has_warden1   12.99572
profile_nameCompliant Agreeable:has_warden1                      0.22425
profile_nameIdealistic True Believer:has_warden1                 0.22153
profile_nameLonely Isolated:has_warden1                         10.66797
profile_nameLonely Isolated Worker:has_warden1                  24.28444
profile_nameOverconfident Veteran:has_warden1                    0.97937
profile_nameOverwhelmed Time-Pressured:has_warden1               0.20477
profile_nameOverwhelmed Time-Pressured Worker:has_warden1        1.13651
                                                              z value Pr(>|z|)
(Intercept)                                                    -0.957  0.33840
profile_nameAuthority-Deferential Junior Employee               0.051  0.95893
profile_nameCompliant Agreeable                                 0.732  0.46411
profile_nameIdealistic True Believer                            2.182  0.02908
profile_nameLonely Isolated                                    -0.292  0.77006
profile_nameLonely Isolated Worker                             -2.092  0.03639
profile_nameOverconfident Veteran                              -1.413  0.15752
profile_nameOverwhelmed Time-Pressured                         -1.995  0.04606
profile_nameOverwhelmed Time-Pressured Worker                  -1.746  0.08087
has_warden1                                                    -9.044  < 2e-16
profile_nameAuthority-Deferential Junior Employee:has_warden1  -1.025  0.30544
profile_nameCompliant Agreeable:has_warden1                    -1.839  0.06596
profile_nameIdealistic True Believer:has_warden1               -2.662  0.00778
profile_nameLonely Isolated:has_warden1                        -1.290  0.19688
profile_nameLonely Isolated Worker:has_warden1                 -0.461  0.64498
profile_nameOverconfident Veteran:has_warden1                  -0.085  0.93197
profile_nameOverwhelmed Time-Pressured:has_warden1              1.187  0.23526
profile_nameOverwhelmed Time-Pressured Worker:has_warden1      -1.314  0.18884
                                                                 
(Intercept)                                                      
profile_nameAuthority-Deferential Junior Employee                
profile_nameCompliant Agreeable                                  
profile_nameIdealistic True Believer                          *  
profile_nameLonely Isolated                                      
profile_nameLonely Isolated Worker                            *  
profile_nameOverconfident Veteran                                
profile_nameOverwhelmed Time-Pressured                        *  
profile_nameOverwhelmed Time-Pressured Worker                 .  
has_warden1                                                   ***
profile_nameAuthority-Deferential Junior Employee:has_warden1    
profile_nameCompliant Agreeable:has_warden1                   .  
profile_nameIdealistic True Believer:has_warden1              ** 
profile_nameLonely Isolated:has_warden1                          
profile_nameLonely Isolated Worker:has_warden1                   
profile_nameOverconfident Veteran:has_warden1                    
profile_nameOverwhelmed Time-Pressured:has_warden1               
profile_nameOverwhelmed Time-Pressured Worker:has_warden1        
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                          Chisq Df Pr(>Chisq)    
(Intercept)              0.9165  1  0.3384027    
profile_name            27.5116  8  0.0005766 ***
has_warden              81.7941  1  < 2.2e-16 ***
profile_name:has_warden 22.5650  8  0.0039700 ** 
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name        Std.Dev. Corr 
 scenario     (Intercept) 1.06423       
              has_warden1 0.56103  0.525
 target_model (Intercept) 0.62287       

--- Odds Ratios ---
                                                                        OR
(Intercept)                                                   6.711165e-01
profile_nameAuthority-Deferential Junior Employee             1.041394e+00
profile_nameCompliant Agreeable                               1.097625e+00
profile_nameIdealistic True Believer                          1.315552e+00
profile_nameLonely Isolated                                   8.144968e-01
profile_nameLonely Isolated Worker                            2.010309e-01
profile_nameOverconfident Veteran                             4.670390e-01
profile_nameOverwhelmed Time-Pressured                        7.797740e-01
profile_nameOverwhelmed Time-Pressured Worker                 4.450244e-01
has_warden1                                                   1.189806e-01
profile_nameAuthority-Deferential Junior Employee:has_warden1 1.643758e-06
profile_nameCompliant Agreeable:has_warden1                   6.621073e-01
profile_nameIdealistic True Believer:has_warden1              5.545329e-01
profile_nameLonely Isolated:has_warden1                       1.049795e-06
profile_nameLonely Isolated Worker:has_warden1                1.382514e-05
profile_nameOverconfident Veteran:has_warden1                 9.197889e-01
profile_nameOverwhelmed Time-Pressured:has_warden1            1.275130e+00
profile_nameOverwhelmed Time-Pressured Worker:has_warden1     2.246052e-01
                                                                  CI_lower
(Intercept)                                                   2.966168e-01
profile_nameAuthority-Deferential Junior Employee             2.224231e-01
profile_nameCompliant Agreeable                               8.553608e-01
profile_nameIdealistic True Believer                          1.028339e+00
profile_nameLonely Isolated                                   2.057689e-01
profile_nameLonely Isolated Worker                            4.473551e-02
profile_nameOverconfident Veteran                             1.625049e-01
profile_nameOverwhelmed Time-Pressured                        6.106968e-01
profile_nameOverwhelmed Time-Pressured Worker                 1.793079e-01
has_warden1                                                   7.500997e-02
profile_nameAuthority-Deferential Junior Employee:has_warden1 1.425155e-17
profile_nameCompliant Agreeable:has_warden1                   4.266256e-01
profile_nameIdealistic True Believer:has_warden1              3.592192e-01
profile_nameLonely Isolated:has_warden1                       8.719849e-16
profile_nameLonely Isolated Worker:has_warden1                2.949302e-26
profile_nameOverconfident Veteran:has_warden1                 1.349096e-01
profile_nameOverwhelmed Time-Pressured:has_warden1            8.535979e-01
profile_nameOverwhelmed Time-Pressured Worker:has_warden1     2.421146e-02
                                                                  CI_upper
(Intercept)                                                   1.518448e+00
profile_nameAuthority-Deferential Junior Employee             4.875853e+00
profile_nameCompliant Agreeable                               1.408507e+00
profile_nameIdealistic True Believer                          1.682982e+00
profile_nameLonely Isolated                                   3.224030e+00
profile_nameLonely Isolated Worker                            9.033858e-01
profile_nameOverconfident Veteran                             1.342270e+00
profile_nameOverwhelmed Time-Pressured                        9.956618e-01
profile_nameOverwhelmed Time-Pressured Worker                 1.104506e+00
has_warden1                                                   1.887268e-01
profile_nameAuthority-Deferential Junior Employee:has_warden1 1.895891e+05
profile_nameCompliant Agreeable:has_warden1                   1.027566e+00
profile_nameIdealistic True Believer:has_warden1              8.560421e-01
profile_nameLonely Isolated:has_warden1                       1.263863e+03
profile_nameLonely Isolated Worker:has_warden1                6.480664e+15
profile_nameOverconfident Veteran:has_warden1                 6.270951e+00
profile_nameOverwhelmed Time-Pressured:has_warden1            1.904827e+00
profile_nameOverwhelmed Time-Pressured Worker:has_warden1     2.083620e+00
Loading required package: Matrix
Loading required package: carData

Correlation matrix not shown by default, as p = 18 > 12.
Use print(summary(m3), correlation=TRUE)  or
    vcov(summary(m3))        if you need it
```


---

## Model 4: Capability Asymmetry

**Formula**: `success ~ warden_tier + (1|model_family) + (1 + warden_tier|scenario) + (1|profile_name)`

**Family**: Binomial (logit link)

**Data**: Adversary runs only (cap_asym study)

**N** = 5,756 | 7 model families | 38 scenarios | 10 profiles

**Reference level**: warden_tier=none

**Warden tier counts**:

- none: 2899
- weak: 302
- mid: 1987
- strong: 568

### Output

```
--- Data Summary ---
Observations: 5756
Model families: 7
Scenarios: 38, Profiles: 10
Overall success rate: 29.2%

Runs by warden tier:

  none   weak    mid strong 
  2899    302   1987    568 

Success rate by warden tier:
  none        45.0%  (n=2899)
  weak        18.5%  (n=302)
  mid         11.4%  (n=1987)
  strong      16.4%  (n=568)

Success rate by model_family x warden_tier:
         none          weak         mid           strong       
claude   "38% (n=82)"  NA           "7% (n=56)"   "38% (n=13)" 
deepseek "0% (n=1)"    NA           NA            NA           
gemini   "70% (n=812)" "25% (n=75)" "14% (n=465)" "14% (n=287)"
gemma    "37% (n=747)" "18% (n=76)" "14% (n=533)" "16% (n=76)" 
gpt      "40% (n=42)"  NA           NA            "36% (n=42)" 
llama    "35% (n=604)" "16% (n=75)" "15% (n=484)" "24% (n=74)" 
mistral  "34% (n=611)" "14% (n=76)" "2% (n=449)"  "4% (n=76)"  

--- Fitting Model 4: Capability Asymmetry ---
  [Model 4] Default optimizer warning: Model failed to converge with max|grad| = 0.0173117 (tol = 0.002, component 1)
  [Model 4] Retrying with bobyqa...

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ warden_tier + (1 | model_family) + (1 + warden_tier |  
    scenario) + (1 | profile_name)
   Data: data
Control: glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e+05))

     AIC      BIC   logLik deviance df.resid 
  5229.9   5336.4  -2599.0   5197.9     5740 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-3.0786 -0.5205 -0.2788  0.5673 12.1826 

Random effects:
 Groups       Name              Variance Std.Dev. Corr             
 scenario     (Intercept)       0.94029  0.9697                    
              warden_tierweak   0.06864  0.2620   -0.03            
              warden_tiermid    0.27471  0.5241    0.51  0.84      
              warden_tierstrong 0.42879  0.6548    0.63  0.76  0.99
 profile_name (Intercept)       0.01906  0.1381                    
 model_family (Intercept)       0.27806  0.5273                    
Number of obs: 5756, groups:  scenario, 38; profile_name, 10; model_family, 7

Fixed effects:
                  Estimate Std. Error z value Pr(>|z|)    
(Intercept)        -0.1328     0.3043  -0.436    0.663    
warden_tierweak    -1.5258     0.2001  -7.625 2.43e-14 ***
warden_tiermid     -2.3937     0.1771 -13.517  < 2e-16 ***
warden_tierstrong  -2.3176     0.2339  -9.908  < 2e-16 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) wrdn_trw wrdn_trm
warden_trwk -0.051                  
warden_trmd  0.116  0.304           
wrdn_trstrn  0.083  0.184    0.426  
optimizer (bobyqa) convergence code: 0 (OK)
boundary (singular) fit: see help('isSingular')


--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
               Chisq Df Pr(>Chisq)    
(Intercept)   0.1903  1     0.6626    
warden_tier 215.3275  3     <2e-16 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name              Std.Dev. Corr                
 scenario     (Intercept)       0.96969                      
              warden_tierweak   0.26200  -0.029              
              warden_tiermid    0.52413   0.514  0.842       
              warden_tierstrong 0.65482   0.632  0.756  0.990
 profile_name (Intercept)       0.13807                      
 model_family (Intercept)       0.52731                      

--- Odds Ratios (exp of fixed effects) ---
                          OR   CI_lower  CI_upper
(Intercept)       0.87567104 0.48229231 1.5899067
warden_tierweak   0.21745378 0.14690888 0.3218740
warden_tiermid    0.09128821 0.06451674 0.1291686
warden_tierstrong 0.09850740 0.06228182 0.1558032

--- Linear Trend Test (ordered warden_tier) ---
Linear slope for warden tier (0=none -> 3=strong):
                  Estimate Std. Error    z value     Pr(>|z|)
(Intercept)      0.9385306 0.29247433   3.208933 1.332284e-03
warden_tier_ord -0.9929893 0.08078069 -12.292410 9.949549e-35

OR per tier increase: 0.370
Loading required package: Matrix
Loading required package: carData
boundary (singular) fit: see help('isSingular')
```
