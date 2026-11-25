# Experiment 4: Next-Visit Average Fish Weight Prediction — Final Status & Project Synthesis

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Experiment:** Experiment 4 — Next-Visit Average Fish Weight Prediction (`experiment_4_next_visit_weight_v1/`)  
**Audit Directories:** `experiment_4_yield_feasibility_audit/`, `experiment_4_final_audit/`, `experiment_4_final_audit/statistical_robustness_audit/`  
**Date:** 2026-11-04  
**Status:** **COMPLETED AND FROZEN**  

---

## 1. Executive Summary & Core Verdict

| Operational & Scientific Dimension | Verified Status / Metric | Primary Evidence / Reference |
| :--- | :--- | :--- |
| **Operational Baseline Retained** | **Persistence Baseline ($\hat{W}_{t+1} = W_t$)** | **MAE = 93.38 g** (RMSE = 189.96 g, $R^2 = 0.7600$) |
| **Exploratory Retrospective Model** | **Gradient Boosting Regressor (GBDT)** | **MAE = 57.22 g** (+12.59% over Persistence on clean subset) |
| **Rejected Model** | **Random Forest Regressor** | Not statistically significant under pond clustering ($p = 0.517$; 95% CI spans zero) |
| **Operational Deployment Status** | **ML models are NOT deployable on uncurated farm visits** | ML models suffer -20.1% to -36.4% error penalties on unrecorded partial harvests |
| **Data Integrity Verification** | **100% Preserved & Audited** | Raw datasets and Experiments 1, 2, and 3 remain frozen and untouched |

> [!IMPORTANT]
> **Operational Deployment Declaration:**
> **Persistence ($\hat{W}_{t+1} = W_t$) is retained as the sole operational baseline** for live farm deployment on uncurated routine visits. On the real-world chronological holdout test set ($N = 1,689$ pairs across 163 ponds), Persistence achieves an **MAE of 93.38 g**, outperforming all evaluated machine learning models (Linear Regression MAE: 117.74 g, -26.1%; Random Forest MAE: 112.15 g, -20.1%; Gradient Boosting MAE: 127.34 g, -36.4%).
> 
> **Gradient Boosting is strictly designated as an exploratory model for retrospective biological analysis on curated cohorts.** Its apparent superior performance (MAE = 57.22 g, +12.59% improvement) is only achievable after filtering out unrecorded management anomalies using future target observations (`next_weight`), making it operationally unavailable prior to the visit.

---

## 2. Research Objective & Scientific Scoping

The initial aim of Experiment 4 was to investigate fish growth and yield forecasting for commercial inland semi-intensive aquaculture ponds (primarily *Labeo rohita*, *Catla catla*, and *Pangasius* polyculture in Eluru and Nellore, Andhra Pradesh).

### 2.1 The Feasibility Audit Findings
Prior to model training, a systematic data inventory and feasibility audit (`experiment_4_yield_feasibility_audit/`) evaluated the source tables (`dataset/water_quality.csv`, `processed_data_v2/enrolled_ponds_v2.csv`, `processed_data_v2/dropouts_v2.csv`):
1. **Complete Absence of Harvest Yield Metrics:** Total harvest biomass (kg), harvest yield (tons/acre), commercial harvest dates, and stocking dates are **0.00% populated (completely missing)** across all farm records.
2. **Arbitrary Culture Stage Enrollment:** Ponds were enrolled at arbitrary mid-culture points: **74.8%** of ponds enrolled with fish already $> 100\text{ g}$, and **32.7%** enrolled with fish already $> 500\text{ g}$. Days of Culture (DOC) cannot be determined.
3. **Pivoting to Next-Visit Body Weight Forecasting:** In lieu of cumulative harvest yield, the prediction target was scientifically restructured to **Next-Visit Average Fish Body Weight ($W_{t+1}$ in grams)** at the next routine farm visit ($t+1$), given observed water quality, feeding, and biological conditions at visit $t$ and scheduled revisit interval $\Delta t$.

```
+---------------------------------------------------------------------------------------------------+
| PREDICTION FORMULATION                                                                            |
| Given at Visit t:                                                                                 |
|   - Current Body Weight (W_t, grams)                                                              |
|   - Scheduled Revisit Gap (gap_days, 3 <= Delta t <= 45 days)                                     |
|   - Feeding Practices (curr_feed_amount_kg, curr_feed_per_acre_kg, feed_type)                     |
|   - Pond Environment (pond_area_acres, depth_meters, curr_do_mg_l, curr_ph, curr_temp_c)          |
|   - Biological & Operational Covariates (stocking_density, species, weather, mortality/distress)  |
|                                                                                                   |
| Target to Predict at Visit t+1:                                                                   |
|   - Next-Visit Average Fish Weight: W_{t+1} (grams)                                               |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Dataset Construction & Observation Partitions

### 3.1 Temporal Pair Construction
Using `dataset/water_quality.csv` and point-in-time pond profiles from `processed_data_v2/enrolled_ponds_v2.csv`, observations were consolidated daily (morning nadir DO, pH, temperature, and feeding) and chained chronologically within each unique pond.
- **Total consecutive same-pond transitions evaluated:** 3,024
- **Excluded revisit intervals $< 3$ days (sub-revisit noise / duplicate inspections):** 488 (16.14%)
- **Excluded revisit intervals $> 45$ days (broken production cycles / seasonal fallowing):** 39 (1.29%)
- **Master Valid Temporal Dataset (`temporal_growth_dataset.csv`):** **$N = 2,497$ pairs** across **240 unique ponds** (revisit interval: mean 18.06 days, median 14.96 days).

### 3.2 Chronological Partitioning (Cutoff: 2025-01-01)
To ensure zero temporal leakage across train and test horizons, pairs were partitioned strictly by calendar date:

| Partition Name | Temporal Boundary Criterion | Pair Count ($N$) | Unique Ponds | Clean Pairs | Suspicious Pairs | Role in Study |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Training Partition** | Both visits $t, t+1 < \text{2025-01-01}$ | **741** | 140 | 703 | 38 | Model training & cross-validation |
| **Cross-Cutoff Partition** | Visit $t < \text{2025-01-01} \le \text{Visit } t+1$ | **67** | 67 | 60 | 7 | **Strictly Quarantined & Excluded** |
| **Holdout Testing Partition**| Both visits $t, t+1 \ge \text{2025-01-01}$ | **1,689** | 163 | 1,601 | 88 | **Unbiased Chronological Evaluation** |
| **Total Master Dataset** | All valid pairs ($3 \le \Delta t \le 45\text{d}$) | **2,497** | 240 | 2,364 | 133 | Complete reconciled inventory |

### 3.3 The Data Quality Spectrum & Suspicious Anomalies
Analysis of empirical somatic growth revealed distinct biological and operational patterns:
- **Normal Somatic Growth ($0 < \text{ADG} \le 10\text{ g/day}$):** 1,378 pairs (55.19%)
- **Zero Weight Change ($\Delta W = 0\text{ g}$):** 859 pairs (34.40%) — resulting from coarse 25/50/100g visual rounding bins by field personnel.
- **Minor Net Weight Decrease ($-100\text{ g} < \Delta W < 0\text{ g}$):** 22 pairs (0.88%) — normal cast-net sampling variance across heterogeneous pond cohorts.
- **High Positive Growth ($10 < \text{ADG} \le 20\text{ g/day}$):** 105 pairs (4.21%) — accelerated juvenile growth surges.
- **Major Weight Loss ($\Delta W \le -100\text{ g}$ or $\text{ADG} < -5\text{ g/day}$):** 119 pairs (4.77%) — commercial partial harvests, fish thinning, or batch restocking.
- **Extreme Positive Gain ($\Delta W > 800\text{ g}$ or $\text{ADG} > 20\text{ g/day}$):** 14 pairs (0.56%) — biological impossibility; field logging or species transcription errors.
- **Total Suspicious / Non-Biological Pairs:** **133 pairs** (5.33%) across the master dataset (38 in train, 7 in cross-cutoff, 88 in test).
- **Retrospective Clean Subset:** **2,364 pairs** (703 train, 60 cross-cutoff, 1,601 test).

---

## 4. Models Evaluated

All machine learning models were trained using identical feature inputs, leak-free preprocessing pipelines (median numeric imputation, standard scaling, categorical one-hot encoding, and missingness indicators):

1. **Persistence Baseline:** $\hat{W}_{t+1} = W_t$. Represents zero somatic change over revisit interval. Requires zero training parameters.
2. **Mean Predictor Baseline:** $\hat{W}_{t+1} = \bar{W}_{\text{train}}$. Naive unconditional global historical mean.
3. **Linear Regression (Ridge Regressor, $\alpha = 1.0$):** Standard regularized linear model.
4. **Random Forest Regressor:** 100 trees, `min_samples_leaf=5`, `random_state=42`.
5. **Gradient Boosting Regressor (GBDT):** 100 trees, `learning_rate=0.05`, `max_depth=4`, `random_state=42`.

---

## 5. Validation Results Across Evaluation Protocols

### 5.1 Protocol A: 5-Fold GroupKFold Cross-Validation (Grouped by `pond_id`)

| Evaluation Regime | Model Name | Pooled OOF MAE (g) | Pooled OOF RMSE (g) | Pooled OOF $R^2$ | % Imp. vs Persistence | Fold Mean MAE (g) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **All Pairs** ($N=2,497$) | Persistence Baseline | 98.16 | 189.65 | 0.7342 | 0.00% | 98.16 |
| | Mean Predictor Baseline | 309.84 | 368.06 | -0.0012 | -215.64% | 309.84 |
| | Linear Regression (Ridge) | 100.75 | 179.00 | 0.7632 | -2.64% | 100.86 |
| | Random Forest | 85.51 | 159.62 | 0.8117 | **+12.89%** | 85.73 |
| | Gradient Boosting | 91.83 | 169.71 | 0.7872 | **+6.45%** | 92.11 |
| **Clean Subset** ($N=2,364$)| Persistence Baseline | 71.22 | 104.73 | 0.9177 | 0.00% | 71.22 |
| | Mean Predictor Baseline | 307.53 | 366.18 | -0.0065 | -331.78% | 307.53 |
| | Linear Regression (Ridge) | 52.46 | 69.67 | 0.9636 | **+26.34%** | 52.54 |
| | Random Forest | 50.00 | 68.96 | 0.9643 | **+29.80%** | 50.14 |
| | Gradient Boosting | 49.33 | 67.38 | 0.9659 | **+30.75%** | 49.50 |

### 5.2 Protocol B: Strict Chronological Holdout Validation (Train: $N=741$, Test: $N=1,689$)

```
CHRONOLOGICAL TEST ERROR (MAE in Grams)
-------------------------------------------------------------------------------------------------
All-Pairs Operational Test Set (N=1,689, 163 Ponds):
  Persistence Baseline (WINNER) : [====================] 93.38 g
  Random Forest                 : [========================] 112.15 g (-20.1% worse)
  Linear Regression             : [=========================] 117.74 g (-26.1% worse)
  Gradient Boosting             : [===========================] 127.34 g (-36.4% worse)
  Mean Predictor                : [==================================================] 332.06 g

Clean Retrospective Test Set (N=1,601, 163 Ponds):
  Gradient Boosting (WINNER)    : [============] 57.22 g (+12.6% over Persistence)
  Linear Regression             : [==============] 59.92 g (+8.5% over Persistence)
  Random Forest                 : [==============] 63.87 g (+2.4% over Persistence)
  Persistence Baseline          : [===============] 65.47 g
-------------------------------------------------------------------------------------------------
```

| Evaluation Regime | Model Name | Chronological Test MAE (g) | Test RMSE (g) | Test $R^2$ | $\Delta\text{MAE}$ vs. Persistence | % Imp. vs. Persistence | Beats Persistence? | Operational Deployability |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **All Pairs**<br>*(Operational Unfiltered Population, $N=1,689$)* | **Persistence Baseline** | **93.38** | **189.96** | **0.7600** | **0.00** | **0.00%** | — | **DEPLOYABLE OPERATIONAL BASELINE** |
| | Mean Predictor Baseline | 332.06 | 387.94 | -0.0011 | +238.68 | -255.61% | No | Inferior |
| | Linear Regression | 117.74 | 194.14 | 0.7493 | +24.36 | -26.09% | No | Inferior |
| | Random Forest | 112.15 | 184.37 | 0.7739 | +18.77 | -20.11% | No | Inferior |
| | Gradient Boosting | 127.34 | 208.75 | 0.7101 | +33.96 | -36.38% | No | Inferior |
| **Clean Subset**<br>*(Retrospective Exploratory Biological Cohort, $N=1,601$)* | Persistence Baseline | 65.47 | 101.84 | 0.9306 | 0.00 | 0.00% | — | Operational Benchmark |
| | Mean Predictor Baseline | 329.31 | 386.58 | -0.0000 | +263.84 | -403.02% | No | Inferior |
| | Linear Regression | 59.92 | 96.53 | 0.9376 | -5.55 | +8.47% | Yes | Retrospective Exploratory Only |
| | Random Forest | 63.87 | 83.28 | 0.9536 | -1.60 | +2.44% | Yes | Retrospective Exploratory Only |
| | **Gradient Boosting** | **57.22** | **78.07** | **0.9592** | **-8.25** | **+12.59%** | **Yes** | **RETROSPECTIVE EXPLORATORY ONLY** |

---

## 6. Pond-Clustered Statistical Robustness Audit

To resolve whether observed differences between models and persistence were statistically robust or artifacts of pseudo-replication, a rigorous statistical robustness audit (`experiment_4_final_audit/statistical_robustness_audit/`) was conducted.

### 6.1 Intra-Cluster Dependence & Markovian Chaining
- The chronological test set comprises **1,689 observations clustered across only 163 unique ponds** (average 10.36 pairs/pond, range 1 to 29).
- **83.94% of transitions are chained adjacent visits** ($D_t \rightarrow D_{t+1}$ followed by $D_{t+1} \rightarrow D_{t+2}$).
- Standard paired $t$-tests or naive non-parametric tests that treat all 1,689 pairs as independent identically distributed (i.i.d.) observations **artificially inflate degrees of freedom tenfold**, producing spuriously narrow confidence intervals and false significance.

### 6.2 Clustered Block-Bootstrap Protocol (5,000 Resamples of 163 Pond Clusters)

| Evaluation Regime | Model Name | Clustered Mean $\Delta\text{MAE}$ (g) | Clustered Median $\Delta\text{MAE}$ (g) | 95% Clustered CI [Lower, Upper] | CI Spans Zero? | % Bootstrap Draws Beating Persistence | Statistical Verdict Under Pond Clustering |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **All Pairs**<br>*(Operational Unfiltered Population, $N=1,689$)* | Linear Regression | +24.30 | +24.23 | [+18.67, +30.43] | No | 0.00% | **Statistically significantly inferior to Persistence** ($p < 10^{-12}$) |
| | Random Forest | +18.70 | +18.48 | [+11.43, +27.25] | No | 0.00% | **Statistically significantly inferior to Persistence** ($p < 10^{-12}$) |
| | Gradient Boosting | +33.85 | +33.40 | [+23.55, +47.09] | No | 0.00% | **Statistically significantly inferior to Persistence** ($p < 10^{-12}$) |
| **Clean Subset**<br>*(Retrospective Exploratory Subset, $N=1,601$)* | Linear Regression | -5.54 | -5.52 | [-10.15, -0.93] | No | 98.98% | **Statistically significantly superior to Persistence** |
| | **Random Forest** | **-1.59** | **-1.62** | **[-6.55, +3.52]** | **YES** | **74.16%** | **NO STATISTICALLY SIGNIFICANT DIFFERENCE** ($p = 0.517$) |
| | **Gradient Boosting** | **-8.26** | **-8.24** | **[-12.05, -4.44]** | **No** | **100.00%** | **Statistically significantly superior to Persistence** ($p < 0.0002$) |

### 6.3 Pair-Weighted vs. Pond-Weighted Sensitivity Analysis
When each pond is weighted equally (preventing frequently sampled ponds from dominating results):
- On All Pairs: Persistence remains the clear winner (Pond-weighted MAE: Persistence = 81.65 g vs. RF = 100.06 g, GBDT = 112.45 g).
- On Clean Subset:
  - **Random Forest flips to inferior to persistence** under pond weighting (Pond-weighted MAE: RF = 65.32 g vs. Persistence = 63.02 g, a **-3.65% degradation**).
  - **Gradient Boosting retains superiority** under pond weighting (Pond-weighted MAE: GBDT = 53.52 g vs. Persistence = 63.02 g, **+15.07% improvement**).

---

## 7. Limitations & Scientific Constraints

1. **Unrecorded Commercial Management Operations (Partial Harvests):**
   Commercial carp ponds regularly conduct partial netting to thin marketable fish (100–300 kg removed), or drain and restock ponds. Because commercial harvesting is not logged in farm water quality tables, ML models assume uninterrupted biological growth and predict $\hat{W}_{t+1} > W_t$, incurring massive penalty errors ($\le -100\text{ g}$ drops across 88 test pairs). Persistence naturally incurs an error equal to the harvest magnitude, whereas ML models add growth to the error.
2. **Coarse Field Measurement Granularity:**
   Field officers visually categorize cast-net samples into rounded increments (25 g, 50 g, 100 g). In **34.40%** of consecutive visits, recorded weight is identical ($\Delta W = 0\text{ g}$), producing artificial step-function plateaus.
3. **Absence of Stocking Dates and Culture Age (DOC):**
   Without known stocking dates or Day of Culture, standard bioenergetic and sigmoidal growth curves (von Bertalanffy, Gompertz) cannot be parameterized.
4. **Pre-Scheduling Requirement for `gap_days`:**
   The revisit interval $\Delta t$ must be pre-specified as an input feature. The model forecasts weight conditional upon an inspection occurring at day $t + \Delta t$; it does not optimize or schedule the visit date.
5. **Outcome-Dependent Filtering of the Clean Subset:**
   The clean biological subset was constructed using future target observations (`next_weight` and derived `weight_change_g`). Consequently, **the clean subset is strictly an ex-post exploratory cohort** and cannot be operationalized prior to visit $t+1$.

---

## 8. Final Scientific Conclusions & Baseline Retention

1. **Retained Operational Baseline:**
   **Persistence Baseline ($\hat{W}_{t+1} = W_t$) is retained as the sole operational baseline** for deployment in live farm management. In real-world operation where unrecorded partial harvests occur, Persistence achieves the lowest error ($\text{MAE} = 93.38\text{ g}$) and beats every ML model by 18 to 34 grams per fish.
2. **Status of Gradient Boosting (GBDT):**
   **Gradient Boosting is designated as an exploratory model strictly for retrospective clean biological cohorts.** When unrecorded management noise is filtered, GBDT demonstrates true bioenergetic signal, achieving $\text{MAE} = 57.22\text{ g}$ (+12.59% pair-weighted, +15.07% pond-weighted improvement; 95% cluster-CI $[-12.05\text{g}, -4.44\text{g}]$). It serves as proof-of-concept for digital aquaculture systems once farm harvest logging is formalized.
3. **Rejection of Random Forest:**
   Random Forest is rejected. While appearing modestly better than persistence under naive pair-weighted metrics (+2.44%), its 95% clustered confidence interval spans zero ($[-6.55\text{g}, +3.52\text{g}]$, $p=0.517$), and it actively degrades below persistence under pond-weighted evaluation.

---

## 9. Comprehensive Project File & Artifact Inventory

All original raw datasets, previous experiment deliverables, and Experiment 4 artifacts are verified present, complete, and frozen:

```
AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/
├── dataset/                                                        [5 source files, 4,318,173 bytes - FROZEN]
│   ├── Data_Model_IoTMLCQ_2024.xlsx
│   ├── dropouts.csv
│   ├── enrolled_ponds.csv
│   ├── water_quality.csv
│   └── water_quality_nellore_retracted.csv
├── processed_data_v2/                                              [10 cleaned files, 8,044,597 bytes - FROZEN]
│   ├── dropouts_v2.csv
│   ├── enrolled_ponds_v2.csv
│   ├── feeding_analysis_v2.csv
│   ├── fish_health_growth_analysis_v2.csv
│   ├── iot_water_model_v2.csv
│   ├── preprocessing_v2_report.json
│   ├── preprocessing_v2_report.md
│   ├── thresholds_config.json
│   ├── toxicity_analysis_v2.csv
│   └── water_quality_cleaned_v2.csv
├── baseline_toxicity_v1/                                           [Experiment 1: 17 files, 17,627,825 bytes - FROZEN]
├── experiment_2_mortality_v1/                                      [Experiment 2: 23 files, 1,975,615 bytes - FROZEN]
├── experiment_3_next_visit_risk_v1/                                [Experiment 3: 24 files, 3,425,042 bytes - FROZEN]
├── experiment_3_target_definition_audit/                           [Experiment 3 Audit: 4 files, 29,945 bytes - FROZEN]
├── experiment_4_yield_feasibility_audit/                           [Experiment 4 Feasibility: 4 files, 35,387 bytes]
│   ├── experiment_4_feasibility_report.md
│   ├── yield_data_inventory.csv
│   ├── yield_data_quality_report.csv
│   └── yield_target_feasibility.csv
├── experiment_4_next_visit_weight_v1/                              [Experiment 4 Execution: 8 files, 661,222 bytes]
│   ├── baseline_comparison.csv
│   ├── chronological_metrics.csv
│   ├── experiment_4_results_report.md
│   ├── feature_availability_audit.csv
│   ├── groupkfold_metrics.csv
│   ├── growth_data_quality_report.csv
│   ├── temporal_growth_dataset.csv
│   └── metrics/
│       └── test_subgroup_error_analysis.csv
├── experiment_4_final_audit/                                       [Experiment 4 Scientific Audit: 10 files, 61,095 bytes]
│   ├── all_pairs_vs_clean_metrics.csv
│   ├── chronological_split_verification.csv
│   ├── experiment_4_final_audit_report.md
│   ├── feature_operational_availability.csv
│   ├── scientific_threshold_review.csv
│   ├── suspicious_filter_audit.csv
│   └── statistical_robustness_audit/
│       ├── pair_vs_pond_weighted_metrics.csv
│       ├── pond_cluster_structure.csv
│       ├── pond_clustered_bootstrap_results.csv
│       └── statistical_robustness_report.md
├── train_experiment_4.py                                           [Experiment 4 Pipeline Code, 36,212 bytes]
└── EXPERIMENT_4_FINAL_STATUS.md                                    [Final Master Status Document]
```

