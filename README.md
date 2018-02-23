# MonkeyProject
Kind of sophisticated dual bandit task whose purpose is to study attitude 
towards risk in macaques.

## Experiments
Run "main.py".

## Analysis

### Re-produce figures contained in paper

### Supplementary analysis

##### Stability of modelling

For having an idea about the stability of fitting parameters, run "analysis/evolution.py".

##### Progress - performances

1) For assessing progress over time, run "analysis/progress_per_arbitrary_pool.py".

2) For evaluating performances, run "analysis/progress_histo.py". It produces 
figures that depict performances for control trials 
(i.e. trials in which just p values change between lotteries, etc.). 
You can access values running "analysis/progress_summary.py".

3) For evaluating performances for 'non-control' trials, 
run 'analysis/preference_towards_risk_against_expected_value'.

### Step by step
For evaluating performances, run "analysis/progress_histo.py". 

##### Progress

##### Kahneman replication
Run 'equal_expected_value.py'
 
##### Modelling 

1) For fitting data with the DM model, run 'analysis/modelling'.

2) Run 'analysis/main_figures' for creating the figures corresponding 
to the modelling.

