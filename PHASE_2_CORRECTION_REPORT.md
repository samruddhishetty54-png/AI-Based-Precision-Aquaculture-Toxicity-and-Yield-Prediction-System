# Phase 2 Scientific Corrections Report: Model Wrappers and Operational Benchmark Integrity

**Document ID:** `P2-CR-AQUASYSTEM-2026-FINAL`  
**Date:** 2026-11-05  
**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System (BAI507P Mini Project)  
**Scope:** Scientific & Metric Corrections of Phase 2 Wrappers (`app/models/`) and Test Suite (`app/tests/test_models.py`)  
**Status:** Complete & Fully Validated (Zero Retraining, Zero Dataset Modifications)  
**Author:** AI Technical Lead & Scientific Verification System  

---

## Executive Summary

Following the read-only audit in `PHASE_2_SCIENTIFIC_VERIFICATION.md`, strictly limited corrections were applied to the application model wrappers (`app/models/`) and test suite (`app/tests/test_models.py`). These corrections eliminate the unsupported 2.0 mg/L warning threshold in Experiment 1, correctly distinguish spatial cross-validation from chronological holdout benchmarks in Experiments 2 and 3, and ensure rigorous scientific accuracy throughout the application codebase.

### Core Summary of Corrections
1. **Experiment 1 (Ammonia Soft-Sensor):**
   - Removed every claim stating the model systematically underpredicts $\text{NH}_3$ spikes above $2.0\text{ mg/L}$.
   - Explained the physical chemistry distinction: The un-ionized $\text{NH}_3$ fraction depends on pH and temperature and is calculated using the Emerson equation. $2.0\text{ mg/L}$ is the TAN test-kit graduation, not an $\text{NH}_3$ toxicity threshold.
   - Incorporated the verified chronological holdout spike underprediction audit across audited $\text{NH}_3$ concentration tiers:
     - Actual $\text{NH}_3 \ge 0.05\text{ mg/L}$: **$79.59\%$ underpredicted** ($N = 98$, Mean Bias $= -0.0537\text{ mg/L}$, MAE $= 0.0666\text{ mg/L}$).
     - Actual $\text{NH}_3 \ge 0.10\text{ mg/L}$: **$100.00\%$ underpredicted** ($N = 33$, Mean Bias $= -0.1336\text{ mg/L}$, MAE $= 0.1336\text{ mg/L}$).
     - Actual $\text{NH}_3 \ge 0.20\text{ mg/L}$: **$100.00\%$ underpredicted** ($N = 10$, Mean Bias $= -0.2234\text{ mg/L}$, MAE $= 0.2234\text{ mg/L}$).
   - Emphasized that the soft-sensor is strictly experimental and must never be used as an independent safety alarm.

2. **Experiment 2 (Fish Mortality Diagnostic):**
   - Replaced spatial GroupKFold cross-validation metrics ($\text{ROC-AUC} = 0.7712, \text{PR-AUC} = 0.0821$) with strict chronological holdout benchmarks ($2025\text{--}2026, N = 2,600, 44$ mortalities, baseline prevalence $= 1.69\%$):
     - **Logistic Regression (Primary Benchmark):** $\text{ROC-AUC} = 0.5917$, $\text{PR-AUC} = 0.0499$, $\text{Recall} = 20.45\%$ (detected 9 of 44 mortalities), $\text{Precision} = 3.81\%$ (9 true positives out of 236 alarms; 227 false alarms), $\text{F1} = 0.0643$.
     - **Random Forest (Alternative Benchmark, $\tau = 0.40$):** $\text{ROC-AUC} = 0.7322$, $\text{PR-AUC} = 0.0648$, $\text{Recall} = 13.64\%$ (detected 6 of 44 mortalities), $\text{Precision} = 11.54\%$ (6 true positives out of 52 alarms; 46 false alarms), $\text{F1} = 0.1250$.
   - Preserved GroupKFold spatial metrics strictly as historical reference in `spatial_groupkfold_reference`, clearly labeled as unsuitable for predicting future temporal performance.

3. **Experiment 3 (Next-Visit Ammonia Risk):**
   - Explicitly clarified the temporal horizon: discrete multi-week revisit intervals of $3\text{ to }45$ days (median 22 days). Confirmed that this is **NOT an hourly, diurnal, or overnight forecast**.
   - Replaced pooled spatial GroupKFold metrics ($\text{PR-AUC} = 0.3461, \text{ROC-AUC} = 0.8137$) with strict chronological holdout benchmarks ($2025\text{--}2026, N = 2,034$ pairs, 57 events, baseline prevalence $= 2.80\%$):
     - **Random Forest (Primary Benchmark):** $\text{PR-AUC} = 0.0305$ (near no-skill baseline of $0.0280$), $\text{ROC-AUC} = 0.5061$ (near random coin toss of $0.5000$), $\text{Recall} = 31.58\%$ (18 of 57 events), $\text{Precision} = 2.63\%$ (18 total true positives out of 684 alarms; 666 false alarms), $\text{F1} = 0.0486$.
     - **Logistic Regression (Alternative Benchmark):** $\text{PR-AUC} = 0.0309$, $\text{ROC-AUC} = 0.5010$, $\text{Recall} = 36.84\%$ (21 of 57 events), $\text{Precision} = 2.36\%$, $\text{F1} = 0.0444$.
     - **Persistence Baseline:** $\text{Recall} = 5.26\%$ (3 total true positives out of 57 events), completely blind to newly developed spikes ($0/54$, $0.0\%$ sensitivity).
   - Documented that for Random Forest, 18 total true positives were detected, distinguishing 15 of 54 newly developed spikes ($27.8\%$ sensitivity) plus 3 persistent spikes, while ranking discrimination was severely compressed by the 2026 test-kit protocol shift.

4. **Zero Model Retraining & Zero Data Modification:**
   - All pre-trained model artifacts (`baseline_toxicity_v1/`, `experiment_2_mortality_v1/`, `experiment_3_next_visit_risk_v1/`) remain 100% bit-for-bit unchanged.
   - All 10 audited datasets in `processed_data_v2/` remain 100% bit-for-bit identical to their verified SHA-256 hashes.
   - Test suite updated and verified: **29/29 tests pass** in both `unittest` and `pytest`.

---

## 1. Module-by-Module Code Changes

### 1.1 Experiment 1: Ammonia Soft-Sensor (`app/models/exp1_soft_sensor.py`)

#### Problem Corrected
The previous wrapper text stated:
> *"Under chronological validation, it systematically underpredicted dangerous acute ammonia spikes (> 2.0 mg/L)."*

This was scientifically flawed. The un-ionized $\text{NH}_3$ fraction depends on pH and temperature and is calculated using the Emerson equation. $2.0\text{ mg/L}$ is the TAN test-kit graduation, not an $\text{NH}_3$ toxicity threshold. In the dataset, the maximum calculated $\text{NH}_3$ value is $0.684\text{ mg/L}$.

#### Implementation Changes
1. **Module Docstring:** Corrected to explain that the un-ionized $\text{NH}_3$ fraction depends on pH and temperature and is calculated using the Emerson equation, that molecular un-ionized ammonia ($\text{NH}_3$) is distinct from Total Ammonia Nitrogen (TAN), and that $2.0\text{ mg/L}$ is the TAN test-kit graduation, not an $\text{NH}_3$ toxicity threshold.
2. **Runtime Warning & Limitations:** Updated warning string to state:
   ```python
   "warning": (
       "EXPERIMENTAL SOFT-SENSOR ESTIMATE ONLY: Estimates un-ionized ammonia proxy "
       "from physical water quality parameters. Under chronological holdout validation (2025–2026), "
       "it systematically underpredicted dangerous acute ammonia spikes: 79.59% underpredicted at "
       "actual NH3 >= 0.05 mg/L (N=98), 100.0% underpredicted at actual NH3 >= 0.10 mg/L (N=33), "
       "and 100.0% underpredicted at actual NH3 >= 0.20 mg/L (N=10). It must NEVER be used as an "
       "independent safety alarm, regulatory compliance metric, or certified laboratory measurement."
   )
   ```
3. **Structured Audit Metadata:** Added a `chronological_underprediction_audit` dictionary to `get_metadata()`:
   ```python
   "chronological_underprediction_audit": {
       "nh3_ge_0_05_mg_l": {"count": 98, "underprediction_pct": 79.59, "mean_bias_mg_l": -0.05371, "mae_mg_l": 0.06664},
       "nh3_ge_0_10_mg_l": {"count": 33, "underprediction_pct": 100.00, "mean_bias_mg_l": -0.13358, "mae_mg_l": 0.13358},
       "nh3_ge_0_20_mg_l": {"count": 10, "underprediction_pct": 100.00, "mean_bias_mg_l": -0.22343, "mae_mg_l": 0.22343},
       "max_holdout_underestimation_error_mg_l": 0.50540,
       "note": (
           "2.0 mg/L is the TAN test-kit graduation, not an NH3 toxicity threshold. "
           "The un-ionized NH3 fraction depends on pH and temperature and is calculated using the Emerson equation."
       )
   }
   ```

---

### 1.2 Experiment 2: Fish Mortality Diagnostic (`app/models/exp2_mortality.py`)

#### Problem Corrected
Initial wrapper documentation presented spatial GroupKFold cross-validation metrics ($\text{ROC-AUC} = 0.771, \text{PR-AUC} = 0.082$) without clearly identifying them as spatial CV. On the chronological holdout test set (unseen future production cycles in 2025–2026), model ranking discrimination was significantly lower.

#### Implementation Changes
1. **Module Docstring:** Explicitly separated the **Chronological Holdout Benchmark** from the **Spatial GroupKFold Reference**.
2. **Runtime Warning:** Updated to highlight chronological performance:
   ```python
   "warning": (
       "ADVISORY DIAGNOSTIC ONLY: Evaluates concurrent statistical association between "
       "environmental water parameters and mortality events. Due to extreme natural "
       "class imbalance (1.69% test prevalence) and low precision (chronological holdout "
       "PR-AUC = 0.0499, precision = 3.81%), this model generates frequent false alarms "
       "(227 false alarms vs. 9 true detections). It must NOT be used to trigger automated "
       "operational mortality alerts."
   )
   ```
3. **Structured Benchmark Metadata:** Updated `get_metadata()` with distinct dictionaries:
   ```python
   "chronological_holdout_benchmark": {
       "cohort": "2025–2026 Holdout Test (N = 2,600, Positives = 44, Prevalence = 1.69%)",
       "no_skill_baseline_pr_auc": 0.0169,
       "logistic_regression": {
           "roc_auc": 0.5917,
           "pr_auc": 0.0499,
           "recall": 0.2045,
           "precision": 0.0381,
           "f1_score": 0.0643,
           "true_positives": 9,
           "false_positives": 227
       },
       "random_forest_tuned": {
           "roc_auc": 0.7322,
           "pr_auc": 0.0648,
           "recall": 0.1364,
           "precision": 0.1154,
           "f1_score": 0.1250,
           "true_positives": 6,
           "false_positives": 46
       }
   },
   "spatial_groupkfold_reference": {
       "cohort": "5-Fold GroupKFold OOF across all historical dates (N = 5,122, Positives = 75, Prev = 1.46%)",
       "logistic_regression": {"roc_auc": 0.7712, "pr_auc": 0.0821},
       "random_forest": {"roc_auc": 0.8137, "pr_auc": 0.0934},
       "caution": "GroupKFold metrics evaluate spatial cross-validation and MUST NOT be presented as future temporal forecasting ability."
   }
   ```

---

### 1.3 Experiment 3: Next-Visit Ammonia Risk (`app/models/exp3_ammonia_risk.py`)

#### Problem Corrected
Previous reports highlighted the spatial cross-validation score of $\text{PR-AUC} = 0.346$, which did not represent the operational reality of forecasting future production cycles where test-kit protocols changed. Furthermore, the forecast horizon required unambiguous labeling to prevent confusion with real-time or overnight forecasts.

#### Implementation Changes
1. **Module Docstring:** Emphasized that the model operates strictly over discrete multi-week revisit intervals ($3 \le \Delta t \le 45$ days, median 22 days), and is not an hourly or overnight forecast.
2. **Runtime Warning:** Explicitly documented chronological holdout degradation:
   ```python
   "warning": (
       "EXPLORATORY MULTI-WEEK ESTIMATE ONLY: Evaluates transition risk over discrete revisit "
       "intervals of 3 to 45 days (median 22 days). This is NOT an hourly or overnight forecast. "
       "Chronological holdout validation (2025–2026) showed performance close to the no-skill baseline "
       "(PR-AUC = 0.0305 vs. no-skill 0.0280; ROC-AUC = 0.5061 vs. random 0.5000) due to field kit "
       "protocol shifts. Do NOT use for automatic operational alerts."
   )
   ```
3. **Structured Benchmark Metadata:** Updated `get_metadata()` with verified chronological metrics:
   ```python
   "chronological_holdout_benchmark": {
       "cohort": "2025–2026 Holdout Test (N = 2,034 pairs, Positives = 57, Prevalence = 2.80%)",
       "no_skill_baseline_pr_auc": 0.0280,
       "random_forest": {
           "pr_auc": 0.0305,
           "roc_auc": 0.5061,
           "recall": 0.3158,
           "precision": 0.0263,
           "f1_score": 0.0486,
           "total_true_positives": 18,
           "true_positives": 18,
           "false_positives": 666,
           "newly_developed_spikes_detected": "15 / 54 (27.8%)",
           "new_spikes_detected": "15 / 54 (27.8%)",
           "detection_distinction": "18 total true positives (15 of 54 newly developed spikes + 3 persistent spikes)"
       },
       "logistic_regression": {
           "pr_auc": 0.0309,
           "roc_auc": 0.5010,
           "recall": 0.3684,
           "precision": 0.0236,
           "f1_score": 0.0444,
           "total_true_positives": 21,
           "true_positives": 21,
           "false_positives": 868,
           "newly_developed_spikes_detected": "18 / 54 (33.3%)",
           "new_spikes_detected": "18 / 54 (33.3%)",
           "detection_distinction": "21 total true positives (18 of 54 newly developed spikes + 3 persistent spikes)"
       },
       "persistence_baseline": {
           "recall": 0.0526,
           "precision": 0.0577,
           "f1_score": 0.0550,
           "total_true_positives": 3,
           "newly_developed_spikes_detected": "0 / 54 (0.0% [BLIND])",
           "new_spikes_detected": "0 / 54 (0.0% [BLIND])",
           "detection_distinction": "3 total true positives (0 of 54 newly developed spikes + 3 persistent spikes)"
       }
   },
   "spatial_groupkfold_reference": {
       "cohort": "5-Fold GroupKFold OOF across all historical dates (N = 4,900 pairs, Positives = 314, Prev = 6.41%)",
       "random_forest": {"pr_auc": 0.3461, "roc_auc": 0.8137, "recall": 0.6115, "precision": 0.2471},
       "logistic_regression": {"pr_auc": 0.2893, "roc_auc": 0.7876, "recall": 0.7134, "precision": 0.1833},
       "caution": "GroupKFold metrics evaluate spatial cross-validation and MUST NOT be presented as future temporal forecasting ability."
   }
   ```

---

### 1.4 Test Suite Alignment (`app/tests/test_models.py`)

The test suite in `app/tests/test_models.py` was updated to rigorously verify the scientific corrections:
- `test_exp1_soft_sensor_prediction_and_metadata`:
  - Asserted that `"> 2.0 mg/L"` is **NOT** in `meta["warning"]` or `meta["limitations"]`.
  - Asserted that `"0.05 mg/L"`, `"0.10 mg/L"`, and `"0.20 mg/L"` are present in `meta["warning"]`.
  - Asserted that `chronological_underprediction_audit` dictionary exists and contains accurate sub-dictionaries.
- `test_exp2_mortality_diagnostic_prediction_and_metadata`:
  - Asserted that `chronological_holdout_benchmark` exists in metadata.
  - Asserted that `logistic_regression["roc_auc"] == 0.5917` and `logistic_regression["pr_auc"] == 0.0499`.
  - Asserted that `spatial_groupkfold_reference` exists and contains caution text.
- `test_exp3_next_visit_ammonia_risk_prediction_and_metadata`:
  - Asserted that `"3 to 45 days"` and `"NOT an hourly or overnight forecast"` are in `res["warning"]`.
  - Asserted that `chronological_holdout_benchmark` exists with `random_forest["pr_auc"] == 0.0305`.
  - Asserted that `spatial_groupkfold_reference` exists.

---

## 2. Quantitative Verification Matrix

The table below reconciles the original audited ground truth against the corrected Phase 2 implementation:

```
+==================================================================================================================================+
|                                    PHASE 2 SCIENTIFIC CORRECTION VERIFICATION MATRIX                                             |
+------------+-------------------------------+-----------------------------------+-------------------------------------------------+
| Module     | Attribute                     | Before Correction (Inaccurate)    | After Correction (Verified Ground Truth)        |
+------------+-------------------------------+-----------------------------------+-------------------------------------------------+
| Exp 1      | Underpredicted Spike Threshold| "> 2.0 mg/L"                      | Audited NH3 concentration tiers:                 |
|            |                               |                                   | >= 0.05 mg/L: 79.59% underpredicted (N=98)      |
|            |                               |                                   | >= 0.10 mg/L: 100.0% underpredicted (N=33)      |
|            |                               |                                   | >= 0.20 mg/L: 100.0% underpredicted (N=10)      |
|            |                               |                                   | (2.0 mg/L is TAN test-kit graduation)            |
+------------+-------------------------------+-----------------------------------+-------------------------------------------------+
| Exp 2      | Primary Reported Metrics      | ROC-AUC = 0.771, PR-AUC = 0.082   | Chronological Holdout (N = 2,600, Prev = 1.69%):|
|            |                               | (Spatial GroupKFold CV)           | LR ROC-AUC = 0.5917, PR-AUC = 0.0499            |
|            |                               |                                   | LR Recall = 20.45%, Precision = 3.81%           |
|            |                               |                                   | (GroupKFold metrics labeled as spatial ref)     |
+------------+-------------------------------+-----------------------------------+-------------------------------------------------+
| Exp 3      | Forecast Horizon Definition   | "Next visit" (Ambiguous)          | Multi-week revisit intervals of 3 to 45 days    |
|            |                               |                                   | (Median 22 days; NOT an hourly/overnight model) |
+------------+-------------------------------+-----------------------------------+-------------------------------------------------+
| Exp 3      | Headline PR-AUC Metric        | PR-AUC = 0.346                    | Chronological Holdout (N = 2,034, Prev = 2.80%):|
|            |                               | (Spatial GroupKFold CV)           | RF PR-AUC = 0.0305 (No-skill baseline = 0.0280) |
|            |                               |                                   | RF ROC-AUC = 0.5061 (Random = 0.5000)           |
|            |                               |                                   | RF: 18 total TP (15/54 new spikes detected)     |
|            |                               |                                   | Baseline: 3 total TP (0/54 new spikes detected) |
+------------+-------------------------------+-----------------------------------+-------------------------------------------------+
```

---

## 3. Test Suite Execution & Verification

Both `unittest` and `pytest` test runners were executed to verify that all modules and test cases pass cleanly:

### 3.1 Pytest Execution Summary
```text
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.7.0 -- C:\Python314\python.exe
rootdir: D:\AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System
collected 29 items

app/tests/test_chemistry.py ...........                                  [ 37%]
app/tests/test_data_manager.py ........                                  [ 65%]
app/tests/test_models.py ..........                                      [100%]

====================== 29 passed, 7564 warnings in 5.45s ======================
```

### 3.2 Unittest Execution Summary
```text
Ran 29 tests in 4.223s

OK
```

All 29 tests pass with zero errors and zero failures.

---

## 4. Preservation of Data & Model Artifacts

To guarantee research integrity and compliance with project governance:
1. **Model Artifacts:**
   - `baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib`: Unmodified (60,490,447 bytes).
   - `experiment_2_mortality_v1/models/logistic_regression_pipeline.joblib`: Unmodified (3,098 bytes).
   - `experiment_2_mortality_v1/models/random_forest_pipeline.joblib`: Unmodified (15,907,030 bytes).
   - `experiment_3_next_visit_risk_v1/models/random_forest_pipeline.joblib`: Unmodified (14,401,960 bytes).
   - `experiment_3_next_visit_risk_v1/models/logistic_regression_pipeline.joblib`: Unmodified (3,164 bytes).
2. **Processed Datasets:**
   - All 10 CSV and JSON files in `processed_data_v2/` match their verified SHA-256 hashes exactly.

---

## 5. Summary & Sign-Off

The scientific corrections to Phase 2 are complete, robustly tested, and strictly aligned with the audited research findings:
- The misleading $2.0\text{ mg/L}$ claim has been eliminated.
- Spatial GroupKFold and chronological holdout metrics are cleanly distinguished across all models.
- Revisit horizons ($3\text{ to }45$ days) are clearly communicated to prevent operational misapplication.
- All code changes are defensive, backward-compatible, and fully validated.

**Status:** Phase 2 is officially complete. Execution is halted awaiting user review and explicit authorization prior to commencing Phase 3 (Fish Growth and Feeding Module Integration).

