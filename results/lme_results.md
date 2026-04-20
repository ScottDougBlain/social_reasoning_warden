# Mixed-Effects Model Results

**Social Reasoning Warden — ERA Project**

**Generated**: 2026-04-20 16:56

**Data**: 4,032 observations | 2,688 adversary, 1,344 benign | 14 scenarios | overall SR = 38.4%

**Software**: R lme4 (glmer, binomial) + lmerTest | Wald chi-square tests | Satterthwaite df

---

## Model 1: Warden Effectiveness

**Formula**: `success ~ requester_type * has_warden + (1 + has_warden|scenario) + (1|profile_name) + (1|target_model) + (1|requester_model)`

**Family**: Binomial (logit link)

**N** = 4,032 (2,688 adversary, 1,344 benign) | 14 scenarios | 8 profiles | 3 target models | 3 requester models

**Overall success rate**: 38.4%

**Reference levels**: requester_type=benign_agent, has_warden=0

### Output

```
--- Data Summary ---
Observations: 4032
Success rate: 38.4%

Success by condition:
                     0          1
benign_agent 0.9136905 0.77579365
adversary    0.3839286 0.09920635

Cell counts:
              has_warden
requester_type    0    1
  benign_agent  336 1008
  adversary     672 2016

--- Fitting Model 1: Warden Effectiveness ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ requester_type * has_warden + (1 + has_warden | scenario) +  
    (1 | profile_name) + (1 | target_model) + (1 | requester_model)
   Data: data

      AIC       BIC    logLik -2*log(L)  df.resid 
   3061.7    3124.8   -1520.9    3041.7      4022 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-8.1568 -0.3722 -0.2129  0.3549  9.2029 

Random effects:
 Groups          Name        Variance Std.Dev. Corr 
 scenario        (Intercept) 0.77626  0.8811        
                 has_warden1 1.47396  1.2141   -0.41
 profile_name    (Intercept) 0.04230  0.2057        
 target_model    (Intercept) 0.06323  0.2515        
 requester_model (Intercept) 0.03425  0.1851        
Number of obs: 4032, groups:  
scenario, 14; profile_name, 8; target_model, 3; requester_model, 3

Fixed effects:
                                    Estimate Std. Error z value Pr(>|z|)    
(Intercept)                           2.7176     0.3727   7.292 3.05e-13 ***
requester_typeadversary              -3.2982     0.2381 -13.852  < 2e-16 ***
has_warden1                          -1.1419     0.3991  -2.861  0.00422 ** 
requester_typeadversary:has_warden1  -0.9582     0.2753  -3.481  0.00050 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) rqstr_ hs_wr1
rqstr_typdv -0.532              
has_warden1 -0.515  0.495       
rqstr_ty:_1  0.456 -0.858 -0.517

--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                            Chisq Df Pr(>Chisq)    
(Intercept)                53.175  1  3.051e-13 ***
requester_type            191.867  1  < 2.2e-16 ***
has_warden                  8.185  1  0.0042237 ** 
requester_type:has_warden  12.116  1  0.0004999 ***
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups          Name        Std.Dev. Corr  
 scenario        (Intercept) 0.88105        
                 has_warden1 1.21407  -0.406
 profile_name    (Intercept) 0.20566        
 target_model    (Intercept) 0.25146        
 requester_model (Intercept) 0.18506        

--- Odds Ratios (exp of fixed effects) ---
                                             OR   CI_lower    CI_upper
(Intercept)                         15.14427206 7.29498477 31.43926732
requester_typeadversary              0.03695057 0.02317092  0.05892491
has_warden1                          0.31919940 0.14598488  0.69793706
requester_typeadversary:has_warden1  0.38357156 0.22362536  0.65791799
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

**N** = 2,688 (1,344 with dossier, 1,344 without) | 14 scenarios | 8 profiles

**Reference levels**: adversary_has_data=0, has_warden=0

### Output

```
--- Data Summary ---
Observations: 2688
With dossier: 1344, Without: 1344

Success by condition:
          0          1
0 0.3958333 0.09424603
1 0.3720238 0.10416667

Cell counts:
                  has_warden
adversary_has_data    0    1
                 0  336 1008
                 1  336 1008

--- Fitting Model 2: Dossier Impact ---

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ adversary_has_data * has_warden + (1 + has_warden |  
    scenario) + (1 | profile_name) + (1 | target_model)
   Data: data

      AIC       BIC    logLik -2*log(L)  df.resid 
   1754.6    1807.7    -868.3    1736.6      2679 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-2.0689 -0.3534 -0.1797 -0.0548 21.3691 

Random effects:
 Groups       Name        Variance Std.Dev. Corr
 scenario     (Intercept) 2.06648  1.4375       
              has_warden1 0.84841  0.9211   0.28
 profile_name (Intercept) 0.09655  0.3107       
 target_model (Intercept) 0.25217  0.5022       
Number of obs: 2688, groups:  scenario, 14; profile_name, 8; target_model, 3

Fixed effects:
                                Estimate Std. Error z value Pr(>|z|)    
(Intercept)                      -0.6980     0.5139  -1.358    0.174    
adversary_has_data1              -0.1359     0.1832  -0.742    0.458    
has_warden1                      -2.7153     0.3487  -7.786 6.91e-15 ***
adversary_has_data1:has_warden1   0.2768     0.2473   1.119    0.263    
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

Correlation of Fixed Effects:
            (Intr) adv__1 hs_wr1
advrsry_h_1 -0.175              
has_warden1  0.040  0.259       
advrs__1:_1  0.130 -0.741 -0.361

--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                                Chisq Df Pr(>Chisq)    
(Intercept)                    1.8450  1     0.1744    
adversary_has_data             0.5503  1     0.4582    
has_warden                    60.6235  1  6.911e-15 ***
adversary_has_data:has_warden  1.2530  1     0.2630    
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name        Std.Dev. Corr 
 scenario     (Intercept) 1.43752       
              has_warden1 0.92109  0.276
 profile_name (Intercept) 0.31072       
 target_model (Intercept) 0.50217       

--- Odds Ratios ---
                                        OR   CI_lower  CI_upper
(Intercept)                     0.49756024 0.18172459 1.3623153
adversary_has_data1             0.87292678 0.60958033 1.2500423
has_warden1                     0.06618572 0.03341337 0.1311017
adversary_has_data1:has_warden1 1.31891732 0.81231305 2.1414686
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

**N** = 2,688 | 14 scenarios | 8 profiles

**Profile counts**:

- E=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM: 336
- E=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM: 336
- E=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW: 336
- E=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM: 336
- E=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH: 336
- E=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM: 336
- E=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW: 336
- E=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH: 336

### Output

```
--- Data Summary ---
Observations: 2688
Profiles: 8, Scenarios: 14
Reference profile: E=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM

Success rate by profile:
  E=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM  23.8%  (n=336)
  E=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM  20.2%  (n=336)
  E=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH  18.5%  (n=336)
  E=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW  16.1%  (n=336)
  E=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM  15.5%  (n=336)
  E=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH  14.6%  (n=336)
  E=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW  14.3%  (n=336)
  E=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM  13.4%  (n=336)

Success by profile x warden:
                                                        0          1
E=HIGH | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM   0.5595238 0.13095238
E=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM       0.3095238 0.07539683
E=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH      0.2619048 0.10714286
E=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM    0.3452381 0.09126984
E=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW     0.3809524 0.08730159
E=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM 0.4880952 0.10714286
E=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH       0.4285714 0.10317460
E=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW  0.2976190 0.09126984

--- Fitting Model 3: Profile Vulnerability ---
  [Model 3] Default optimizer warning: Model failed to converge with max|grad| = 0.0175776 (tol = 0.002, component 1)
  See ?lme4::convergence and ?lme4::troubleshooting.
  [Model 3] Retrying with bobyqa...

--- Fixed Effects ---
Generalized linear mixed model fit by maximum likelihood (Laplace
  Approximation) [glmerMod]
 Family: binomial  ( logit )
Formula: success ~ profile_name * has_warden + (1 + has_warden | scenario) +  
    (1 | target_model)
   Data: data
Control: glmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 1e+05))

      AIC       BIC    logLik -2*log(L)  df.resid 
   1748.6    1866.6    -854.3    1708.6      2668 

Scaled residuals: 
    Min      1Q  Median      3Q     Max 
-2.6116 -0.3547 -0.1767 -0.0549 23.2921 

Random effects:
 Groups       Name        Variance Std.Dev. Corr
 scenario     (Intercept) 2.2321   1.494        
              has_warden1 0.8173   0.904    0.21
 target_model (Intercept) 0.2601   0.510        
Number of obs: 2688, groups:  scenario, 14; target_model, 3

Fixed effects:
                                                                        Estimate
(Intercept)                                                               0.2233
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                    -1.4442
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                   -1.7433
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM                 -1.2312
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                  -1.0243
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM              -0.4159
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                    -0.7535
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW               -1.5171
has_warden1                                                              -3.1353
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1         0.6713
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1        1.4492
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM:has_warden1      0.7135
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1       0.4462
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1   0.1218
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1         0.4059
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1    0.9993
                                                                        Std. Error
(Intercept)                                                                 0.5638
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                       0.3804
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                      0.3885
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM                    0.3761
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                     0.3732
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM                 0.3708
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                       0.3710
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW                  0.3821
has_warden1                                                                 0.4469
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1           0.5071
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1          0.4973
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM:has_warden1        0.4945
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1         0.4944
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1     0.4837
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1           0.4854
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1      0.4990
                                                                        z value
(Intercept)                                                               0.396
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                    -3.797
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                   -4.487
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM                 -3.274
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                  -2.745
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM              -1.122
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                    -2.031
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW               -3.970
has_warden1                                                              -7.015
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1         1.324
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1        2.914
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM:has_warden1      1.443
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1       0.903
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1   0.252
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1         0.836
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1    2.003
                                                                        Pr(>|z|)
(Intercept)                                                             0.692005
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                   0.000147
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                  7.22e-06
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM                0.001062
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                 0.006056
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM             0.262013
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                   0.042266
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW              7.17e-05
has_warden1                                                             2.30e-12
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1       0.185567
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1      0.003569
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM:has_warden1    0.149030
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1     0.366743
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1 0.801227
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1       0.403002
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1  0.045223
                                                                           
(Intercept)                                                                
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                   ***
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                  ***
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM                ** 
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                 ** 
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM                
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                   *  
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW              ***
has_warden1                                                             ***
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1          
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1      ** 
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM:has_warden1       
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1        
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1    
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1          
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1  *  
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Type III Wald Chi-Square Tests ---
Analysis of Deviance Table (Type III Wald chisquare tests)

Response: success
                          Chisq Df Pr(>Chisq)    
(Intercept)              0.1569  1    0.69200    
profile_name            33.1725  7  2.459e-05 ***
has_warden              49.2094  1  2.301e-12 ***
profile_name:has_warden 12.2419  7    0.09288 .  
---
Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1

--- Random Effects ---
 Groups       Name        Std.Dev. Corr 
 scenario     (Intercept) 1.49403       
              has_warden1 0.90404  0.212
 target_model (Intercept) 0.51005       

--- Odds Ratios ---
                                                                                OR
(Intercept)                                                             1.25025487
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                   0.23593612
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                  0.17493434
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM                0.29193456
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                 0.35903155
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM             0.65971828
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                   0.47069458
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW              0.21935305
has_warden1                                                             0.04348746
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1       1.95677719
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1      4.25964565
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM:has_warden1    2.04112976
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1     1.56241251
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1 1.12951095
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1       1.50067945
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1  2.71651243
                                                                          CI_lower
(Intercept)                                                             0.41407445
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                   0.11195132
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                  0.08168918
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM                0.13968562
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                 0.17276743
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM             0.31893734
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                   0.22746152
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW              0.10373115
has_warden1                                                             0.01811027
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1       0.72426882
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1      1.60709938
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM:has_warden1    0.77442093
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1     0.59288598
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1 0.43765722
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1       0.57959347
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1  1.02149324
                                                                          CI_upper
(Intercept)                                                              3.7750150
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM                    0.4972327
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH                   0.3746154
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM                 0.6101257
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW                  0.7461109
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM              1.3646198
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH                    0.9740258
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW               0.4638507
has_warden1                                                              0.1044247
profile_nameE=LOW | A=LOW | C=LOW | N=HIGH | O=MEDIUM:has_warden1        5.2866793
profile_nameE=LOW | A=LOW | C=MEDIUM | N=HIGH | O=HIGH:has_warden1      11.2902670
profile_nameE=LOW | A=MEDIUM | C=HIGH | N=LOW | O=MEDIUM:has_warden1     5.3797755
profile_nameE=LOW | A=MEDIUM | C=LOW | N=MEDIUM | O=LOW:has_warden1      4.1173732
profile_nameE=MEDIUM | A=HIGH | C=LOW | N=MEDIUM | O=MEDIUM:has_warden1  2.9150553
profile_nameE=MEDIUM | A=LOW | C=LOW | N=LOW | O=HIGH:has_warden1        3.8855490
profile_nameE=MEDIUM | A=LOW | C=MEDIUM | N=MEDIUM | O=LOW:has_warden1   7.2241690
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
