# Phase 4 Final Acceptance Audit Report: Dissolved Oxygen & Hypoxia Module Integration

**Document ID:** `P4-FAA-AQUASYSTEM-2026-FINAL`  
**Date:** November 11, 2026  
**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System (BAI507P Mini Project)  
**Audit Scope:** Independent Final Read-Only Acceptance Audit of Phase 4 Implementation (`app/models/do_hypoxia.py`, `app/models/registry.py`, `app/tests/test_do_hypoxia.py`, `app/tests/test_models.py`, Experiment 5 Audit Alignment, and Phases 1–3 Preservation)  
**Audit Mode:** Independent Read-Only Formal Review (Zero source code edits, zero model retraining, zero dataset modifications)  
**Overall Phase 4 Final Verdict:** **ACCEPTED**  

---

## 1. Executive Summary & Audit Decision

This independent final acceptance audit evaluates the integration of Experiment 5 (Dissolved Oxygen Forecasting & Hypoxia Risk Prediction) into the application architecture.

### Scope of Verification
1. **Scientific Correctness:** Audited training mean DO ($3.4984\text{ mg/L} \approx 3.50\text{ mg/L}$), historical point benchmark designation (not dynamic biological prediction), exact test MAE ($0.3963\text{ mg/L}$) and RMSE ($0.6450\text{ mg/L}$), exploratory status of Gradient Boosting moderate-hypoxia classifier ($p^* = 0.090$, 1,022 alerts, 930 false alarms, 92 true positives, 80 false negatives, 91.0% FDR), complete rejection of the degenerate severe-hypoxia Random Forest classifier, and multi-week revisit horizon ($3 \le \Delta t \le 45$ days) with zero hourly/overnight claims.
2. **Implementation & Safety:** Comprehensive physical input validations ($0.0 \le \text{DO} \le 25.0\text{ mg/L}$, temperature, pH, positive revisit intervals), rejection of NaN, infinite, and non-numeric values, graceful handling of optional missing features, structural simulation isolation (`SIMULATED_SCENARIO_ONLY`, `operational_use_permitted = False`), and fault-isolated central model registry integration.
3. **Test Suite Execution & Cryptographic Integrity:** 100% pass rate across both `unittest` (79/79) and `pytest` (79 passed, 4 subtests passed); 100% cryptographic match against original pre-Phase-4 SHA-256 hashes across all 10 datasets in `processed_data_v2/` and all 9 pre-trained `.joblib` model artifacts.
4. **Preservation of Previous Phases:** Zero regression or drift across Phase 1 (Emerson dissociation chemistry, data manager), Phase 2 (soft-sensor, mortality diagnostic, ammonia risk wrappers), and Phase 3 (persistence fish growth, rule-based feeding advisor).

### Global Decision Summary
- **Total Audit Checkpoints:** 12 / 12 **PASS**
- **Test Suite Results:**
  - `unittest`: **79 / 79 tests PASSED** (0 failures, 0 errors, runtime: 4.86s)
  - `pytest`: **79 / 79 tests PASSED**, 4 subtests PASSED (100% pass rate, runtime: 6.58s)
- **Dataset Immutability:** 10 / 10 datasets in `processed_data_v2/` confirmed **100% bit-for-bit unchanged** via pre-Phase-4 baseline SHA-256 hashes.
- **Model Artifact Immutability:** 9 / 9 pre-trained `.joblib` model files confirmed **100% bit-for-bit unchanged** via pre-Phase-4 baseline SHA-256 hashes.
- **Final Verdict:** **ACCEPTED** (System is fully verified; Phase 5 has not been started).

---

## 2. Check-by-Check Acceptance Audit Matrix

| Check ID | Verification Dimension | Target Files & References | Core Criteria | Verdict |
| :---: | :--- | :--- | :--- | :---: |
| **AUD-01** | **Historical Mean DO Accuracy & Designation** | `app/models/do_hypoxia.py` (L38–L40, L174–L186)<br>`experiment_5_do_hypoxia_v1/data/train_pairs.csv` | Exact training mean of 3.4984 mg/L (~3.50 mg/L); designated as constant historical benchmark, NOT dynamic prediction. | **PASS** |
| **AUD-02** | **Regression Benchmark Metrics Alignment** | `app/models/do_hypoxia.py` (L180–L208)<br>`experiment_5_do_hypoxia_v1/metrics/phase2_regression_metrics.csv` | MAE = 0.3963 mg/L and RMSE = 0.6450 mg/L match audit; persistence MAE = 0.5334 mg/L rejected ($R^2 = -0.7071$). | **PASS** |
| **AUD-03** | **GBDT Moderate Hypoxia Exploratory Screening** | `app/models/do_hypoxia.py` (L209–L227, L366–L381)<br>`experiment_5_do_hypoxia_v1/metrics/phase2_classification_metrics.csv` | Status exploratory only; threshold $p^* = 0.090$, 1,022 alerts, 930 false positives, 92 true positives, 80 false negatives reported. | **PASS** |
| **AUD-04** | **Rejection of Severe Hypoxia RF Classifier** | `app/models/do_hypoxia.py` (L228–L240, L382–L393)<br>`experiment_5_do_hypoxia_v1/final_model_selection_audit/` | Severe RF model rejected as degenerate; 99.56% alarm rate and `class_weight='balanced'` probability inflation documented. | **PASS** |
| **AUD-05** | **Prediction Horizon & Environmental Disclaimers** | `app/models/do_hypoxia.py` (L158–L165, L358–L364)<br>`app/tests/test_do_hypoxia.py` (L269–L278) | Horizon is next-visit morning DO (3–45 days); zero claims of hourly, overnight, real-time, or continuous nadir forecasts. | **PASS** |
| **AUD-06** | **Provisional Status & No-Control Guardrails** | `app/models/do_hypoxia.py` (L24–L27, L394–L401)<br>`app/tests/test_do_hypoxia.py` (L113–L116) | Decision-support only; `is_automatic_control = False`, `control_action = None`; no actuator/aerator commands executed. | **PASS** |
| **AUD-07** | **Physical Input Validation & Bounds** | `app/models/do_hypoxia.py` (L255–L314)<br>`app/tests/test_do_hypoxia.py` (L146–L223) | Validates $0.0 \le \text{DO} \le 25.0\text{ mg/L}$, temperature, pH, positive revisit interval; rejects NaN, inf, negatives, strings. | **PASS** |
| **AUD-08** | **Missing Optional Values & Alias Resolution** | `app/models/do_hypoxia.py` (L48–L72, L325–L340)<br>`app/tests/test_do_hypoxia.py` (L118–L144, L225–L242) | Resolves common aliases (`curr_do`, `dissolved_oxygen_mg_l`, `DO`); safely handles NaNs in turbidity, TDS, feed, weight. | **PASS** |
| **AUD-09** | **Simulated-Data Isolation & Gating** | `app/models/do_hypoxia.py` (L327–L355)<br>`app/tests/test_do_hypoxia.py` (L244–L262) | Simulated inputs enforce `status = "SIMULATED_SCENARIO_ONLY"`, `operational_use_permitted = False`, demonstration warning. | **PASS** |
| **AUD-10** | **Central Registry Integration & Fault Isolation** | `app/models/registry.py` (L32, L46, L57, L65, L157–L162)<br>`app/tests/test_do_hypoxia.py` (L280–L315) | Registered as 6th model; `predict_do_hypoxia()` domain method added; broken artifact does not crash other 5 models. | **PASS** |
| **AUD-11** | **Preservation of Phases 1, 2, and 3** | `app/core/chemistry.py`<br>`app/core/data_manager.py`<br>`app/models/exp1_4.py`, `feeding_advisor.py` | Emerson formulas, dataset isolation, soft-sensor tiers, mortality benchmarks, fish growth persistence intact. | **PASS** |
| **AUD-12** | **Test Suite & Cryptographic Immutability** | Full unittest & pytest suites<br>Pre-Phase-4 SHA-256 hash comparison | 79/79 tests pass (100%); 10/10 datasets and 9/9 pre-trained model artifacts match original pre-Phase-4 hashes. | **PASS** |

---

## 3. Scientific Correctness Verification

### 3.1 Historical Mean Baseline Accuracy & Benchmark Designation
- **Audited Training Mean DO:**
  - File inspected: `experiment_5_do_hypoxia_v1/data/train_pairs.csv` ($N = 3,066$ training pairs).
  - Exact calculated mean of `next_do`: $3.498369210697978\text{ mg/L}$.
  - Implementation in `app/models/do_hypoxia.py` Line 39: `HISTORICAL_TRAIN_MEAN_DO: float = 3.4984` and `HISTORICAL_TRAIN_MEAN_DISPLAY: float = 3.50`.
  - **Verdict:** **EXACT MATCH.**
- **Point Prediction Benchmark Nature:**
  - Implementation in `app/models/do_hypoxia.py` Lines 174–186 & Lines 360–362:
    `"point_prediction_method": "Historical Training Mean Baseline (unconditional 3.50 mg/L)"`
  - Explicit narrative in docstrings and warnings:
    > *"Predicted next-visit DO is an unconditional historical training mean (3.50 mg/L), NOT a dynamic biological or bioenergetic prediction."*
  - **Verdict:** **EXACT MATCH.**
- **Error Metrics Against Audit Report:**
  - File inspected: `experiment_5_do_hypoxia_v1/metrics/phase2_regression_metrics.csv` & `final_model_selection_audit/EXPERIMENT_5_FINAL_MODEL_SELECTION_AUDIT.md`.
  - Historical Mean Baseline test metrics: $\text{MAE} = 0.3963\text{ mg/L}$, $\text{RMSE} = 0.6450\text{ mg/L}$.
  - Persistence Baseline test metrics: $\text{MAE} = 0.5334\text{ mg/L}$, $\text{RMSE} = 0.8237\text{ mg/L}$, $R^2 = -0.7071$.
  - Random Forest Regressor: $\text{MAE} = 0.4172\text{ mg/L}$, $\text{RMSE} = 0.6602\text{ mg/L}$.
  - Gradient Boosting Regressor: $\text{MAE} = 0.4260\text{ mg/L}$, $\text{RMSE} = 0.6668\text{ mg/L}$.
  - Implementation in `DOHypoxiaModel.get_metadata()` Lines 187–208: All four models and metrics are recorded exactly as audited.
  - **Verdict:** **EXACT MATCH.**

---

### 3.2 Gradient Boosting Moderate Hypoxia Classifier (< 3.0 mg/L)
- **Status:** Labeled strictly as `EXPLORATORY_SCREENING_RANKING_ONLY`.
- **Classification Metrics on Prospective Test Cohort ($N = 2,034$ visits, 172 true hypoxia events, base rate 8.46%):**
  - File inspected: `experiment_5_do_hypoxia_v1/metrics/phase2_classification_metrics.csv` (Row 10).
  - Frozen High-Recall Threshold: $p^* = 0.090$ (train OOF recall $\ge 80\%$).
  - Prospective Test Confusion Matrix: $\text{TP} = 92$, $\text{FP} = 930$, $\text{FN} = 80$, $\text{TN} = 932$.
  - Total Alerts Raised: $\text{TP} + \text{FP} = 92 + 930 = \mathbf{1,022\text{ alerts}}$ ($\mathbf{50.25\%}$ of all test visits).
  - True Hypoxia Caught: $\text{TP} = \mathbf{92}$ (Recall = $92 / 172 = \mathbf{53.49\%}$).
  - False Alarms Incurred: $\text{FP} = \mathbf{930}$.
  - Missed Hypoxia Crises: $\text{FN} = 172 - 92 = \mathbf{80}$.
  - False Discovery Rate (FDR): $930 / 1,022 = \mathbf{91.00\%}$ (Precision = $9.00\%$).
  - Overall Test PR-AUC: $0.0950$ (vs. no-skill $0.0846$, persistence $0.0873$).
  - Clustered Bootstrap 95% Confidence Interval: $[-0.0022, +0.0316]$ spans zero ($p = 0.086$), confirming superiority is directional rather than statistically conclusive at $\alpha = 0.05$.
- **Audit Findings in `app/models/do_hypoxia.py`:**
  - Lines 209–227 and Lines 366–381 document every single one of these exact figures: threshold 0.090, 1,022 alerts, 930 false alarms, 92 true positives, 80 false negatives, 91.00% FDR, and 50.25% alarm rate.
  - Explains the economic cost of false alarms (\$15–\$35 per night per pond in unnecessary aeration) and severe alarm fatigue.
  - **Verdict:** **EXACT MATCH.**

---

### 3.3 Rejection of Severe Hypoxia Random Forest Classifier (< 2.0 mg/L)
- **Operational Status:** Labeled strictly as `REJECTED ENTIRELY AS DEGENERATE`.
- **Degeneracy Diagnosis:**
  - Files inspected: `experiment_5_do_hypoxia_v1/final_model_selection_audit/severe_hypoxia_rf_degeneracy_audit.csv` & `secondary_severe_hypoxia_metrics.csv`.
  - Cutoff $p = 0.10$ test evaluation:
    * Total visits predicted positive: $\mathbf{2,025\text{ out of }2,034}$ ($\mathbf{99.56\%}$ alarm rate).
    * True Positives: 91 / 92 ($98.91\%$ apparent recall).
    * False Positives: 1,934 / 1,942.
    * Specificity: $8 / 1,942 = \mathbf{0.41\%}$.
  - Root Cause: Applying `class_weight='balanced'` on an 8.58% rare training event shifted the minimum predicted probability in the test set to $0.0724$ and the 1st percentile to $0.1169$. The $p = 0.10$ cutoff trivially classified $99.56\%$ of the cohort as positive, acting as a near-constant positive predictor with zero clinical discrimination.
- **Audit Findings in `app/models/do_hypoxia.py`:**
  - Lines 228–240 & Lines 382–393 permanently attach this rejection notice and mathematical root cause to output payloads.
  - Severe hypoxia predictions cannot be output as usable operational guidance.
  - **Verdict:** **EXACT MATCH.**

---

### 3.4 Prediction Horizon & Environmental Disclaimers
- Revisit interval strictly defined as routine inspection visits spanning **3 to 45 days** (mean 21.8 days, median 21.0 days).
- Sample collection time anchored to morning respiration nadirs (06:00–08:30 AM).
- Module docstrings (Lines 11–13), metadata (Lines 158–165), output dictionary (Lines 358–364), and tests (`test_prediction_horizon_disclaimers`) explicitly state:
  > *"Strictly NOT an hourly, diurnal, overnight, or real-time nadir forecast."*
- Zero claims of continuous IoT sensor streaming or automatic nocturnal aeration control.
- **Verdict:** **EXACT MATCH.**

---

## 4. Implementation and Safety Verification

### 4.1 Physical Input Validations & Bounds
Line-by-line inspection of [`app/models/do_hypoxia.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/do_hypoxia.py#L255-L314):
1. **Mandatory Dissolved Oxygen (`curr_do`):**
   - Missing check: raises `ValueError("Missing required core input feature 'curr_do'...")`.
   - Non-numeric check: raises `ValueError("Must be a valid numeric quantity")`.
   - NaN check: raises `ValueError("Dissolved oxygen cannot be NaN.")`.
   - Infinite check: raises `ValueError("Dissolved oxygen cannot be infinite.")`.
   - Negative check: raises `ValueError("Dissolved oxygen cannot be negative. Received: {curr_do} mg/L.")`.
   - Physical upper saturation bound: raises `ValueError("Dissolved oxygen exceeds physical aquaculture saturation bounds (> 25.0 mg/L)...")`.
2. **Water Temperature (`temp_c`):**
   - Physical bounds check: $\text{Temp} \le -273.15^\circ\text{C}$ or $\text{Temp} > 60.0^\circ\text{C}$ raises `ValueError("Water temperature is physically impossible...")`.
3. **Water pH (`ph`):**
   - Standard range check: $\text{pH} < 0.0$ or $\text{pH} > 14.0$ raises `ValueError("Water pH must be within physical range (0.0 to 14.0)...")`.
4. **Revisit Interval (`gap_days`):**
   - Positive interval check: $\text{gap\_days} \le 0.0$ raises `ValueError("Revisit interval gap_days must be strictly positive...")`.
5. **Safe Mode:**
   - In `predict(features, safe_mode=True)`, validation errors are captured and returned safely as:
     `{"is_valid": False, "status": "INVALID_PHYSICAL_MEASUREMENT", "explanation": str(exc), "operational_use_permitted": False}`.

### 4.2 Handling of Missing Values & Aliases
1. Optional features (`curr_turbidity_cm`, `curr_tds_ppt`, `curr_feed_amount_kg`, `curr_weight`, `curr_stocking_density`) can be omitted or passed as `np.nan` without error.
2. Robust alias resolution:
   - `curr_do`: resolved across `["curr_do", "dissolved_oxygen_mg_l", "DO (mg/L)", "do_mg_l", "DO", "current_do"]`.
   - `temp_c`: resolved across `["curr_temp_c", "curr_temp", "temp_c", "Temp (in °C)", "temperature_c"]`.
   - `ph`: resolved across `["curr_ph", "ph", "pH"]`.
   - `gap_days`: resolved across `["gap_days", "revisit_interval_days", "days"]`.

### 4.3 Simulated-Data Separation
Inspection of Lines 327–355 in `app/models/do_hypoxia.py`:
- Checks `is_simulated` (supports boolean or string `"true"`, `"1"`, `"yes"`) and `data_source` containing `"simulat"` or `"synthetic"`.
- When simulated:
  - `status = "SIMULATED_SCENARIO_ONLY"`
  - `operational_use_permitted = False`
  - Attached `demonstration_warning`:
    > *"SIMULATED SCENARIO ONLY (DEMONSTRATION): This output was generated from synthetic or simulated benchmark data. It is intended strictly for model demonstration and testing, and MUST NOT be used to guide actual commercial pond management, aeration decisions, or live biological operations."*

### 4.4 Central Model Registry Integration & Fault Isolation
Inspection of [`app/models/registry.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/registry.py):
1. **Registered Models (Line 59):** Aggregates 6 models: `exp1_soft_sensor`, `exp2_mortality`, `exp3_ammonia_risk`, `fish_growth`, `feeding_advisor`, and `do_hypoxia`.
2. **Domain Method (Lines 157–162):** `predict_do_hypoxia(features)` cleanly delegates to `self.do_hypoxia_model.predict(features)`.
3. **Fault Isolation Proof:**
   - Evaluated in `app/tests/test_do_hypoxia.py::test_registry_fault_isolation_with_broken_do_hypoxia`.
   - When `do_hypoxia_path` points to a missing/broken artifact (`Path("broken_folder/non_existent_exp5.joblib")`):
     * `do_hypoxia.is_loaded` evaluates to `False`.
     * `registry.health_check()` reports `all_models_loaded = False` and `total_loaded = 5` (out of 6).
     * `models["do_hypoxia"]["loaded"] = False`.
     * All remaining five models (`exp1`, `exp2`, `exp3`, `fish_growth`, `feeding_advisor`) remain 100% loaded and execute predictions without error.
   - Evaluated in `app/tests/test_models.py::test_registry_partial_failure_tolerance`.
   - When `exp1_path` points to a broken artifact:
     * `do_hypoxia` remains loaded (`loaded = True`) and fully operational alongside `exp2` and `exp3`.

---

## 5. Verification of Tests and Cryptographic Integrity

### 5.1 Test Suite Results
Both test suites were executed independently in the workspace virtual environment (`.venv`):

#### Unittest Execution:
- **Command:** `python -m unittest discover -s app/tests -p "test_*.py" -v`
- **Total Tests Collected:** 79 tests
- **Result:** **79 PASSED, 0 FAILURES, 0 ERRORS** (Runtime: 4.861s)

#### Pytest Execution:
- **Command:** `python -m pytest app/tests/ -v`
- **Total Tests Collected:** 79 test functions + 4 subtests
- **Result:** **79 passed, 4 subtests passed** (Runtime: 6.58s, 100% pass rate)

#### Pytest Warnings Audit:
- Total warnings: 8,994 warning events.
- All 8,994 warnings are the identical third-party `DeprecationWarning` from `joblib/numpy_pickle.py:207` (`array.shape = self.shape`) when loading pre-trained models under NumPy 2.5+.
- **Zero (0)** warnings originate from application code in `app/`.
- **Zero (0)** numerical or runtime warnings.

---

### 5.2 Cryptographic Dataset and Model Artifact Verification
Every dataset and pre-trained model artifact was hashed with SHA-256 and compared directly against the **original pre-Phase-4 baseline hashes** recorded in `PHASE_3_FINAL_ACCEPTANCE_AUDIT.md`:

#### Audited Datasets (`processed_data_v2/`):
| File Name | Original Pre-Phase-4 SHA-256 Baseline | Current Computed SHA-256 Hash | Integrity Status |
| :--- | :--- | :--- | :---: |
| `dropouts_v2.csv` | `12b7e730aac7ae9e4eed0b89d3a98489ac6cd3c72d55cd4f9b4e3d6dd424d250` | `12b7e730aac7ae9e4eed0b89d3a98489ac6cd3c72d55cd4f9b4e3d6dd424d250` | **MATCH (Unchanged)** |
| `enrolled_ponds_v2.csv` | `94dae8de04c53891af6550afa39a8df8920b67f4b347d01cf9aa5f73aaa16e57` | `94dae8de04c53891af6550afa39a8df8920b67f4b347d01cf9aa5f73aaa16e57` | **MATCH (Unchanged)** |
| `feeding_analysis_v2.csv` | `c6cf43d6449d81ed7d591f4bbcf5a74a880a6c0f89bcda126f065921a5b3a582` | `c6cf43d6449d81ed7d591f4bbcf5a74a880a6c0f89bcda126f065921a5b3a582` | **MATCH (Unchanged)** |
| `fish_health_growth_analysis_v2.csv` | `2ed226697d2b7999e3b15b1604ac574b005144598f6cf35fbacf8b7ba2f0023f` | `2ed226697d2b7999e3b15b1604ac574b005144598f6cf35fbacf8b7ba2f0023f` | **MATCH (Unchanged)** |
| `iot_water_model_v2.csv` | `4a577164b2836ffb77ab2f102eea2c8ab5a9898d88590c3cf969808b370ea5af` | `4a577164b2836ffb77ab2f102eea2c8ab5a9898d88590c3cf969808b370ea5af` | **MATCH (Unchanged)** |
| `preprocessing_v2_report.json` | `b163443291beccefea488270e7dde780d20aad806ab95cd1b1f59ec5d6205333` | `b163443291beccefea488270e7dde780d20aad806ab95cd1b1f59ec5d6205333` | **MATCH (Unchanged)** |
| `preprocessing_v2_report.md` | `66775bbf0ee2a5c423f5d9e372cd0692cff432908d03f476a0e49c6c2323058c` | `66775bbf0ee2a5c423f5d9e372cd0692cff432908d03f476a0e49c6c2323058c` | **MATCH (Unchanged)** |
| `thresholds_config.json` | `7aad8fc6df5cebfb311b0ca97d6764f25eb313c35814740ad0d8e6953cad3e94` | `7aad8fc6df5cebfb311b0ca97d6764f25eb313c35814740ad0d8e6953cad3e94` | **MATCH (Unchanged)** |
| `toxicity_analysis_v2.csv` | `073f5ab11da085160dcb0821e4a16533d96555f8587261c0bd348f385c60c462` | `073f5ab11da085160dcb0821e4a16533d96555f8587261c0bd348f385c60c462` | **MATCH (Unchanged)** |
| `water_quality_cleaned_v2.csv` | `500b2d6fd032eeabb6d1b947dbc6d93b4464c146d41d9e91f4a0367f54f50e1b` | `500b2d6fd032eeabb6d1b947dbc6d93b4464c146d41d9e91f4a0367f54f50e1b` | **MATCH (Unchanged)** |

#### Pre-Trained Model Artifacts (`.joblib`):
| File Path | Original Pre-Phase-4 SHA-256 Baseline | Current Computed SHA-256 Hash | Integrity Status |
| :--- | :--- | :--- | :---: |
| `baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib` | `e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a` | `e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a` | **MATCH (Unchanged)** |
| `experiment_1_sensor_ablation_v1/models/model_a_rf_pipeline.joblib` | `e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a` | `e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a` | **MATCH (Unchanged)** |
| `experiment_1_sensor_ablation_v1/models/model_b_rf_pipeline.joblib` | `08907e58a01036eaadb44b6c10370e0219b920ddaa07279504b6e101a0f4a281` | `08907e58a01036eaadb44b6c10370e0219b920ddaa07279504b6e101a0f4a281` | **MATCH (Unchanged)** |
| `experiment_2_mortality_v1/models/dummy_prior_pipeline.joblib` | `c6259edd0a0908614ba93b3faa78256359098c4461576ec08d40ae46714985fa` | `c6259edd0a0908614ba93b3faa78256359098c4461576ec08d40ae46714985fa` | **MATCH (Unchanged)** |
| `experiment_2_mortality_v1/models/logistic_regression_pipeline.joblib` | `02c8a34ae4ff8b8d907beeed18be4ecd00bb463cd204e8298163f6864afcdadf` | `02c8a34ae4ff8b8d907beeed18be4ecd00bb463cd204e8298163f6864afcdadf` | **MATCH (Unchanged)** |
| `experiment_2_mortality_v1/models/random_forest_pipeline.joblib` | `464344d33ffc3cff26726bfa15ec73d6b8a59b773ae61083db3d3082f44b4216` | `464344d33ffc3cff26726bfa15ec73d6b8a59b773ae61083db3d3082f44b4216` | **MATCH (Unchanged)** |
| `experiment_3_next_visit_risk_v1/models/dummy_prior_pipeline.joblib` | `2a51e871bbf2fa4d0d5f7a3c1f0dcbfc49499418383cc887514112bf8fa0de8b` | `2a51e871bbf2fa4d0d5f7a3c1f0dcbfc49499418383cc887514112bf8fa0de8b` | **MATCH (Unchanged)** |
| `experiment_3_next_visit_risk_v1/models/logistic_regression_pipeline.joblib` | `957aea9b8cd0066e364c776c76b12128b7b8e63cafe9800cbda39a03d8486ad7` | `957aea9b8cd0066e364c776c76b12128b7b8e63cafe9800cbda39a03d8486ad7` | **MATCH (Unchanged)** |
| `experiment_3_next_visit_risk_v1/models/random_forest_pipeline.joblib` | `2f7980756c02a5fa00e325919944c8dd416456d785af9f110135e10edd38853c` | `2f7980756c02a5fa00e325919944c8dd416456d785af9f110135e10edd38853c` | **MATCH (Unchanged)** |

---

## 6. Verification of Previous Phases (Phases 1–3)

1. **Phase 1 (Chemistry & Data Management):**
   - [`app/core/chemistry.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/core/chemistry.py): Emerson dissociation constants, pKa temperature dependence ($0.09018 + 2729.92 / T_K$), molecular weight conversion ratio ($17.031 / 14.007$) applied once for TAN-N and zero times for TAN-NH3, and absolute preservation of NaNs verified unchanged. All 11 tests in `test_chemistry.py` pass.
   - [`app/core/data_manager.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/core/data_manager.py): Read-only dataset access, defensive caching, and strict separation between historical field inspection logs and synthetic hourly IoT simulation models verified unchanged. All 8 tests in `test_data_manager.py` pass.
2. **Phase 2 (Experiments 1–3 Wrappers):**
   - [`app/models/exp1_soft_sensor.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/exp1_soft_sensor.py): Underprediction warnings across audited concentration tiers (actual $\ge 0.05$: 79.59%, $\ge 0.10$: 100%, $\ge 0.20$: 100%), TAN 2.0 mg/L as test-kit graduation, and experimental status verified unchanged.
   - [`app/models/exp2_mortality.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/exp2_mortality.py): Chronological holdout Logistic Regression primary benchmark (ROC-AUC 0.5917, PR-AUC 0.0499, recall 20.45%, precision 3.81%), and GroupKFold documented strictly as spatial reference verified unchanged.
   - [`app/models/exp3_ammonia_risk.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/exp3_ammonia_risk.py): Chronological holdout Random Forest benchmark (PR-AUC 0.0305, ROC-AUC 0.5061, recall 31.58%, precision 2.63%), distinguishing 18 total true positives from 15 of 54 newly developed spikes detected verified unchanged.
3. **Phase 3 (Fish Growth & Feeding Advisor):**
   - [`app/models/fish_growth.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/fish_growth.py): Persistence baseline ($\hat{W}_{t+1} = W_t$), MAE = 93.38 g benchmark, input validation ($W > 0$), and commercial harvest yield disclaimers verified unchanged. All 11 tests in `test_fish_growth.py` pass.
   - [`app/models/feeding_advisor.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/feeding_advisor.py): Provisional rule-based DO and ammonia throttles, TAN 2.0 mg/L test-kit graduation wording, simulation gating (`SIMULATED_SCENARIO_ONLY`, `operational_use_permitted = False`), and observational feedback tracking verified unchanged. All 21 tests in `test_feeding_advisor.py` pass.

---

## 7. Directory Architecture & Evidence Verification Note

- **User Inspection Request:** `experiment_5_final_audit/`.
- **Finding:** The independent audit artifacts for Experiment 5 are housed in `experiment_5_do_hypoxia_v1/final_model_selection_audit/` (`EXPERIMENT_5_FINAL_MODEL_SELECTION_AUDIT.md`), with data in `experiment_5_do_hypoxia_v1/data/` and metrics in `experiment_5_do_hypoxia_v1/metrics/`. An independent directory named `experiment_5_final_audit/` does not exist at the repository root. All metrics, thresholds, and evidence were verified directly against the canonical files in `experiment_5_do_hypoxia_v1/`.

---

## 8. Unresolved Limitations & Risk Assessment

| Risk / Limitation | Severity | Status | Audit Findings |
| :--- | :---: | :---: | :--- |
| **Constant Point Estimate (3.50 mg/L)** | Low | **ACCEPTED** | The historical training mean does not forecast sudden diurnal oxygen crashes. However, because it achieves the lowest test error ($0.3963\text{ mg/L}$) on low-variance commercial pond nadirs across multi-week revisit gaps, designating it as the primary point benchmark is scientifically sound. It is clearly labeled as an unconditional training mean, never disguised as a dynamic biological simulation. |
| **High False Alarm Rate in Hypoxia Screening (91% FDR)** | Medium | **MITIGATED** | At $p^* = 0.090$, GBDT triggers 930 false alarms out of 1,022 alerts (50.25% alarm rate). This makes it clinically and economically unviable as an automated alarm trigger. Mitigated by strictly classifying it as an **exploratory ranking score** for queue prioritization; automated alerting is permanently barred. |
| **Degenerate Severe Hypoxia Predictor** | Low | **MITIGATED** | The Random Forest model for severe hypoxia (< 2.0 mg/L) is completely rejected and cannot be called as an operational model. Documented in all output payloads. |
| **Third-Party Upstream NumPy 2.5 Deprecation** | Low | **ACCEPTED** | All 8,994 pytest warnings originate from `joblib/numpy_pickle.py:207` during pre-trained model unpickling. Project code produces 0 warnings and 0 numerical errors. Pre-trained models are kept unpickled read-only to preserve SHA-256 hashes. |

---

## 9. Final Acceptance Verdict

- **Scientific Correctness:** **PASS** (Historical mean 3.4984 mg/L, GBDT screening 91% FDR, severe RF rejected).
- **Safety & Boundary Validations:** **PASS** (Physical input guards, NaN/inf rejection, simulation isolation).
- **Registry Integration & Fault Isolation:** **PASS** (6 models coordinated; broken DO artifact does not break remaining 5 models).
- **Test Suite Pass Rate:** **PASS** (79 / 79 unittest, 79 / 79 pytest, 100% pass rate).
- **Cryptographic Immutability:** **PASS** (10/10 datasets and 9/9 model files match pre-Phase-4 baseline hashes).
- **Phase 5 Status:** **NOT STARTED.**

### Final Formal Decision: **ACCEPTED**

