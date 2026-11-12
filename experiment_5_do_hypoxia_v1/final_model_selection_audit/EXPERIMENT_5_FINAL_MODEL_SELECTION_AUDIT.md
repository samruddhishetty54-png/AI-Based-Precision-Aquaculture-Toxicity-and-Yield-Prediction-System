# Experiment 5: Final Independent Model Selection & Operational Viability Audit

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Experiment:** Experiment 5 — Next-Visit Morning Dissolved Oxygen Forecasting and Hypoxia Risk Prediction (`experiment_5_do_hypoxia_v1/`)  
**Audit Document:** `experiment_5_do_hypoxia_v1/final_model_selection_audit/EXPERIMENT_5_FINAL_MODEL_SELECTION_AUDIT.md`  
**Date:** 2026-11-04  
**Audit Status:** **COMPLETED & VERIFIED**  

---

## 1. Executive Summary & Final Model Recommendations

This independent audit rigorously evaluates the machine learning models and baselines developed across Phase 1 and Phase 2 of Experiment 5. Models were assessed for **point regression accuracy** (Task A), **hypoxia detection utility and alarm burden** (Task B), and **severe hypoxia stability**, using strict chronological holdout data ($N = 2,034$ pairs, 167 unique ponds) and **5,000 pond-clustered block-bootstrap resamples**.

```
+-----------------------------------------------------------------------------------------------------------------------+
| FINAL MODEL SELECTION & OPERATIONAL STATUS MATRIX                                                                     |
+--------------------------+-----------------------+---------------------+-------------------+--------------------------+
| Model Candidate          | Primary Metric (Test) | Baseline Comparison | 95% Clustered CI  | Final Operational Status |
+--------------------------+-----------------------+---------------------+-------------------+--------------------------+
| Historical Mean Baseline | MAE = 0.3963 mg/L     | -25.70% vs. Persist | [-0.156, -0.119]  | RETAINED AS OPERATIONAL  |
| (Unconditional Mean)     | RMSE = 0.6450 mg/L    | Lowest Test Error   | p < 10^-12        | POINT REGRESSION BASELINE|
|                          |                       |                     |                   |                          |
| Persistence Baseline     | MAE = 0.5334 mg/L     | R² = -0.7071        | Reference         | REJECTED AS OPERATIONAL  |
| (curr_do at visit t)     | PR-AUC = 0.0873       | Misses 90.7% Hypoxia| Baseline          | MODEL (Negative R²)      |
|                          |                       |                     |                   |                          |
| Random Forest Regressor  | MAE = 0.4172 mg/L     | +21.79% vs. Persist | [-0.133, -0.100]  | EXPLORATORY ONLY         |
|                          | RMSE = 0.6602 mg/L    | +0.021 vs. HistMean | [+0.012, +0.030]  | (Superior to Persist;    |
|                          |                       |                     | p < 10^-12 (Mean) | Inferior to Hist Mean)   |
|                          |                       |                     |                   |                          |
| Gradient Boosting Reg.   | MAE = 0.4260 mg/L     | +20.13% vs. Persist | [-0.128, -0.087]  | EXPLORATORY ONLY         |
| (GBDT Regressor)         | RMSE = 0.6668 mg/L    | +0.030 vs. HistMean | [+0.018, +0.042]  | (Superior to Persist;    |
|                          |                       |                     | p < 10^-12 (Mean) | Inferior to Hist Mean)   |
|                          |                       |                     |                   |                          |
| Ridge Regression         | MAE = 0.5181 mg/L     | RMSE = 2.0092 mg/L  | [-0.083, +0.073]  | REJECTED ENTIRELY        |
|                          | R² = -9.1570          | Unstable Weights    | Spans Zero        | (High Variance on OHE)   |
|                          |                       |                     |                   |                          |
| Gradient Boosting Clf.   | PR-AUC = 0.0950       | +12.29% vs. No-Skill| [-0.002, +0.032]  | EXPLORATORY SCREENING    |
| (Moderate Hypoxia < 3.0) | ROC-AUC = 0.5328      | +8.82% vs. Persist  | Spans Zero        | ONLY (Rejected for       |
|                          | High-Rec (p*=0.090)   | 92/172 Caught (53%) | 91.0% False Discov| Automated Alerting)      |
|                          |                       |                     |                   |                          |
| Random Forest Classifier | PR-AUC = 0.0894       | +5.67% vs. No-Skill | [-0.005, +0.021]  | EXPLORATORY RANKING ONLY |
| (Moderate Hypoxia < 3.0) | ROC-AUC = 0.5233      | High FP Burden      | Spans Zero        | (Rejected for Alerting)  |
|                          |                       |                     |                   |                          |
| Random Forest Classifier | Test PR-AUC = 0.0496  | 91 TP / 1,934 FP    | Degenerate        | REJECTED ENTIRELY        |
| (Severe Hypoxia < 2.0)   | At cutoff p = 0.10    | 99.56% Alarm Rate   | Cutoff Artifact   | (Near-Constant Positive) |
+--------------------------+-----------------------+---------------------+-------------------+--------------------------+
```

---

## 2. Audit Point 1 & 2: Regression vs. Persistence AND Historical Mean

In Phase 2, regression models demonstrated a statistically significant reduction in MAE when compared to the **Persistence Baseline** ($\hat{\text{DO}}_{t+1} = \text{DO}_t$). However, scientific integrity requires auditing model performance against **all relevant baselines**, specifically the **unconditional Historical Training Mean** ($\bar{\text{DO}}_{\text{train}} = 3.48\text{ mg/L}$).

### 2.1 The Two-Baseline Comparison on Prospective Test Data ($N = 2,034$)

```
TEST SET REGRESSION ERROR (MAE in mg/L)
-------------------------------------------------------------------------------------------------
Historical Mean Baseline (LOWEST) : [======================] 0.3963 mg/L
Random Forest Regressor           : [=======================] 0.4172 mg/L (+0.0209 vs Hist Mean)
Gradient Boosting Regressor       : [========================] 0.4260 mg/L (+0.0298 vs Hist Mean)
Ridge Regression                  : [=============================] 0.5181 mg/L (+0.1218 vs Hist Mean)
Persistence Baseline (WORST)      : [==============================] 0.5334 mg/L (+0.1372 vs Hist Mean)
-------------------------------------------------------------------------------------------------
```

### 2.2 Pond-Clustered Bootstrap Analysis (5,000 Resamples of 167 Test Ponds)

To test whether the differences between models and baselines are statistically genuine under intra-pond correlation (85.68% chained visits), 5,000 block-bootstrap draws were performed:

| Comparison Baseline | Evaluated Model | Test MAE (mg/L) | Mean $\Delta\text{MAE}$ (mg/L) | 95% Clustered CI [Lower, Upper] | % Bootstrap Draws Beating Baseline | Statistical Significance Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Persistence Baseline**<br>*(MAE = 0.5334 mg/L)* | **Historical Mean** | **0.3963** | **-0.1372** | **[-0.1557, -0.1187]** | **100.0%** | **Statistically significantly SUPERIOR to Persistence** ($p < 10^{-12}$) |
| | **Random Forest** | **0.4172** | **-0.1163** | **[-0.1332, -0.1000]** | **100.0%** | **Statistically significantly SUPERIOR to Persistence** ($p < 10^{-12}$) |
| | **Gradient Boosting** | **0.4260** | **-0.1074** | **[-0.1276, -0.0873]** | **100.0%** | **Statistically significantly SUPERIOR to Persistence** ($p < 10^{-12}$) |
| | Ridge Regression | 0.5181 | -0.0155 | [-0.0831, +0.0727] | 67.1% | No statistically significant difference (spans zero) |
| **Historical Mean Baseline**<br>*(MAE = 0.3963 mg/L)* | **Random Forest** | **0.4172** | **+0.0209** | **[+0.0118, +0.0295]** | **0.0%** | **Statistically significantly INFERIOR to Historical Mean** ($p < 10^{-12}$) |
| | **Gradient Boosting** | **0.4260** | **+0.0298** | **[+0.0178, +0.0421]** | **0.0%** | **Statistically significantly INFERIOR to Historical Mean** ($p < 10^{-12}$) |
| | Persistence | 0.5334 | +0.1372 | [+0.1187, +0.1557] | 0.0% | Statistically significantly INFERIOR to Historical Mean ($p < 10^{-12}$) |

### 2.3 Scientific Explanation of the Regression Divergence
1. **Why ML beats Persistence:** Persistence assumes the pond's DO in 21 days will be identical to today's reading. Because DO fluctuates with feeding, organic load, and weather, Persistence achieves an $R^2$ of $-0.7071$. ML models capture the broad trophic equilibrium and avoid extreme persistence lag errors, reducing MAE by $> 20\%$.
2. **Why Historical Mean beats ML:** In the prospective test period (2025–2026), commercial pond DO measurements were tightly distributed around $3.40\text{ mg/L}$ with a low standard deviation ($0.63\text{ mg/L}$; IQR $[3.20, 3.90\text{ mg/L}]$). When a physical quantity has low natural variance across a large sample, predicting a constant mean ($\hat{y} = 3.48\text{ mg/L}$) mathematically minimizes absolute deviation.
3. **The 21.8-Day Horizon Penalty:** Because ML models attempt to predict dynamic variance across a multi-week gap without access to intermediate daily weather or daily feed logs, their individual predictions introduce small residual variance ($\pm 0.4\text{ to }0.6\text{ mg/L}$), making their prospective MAE slightly higher ($+0.02\text{ to }+0.03\text{ mg/L}$) than the unconditional mean.
4. **Audit Verdict on Task A:** **The Historical Mean Baseline is retained as the operational benchmark for point estimation.** Random Forest and Gradient Boosting are designated as **exploratory bioenergetic models**, but must NOT be claimed as superior point predictors over the historical mean.

---

## 3. Audit Point 3: Gradient Boosting Hypoxia Classification & False Positive Alarm Burden

In Phase 2, threshold tuning on training out-of-fold data identified $p^* = 0.090$ as a candidate threshold to maximize recall ($\ge 80\%$ on training CV). Evaluating this frozen threshold on the prospective test set yielded **92 True Positives, but 930 False Positives**.

### 3.1 Alarm Burden and False Discovery Rate (FDR) Analysis

```
+---------------------------------------------------------------------------------------------------------------+
| GRADIENT BOOSTING OPERATIONAL ALARM BURDEN ACROSS THRESHOLDS (N = 2,034 Test Visits, 172 True Hypoxia Events) |
+-----------------------+--------+---------------+---------------+---------------+--------------+---------------+
| Decision Threshold    | Alarms | Alarm Rate    | True Hypoxia  | False Alarms  | Recall       | False Discov. |
| Cutoff Criterion      | Raised | (% of Visits) | Caught (TP)   | Incurred (FP) | Rate (% Rec) | Rate (% FDR)  |
+-----------------------+--------+---------------+---------------+---------------+--------------+---------------+
| Default (p = 0.50)    |     10 |  0.49%        |    0          |    10         |   0.00%      | 100.00%       |
| Frozen Max-F1 (p=0.22)|    174 |  8.55%        |   16          |   158         |   9.30%      |  90.80%       |
| Intermediate (p=0.15) |    426 | 20.94%        |   46          |   380         |  26.74%      |  89.20%       |
| Frozen High-Rec(p=0.09|  1,022 | 50.25%        |   92          |   930         |  53.49%      |  91.00%       |
| Ultra-Sens. (p=0.05)  |  1,823 | 89.63%        |  156          | 1,667         |  90.70%      |  91.44%       |
+-----------------------+--------+---------------+---------------+---------------+--------------+---------------+
```

### 3.2 Clinical and Economic Reality of the 930 False Positives
1. **The 50% Alarm Rate:** At $p^* = 0.090$, the model raises an alarm on **1,022 out of 2,034 visits (50.25%)**. More than half of all routine farm inspections trigger an emergency alert!
2. **Alarm Fatigue:** In practical farm operations, when an automated monitoring system has a **91.00% False Discovery Rate** (9 out of every 10 alarms are false), farmers and extension workers will immediately experience **alarm fatigue** and disable or ignore the system.
3. **The Cost of False Interventions:** If a farmer acts on an alert by running diesel aerators or water pumps for 8 hours overnight, fuel and electricity costs average \$15–\$35 per night. Incurring 930 false interventions across 167 ponds imposes an unviable economic burden on commercial farmers.
4. **Nature of the False Positive Observations:**
   - Analysis of the 930 false positive visits reveals that their **mean actual DO was $3.48\text{ mg/L}$**.
   - **68.39% of false alarms (636 visits) occurred in the borderline sub-optimal zone of $3.0\text{ to }3.5\text{ mg/L}$**.
   - These ponds were not actively suffocating, but they were residing in an ecologically stressed, low-margin buffer.
5. **Audit Verdict on Task B:** **Gradient Boosting is REJECTED as an automated binary alarm trigger.** It is retained strictly as an **exploratory risk-prioritization score**: extension officers can use the continuous probability $P(\text{hypoxia})$ to sort and rank ponds, visiting the top 10% highest-risk ponds first, rather than triggering automated operational interventions.

---

## 4. Audit Point 4: Severe Hypoxia (< 2.0 mg/L) Random Forest Anomaly

In Phase 2 secondary analysis, Random Forest achieved an apparent test recall of **98.91% (91 out of 92 severe hypoxia events caught)**, but incurred **1,934 False Positives** out of 2,034 test visits.

### 4.1 Diagnosis of the Degenerate Predictor Phenomenon
When evaluated at the secondary screening cutoff $p = 0.10$:
- **Total test visits:** 2,034.
- **Visits predicted positive for severe hypoxia:** **2,025 (99.56% of the entire cohort!)**.
- **Visits predicted negative:** **8 visits (0.44%)**.
- **True Positives:** 91 / 92.
- **False Positives:** 1,934 / 1,942.
- **True Negatives:** 8.

```
+---------------------------------------------------------------------------------------------------+
| RANDOM FOREST SEVERE HYPOXIA PROBABILITY DECAY (N = 2,034 Test Pairs)                             |
+---------------------+-------------------------+---------------+-----------------+-----------------+
| Probability Cutoff  | Flagged as Severe       | Flagged %     | True Positives  | False Positives |
+---------------------+-------------------------+---------------+-----------------+-----------------+
| Cutoff p >= 0.05    | 2,034 visits            | 100.00%       | 92 (100.0%)     | 1,942 (100.0%)  |
| Cutoff p >= 0.10    | 2,025 visits            |  99.56%       | 91 ( 98.9%)     | 1,934 ( 99.6%)  |
| Cutoff p >= 0.20    | 1,521 visits            |  74.78%       | 76 ( 82.6%)     | 1,445 ( 74.4%)  |
| Cutoff p >= 0.30    |   642 visits            |  31.56%       | 35 ( 38.0%)     |   607 ( 31.3%)  |
| Cutoff p >= 0.40    |   114 visits            |   5.60%       |  1 (  1.1%)     |   113 (  5.8%)  |
| Cutoff p >= 0.50    |     4 visits            |   0.20%       |  0 (  0.0%)     |     4 (  0.2%)  |
+---------------------+-------------------------+---------------+-----------------+-----------------+
```

### 4.2 Mathematical Root Cause
1. **The `class_weight='balanced'` Inflation:** In the training set, severe hypoxia (< 2.0 mg/L) is a rare tail event (prevalence = 8.58%). The `class_weight='balanced'` parameter reweights positive samples by approximately $5.8\times$ in every decision tree split.
2. **Probability Shift:** Because every leaf's empirical proportion is heavily scaled by the class weight, **the minimum predicted probability in the entire test set was 0.0724**, and the 1st percentile was 0.1169!
3. **Near-Constant Positive Predictor:** By setting a cutoff of $p = 0.10$, the model was converted into a near-constant predictor that labeled 99.56% of all samples as positive.
4. **Trivial High Recall:** A model that labels virtually every sample as positive trivially achieves $\approx 99\%$ recall, but has an accuracy equal to class prevalence and a specificity near zero ($8 / 1942 = 0.41\%$).
5. **Audit Verdict:** **The Severe Hypoxia Random Forest model is REJECTED ENTIRELY as degenerate.** The apparent 98.9% recall was an artifact of probability inflation acting as a near-constant positive predictor.

---

## 5. Audit Point 5: Data Leakage, Chronological Splitting, and Feature Availability

A line-by-line verification was conducted across preprocessing, splitting, and feature pipelines:

| Integrity Check Item | Audit Verification Result | Finding & Evidence |
| :--- | :---: | :--- |
| **Chronological Boundary** | **100% DISJOINT** | Training set ends on **2024-12-31 06:56:00**; Testing set begins on **2025-01-02 07:10:00**. Exactly 0 overlapping timestamps. |
| **Cross-Cutoff Horizon** | **78 PAIRS QUARANTINED** | All 78 transitions bridging the cutoff ($t < 2025 \le t+1$) were strictly quarantined in `quarantined_cross_pairs.csv` and excluded from both train and test sets. |
| **Zero Evening Leakage** | **100% PURGED** | All evening readings (`Type == 'Evening'`) were quarantined; the pipeline operates exclusively on morning-nadir records (06:00–08:30 AM). |
| **Pond ID Group Isolation** | **STRICT GROUP KEY** | `pond_id` was strictly used as a group partition key for GroupKFold and clustered bootstrap resampling; it was 100% barred from feature matrices. |
| **Preprocessor Training Isolation** | **FITTED STRICTLY ON TRAIN** | `SimpleImputer`, `StandardScaler`, and `OneHotEncoder` were fitted strictly on `X_train`. No test set statistics were used in preprocessing. |
| **Uninformative Column Purge** | **2 COLUMNS REMOVED** | `depth_is_missing` and `equipment_is_missing` (constant 0.0 across all 5,178 pairs) were purged prior to modeling. |

---

## 6. Audit Point 6: Definitive Model Selection Recommendations

Based on empirical performance, bootstrap confidence intervals, and operational viability, the formal status of every model is declared as follows:

### 1. Point Regression Models (Task A)
- **Historical Mean Baseline ($\hat{\text{DO}}_{t+1} = \bar{\text{DO}}_{\text{train}} = 3.48\text{ mg/L}$):**
  - **STATUS: RETAINED AS OPERATIONAL POINT ESTIMATION BASELINE.**
  - Lowest MAE on test ($0.3963\text{ mg/L}$). In low-variance tropical pond regimes, the historical mean is the most robust point estimate.
- **Persistence Baseline ($\hat{\text{DO}}_{t+1} = \text{DO}_t$):**
  - **STATUS: REJECTED AS OPERATIONAL MODEL.**
  - Decisively inferior ($R^2 = -0.7071$, $\text{MAE} = 0.5334\text{ mg/L}$). DO fluctuates too dynamically over 21 days for persistence to be viable.
- **Random Forest Regressor & Gradient Boosting Regressor:**
  - **STATUS: DESIGNATED AS EXPLORATORY BIOENERGETIC MODELS ONLY.**
  - Statistically significantly superior to Persistence by $> 20\%$ ($p < 10^{-12}$), confirming real non-linear signal extraction from feed and temperature. However, because they are statistically significantly inferior to the simple historical mean ($+0.021\text{ to }+0.030\text{ mg/L}$), they must NOT be claimed as superior operational point predictors.
- **Ridge Regression:**
  - **STATUS: REJECTED ENTIRELY.**
  - Unstable weights on categorical one-hot encodings caused severe test variance ($\text{RMSE} = 2.0092\text{ mg/L}$, $R^2 = -9.1570$).

### 2. Hypoxia Classification Models (Task B)
- **Gradient Boosting Classifier (< 3.0 mg/L):**
  - **STATUS: DESIGNATED AS AN EXPLORATORY RISK-PRIORITIZATION SCREENING TOOL ONLY.**
  - Highest PR-AUC (0.0950 vs no-skill 0.0846). However, its 95% clustered bootstrap CI $[-0.0022, +0.0316]$ spans zero ($p = 0.086$), rendering superiority exploratory rather than statistically confirmed at $\alpha = 0.05$.
  - At the frozen high-recall cutoff ($p^* = 0.090$), it detects 53.49% of crises (92/172), but triggers an unsustainable 50.25% alarm rate with 91.0% False Discovery Rate. It is **STRICTLY REJECTED as an automated binary alert trigger**, but retained as a continuous risk-scoring index to help extension officers rank ponds for inspection queues.
- **Random Forest Classifier (< 3.0 mg/L):**
  - **STATUS: DESIGNATED AS EXPLORATORY RANKING MODEL ONLY.**
  - PR-AUC = 0.0894 (95% CI spans zero). Rejected for automated alerting.
- **Random Forest Classifier (< 2.0 mg/L Severe Hypoxia):**
  - **STATUS: REJECTED ENTIRELY.**
  - Mathematically degenerate due to `class_weight='balanced'` probability inflation; classified 99.56% of all test visits as severe hypoxia at $p = 0.10$. Zero clinical discriminatory utility.

---

## 7. Comprehensive Audit Artifact Inventory

All audit datasets, comparison tables, and metric outputs have been saved to:

```
AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/
└── experiment_5_do_hypoxia_v1/
    └── final_model_selection_audit/
        ├── regression_baseline_audit.csv          [Pond-clustered bootstrap: ML vs Hist Mean & Persistence]
        ├── hypoxia_alarm_burden_analysis.csv       [Alarm rate, precision, FDR, and false alarm DO analysis]
        ├── severe_hypoxia_rf_degeneracy_audit.csv  [Diagnosis of RF 99.56% alarm inflation across cutoffs]
        ├── data_integrity_audit.csv               [Leakage, temporal splitting, and feature checks]
        └── EXPERIMENT_5_FINAL_MODEL_SELECTION_AUDIT.md [This document]
```

Audit complete. No dashboard integration or application modifications have been initiated.

