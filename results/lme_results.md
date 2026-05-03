# Mixed-Effects Model Results

**Social Reasoning Warden — ERA Project**

**Generated**: 2026-05-03 18:20

**Filters**: tag=final-within-family

**Data**: 9,399 observations | 6,263 adversary, 3,136 benign | 14 scenarios | overall SR = 38.5%

**Software**: R lme4 (glmer, binomial) + lmerTest | Wald chi-square tests | Satterthwaite df

---

## Model 1: Warden Effectiveness

**Formula**: `success ~ requester_type * has_warden + (1 + has_warden|scenario) + (1|profile_name) + (1|model_family)`

**Family**: Binomial (logit link)

**N** = 9,399 (6,263 adversary, 3,136 benign) | 14 scenarios | 8 profiles | 7 model families

**Overall success rate**: 38.5%

**Reference levels**: requester_type=benign_agent, has_warden=0

### Output

```
--- Data Summary ---
Observations: 9399
Success rate: 38.5%

Success by condition:
                     0         1
benign_agent 0.9081633 0.7597789
adversary    0.3467433 0.1234831

Cell counts:
              has_warden
requester_type    0    1
  benign_agent  784 2352
  adversary    1566 4697

--- Fitting Model 1: Warden Effectiveness ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ requester_type * has_warden + (1 + has_warden | scenario) +  
    (1 | profile_name) + (1 | model_family)
   Data: data

      AIC       BIC    logLik -2*log(L)  df.resid 
   7300.9    7365.3   -3641.5    7282.9      9390 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-9.9000 -0.4455 -0.1789  0.3448 15.1229 

Random effects:
 Groups       Name        Variance Std.Dev. Corr 
 scenario     (Intercept) 0.57410  0.7577        
              has_warden1 1.08258  1.0405   -0.04
 profile_name (Intercept) 0.03888  0.1972        
 model_family (Intercept) 0.22637  0.4758        
Number of obs: 9399, groups:  scenario, 14; profile_name, 8; model_family, 7

Fixed effects:
                                    Estimate Std. Error z value Pr(>|z|)    
(Intercept)                           2.5942     0.3095   8.382  < 2e-16 ***
requester_typeadversary              -3.3365     0.1481 -22.535  < 2e-16 ***
has_warden1                          -1.0557     0.3136  -3.366 0.000763 ***
requester_typeadversary:has_warden1  -0.7290     0.1726  -4.224  2.4e-05 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) rqstr_ hs_wr1
rqstr_typdv -0.393              
has_warden1 -0.203  0.385       
rqstr_ty:_1  0.333 -0.845 -0.407

--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                            Chisq Df Pr(>Chisq)    
(Intercept)                70.253  1  < 2.2e-16 ***
requester_type            507.831  1  < 2.2e-16 ***
has_warden                 11.329  1  0.0007629 ***
requester_type:has_warden  17.845  1  2.396e-05 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name        Std.Dev. Corr  
 scenario     (Intercept) 0.75770        
              has_warden1 1.04047  -0.040
 profile_name (Intercept) 0.19717        
 model_family (Intercept) 0.47579        

--- Odds Ratios (exp of fixed effects) ---
                                             OR   CI_lower    CI_upper
(Intercept)                         13.38550350 7.29766825 24.55191137
requester_typeadversary              0.03556076 0.02660379  0.04753337
has_warden1                          0.34794695 0.18816403  0.64341248
requester_typeadversary:has_warden1  0.48237739 0.34394417  0.67652825
Loading required package: Matrix
Warning messages:
1: package ‘lme4’ was built under R version 4.4.3 
2: package ‘Matrix’ was built under R version 4.4.3 
Loading required package: carData
Warning messages:
1: package ‘car’ was built under R version 4.4.3 
2: package ‘carData’ was built under R version 4.4.3
```


---

## Model 2: Dossier Impact

**Formula**: `success ~ adversary_has_data * has_warden + (1 + has_warden|scenario) + (1|profile_name) + (1|target_model)`

**Family**: Binomial (logit link)

**Data**: Adversary runs with profiled targets only

**N** = 6,263 (3,134 with dossier, 3,129 without) | 14 scenarios | 8 profiles

**Reference levels**: adversary_has_data=0, has_warden=0

### Output

```
--- Data Summary ---
Observations: 6263
With dossier: 3134, Without: 3129

Success by condition:
          0         1
0 0.3384419 0.1248934
1 0.3550447 0.1220757

Cell counts:
                  has_warden
adversary_has_data    0    1
                 0  783 2346
                 1  783 2351

--- Fitting Model 2: Dossier Impact ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ adversary_has_data * has_warden + (1 + has_warden |  
    scenario) + (1 | profile_name) + (1 | target_model)
   Data: data

      AIC       BIC    logLik -2*log(L)  df.resid 
   4330.0    4390.7   -2156.0    4312.0      6254 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-2.2636 -0.4334 -0.1788 -0.0464 30.7038 

Random effects:
 Groups       Name        Variance Std.Dev. Corr
 scenario     (Intercept) 1.5929   1.2621       
              has_warden1 0.7443   0.8627   0.72
 profile_name (Intercept) 0.1021   0.3196       
 target_model (Intercept) 0.3795   0.6160       
Number of obs: 6263, groups:  scenario, 14; profile_name, 8; target_model, 7

Fixed effects:
                                Estimate Std. Error z value Pr(>|z|)    
(Intercept)                     -0.95915    0.43544  -2.203   0.0276 *  
adversary_has_data1              0.09795    0.12183   0.804   0.4214    
has_warden1                     -2.12764    0.27963  -7.609 2.76e-14 ***
adversary_has_data1:has_warden1 -0.12800    0.15736  -0.813   0.4160    
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) adv__1 hs_wr1
advrsry_h_1 -0.142              
has_warden1  0.392  0.221       
advrs__1:_1  0.110 -0.774 -0.282

--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                                Chisq Df Pr(>Chisq)    
(Intercept)                    4.8519  1    0.02762 *  
adversary_has_data             0.6463  1    0.42142    
has_warden                    57.8950  1  2.765e-14 ***
adversary_has_data:has_warden  0.6616  1    0.41599    
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name        Std.Dev. Corr 
 scenario     (Intercept) 1.26210       
              has_warden1 0.86271  0.717
 profile_name (Intercept) 0.31955       
 target_model (Intercept) 0.61605       

--- Odds Ratios ---
                                       OR   CI_lower  CI_upper
(Intercept)                     0.3832180 0.16322912 0.8996925
adversary_has_data1             1.1029033 0.86863189 1.4003580
has_warden1                     0.1191183 0.06885895 0.2060612
adversary_has_data1:has_warden1 0.8798547 0.64634362 1.1977288
Loading required package: Matrix
Warning messages:
1: package ‘lme4’ was built under R version 4.4.3 
2: package ‘Matrix’ was built under R version 4.4.3 
Loading required package: carData
Warning messages:
1: package ‘car’ was built under R version 4.4.3 
2: package ‘carData’ was built under R version 4.4.3
```


---

## Model 3: Profile Vulnerability

**Formula**: `success ~ profile_name * has_warden + (1 + has_warden|scenario) + (1|target_model)`

**Family**: Binomial (logit link)

**Data**: Adversary runs with profiled targets only

**N** = 6,263 | 14 scenarios | 8 profiles

**Profile counts**:

- E=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH: 784
- E=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM: 784
- E=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM: 783
- E=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW: 783
- E=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH: 783
- E=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM: 782
- E=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM: 782
- E=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW: 782

### Output

```
--- Data Summary ---
Observations: 6263
Profiles: 8, Scenarios: 14
Reference profile: E=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM

Success rate by profile:
  E=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM  24.5%  (n=783)
  E=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM  21.6%  (n=782)
  E=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH  19.8%  (n=784)
  E=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH  17.1%  (n=783)
  E=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM  16.2%  (n=784)
  E=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW  16.0%  (n=782)
  E=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM  14.2%  (n=782)
  E=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW  14.0%  (n=783)

Success by profile x warden:
                                                        0         1
E=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM    0.2959184 0.1173469
E=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM   0.5000000 0.1601363
E=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM       0.2717949 0.0988075
E=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH      0.2908163 0.1311755
E=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW     0.3179487 0.1073254
E=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM 0.4693878 0.1313993
E=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH       0.3826531 0.1360544
E=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW  0.2448980 0.1056218

--- Fitting Model 3: Profile Vulnerability ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ profile_name * has_warden + (1 + has_warden | scenario) +  
    (1 | target_model)
   Data: data

      AIC       BIC    logLik -2*log(L)  df.resid 
   4309.2    4444.0   -2134.6    4269.2      6243 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-2.6880 -0.4311 -0.1764 -0.0454 30.8239 

Random effects:
 Groups       Name        Variance Std.Dev. Corr
 scenario     (Intercept) 1.6853   1.2982       
              has_warden1 0.6891   0.8301   0.69
 target_model (Intercept) 0.3841   0.6198       
Number of obs: 6263, groups:  scenario, 14; target_model, 7

Fixed effects:
                                                                        Estimate
(Intercept)                                                             -1.21928
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM                1.16370
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                   -0.16150
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                  -0.03187
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                  0.12892
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM              0.99477
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                    0.51209
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW              -0.33193
has_warden1                                                             -1.92657
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1   -0.70388
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1       -0.07849
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1       0.18980
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1     -0.25610
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1 -0.83686
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1       -0.29793
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1   0.18270
                                                                        Std. Error
(Intercept)                                                                0.45666
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM                  0.24544
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                      0.25391
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                     0.25162
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                    0.24950
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM                0.24486
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                      0.24572
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW                 0.25742
has_warden1                                                                0.33796
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1      0.31158
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1          0.32856
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1         0.32020
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1        0.32305
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1    0.31488
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1          0.31478
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1     0.32956
                                                                        z value
(Intercept)                                                              -2.670
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM                 4.741
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                    -0.636
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                   -0.127
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                   0.517
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM               4.063
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                     2.084
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW               -1.289
has_warden1                                                              -5.701
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1    -2.259
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1        -0.239
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1        0.593
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1      -0.793
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1  -2.658
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1        -0.946
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1    0.554
                                                                        Pr(>|z|)
(Intercept)                                                              0.00759
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM               2.12e-06
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                    0.52475
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                   0.89921
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                  0.60536
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM             4.85e-05
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                    0.03716
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW               0.19724
has_warden1                                                             1.19e-08
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1    0.02388
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1        0.81119
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1       0.55334
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1      0.42793
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1  0.00787
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1        0.34391
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1   0.57933
                                                                           
(Intercept)                                                             ** 
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM               ***
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                      
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                     
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                    
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM             ***
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                   *  
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW                 
has_warden1                                                             ***
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1   *  
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1          
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1         
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1        
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1 ** 
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1          
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1     
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                          Chisq Df Pr(>Chisq)    
(Intercept)              7.1288  1   0.007585 ** 
profile_name            68.2667  7  3.307e-12 ***
has_warden              32.4962  1  1.194e-08 ***
profile_name:has_warden 20.5226  7   0.004545 ** 
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name        Std.Dev. Corr 
 scenario     (Intercept) 1.29819       
              has_warden1 0.83011  0.694
 target_model (Intercept) 0.61977       

--- Odds Ratios ---
                                                                               OR
(Intercept)                                                             0.2954433
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM               3.2017505
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                   0.8508678
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                  0.9686307
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                 1.1376004
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM             2.7041115
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                   1.6687798
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW              0.7175380
has_warden1                                                             0.1456466
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1   0.4946608
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1       0.9245132
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1      1.2090069
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1     0.7740663
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1 0.4330673
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1       0.7423525
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1  1.2004490
                                                                          CI_lower
(Intercept)                                                             0.12071565
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM               1.97912280
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                   0.51728639
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                  0.59152755
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                 0.69760894
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM             1.67341079
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                   1.03096069
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW              0.43324202
has_warden1                                                             0.07509758
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1   0.26859132
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1       0.48556209
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1      0.64547024
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1     0.41095679
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1 0.23362970
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1       0.40056155
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1  0.62924795
                                                                         CI_upper
(Intercept)                                                             0.7230771
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM               5.1796715
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                   1.3995652
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                  1.5861400
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                 1.8551006
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM             4.3696497
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                   2.7011951
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW              1.1883907
has_warden1                                                             0.2824715
profile_nameE=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1   0.9110099
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1       1.7602787
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1      2.2645470
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1     1.4580087
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1 0.8027544
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1       1.3757866
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1  2.2901590
Loading required package: Matrix
Warning messages:
1: package ‘lme4’ was built under R version 4.4.3 
2: package ‘Matrix’ was built under R version 4.4.3 
Loading required package: carData
Warning messages:
1: package ‘car’ was built under R version 4.4.3 
2: package ‘carData’ was built under R version 4.4.3 

Correlation matrix not shown by default, as p = 16 > 12.
Use print(summary(m3), correlation=TRUE)  or
    vcov(summary(m3))        if you need it
```


---

## Model 4: Capability Asymmetry

**Formula**: `success ~ warden_tier + (1|model_family) + (1 + warden_tier|scenario) + (1|profile_name)`

**Family**: Binomial (logit link)

**Data**: Adversary runs only (cap_asym study)

**N** = 6,263 | 7 model families | 14 scenarios | 8 profiles

**Reference level**: warden_tier=none

**Warden tier counts**:

- none: 1566
- weak: 1565
- mid: 1568
- strong: 1564

### Output

```
--- Data Summary ---
Observations: 6263
Model families: 7
Scenarios: 14, Profiles: 8
Overall success rate: 17.9%

Runs by warden tier:

  none   weak    mid strong 
  1566   1565   1568   1564 

Success rate by warden tier:
  none        34.7%  (n=1566)
  weak        13.5%  (n=1565)
  mid         12.8%  (n=1568)
  strong      10.8%  (n=1564)

Success rate by model_family x warden_tier:
             none          weak          mid           strong       
claude       "27% (n=223)" "8% (n=221)"  "7% (n=224)"  "10% (n=220)"
gemini_flash "47% (n=224)" "12% (n=224)" "4% (n=224)"  "2% (n=224)" 
gemma        "37% (n=224)" "19% (n=224)" "16% (n=224)" "20% (n=224)"
gpt          "46% (n=224)" "31% (n=224)" "36% (n=224)" "21% (n=224)"
llama        "23% (n=224)" "10% (n=224)" "15% (n=224)" "13% (n=224)"
mistral      "32% (n=224)" "11% (n=224)" "3% (n=224)"  "3% (n=224)" 
qwen         "31% (n=223)" "4% (n=224)"  "9% (n=224)"  "6% (n=224)" 

--- Fitting Model 4: Capability Asymmetry ---
  [Model 4] Default optimizer warning: Model failed to converge with max|grad| = 0.0301367 (tol = 0.002, component 1)
  See ?lme4::convergence and ?lme4::troubleshooting.
  [Model 4] Retrying with bobyqa...

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ warden_tier + (1 | model_family) + (1 + warden_tier |  
    scenario) + (1 | profile_name)
   Data: data
Control: glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e+05))

      AIC       BIC    logLik -2*log(L)  df.resid 
   4331.1    4439.0   -2149.5    4299.1      6247 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-2.3836 -0.4353 -0.1782 -0.0434 27.5638 

Random effects:
 Groups       Name              Variance Std.Dev. Corr          
 scenario     (Intercept)       1.5813   1.2575                 
              warden_tierweak   0.5462   0.7391   0.80          
              warden_tiermid    0.9735   0.9867   0.74 0.99     
              warden_tierstrong 1.1526   1.0736   0.61 0.92 0.97
 profile_name (Intercept)       0.1028   0.3207                 
 model_family (Intercept)       0.3807   0.6170                 
Number of obs: 6263, groups:  scenario, 14; profile_name, 8; model_family, 7

Fixed effects:
                  Estimate Std. Error z value Pr(>|z|)    
(Intercept)        -0.9065     0.4299  -2.109    0.035 *  
warden_tierweak    -2.0064     0.2322  -8.642  < 2e-16 ***
warden_tiermid     -2.2451     0.2977  -7.542 4.63e-14 ***
warden_tierstrong  -2.4834     0.3288  -7.552 4.27e-14 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) wrdn_trw wrdn_trm
warden_trwk 0.504                   
warden_trmd 0.489  0.873            
wrdn_trstrn 0.389  0.799    0.888   
optimizer (bobyqa) convergence code: 0 (OK)
boundary (singular) fit: see help('isSingular')


--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
              Chisq Df Pr(>Chisq)    
(Intercept)  4.4463  1    0.03498 *  
warden_tier 76.7122  3    < 2e-16 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name              Std.Dev. Corr             
 scenario     (Intercept)       1.25751                   
              warden_tierweak   0.73905  0.804            
              warden_tiermid    0.98666  0.742 0.985      
              warden_tierstrong 1.07359  0.606 0.915 0.971
 profile_name (Intercept)       0.32065                   
 model_family (Intercept)       0.61702                   

--- Odds Ratios (exp of fixed effects) ---
                          OR   CI_lower  CI_upper
(Intercept)       0.40393614 0.17393288 0.9380883
warden_tierweak   0.13447251 0.08531226 0.2119608
warden_tiermid    0.10591576 0.05909733 0.1898250
warden_tierstrong 0.08345715 0.04380965 0.1589854
Loading required package: Matrix
Warning messages:
1: package ‘lme4’ was built under R version 4.4.3 
2: package ‘Matrix’ was built under R version 4.4.3 
Loading required package: carData
Warning messages:
1: package ‘car’ was built under R version 4.4.3 
2: package ‘carData’ was built under R version 4.4.3 
boundary (singular) fit: see help('isSingular')
```


---
