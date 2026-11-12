# Phase 3 Safety Correction Report: Simulated-Data Guardrails & Advisory Isolation

**AI-Based Precision Aquaculture Toxicity and Yield Prediction System**  
**Date:** November 11, 2026  
**Status:** Verification & Safety Corrections Complete — All 58 Tests Passing (100%)

---

## 1. Executive Summary

This report documents the implementation and verification of the two simulated-data safety corrections identified during the Phase 3 scientific audit (`PHASE_3_FINAL_SCIENTIFIC_AUDIT.md`).

### Safety Concern Remediated
Previously, `FeedingAdvisorModel.evaluate_advisory()` attached a prose `simulation_warning` string when processing simulated inputs (`data_source="simulated_iot_model"` or `is_simulated=True`), but still emitted:
- `is_valid: True`
- `status: "ADVISORY_GENERATED"`
- An actionable `recommended_feed_kg` value
- Un-prefixed advisory actions (e.g., `NORMAL_FEEDING`, `SUBSTANTIAL_FEED_REDUCTION`)
- No explicit machine-readable operational gating boolean

Downstream consumers (e.g., UI widgets, API integrations, automated dashboards) querying only `status == "ADVISORY_GENERATED"` could inadvertently present simulated scenarios as operational feeding instructions for real fish stocks.

### Safety Corrections Implemented
1. **Unambiguous Structural Simulation Gating:**
   - When inputs are simulated (`is_simulated=True`, or `data_source` contains `"simulat"` / `"synthetic"`):
     - `status` is set to `"SIMULATED_SCENARIO_ONLY"` (distinct from `"ADVISORY_GENERATED"`).
     - `operational_use_permitted` is set to `False` (machine-readable gating flag).
     - `advisory_action` is prefixed as `"SIMULATED_<ACTION>"` (e.g., `"SIMULATED_NORMAL_FEEDING"`, `"SIMULATED_CEASE_FEEDING"`).
     - An explicit `demonstration_warning` is attached prohibiting operational farm application.
2. **Preservation of Genuine Field Observation Payloads:**
   - When inputs originate from field inspections (`data_source="field_inspection"`):
     - `status` remains `"ADVISORY_GENERATED"`.
     - `operational_use_permitted` is `True`.
     - `advisory_action` remains un-prefixed (`"NORMAL_FEEDING"`, `"CEASE_FEEDING"`, etc.).
     - Retains all provisional heuristics and disclaimers (advisory only, no automatic actuator control).
3. **Physical Input Validation Gating:**
   - Missing required DO, negative DO (< 0.0 mg/L), negative feed amount (< 0.0 kg), or missing biomass parameters return `operational_use_permitted: False`.
4. **TAN Test-Kit Graduation Precision:**
   - TAN 2.0 mg/L is strictly documented as a test-kit graduation, never confused with a validated un-ionized $\text{NH}_3$ biological toxicity threshold.

---

## 2. Before-and-After Payload Comparison

### 2.1 Simulated Scenario Payload

#### Before Correction
```json
{
  "is_valid": true,
  "status": "ADVISORY_GENERATED",
  "advisory_action": "NORMAL_FEEDING",
  "recommended_feed_kg": 100.0,
  "is_simulated": true,
  "simulation_warning": "SYNTHETIC / SIMULATED DATA WARNING: The inputs provided originate from a mathematical simulation model...",
  "warning": "PROVISIONAL ADVISORY GUIDANCE ONLY..."
}
```

#### After Correction
```json
{
  "is_valid": true,
  "status": "SIMULATED_SCENARIO_ONLY",
  "advisory_action": "SIMULATED_NORMAL_FEEDING",
  "operational_use_permitted": false,
  "baseline_feed_kg": 100.0,
  "recommended_feed_kg": 100.0,
  "data_source": "simulated_iot_model",
  "is_simulated": true,
  "simulation_warning": "SYNTHETIC / SIMULATED DATA WARNING: The inputs provided originate from a mathematical simulation model, NOT actual commercial pond telemetry. This advisory must NEVER be treated as real-world farm guidance or applied to living fish stocks.",
  "demonstration_warning": "SIMULATED SCENARIO ONLY (DEMONSTRATION): This output was generated from synthetic or simulated benchmark data. It is intended strictly for model demonstration and testing, and MUST NOT be used to guide actual commercial fish feeding, pond management, or live biological operations.",
  "is_automatic_control": false,
  "control_action": null
}
```

---

### 2.2 Genuine Field Inspection Payload

```json
{
  "is_valid": true,
  "status": "ADVISORY_GENERATED",
  "advisory_action": "NORMAL_FEEDING",
  "operational_use_permitted": true,
  "baseline_feed_kg": 100.0,
  "recommended_feed_kg": 100.0,
  "reduction_percentage": 0.0,
  "data_source": "field_inspection",
  "is_simulated": false,
  "simulation_warning": null,
  "demonstration_warning": null,
  "is_automatic_control": false,
  "control_action": null,
  "warning": "PROVISIONAL ADVISORY GUIDANCE ONLY: Feeding recommendations are unverified operational heuristics designed to assist farm managers...",
  "disclaimer": "Provisional advisory guidance for human operator review only. Feed reduction mitigates organic waste loading but does not cause water-quality recovery or cure hypoxia. No automated control actions are executed."
}
```

---

### 2.3 Invalid Physical Measurement Payload (e.g. Negative Feed or Missing DO)

```json
{
  "is_valid": false,
  "status": "INVALID_PHYSICAL_MEASUREMENT",
  "explanation": "Current feed amount cannot be negative. Received: -25.0 kg.",
  "is_simulated": false,
  "simulation_warning": null,
  "operational_use_permitted": false,
  "is_automatic_control": false
}
```

---

## 3. Code Modifications Summary

### 3.1 [`app/models/feeding_advisor.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/feeding_advisor.py)
1. **Rule Summary Metadata (Line 79):**
   Updated TAN rule description:
   `"tan_at_or_above_2_0_mg_l": "50% feed reduction recommended (provisional heuristic based on 2.0 mg/L TAN test-kit graduation, not an NH3 toxicity threshold)"`
2. **Robust Simulation Flag Extraction (Lines 131–141):**
   Supports string or boolean flags:
   ```python
   raw_is_sim = row.get("is_simulated", False)
   if isinstance(raw_is_sim, str):
       flag_sim = raw_is_sim.strip().lower() in ("true", "1", "yes")
   else:
       flag_sim = bool(raw_is_sim)
   is_simulated = bool(flag_sim or "simulat" in data_source or "synthetic" in data_source)
   ```
3. **Invalid Input Guardrails (Lines 114–235):**
   Explicitly injects `"operational_use_permitted": False` across empty inputs, missing DO, negative DO, negative feed quantity, and missing biomass parameters.
4. **Output Structural Separation (Lines 340–385):**
   ```python
   if is_simulated:
       status_label = "SIMULATED_SCENARIO_ONLY"
       action_label = f"SIMULATED_{action}"
       operational_permitted = False
       demonstration_notice = (
           "SIMULATED SCENARIO ONLY (DEMONSTRATION): This output was generated from synthetic or "
           "simulated benchmark data. It is intended strictly for model demonstration and testing, "
           "and MUST NOT be used to guide actual commercial fish feeding, pond management, or live biological operations."
       )
   else:
       status_label = "ADVISORY_GENERATED"
       action_label = action
       operational_permitted = True
       demonstration_notice = None
   ```
5. **Observational Feedback Tracking (Line 454):**
   `FeedingFeedbackTracker.record_feedback()` records `operational_use_permitted` in stored records.

---

### 3.2 [`app/tests/test_feeding_advisor.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/tests/test_feeding_advisor.py)
Added and updated tests:
1. `test_simulated_versus_historical_data_labeling`: Asserts `status == "SIMULATED_SCENARIO_ONLY"`, `operational_use_permitted is False`, `advisory_action == "SIMULATED_NORMAL_FEEDING"`, and presence of demonstration warning.
2. `test_simulated_inputs_cannot_produce_operational_advisory`: Subtest matrix evaluating `is_simulated=True`, `is_simulated="true"`, `data_source="simulated_scenario"`, and `data_source="synthetic_benchmarking"`. Asserts all 4 return `operational_use_permitted is False` and `SIMULATED_` actions.
3. `test_negative_feed_returns_invalid`: Asserts negative feed is rejected with `INVALID_PHYSICAL_MEASUREMENT` and `operational_use_permitted is False`.
4. `test_tan_test_kit_graduation_wording_and_throttle`: Asserts TAN 2.0 mg/L triggers 50% feed cut and is phrased strictly as a test-kit graduation.
5. `test_adaptive_feedback_recording_and_condition_evaluation`: Verifies `operational_use_permitted` tracking across field and simulated records.

---

## 4. Test Suite Execution Results

### 4.1 Pytest Full Suite
```text
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.7.0 -- C:\Python314\python.exe
rootdir: D:\AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System
collected 58 items

app/tests/test_chemistry.py ...........                                  [ 18%]
app/tests/test_data_manager.py ........                                  [ 32%]
app/tests/test_feeding_advisor.py ..................                     [ 63%]
app/tests/test_fish_growth.py ...........                                [ 82%]
app/tests/test_models.py ..........                                      [100%]

============ 58 passed, 8279 warnings, 4 subtests passed in 6.93s =============
```

### 4.2 Unittest Full Suite
```text
Ran 58 tests in 7.522s

OK (58 passed, 0 failures, 0 errors)
```

---

## 5. Artifact and Dataset Integrity Checks

Cryptographic SHA-256 hashes confirm zero modifications to datasets and pre-trained models:

### 5.1 Datasets (`processed_data_v2/`)
| File | SHA-256 Hash | Verification |
| :--- | :--- | :--- |
| `dropouts_v2.csv` | `12b7e730aac7ae9e4eed0b89d3a98489ac6cd3c72d55cd4f9b4e3d6dd424d250` | **MATCH (Unchanged)** |
| `enrolled_ponds_v2.csv` | `94dae8de04c53891af6550afa39a8df8920b67f4b347d01cf9aa5f73aaa16e57` | **MATCH (Unchanged)** |
| `feeding_analysis_v2.csv` | `c6cf43d6449d81ed7d591f4bbcf5a74a880a6c0f89bcda126f065921a5b3a582` | **MATCH (Unchanged)** |
| `fish_health_growth_analysis_v2.csv` | `2ed226697d2b7999e3b15b1604ac574b005144598f6cf35fbacf8b7ba2f0023f` | **MATCH (Unchanged)** |
| `iot_water_model_v2.csv` | `4a577164b2836ffb77ab2f102eea2c8ab5a9898d88590c3cf969808b370ea5af` | **MATCH (Unchanged)** |
| `preprocessing_v2_report.json` | `b163443291beccefea488270e7dde780d20aad806ab95cd1b1f59ec5d6205333` | **MATCH (Unchanged)** |
| `preprocessing_v2_report.md` | `66775bbf0ee2a5c423f5d9e372cd0692cff432908d03f476a0e49c6c2323058c` | **MATCH (Unchanged)** |
| `thresholds_config.json` | `7aad8fc6df5cebfb311b0ca97d6764f25eb313c35814740ad0d8e6953cad3e94` | **MATCH (Unchanged)** |
| `toxicity_analysis_v2.csv` | `073f5ab11da085160dcb0821e4a16533d96555f8587261c0bd348f385c60c462` | **MATCH (Unchanged)** |
| `water_quality_cleaned_v2.csv` | `500b2d6fd032eeabb6d1b947dbc6d93b4464c146d41d9e91f4a0367f54f50e1b` | **MATCH (Unchanged)** |

### 5.2 Pre-Trained Model Artifacts
| Model Artifact | SHA-256 Hash | Verification |
| :--- | :--- | :--- |
| `baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib` | `e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a` | **MATCH (Unchanged)** |
| `experiment_2_mortality_v1/models/logistic_regression_pipeline.joblib` | `02c8a34ae4ff8b8d907beeed18be4ecd00bb463cd204e8298163f6864afcdadf` | **MATCH (Unchanged)** |
| `experiment_2_mortality_v1/models/random_forest_pipeline.joblib` | `464344d33ffc3cff26726bfa15ec73d6b8a59b773ae61083db3d3082f44b4216` | **MATCH (Unchanged)** |
| `experiment_3_next_visit_risk_v1/models/random_forest_pipeline.joblib` | `2f7980756c02a5fa00e325919944c8dd416456d785af9f110135e10edd38853c` | **MATCH (Unchanged)** |
| `experiment_3_next_visit_risk_v1/models/logistic_regression_pipeline.joblib` | `957aea9b8cd0066e364c776c76b12128b7b8e63cafe9800cbda39a03d8486ad7` | **MATCH (Unchanged)** |

---

## 6. Strict Project Boundary Verification

1. **Zero Dataset / Model Retraining Modifications:** No CSV, JSON, or `.joblib` files were altered or retrained.
2. **Phase 1 & Phase 2 Untouched:** All chemistry equations, dataset managers, and wrappers from Experiments 1–3 maintain unchanged functionality.
3. **No Automated Control:** Module output remains strictly decision-support advisory.
4. **No New Biological Claims:** Feeding throttles remain provisional heuristics; no claim that feed reduction causes water quality recovery.
5. **Phase 4 Not Started:** Execution stopped immediately following Phase 3 safety correction and test suite sign-off.

