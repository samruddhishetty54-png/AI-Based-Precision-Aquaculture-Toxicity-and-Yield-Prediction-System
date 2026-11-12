# Experiment 5: Dissolved Oxygen (DO) Forecasting & Hypoxia Risk Prediction — Detailed Target & Data Feasibility Audit

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Document:** `experiment_5_planning/EXPERIMENT_5_DO_TARGET_FEASIBILITY_AUDIT.md`  
**Date:** 2026-11-04  
**Audit Status:** **COMPLETED — VERDICT: RESOUNDING GO**  

---

## 1. Executive Summary & Audit Verdict

| Feasibility & Scientific Dimension | Verified Metric / Finding | Audit Status |
| :--- | :--- | :---: |
| **Target Variable Completeness** | `DO (mg/L)` has **0 missing values across 12,399 records (100.0% populated)** | **PERFECT** |
| **Morning Nadir Verification** | Both visit $t$ and $t+1$ sampled between **06:00 and 08:30 AM** (mean 07:12 AM) | **VERIFIED** |
| **Valid Consecutive Pairs** | **$N = 5,178$ pairs** across **304 unique ponds** ($3 \le \Delta t \le 45$ days) | **VERIFIED** |
| **Low-DO Event Count (< 3.0 mg/L)**| **649 events (12.53% prevalence)**: 473 in train, 4 in cross-cutoff, 172 in test | **ABUNDANT** |
| **Severe Hypoxia Count (< 2.0 mg/L)**| **356 events (6.88% prevalence)**: 263 in train, 1 in cross-cutoff, 92 in test | **ROBUST** |
| **Persistence Baseline Difficulty** | Correlation $r = 0.2892$ ($R^2 = -0.3956$ on full dataset, $-0.7071$ on test set) | **WEAK BASELINE** |
| **Anti-Leakage Architecture** | Evening visits quarantined; point-in-time profile merging via `merge_asof` | **ENFORCED** |
| **Statistical Independence** | 85.68% chained transition pairs; GroupKFold & cluster bootstrap mandatory | **ADDRESSED** |
| **FINAL FEASIBILITY VERDICT** | **RESOUNDING "GO" FOR EXPERIMENT 5 IMPLEMENTATION** | **APPROVED** |

> [!IMPORTANT]
> **Audit Finding on Baseline Contrast (Exp 4 vs. Exp 5):**
> In Experiment 4 (Fish Weight Prediction), fish body weight was highly auto-correlated ($r > 0.87, R^2 \approx 0.76$), causing the trivial Persistence Baseline to outperform all ML models on uncurated data.
> In contrast, for **Dissolved Oxygen Forecasting in Experiment 5**, the correlation between consecutive visits ($14–21$ days apart) is only **$r = 0.2892$ ($R^2 = 0.0836$)**.
> The Persistence Baseline achieves a **negative $R^2$ of $-0.3956$ across the full dataset and $-0.7071$ on the chronological test set**, with a classification F1-score of only **0.1022**. 
> Dissolved oxygen is an ecologically dynamic parameter governed by temperature, organic feed loading, algal respiration, and pond morphology. **Machine learning models have substantial opportunity to provide genuine predictive value over persistence.**

---

## 2. Verification of Temporal Pairs & Pond Counts

### 2.1 Reconciling Transition Filtering
From the cleaned dataset `processed_data_v2/water_quality_cleaned_v2.csv`:
- Total records: **12,399 observations**.
- Morning records (`Type == 'Morning'`): **6,436 observations** across **317 unique ponds**.
- Duplicate morning records on the same pond on the exact same date: **1 record** (resolved by keeping the first valid entry).
- Total consecutive same-pond morning transitions: **6,119 transitions**.

```
+---------------------------------------------------------------------------------------------------+
| TEMPORAL REVISIT PAIR FILTERING FLOW                                                              |
|                                                                                                   |
| Total Consecutive Same-Pond Morning Transitions Evaluated : 6,119                                  |
|   |                                                                                               |
|   +---> Excluded: Revisit Gap < 3.0 Days (Duplicate/Follow-up visits) : 414 transitions (6.77%)   |
|   |                                                                                               |
|   +---> Excluded: Revisit Gap > 45.0 Days (Broken cycles / fallowing) : 527 transitions (8.61%)   |
|   |                                                                                               |
|   +===> Retained Valid Modeling Pairs (3.0 <= gap_days <= 45.0)       : 5,178 pairs (84.62%)      |
+---------------------------------------------------------------------------------------------------+
```

### 2.2 Pond Population Reconciliation
- **317 unique ponds** have at least one morning record in `water_quality_cleaned_v2.csv`.
- **13 ponds** had only a single visit or all consecutive transitions separated by $> 45$ days (fallowing/dropout).
- **304 unique ponds** form the final master pair dataset of **5,178 valid temporal pairs** (average: 17.03 pairs per pond, range: 1 to 32 pairs).

---

## 3. Verification of Morning Nadir Timing

A critical risk in dissolved oxygen modeling is time-of-day contamination. In tropical ponds, DO follows an extreme diurnal sinusoidal curve: it drops to a minimum (nadir) right before or during sunrise (~06:00–07:30) and surges to a supersaturated maximum in late afternoon (~15:30–17:00).

### 3.1 Time of Data Collection Distribution
Both visit $t$ (`curr_time`) and visit $t+1$ (`next_time`) were audited for time-of-day distribution:

| Sampling Time Window | Record Count | Percentage | Biological Phase |
| :--- | :---: | :---: | :--- |
| **06:00 – 06:59 AM** | 1,482 | 28.62% | Dawn respiration nadir (critical minimum) |
| **07:00 – 07:59 AM** | 3,124 | 60.33% | Early morning nadir (minimal photosynthetic onset) |
| **08:00 – 08:30 AM** | 572 | 11.05% | Early morning post-nadir |
| **> 09:00 AM** | 0 | 0.00% | *Zero daytime / afternoon contamination* |

- **Mean Sampling Time:** **07:12 AM** ($\pm 38$ minutes).
- **Confirmation:** Both current and next-visit DO measurements are **genuinely pre-dawn / early-morning nadir measurements**. There is zero contamination from midday or evening visits.

---

## 4. Revisit Intervals (`gap_days`) Distribution

Inspection of elapsed calendar days between consecutive inspections:

```
REVISIT INTERVAL DISTRIBUTION (gap_days)
-------------------------------------------------------------------------------------------------
Min         : 3.00 days (scheduled short-interval re-test)
10th Pct    : 8.68 days
25th Pct    : 14.03 days (biweekly inspection routine)
Median      : 21.00 days (three-week cycle)
Mean        : 21.81 days (+/- 10.03 days)
75th Pct    : 29.99 days (monthly monitoring cycle)
90th Pct    : 35.00 days
Max         : 44.99 days (maximum permitted transition)
-------------------------------------------------------------------------------------------------
```

### Gap Interval Bins
- **Short Horizon (3 to 7 days):** 441 pairs (8.52%) — intensive problem-pond follow-ups.
- **Biweekly Horizon (8 to 14 days):** 1,228 pairs (23.72%) — standard commercial biweekly schedule.
- **Triweekly Horizon (15 to 21 days):** 1,029 pairs (19.87%) — standard three-week inspection.
- **Monthly Horizon (22 to 30 days):** 1,675 pairs (32.35%) — routine monthly extension visits.
- **Extended Horizon (31 to 45 days):** 805 pairs (15.55%) — extended routine visits.

---

## 5. Distribution of Dissolved Oxygen & Hypoxia Targets

### 5.1 Continuous Summary Statistics

| Variable | Observations ($N$) | Mean (mg/L) | Std (mg/L) | Min (mg/L) | 25% | Median | 75% | Max (mg/L) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Current DO ($\text{DO}_t$)** | 5,178 | 3.485 | 0.823 | 0.000 | 3.200 | 3.500 | 3.900 | 14.600 |
| **Next-Visit DO ($\text{DO}_{t+1}$)** | 5,178 | 3.447 | 0.840 | 0.000 | 3.200 | 3.500 | 3.900 | 9.900 |
| **Delta DO ($\Delta\text{DO}$)** | 5,178 | -0.038 | 0.991 | -11.000 | -0.400 | 0.000 | +0.400 | +5.500 |

- The distribution of morning DO is centered between 3.2 and 3.9 mg/L (median 3.5 mg/L).
- Linear correlation between consecutive visits: **$r = 0.2892$ ($R^2 = 0.0836$)**.

### 5.2 Verification of Hypoxia Prevalence Thresholds

```
HYPOXIA THRESHOLD AUDIT (N = 5,178 Temporal Pairs)
-------------------------------------------------------------------------------------------------
Next DO < 3.0 mg/L (Moderate Hypoxia, Sub-lethal Stress)  : 649 events (12.53% prevalence)
Next DO < 2.0 mg/L (Severe Hypoxia, Acute Lethal Risk)    : 356 events ( 6.88% prevalence)
Next DO < 1.0 mg/L (Near-anoxic Emergency)               :  68 events ( 1.31% prevalence)
-------------------------------------------------------------------------------------------------
Current DO < 3.0 mg/L                                     : 566 events (10.93% prevalence)
Current DO < 2.0 mg/L                                     : 309 events ( 5.97% prevalence)
-------------------------------------------------------------------------------------------------
```

### 5.3 Hypoxia (< 3.0 mg/L) State Transition Dynamics

```
+-------------------------------------------------------------------------------+
| HYPOXIA TRANSITION MATRIX                                                     |
|                                                                               |
|                            Next Visit: Normal    Next Visit: Hypoxia (<3.0)   |
| Current Visit: Normal             4,168                    444  (9.63% onset) |
| Current Visit: Hypoxia (<3.0)       361  (63.78% recovery) 205 (36.22% persist|
+-------------------------------------------------------------------------------+
```

**Key Epidemiological Insight:**
- When current DO is normal ($\ge 3.0\text{ mg/L}$), **444 visits transition into hypoxia at the next visit**. This "new onset hypoxia" represents **68.4% of all hypoxia events**!
- When current DO is hypoxic ($< 3.0\text{ mg/L}$), the pond recovers to normal in **63.78% of cases** (due to emergency aeration, fresh water flushing, or reduced feeding).
- Consequently, a model that simply predicts persistence ($\hat{y}_{t+1} = y_t$) **misses 444 out of 649 hypoxia events (Recall = 31.59%)**. Predicting new onsets is the core clinical challenge.

---

## 6. Repeated Measurements & Target Overlap Audit

In longitudinal farm monitoring, consecutive temporal pairs are formed by sliding a window over visit dates:
- Transition $i$: $D_t \rightarrow D_{t+1}$
- Transition $i+1$: $D_{t+1} \rightarrow D_{t+2}$

### 6.1 Empirical Chaining Statistics
- **Total valid pairs:** 5,178 across 304 unique ponds.
- **Maximum possible chained transitions:** $5,178 - 304 = 4,874$.
- **Actual chained transitions with shared visit endpoints:** **4,176 pairs (85.68%)**.
- **Ponds with $\ge 10$ pairs:** 192 ponds (63.16%).

### 6.2 Statistical Implications & Anti-Leakage Rules
1. **Target Overlap:** The target value $\text{DO}_{t+1}$ in pair $i$ becomes the input feature $\text{DO}_t$ in pair $i+1$. 
2. **Invalidity of Standard K-Fold:** Standard random cross-validation would put pair $i$ in train and pair $i+1$ in test, creating massive label leakage.
3. **Mandatory GroupKFold by `pond_id`:** All pairs belonging to a given pond MUST remain entirely in train or entirely in test.
4. **Mandatory Clustered Inference:** Paired $t$-tests or non-parametric tests that treat pairs as independent i.i.d. observations will artificially inflate degrees of freedom tenfold. All hypothesis tests and confidence intervals must use **pond-clustered block-bootstrap resampling**.

---

## 7. Feature Space Inventory & Anti-Leakage Audit

### 7.1 Features Available at Visit $t$ (Candidate Feature Matrix)

| Feature Name | Category | Type / Units | Missingness | Leakage Status | Modeling Rationale |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `curr_do` | Water Sensor | Continuous (mg/L) | **0.00%** | SAFE | Mandatory initial morning DO anchor. |
| `curr_ph` | Water Sensor | Continuous (pH) | **0.00%** | SAFE | Carbonate buffer & phytoplankton respiration proxy. |
| `curr_temp_c` | Water Sensor | Continuous (°C) | **0.00%** | SAFE | Temperature governs oxygen solubility & bacterial BOD. |
| `curr_turbidity_cm`| Water Sensor | Continuous (cm) | 44.48% | SAFE | Secchi disk depth reflecting phytoplankton density. |
| `curr_tds_ppt` | Water Sensor | Continuous (ppt) | 49.19% | SAFE | Salinity / total dissolved solids. |
| `curr_water_color` | Water Visual | Categorical | 5.85% | SAFE | Bloom indicator (Dark green, Light green, Saturated). |
| `curr_weather` | Meteorology | Categorical | 6.62% | SAFE | Insolation conditions (Sunny, Cloudy, Rainy, Foggy). |
| `curr_feed_kg` | Management | Continuous (kg) | 6.47% | SAFE | Daily organic nutrient loading. |
| `curr_feed_per_acre`| Management | Continuous (kg/ac)| 14.52% | SAFE | Nutrient density per unit water surface. |
| `curr_stocking_density`| Biology | Continuous (#/ac) | 13.87% | SAFE | Cumulative fish respiration biomass pressure. |
| `curr_species` | Biology | Categorical | 23.99% | SAFE | Species tolerance (Rohu/Catla polyculture vs Pangasius). |
| `curr_weight` | Biology | Continuous (g) | 48.65% | SAFE | Fish size (larger fish have higher absolute O₂ demand). |
| `pond_area_acres`| Pond Profile | Continuous (acres)| 9.15% | SAFE | Surface area available for atmospheric gas diffusion. |
| `depth_meters` | Pond Profile | Continuous (m) | 0.21% | SAFE | Water column depth modulating thermal stratification. |
| `Equipment` | Farm Profile | Categorical | 0.21% | SAFE | Mechanical aeration capacity (aerators, water pumps). |
| `Feed type` | Management | Categorical | 0.21% | SAFE | Floating pellets vs mash (dissolution kinetics). |
| `gap_days` | Scheduling | Continuous (days) | **0.00%** | SAFE | Elapsed time interval to the next visit. |
| `day_of_year` | Seasonality | Continuous (1–365)| **0.00%** | SAFE | Captures tropical summer heat vs winter inversion. |
| `curr_time_hour` | Sampling | Continuous (hour) | **0.00%** | SAFE | Controls for slight pre-dawn vs post-dawn sampling drift.|

### 7.2 Features Strictly Excluded (Quarantined)

| Excluded Field | Source Table | Reason for Strict Exclusion |
| :--- | :--- | :--- |
| `next_do` | `water_quality.csv` | **Primary Target Variable.** Strictly barred from inputs. |
| `next_datetime`, `next_date` | `water_quality.csv` | Future metadata; barred from inputs. |
| `next_ph`, `next_temp_c`, etc. | `water_quality.csv` | Future sensor measurements at $t+1$; direct future leakage. |
| `DO (mg/L)_eve` (Evening DO) | `water_quality.csv` | Evening measurements are barred to ensure a pure morning-to-morning pipeline. |
| `Have fish been helped` | `water_quality.csv` | Post-inspection intervention; outcome-revealing. |
| `Corrective actions taken` | `water_quality.csv` | Unstandardized post-event farmer actions. |
| `Dead fish` (at $t+1$) | `water_quality.csv` | Future mortality outcome; direct leakage. |
| `pond_id` | Metadata | Retained strictly as grouping key for GroupKFold; excluded from features. |

---

## 8. Chronological Split & Event Balance Audit

Following the project-wide validation standard, observations are split chronologically at **2025-01-01 00:00:00**:

```
+---------------------------------------------------------------------------------------------------+
| CHRONOLOGICAL HOLD-OUT AUDIT (Cutoff: 2025-01-01)                                                 |
+---------------------+-------------------+---------------------+------------------+----------------+
| Partition           | Temporal Boundary | Pair Count (N)      | Unique Ponds     | Low-DO (<3.0)  |
+---------------------+-------------------+---------------------+------------------+----------------+
| Training Partition  | Both t, t+1 < 2025| 3,066 pairs (59.2%) | 225 unique ponds | 473 (15.43%)   |
| Quarantined Buffer  | t < 2025 <= t+1   |    78 pairs ( 1.5%) |  78 unique ponds |   4 ( 5.13%)   |
| Testing Partition   | Both t, t+1 >=2025| 2,034 pairs (39.3%) | 167 unique ponds | 172 ( 8.46%)   |
+---------------------+-------------------+---------------------+------------------+----------------+
| Reconciled Master   | Full Study Period | 5,178 pairs         | 304 unique ponds | 649 (12.53%)   |
+---------------------+-------------------+---------------------+------------------+----------------+
```

### 8.1 Severe Hypoxia (< 2.0 mg/L) Balance
- **Training Set:** 263 events (8.58% prevalence).
- **Quarantined Buffer:** 1 event (1.28% prevalence).
- **Testing Set:** 92 events (4.52% prevalence).

### 8.2 Audit Finding on Event Sufficiency
Both training ($N = 3,066$, 473 events) and testing ($N = 2,034$, 172 events) contain ample positive instances. The 172 test events provide high statistical power to evaluate Precision-Recall curves, Brier scores, and ROC-AUC without small-sample distortion.

---

## 9. Baseline Comparison & Benchmarking

Unlike Experiment 4 where Persistence was near-unbeatable, Persistence on Dissolved Oxygen performs poorly:

### 9.1 Continuous Regression Benchmark ($\hat{\text{DO}}_{t+1} = \text{DO}_t$)

| Evaluation Partition | Sample Size ($N$) | Persistence MAE (mg/L) | Persistence RMSE (mg/L) | Persistence $R^2$ |
| :--- | :---: | :---: | :---: | :---: |
| **Full Master Dataset** | 5,178 | **0.6669** | **0.9917** | **-0.3956** |
| **Chronological Train Set** | 3,066 | 0.7628 | 1.0971 | -0.3204 |
| **Chronological Test Set** | 2,034 | **0.5334** | **0.8237** | **-0.7071** |

*Interpretation:* A negative $R^2$ indicates that predicting the current DO value is substantially worse than simply predicting the historical mean ($\bar{\text{DO}} = 3.45\text{ mg/L}$).

### 9.2 Binary Classification Benchmark ($\hat{y}_{t+1} = \mathbb{I}(\text{DO}_t < 3.0)$)

| Partition | Accuracy | Balanced Accuracy | Precision | Recall | F1-Score | Confusion Matrix (TP / FP / FN / TN) |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Full Dataset** | 84.45% | 61.81% | 0.3622 | 0.3159 | **0.3374** | TP=205, FP=361, FN=444, TN=4,168 |
| **Training Set** | 83.04% | 65.43% | 0.4447 | 0.3996 | **0.4209** | TP=189, FP=236, FN=284, TN=2,357 |
| **Testing Set** | 86.18% | 51.29% | 0.1135 | 0.0930 | **0.1022** | TP=16, FP=125, FN=156, TN=1,737 |

*Interpretation:* On the prospective test set, Persistence achieves an F1-score of only **0.1022** and misses **156 out of 172 hypoxia crises (Recall = 9.30%)**. Machine learning models that incorporate feeding loads, pond area, depth, and weather have enormous headroom to outperform this baseline.

---

## 10. Confounding Factors & Operational Interventions

### 10.1 Aerator Ownership vs. Aerator Operation
In `enrolled_ponds_v2.csv`, farm equipment was audited:
- **Ponds with aerators:** 1,915 pairs (37.0%) belong to farms possessing paddlewheel or spiral aerators (e.g., "2 aerator, 1 water pump").
- **Ponds without aerators:** 3,263 pairs (63.0%).
- **Hypoxia Rate by Aerator Ownership:**
  - Ponds with aerators: **15.46% next-visit hypoxia** ($< 3.0$), **8.04% severe hypoxia** ($< 2.0$).
  - Ponds without aerators: **10.82% next-visit hypoxia** ($< 3.0$), **6.19% severe hypoxia** ($< 2.0$).

*Why do aerated ponds have higher hypoxia?*  
Larger, high-density commercial farms that stock more fish per acre and apply heavy feed are the exact farms that invest in aerators. However, field logs do **not** record whether the farmer actually ran the aerator during the night preceding inspection. If power failed or the farmer turned off the aerator to save electricity, DO collapses.

### 10.2 Emergency Unrecorded Farm Interventions
If a farmer observes fish air-gulping, they may:
1. Turn on diesel pumps to flush borewell water.
2. Apply chemical oxygen boosters (sodium percarbonate / hydrogen peroxide).
3. Cut daily feeding by 50–100%.
These interventions are rarely timestamped in routine inspection logs. Such unobserved rescues will appear in the model as apparent "false positive" alarms (the model predicted hypoxia based on high biomass and heavy feed, but the farmer intervened). In clinical aquaculture, an early warning that prompted successful preventive intervention is an operational success, even if it counts as a formal false positive.

---

## 11. Recommended Modeling & Evaluation Strategy

### 11.1 Dual Modeling Architecture
Experiment 5 should be structured as two complementary modeling tasks:
1. **Task A: Continuous DO Nadir Regression**
   - Target: $\text{DO}_{t+1}$ in mg/L.
   - Algorithms: Ridge Regression, Random Forest Regressor, Gradient Boosting Regressor (LightGBM / GBDT).
   - Metrics: MAE, RMSE, $R^2$, and Percentage Improvement over Persistence.
2. **Task B: Hypoxia Risk Classification**
   - Target: Binary $\text{Hypoxia}_{t+1} = \mathbb{I}(\text{DO}_{t+1} < 3.0\text{ mg/L})$.
   - Algorithms: Logistic Regression (balanced), Random Forest Classifier, Gradient Boosting Classifier.
   - Metrics: Precision-Recall AUC (PR-AUC), ROC-AUC, Brier Score, and Recall at fixed Precision/Top 20% risk.

### 11.2 Evaluation Protocols
- **Protocol 1 (Cross-Validation):** 5-Fold GroupKFold partitioned strictly by `pond_id`.
- **Protocol 2 (Chronological Evaluation):** Train on $N = 3,066$ ($< 2025$), quarantine 78 cross-cutoff pairs, evaluate prospectively on $N = 2,034$ ($\ge 2025$).
- **Protocol 3 (Statistical Rigor):** Pond-clustered block-bootstrap (5,000 resamples of 167 test ponds) to compute 95% confidence intervals and test for true statistical superiority over Persistence.

---

## 12. Final Feasibility Recommendation

```
===================================================================================================
FINAL FEASIBILITY VERDICT: RESOUNDING GO (APPROVED FOR EXPERIMENT 5 IMPLEMENTATION)
===================================================================================================
1. Target Data Completeness : 100% (Zero missing DO values across 12,399 records).
2. Sample Size & Ponds      : 5,178 valid temporal pairs across 304 unique ponds.
3. Event Abundance          : 649 moderate hypoxia events (<3.0) and 356 severe events (<2.0).
4. Morning Nadir Validity   : Confirmed early morning (06:00-08:30 AM), zero evening contamination.
5. Baseline Headroom        : Persistence baseline R² is negative (-0.71 on test), F1 is 0.10.
                              Massive headroom for ML models to learn organic and environmental signals.
6. Scientific Integrity     : Zero synthetic labels, point-in-time leakage-free pipeline.
===================================================================================================
```

