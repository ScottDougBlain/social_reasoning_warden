# Mixed-Effects Model Results

**Social Reasoning Warden — ERA Project**

**Generated**: 2026-02-18 13:32

**Data**: 937 observations | 637 adversary, 300 benign | 35 scenarios | overall SR = 45.1%

**Software**: R lme4 (glmer, binomial) + lmerTest | Wald chi-square tests | Satterthwaite df

---

## Model 1: Warden Effectiveness

**Formula**: `success ~ requester_type * has_warden + (1|scenario) + (1|target_model) + (1|requester_model)`

**Family**: Binomial (logit link)

**N** = 937 (637 adversary, 300 benign) | 35 scenarios | 11 target models | 11 requester models

**Overall success rate**: 45.1%

**Reference levels**: requester_type=benign_agent, has_warden=0

### Output

```
--- Data Summary ---
Observations: 937
Success rate: 45.1%

Success by condition:
                     0         1
benign_agent 0.6000000 0.6482759
adversary    0.5640244 0.1650485

Cell counts:
              has_warden
requester_type   0   1
  benign_agent 155 145
  adversary    328 309

--- Fitting Model 1: Warden Effectiveness ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ requester_type * has_warden + (1 | scenario) + (1 |  
    target_model) + (1 | requester_model)
   Data: data

     AIC      BIC   logLik deviance df.resid 
  1123.3   1157.2   -554.6   1109.3      930 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-1.6947 -0.8563 -0.3727  0.7837  3.6477 

Random effects:
 Groups          Name        Variance Std.Dev.
 scenario        (Intercept) 0.17966  0.4239  
 target_model    (Intercept) 0.00000  0.0000  
 requester_model (Intercept) 0.04403  0.2098  
Number of obs: 937, groups:  
scenario, 35; target_model, 11; requester_model, 11

Fixed effects:
                                    Estimate Std. Error z value Pr(>|z|)    
(Intercept)                          0.23607    0.22184   1.064    0.287    
requester_typeadversary             -0.09661    0.20930  -0.462    0.644    
has_warden1                          0.19842    0.24424   0.812    0.417    
requester_typeadversary:has_warden1 -2.20541    0.31474  -7.007 2.43e-12 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) rqstr_ hs_wr1
rqstr_typdv -0.635              
has_warden1 -0.497  0.549       
rqstr_ty:_1  0.412 -0.638 -0.774
optimizer (Nelder_Mead) convergence code: 0 (OK)
boundary (singular) fit: see help('isSingular')


--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                            Chisq Df Pr(>Chisq)    
(Intercept)                1.1324  1     0.2873    
requester_type             0.2131  1     0.6444    
has_warden                 0.6600  1     0.4166    
requester_type:has_warden 49.0981  1  2.435e-12 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups          Name        Std.Dev.
 scenario        (Intercept) 0.42386 
 target_model    (Intercept) 0.00000 
 requester_model (Intercept) 0.20982 

--- Odds Ratios (exp of fixed effects) ---
                                           OR   CI_lower  CI_upper
(Intercept)                         1.2662598 0.81976742 1.9559375
requester_typeadversary             0.9079096 0.60239964 1.3683603
has_warden1                         1.2194754 0.75557284 1.9682023
requester_typeadversary:has_warden1 0.1102051 0.05946909 0.2042265
Loading required package: Matrix
Loading required package: carData
boundary (singular) fit: see help('isSingular')
```


---

## Model 2: Dossier Impact

**Formula**: `success ~ adversary_has_data * has_warden + (1|scenario) + (1|profile_name) + (1|target_model)`

**Family**: Binomial (logit link)

**Data**: Adversary runs with profiled targets only

**N** = 264 (107 with dossier, 157 without) | 11 scenarios | 9 profiles

**Reference levels**: adversary_has_data=0, has_warden=0

### Output

```
--- Data Summary ---
Observations: 264
With dossier: 107, Without: 157

Success by condition:
          0          1
0 0.5769231 0.15189873
1 0.4310345 0.08163265

Cell counts:
                  has_warden
adversary_has_data  0  1
                 0 78 79
                 1 58 49

--- Fitting Model 2: Dossier Impact ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ adversary_has_data * has_warden + (1 | scenario) +  
    (1 | profile_name) + (1 | target_model)
   Data: data

     AIC      BIC   logLik deviance df.resid 
   264.8    289.8   -125.4    250.8      257 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-2.1288 -0.5182 -0.2102  0.5524 10.3982 

Random effects:
 Groups       Name        Variance Std.Dev.
 scenario     (Intercept) 1.4901   1.2207  
 profile_name (Intercept) 0.5504   0.7419  
 target_model (Intercept) 0.0000   0.0000  
Number of obs: 264, groups:  scenario, 11; profile_name, 9; target_model, 6

Fixed effects:
                                Estimate Std. Error z value Pr(>|z|)    
(Intercept)                      0.09311    0.57210   0.163    0.871    
adversary_has_data1              0.01436    0.46674   0.031    0.975    
has_warden1                     -2.70238    0.49512  -5.458 4.81e-08 ***
adversary_has_data1:has_warden1 -0.48642    0.82379  -0.590    0.555    
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) adv__1 hs_wr1
advrsry_h_1 -0.371              
has_warden1 -0.220  0.204       
advrs__1:_1  0.117 -0.411 -0.472
optimizer (Nelder_Mead) convergence code: 0 (OK)
boundary (singular) fit: see help('isSingular')


--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                                Chisq Df Pr(>Chisq)    
(Intercept)                    0.0265  1     0.8707    
adversary_has_data             0.0009  1     0.9755    
has_warden                    29.7901  1  4.814e-08 ***
adversary_has_data:has_warden  0.3486  1     0.5549    
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name        Std.Dev.
 scenario     (Intercept) 1.22071 
 profile_name (Intercept) 0.74189 
 target_model (Intercept) 0.00000 

--- Odds Ratios ---
                                        OR   CI_lower  CI_upper
(Intercept)                     1.09758533 0.35765483 3.3683134
adversary_has_data1             1.01446025 0.40639504 2.5323380
has_warden1                     0.06704575 0.02540531 0.1769367
adversary_has_data1:has_warden1 0.61482635 0.12233122 3.0900653
Loading required package: Matrix
Loading required package: carData
boundary (singular) fit: see help('isSingular')
```


---

## Model 3: Profile Vulnerability

**Formula**: `success ~ profile_name * has_warden + (1|scenario) + (1|target_model)`

**Family**: Binomial (logit link)

**Data**: Adversary runs with profiled targets only

**N** = 264 | 11 scenarios | 9 profiles

**Profile counts**:

- Compliant Agreeable: 48
- Overwhelmed Time-Pressured Worker: 45
- Idealistic True Believer: 44
- Overconfident Veteran: 39
- Authority-Deferential Follower: 20
- Lonely Isolated: 20
- Overwhelmed Time-Pressured: 18
- Authority-Deferential Junior Employee: 15
- Lonely Isolated Worker: 15

### Output

```
--- Data Summary ---
Observations: 264
Profiles: 9, Scenarios: 11
Reference profile: Compliant Agreeable

Success rate by profile:
  Authority-Deferential Follower       60.0%  (n=20)
  Overwhelmed Time-Pressured           44.4%  (n=18)
  Compliant Agreeable                  41.7%  (n=48)
  Idealistic True Believer             31.8%  (n=44)
  Authority-Deferential Junior Employee  26.7%  (n=15)
  Lonely Isolated                      25.0%  (n=20)
  Overwhelmed Time-Pressured Worker    24.4%  (n=45)
  Overconfident Veteran                23.1%  (n=39)
  Lonely Isolated Worker               20.0%  (n=15)

Success by profile x warden:
                                              0          1
Compliant Agreeable                   0.7777778 0.20000000
Authority-Deferential Follower        0.8000000 0.40000000
Authority-Deferential Junior Employee 0.4444444 0.00000000
Idealistic True Believer              0.5200000 0.05263158
Lonely Isolated                       0.5000000 0.00000000
Lonely Isolated Worker                0.2727273 0.00000000
Overconfident Veteran                 0.3500000 0.10526316
Overwhelmed Time-Pressured            0.6666667 0.22222222
Overwhelmed Time-Pressured Worker     0.4166667 0.04761905

--- Fitting Model 3: Profile Vulnerability ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: 
success ~ profile_name * has_warden + (1 | scenario) + (1 | target_model)
   Data: data

     AIC      BIC   logLik deviance df.resid 
   268.2    339.8   -114.1    228.2      244 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-2.2849 -0.4933 -0.1615  0.4829  7.0955 

Random effects:
 Groups       Name        Variance  Std.Dev.
 scenario     (Intercept) 1.5439282 1.242549
 target_model (Intercept) 0.0000927 0.009628
Number of obs: 264, groups:  scenario, 11; target_model, 6

Fixed effects:
                                                                Estimate
(Intercept)                                                    1.499e+00
profile_nameAuthority-Deferential Follower                     3.149e-04
profile_nameAuthority-Deferential Junior Employee             -1.248e+00
profile_nameIdealistic True Believer                          -1.294e+00
profile_nameLonely Isolated                                   -1.759e+00
profile_nameLonely Isolated Worker                            -2.696e+00
profile_nameOverconfident Veteran                             -2.247e+00
profile_nameOverwhelmed Time-Pressured                        -1.063e+00
profile_nameOverwhelmed Time-Pressured Worker                 -2.047e+00
has_warden1                                                   -3.380e+00
profile_nameAuthority-Deferential Follower:has_warden1         1.085e+00
profile_nameAuthority-Deferential Junior Employee:has_warden1 -1.366e+01
profile_nameIdealistic True Believer:has_warden1              -3.068e-01
profile_nameLonely Isolated:has_warden1                       -1.331e+01
profile_nameLonely Isolated Worker:has_warden1                -1.404e+01
profile_nameOverconfident Veteran:has_warden1                  1.507e+00
profile_nameOverwhelmed Time-Pressured:has_warden1             9.885e-01
profile_nameOverwhelmed Time-Pressured Worker:has_warden1      2.776e-01
                                                              Std. Error
(Intercept)                                                    7.659e-01
profile_nameAuthority-Deferential Follower                     1.068e+00
profile_nameAuthority-Deferential Junior Employee              9.832e-01
profile_nameIdealistic True Believer                           7.780e-01
profile_nameLonely Isolated                                    9.637e-01
profile_nameLonely Isolated Worker                             1.004e+00
profile_nameOverconfident Veteran                              8.372e-01
profile_nameOverwhelmed Time-Pressured                         1.012e+00
profile_nameOverwhelmed Time-Pressured Worker                  7.960e-01
has_warden1                                                    8.471e-01
profile_nameAuthority-Deferential Follower:has_warden1         1.402e+00
profile_nameAuthority-Deferential Junior Employee:has_warden1  1.478e+03
profile_nameIdealistic True Believer:has_warden1               1.463e+00
profile_nameLonely Isolated:has_warden1                        1.005e+03
profile_nameLonely Isolated Worker:has_warden1                 4.831e+03
profile_nameOverconfident Veteran:has_warden1                  1.298e+00
profile_nameOverwhelmed Time-Pressured:has_warden1             1.448e+00
profile_nameOverwhelmed Time-Pressured Worker:has_warden1      1.438e+00
                                                              z value Pr(>|z|)
(Intercept)                                                     1.958  0.05028
profile_nameAuthority-Deferential Follower                      0.000  0.99976
profile_nameAuthority-Deferential Junior Employee              -1.269  0.20427
profile_nameIdealistic True Believer                           -1.663  0.09629
profile_nameLonely Isolated                                    -1.826  0.06791
profile_nameLonely Isolated Worker                             -2.684  0.00727
profile_nameOverconfident Veteran                              -2.684  0.00727
profile_nameOverwhelmed Time-Pressured                         -1.050  0.29366
profile_nameOverwhelmed Time-Pressured Worker                  -2.571  0.01013
has_warden1                                                    -3.990  6.6e-05
profile_nameAuthority-Deferential Follower:has_warden1          0.773  0.43923
profile_nameAuthority-Deferential Junior Employee:has_warden1  -0.009  0.99262
profile_nameIdealistic True Believer:has_warden1               -0.210  0.83391
profile_nameLonely Isolated:has_warden1                        -0.013  0.98943
profile_nameLonely Isolated Worker:has_warden1                 -0.003  0.99768
profile_nameOverconfident Veteran:has_warden1                   1.161  0.24559
profile_nameOverwhelmed Time-Pressured:has_warden1              0.683  0.49467
profile_nameOverwhelmed Time-Pressured Worker:has_warden1       0.193  0.84695
                                                                 
(Intercept)                                                   .  
profile_nameAuthority-Deferential Follower                       
profile_nameAuthority-Deferential Junior Employee                
profile_nameIdealistic True Believer                          .  
profile_nameLonely Isolated                                   .  
profile_nameLonely Isolated Worker                            ** 
profile_nameOverconfident Veteran                             ** 
profile_nameOverwhelmed Time-Pressured                           
profile_nameOverwhelmed Time-Pressured Worker                 *  
has_warden1                                                   ***
profile_nameAuthority-Deferential Follower:has_warden1           
profile_nameAuthority-Deferential Junior Employee:has_warden1    
profile_nameIdealistic True Believer:has_warden1                 
profile_nameLonely Isolated:has_warden1                          
profile_nameLonely Isolated Worker:has_warden1                   
profile_nameOverconfident Veteran:has_warden1                    
profile_nameOverwhelmed Time-Pressured:has_warden1               
profile_nameOverwhelmed Time-Pressured Worker:has_warden1        
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1
optimizer (Nelder_Mead) convergence code: 0 (OK)
unable to evaluate scaled gradient
Model failed to converge: degenerate  Hessian with 3 negative eigenvalues


--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                          Chisq Df Pr(>Chisq)    
(Intercept)              3.8320  1    0.05028 .  
profile_name            14.0449  8    0.08060 .  
has_warden              15.9221  1  6.601e-05 ***
profile_name:has_warden  2.3134  8    0.96987    
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name        Std.Dev.
 scenario     (Intercept) 1.242549
 target_model (Intercept) 0.009628

--- Odds Ratios ---
                                                                        OR
(Intercept)                                                   4.478458e+00
profile_nameAuthority-Deferential Follower                    1.000315e+00
profile_nameAuthority-Deferential Junior Employee             2.870223e-01
profile_nameIdealistic True Believer                          2.742203e-01
profile_nameLonely Isolated                                   1.721483e-01
profile_nameLonely Isolated Worker                            6.746806e-02
profile_nameOverconfident Veteran                             1.056708e-01
profile_nameOverwhelmed Time-Pressured                        3.454050e-01
profile_nameOverwhelmed Time-Pressured Worker                 1.291673e-01
has_warden1                                                   3.404773e-02
profile_nameAuthority-Deferential Follower:has_warden1        2.958260e+00
profile_nameAuthority-Deferential Junior Employee:has_warden1 1.168004e-06
profile_nameIdealistic True Believer:has_warden1              7.357870e-01
profile_nameLonely Isolated:has_warden1                       1.652949e-06
profile_nameLonely Isolated Worker:has_warden1                7.986822e-07
profile_nameOverconfident Veteran:has_warden1                 4.511933e+00
profile_nameOverwhelmed Time-Pressured:has_warden1            2.687248e+00
profile_nameOverwhelmed Time-Pressured Worker:has_warden1     1.320007e+00
                                                                 CI_lower
(Intercept)                                                   0.998159762
profile_nameAuthority-Deferential Follower                    0.123416919
profile_nameAuthority-Deferential Junior Employee             0.041781819
profile_nameIdealistic True Believer                          0.059689504
profile_nameLonely Isolated                                   0.026036451
profile_nameLonely Isolated Worker                            0.009422353
profile_nameOverconfident Veteran                             0.020478223
profile_nameOverwhelmed Time-Pressured                        0.047496963
profile_nameOverwhelmed Time-Pressured Worker                 0.027139881
has_warden1                                                   0.006472412
profile_nameAuthority-Deferential Follower:has_warden1        0.189436233
profile_nameAuthority-Deferential Junior Employee:has_warden1 0.000000000
profile_nameIdealistic True Believer:has_warden1              0.041813321
profile_nameLonely Isolated:has_warden1                       0.000000000
profile_nameLonely Isolated Worker:has_warden1                0.000000000
profile_nameOverconfident Veteran:has_warden1                 0.354666387
profile_nameOverwhelmed Time-Pressured:has_warden1            0.157463270
profile_nameOverwhelmed Time-Pressured Worker:has_warden1     0.078732758
                                                                CI_upper
(Intercept)                                                   20.0935649
profile_nameAuthority-Deferential Follower                     8.1077221
profile_nameAuthority-Deferential Junior Employee              1.9717140
profile_nameIdealistic True Believer                           1.2597992
profile_nameLonely Isolated                                    1.1382140
profile_nameLonely Isolated Worker                             0.4831000
profile_nameOverconfident Veteran                              0.5452776
profile_nameOverwhelmed Time-Pressured                         2.5118368
profile_nameOverwhelmed Time-Pressured Worker                  0.6147485
has_warden1                                                    0.1791060
profile_nameAuthority-Deferential Follower:has_warden1        46.1965639
profile_nameAuthority-Deferential Junior Employee:has_warden1        Inf
profile_nameIdealistic True Believer:has_warden1              12.9476103
profile_nameLonely Isolated:has_warden1                              Inf
profile_nameLonely Isolated Worker:has_warden1                       Inf
profile_nameOverconfident Veteran:has_warden1                 57.3991229
profile_nameOverwhelmed Time-Pressured:has_warden1            45.8602167
profile_nameOverwhelmed Time-Pressured Worker:has_warden1     22.1307776
Loading required package: Matrix
Loading required package: carData
Warning messages:
1: In checkConv(attr(opt, "derivs"), opt$par, ctrl = control$checkConv,  :
  unable to evaluate scaled gradient
2: In checkConv(attr(opt, "derivs"), opt$par, ctrl = control$checkConv,  :
  unable to evaluate scaled gradient
3: In checkConv(attr(opt, "derivs"), opt$par, ctrl = control$checkConv,  :
  Model failed to converge: degenerate  Hessian with 3 negative eigenvalues

Correlation matrix not shown by default, as p = 18 > 12.
Use print(summary(m3), correlation=TRUE)  or
    vcov(summary(m3))        if you need it

Warning messages:
1: In vcov.merMod(object, use.hessian = use.hessian) :
  variance-covariance matrix computed from finite-difference Hessian is
not positive definite or contains NA values: falling back to var-cov estimated from RX
2: In vcov.merMod(object, correlation = correlation, sigm = sig) :
  variance-covariance matrix computed from finite-difference Hessian is
not positive definite or contains NA values: falling back to var-cov estimated from RX
3: In vcov.merMod(mod, complete = FALSE) :
  variance-covariance matrix computed from finite-difference Hessian is
not positive definite or contains NA values: falling back to var-cov estimated from RX
4: In vcov.merMod(object) :
  variance-covariance matrix computed from finite-difference Hessian is
not positive definite or contains NA values: falling back to var-cov estimated from RX
```
