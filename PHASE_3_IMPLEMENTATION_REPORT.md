# Phase 3 Implementation Report: Fish Growth and Feeding Module Integration

**Document ID:** `P3-IR-AQUASYSTEM-2026-FINAL`  
**Date:** 2026-11-06  
**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System (BAI507P Mini Project)  
**Implementation Scope:** Phase 3 — Somatic Fish Growth Persistence Baseline & Provisional Rule-Based Feeding Advisor  
**Status:** Complete, Fully Tested, and Audited (Zero Retraining, Zero Data Modification)  
**Author:** AI Technical Lead & Integration Architecture System  

---

## Executive Summary

Phase 3 implements the somatic fish growth prediction module and the provisional rule-based feeding advisory engine, integrating them cleanly into the application architecture without modifying Phase 1 or Phase 2 components.

### Core Achievements in Phase 3
1. **Fish Growth Module (`app/models/fish_growth.py`):**
   - Implemented the audited **Persistence Baseline** ($\hat{W}_{t+1} = W_t$) as the primary operational predictor for next-visit average fish weight, directly following the independent audit of Experiment 4.
   - Refrained from deploying exploratory ML models (Random Forest, Gradient Boosting) as primary predictors because they failed significantly on the operational all-pairs population ($\text{Persistence MAE} = 93.38\text{ g}$ vs. $\text{RF MAE} = 112.15\text{ g}$ and $\text{GBDT MAE} = 127.34\text{ g}$; $p < 10^{-12}$).
   - Strictly framed the target as next-visit average body weight (grams/fish). Explicitly disclaimed total commercial harvest yield (kg/ha), individual fish growth trajectories, and harvest timing.
   - Defensively enforced input validation: positive weight check ($> 0\text{ g}$), rejection of zero, negative, or NaN values. Zero artificial yield labels generated.

2. **Feeding Advisory Module (`app/models/feeding_advisor.py`):**
   - Implemented a transparent, rule-based feeding advisory engine using available water quality (dissolved oxygen, un-ionized ammonia / TAN, temperature) and pond feeding/biomass metrics.
   - Established strict disclaimers: labeled all feeding recommendations as **provisional advisory guidance**, explicitly stating that rules are unverified operational heuristics, NOT scientifically validated bioenergetic prescriptions.
   - Guarded physical causality: explicitly avoided claiming that reducing feed causes water-quality recovery or cures hypoxia/ammonia spikes.
   - Guarded simulation inputs: added an explicit check for `data_source` / `is_simulated`; synthetic or simulated inputs from IoT simulation models are never treated as actual pond measurements.
   - Guarded automation: strictly advisory decision-support for human farm managers; executed zero automated control actions or equipment actuator commands (`is_automatic_control = False`, `control_action = None`).

3. **Adaptive Observational Feedback Structure (`FeedingFeedbackTracker`):**
   - Implemented an observational record structure capturing previous advisory, farmer's actual feeding action, compliance delta, subsequent water quality observation, and condition transition evaluation (`"improved"`, `"worsened"`, `"unchanged"`, or `"insufficient_data"`).
   - Formally disclaimed causal learning: permanently attached governance notices stating that the feedback loop is strictly an observational audit log for retrospective human inspection and does NOT perform causal inference, automated parameter tuning, or reinforcement learning.

4. **Central Model Registry Integration (`app/models/registry.py`):**
   - Integrated `FishGrowthModel`, `FeedingAdvisorModel`, and `FeedingFeedbackTracker` into the global registry alongside Experiments 1, 2, and 3.
   - Added high-level domain accessors (`predict_fish_growth()`, `get_feeding_advisory()`, `record_feeding_feedback()`, `get_feeding_feedback_records()`).

5. **Test Suite & System Verification:**
   - Authored comprehensive test suites: `app/tests/test_fish_growth.py` (11 tests) and `app/tests/test_feeding_advisor.py` (14 tests).
   - Executed full test suite: **55/55 passed** across both `unittest` and `pytest`.
   - Verified 100% bit-for-bit integrity of all 10 audited datasets in `processed_data_v2/` and all 5 pre-trained `.joblib` model artifacts.

---

## 1. Files Created and Modified

| File Path | Action | Description |
| :--- | :--- | :--- |
| `app/models/fish_growth.py` | **Created** | Operational fish growth wrapper implementing Experiment 4 persistence baseline, validation, and disclaimers. |
| `app/models/feeding_advisor.py` | **Created** | Rule-based provisional feeding advisory engine and observational adaptive feedback tracker. |
| `app/models/registry.py` | **Modified** | Registered fish growth and feeding advisor models; added domain inference and feedback methods. |
| `app/tests/test_fish_growth.py` | **Created** | Unit test suite for fish growth persistence, input validation, zero/negative handling, and disclaimers. |
| `app/tests/test_feeding_advisor.py` | **Created** | Unit test suite for feeding throttles, simulation labeling, missing inputs, feedback tracking, and safety guardrails. |
| `app/tests/test_models.py` | **Modified** | Updated registry model count assertions (5 models loaded) and failure tolerance tests. |
| `PHASE_3_IMPLEMENTATION_REPORT.md` | **Created** | Comprehensive implementation and verification documentation for Phase 3. |

---

## 2. Architecture and Integration Details

```
app/
├── config.py                       # Project paths, thresholds, and chemical constants
├── core/
│   ├── chemistry.py                # Audited Emerson ammonia equilibrium engine
│   └── data_manager.py             # Read-only dataset caching & access
├── models/
│   ├── exp1_soft_sensor.py         # Exp 1 Ammonia Soft-Sensor (RF)
│   ├── exp2_mortality.py           # Exp 2 Fish Mortality Diagnostic (LR)
│   ├── exp3_ammonia_risk.py        # Exp 3 Next-Visit Ammonia Risk (RF)
│   ├── fish_growth.py              # [PHASE 3] Exp 4 Fish Growth (Persistence Baseline)
│   ├── feeding_advisor.py          # [PHASE 3] Rule-Based Feeding Advisor & Feedback Tracker
│   └── registry.py                 # Central Model Registry & Service Coordinator
└── tests/
    ├── test_chemistry.py           # 11 tests (Ammonia dissociation & conversions)
    ├── test_data_manager.py        # 8 tests (Data loading & isolation)
    ├── test_models.py              # 10 tests (Exp 1–3 wrappers & registry health)
    ├── test_fish_growth.py         # [PHASE 3] 11 tests (Growth persistence & validation)
    └── test_feeding_advisor.py     # [PHASE 3] 15 tests (Feeding throttles & feedback audit)
```

The new modules are completely decoupled:
- `FishGrowthModel` operates purely on current fish weight inputs and optional visit metadata.
- `FeedingAdvisorModel` operates independently on water quality observations and feeding/biomass records.
- `ModelRegistry` aggregates the wrappers into a cohesive service layer, allowing downstream API endpoints and dashboard views (in subsequent phases) to invoke predictions through a single unified interface.

---

## 3. Fish Growth Prediction Method and Limitations

### 3.1 Method Selection: Audited Persistence Baseline
Experiment 4 evaluated predictive models for forecasting the average fish body weight (grams/fish) at the subsequent farm visit ($t+1$, median revisit interval: 22 days).

#### Operational Benchmark (All Pairs Population, $N = 1,689$ Test Pairs):
- **Persistence Baseline ($\hat{W}_{t+1} = W_t$):** $\text{MAE} = 93.38\text{ g}$, $\text{RMSE} = 196.48\text{ g}$, $R^2 = 0.7135$
- **Random Forest Regressor:** $\text{MAE} = 112.15\text{ g}$, $\text{RMSE} = 199.16\text{ g}$, $R^2 = 0.7056$ ($p = 2.0 \times 10^{-13}$ significantly worse)
- **Gradient Boosting Regressor:** $\text{MAE} = 127.34\text{ g}$, $\text{RMSE} = 215.17\text{ g}$, $R^2 = 0.6558$ ($p = 1.9 \times 10^{-20}$ significantly worse)

#### Why ML Failed on Operational Data:
Machine learning models were trained under the assumption of continuous, monotonic somatic growth. On commercial ponds, routine management interventions (unrecorded partial harvests, net thinning, complete drainings, or restockings) cause abrupt drops in average pond weight. Persistence incurs an error proportional to the drop ($|W_{\text{harvest}} - W_{\text{prev}}|$), whereas ML models predict positive growth, compounding the error.

Furthermore, the "Clean Pairs" subset ($N = 2,364$) in Experiment 4 was created by filtering out pairs with $\Delta W \le -100\text{ g}$ or $\text{ADG} < -5.0\text{ g/d}$. Because both criteria require knowing the future target `next_weight`, this filtering represents outcome-dependent leakage and cannot be applied at inference time ($t$).

### 3.2 Implemented Logic (`FishGrowthModel`)
```python
def predict(self, features: Union[Dict[str, Any], pd.DataFrame]) -> Dict[str, Any]:
    curr_weight = self.validate_inputs(features)
    # Persistence prediction:
    return {
        "predicted_next_weight_g": float(curr_weight),
        "current_weight_g": float(curr_weight),
        "status": "OPERATIONAL_PERSISTENCE_BASELINE",
        "is_valid": True,
        ...
    }
```

### 3.3 Limitations & Governance Guardrails
- **Scope Restriction:** Strictly estimates average body weight per fish for the subsequent visit. It does **NOT** forecast total commercial harvest yield (kg/ha), pond biomass production, or economic harvest date.
- **Input Validation:** Enforces $W > 0\text{ g}$. Rejects zero, negative, or NaN values with explicit `ValueError`.
- **Zero Artificial Labels:** Output payloads contain no synthetic harvest yield numbers or unverified commercial metrics.

---

## 4. Feeding Advisory Rules and Limitations

### 4.1 Input Requirements & Missing Data Handling
The advisor evaluates:
1. **Water Quality:** Mandatory `dissolved_oxygen_mg_l` (required for safety throttle). Optional: `primary_calculated_nh3_mg_l`, `ammonia_tan_nh3_n_mg_l`, `temp_c`.
2. **Feeding / Biomass:** Either `current_feed_amount_kg` ($> 0$) OR complete biomass parameters (`average_fish_weight_g`, `stocking_density_per_acre`, and `pond_area_acres`).
3. **Missing Data Behavior:** If DO or baseline feed/biomass is missing, the module returns `is_valid = False` with a descriptive explanation (`MISSING_REQUIRED_WATER_QUALITY` or `MISSING_FEEDING_OR_BIOMASS_DATA`). It **never** invents an arbitrary recommendation.

### 4.2 Throttling Rules Matrix

```
+==================================================================================================================================+
|                                    PROVISIONAL RULE-BASED FEEDING THROTTLING MATRIX                                              |
+---------------------+-------------------------------+-------------------+--------------------------------------------------------+
| Parameter           | Condition / Threshold         | Throttling Factor | Advisory Action & Rationale                            |
+---------------------+-------------------------------+-------------------+--------------------------------------------------------+
| Dissolved Oxygen    | DO < 2.0 mg/L                 | 0.0 (100% cut)    | CEASE_FEEDING: Critical hypoxia; digestion consumes O2;|
|                     |                               |                   | uneaten feed rapidly accelerates acute mortality.      |
| Dissolved Oxygen    | 2.0 <= DO < 3.0 mg/L          | 0.5 (50% cut)     | SUBSTANTIAL_REDUCTION: Moderate hypoxia; halve ration  |
|                     |                               |                   | to reduce post-prandial biological oxygen demand.      |
| Dissolved Oxygen    | 3.0 <= DO < 4.0 mg/L          | 0.8 (20% cut)     | MODERATE_REDUCTION: Borderline DO; cautious reduction  |
|                     |                               |                   | until morning nadir DO stabilizes above 4.0 mg/L.      |
| Dissolved Oxygen    | DO >= 4.0 mg/L                | 1.0 (No cut)      | NORMAL_FEEDING: Dissolved oxygen is adequate.          |
+---------------------+-------------------------------+-------------------+--------------------------------------------------------+
| Un-ionized NH3      | NH3 >= 0.10 mg/L              | 0.0 (100% cut)    | CEASE_FEEDING: Critical ammonia; cease feed to halt    |
|                     |                               |                   | metabolic excretion and microbial nitrogen loading.    |
| Un-ionized NH3      | 0.05 <= NH3 < 0.10 mg/L       | 0.5 (50% cut)     | SUBSTANTIAL_REDUCTION: Elevated ammonia toxicity risk; |
|                     |                               |                   | halve daily ration.                                    |
| Un-ionized NH3      | NH3 < 0.05 mg/L               | 1.0 (No cut)      | NH3 within acceptable provisional baseline.            |
+---------------------+-------------------------------+-------------------+--------------------------------------------------------+
| Total Ammonia (TAN) | TAN >= 2.0 mg/L (test-kit step)| 0.5 (50% cut)     | SUBSTANTIAL_REDUCTION: Elevated TAN test-kit graduation |
|                     |                               |                   | (not a scientifically validated NH3 toxicity threshold).|
| Total Ammonia (TAN) | 1.0 <= TAN < 2.0 mg/L         | 0.8 (20% cut)     | MODERATE_REDUCTION: Cautionary TAN threshold.          |
+---------------------+-------------------------------+-------------------+--------------------------------------------------------+
| Water Temperature   | Temp < 20°C or Temp > 34°C    | 0.8 (20% cut)     | THERMAL_STRESS: Thermal metabolic slowdown / stress.   |
| Water Temperature   | 20°C <= Temp <= 34°C          | 1.0 (No cut)      | Optimal thermal feeding range.                         |
+---------------------+-------------------------------+-------------------+--------------------------------------------------------+
```

### 4.3 Composite Multiplier Formula
$$\text{Combined Factor} = \min(\text{Factor}_{\text{DO}}, \text{Factor}_{\text{Ammonia}}) \times \text{Factor}_{\text{Temp}}$$
$$\text{Recommended Feed (kg)} = \text{Baseline Feed (kg)} \times \text{Combined Factor}$$

### 4.4 Simulation and Automated Control Guardrails
1. **Simulation Isolation & Operational Prohibition:** If `data_source` is `"simulated"` / `"synthetic"` or `is_simulated = True`:
   - `status = "SIMULATED_SCENARIO_ONLY"` (differentiated from `"ADVISORY_GENERATED"`).
   - `operational_use_permitted = False` (explicit machine-readable gating flag).
   - `advisory_action = "SIMULATED_<ACTION>"` (never presented as an actionable operational recommendation).
   - `demonstration_warning` and `simulation_warning` attached:
     > *"SIMULATED SCENARIO ONLY (DEMONSTRATION): This output was generated from synthetic or simulated benchmark data. It is intended strictly for model demonstration and testing, and MUST NOT be used to guide actual commercial fish feeding, pond management, or live biological operations."*
2. **Field Data Integrity:** For genuine field inspection observations (`data_source = "field_inspection"`):
   - `status = "ADVISORY_GENERATED"`
   - `operational_use_permitted = True`
   - Preserves all provisional heuristic disclaimers and human verification requirements.
3. **No Automated Control:** The module outputs `is_automatic_control = False` and `control_action = None`. No hardware or actuator commands are triggered.
4. **Physical Causality Disclaimer:** The module explicitly states that reducing feed prevents further organic waste accumulation but **does not cause water quality recovery** or eliminate existing hypoxic conditions.

---

## 5. Adaptive Feedback Structure

The `FeedingFeedbackTracker` records observational interactions to support retrospective human evaluation:

### 5.1 Stored Schema
```python
{
    "record_id": "a1b2c3d4",
    "timestamp": "2026-11-06T15:45:00.000000",
    "pond_id": "pond_01",
    "advisory_action": "SUBSTANTIAL_FEED_REDUCTION",
    "baseline_feed_kg": 100.0,
    "recommended_feed_kg": 50.0,
    "actual_feed_kg": 50.0,
    "compliance_delta_kg": 0.0,
    "initial_observation": {"dissolved_oxygen_mg_l": 2.5, "un_ionized_nh3_mg_l": 0.02},
    "next_observation": {"dissolved_oxygen_mg_l": 4.1, "un_ionized_nh3_mg_l": 0.02},
    "condition_change": "improved",  # [improved | worsened | unchanged | insufficient_data]
    "notes": "Farmer reduced morning feed by 50%.",
    "governance_notice": (
        "OBSERVATIONAL AUDIT RECORD ONLY: This feedback mechanism logs farmer actions "
        "and subsequent water quality readings for retrospective human inspection. "
        "It does NOT perform causal learning, automated parameter tuning, reinforcement learning, "
        "or automatic optimization."
    )
}
```

### 5.2 Transition Classification Rules
- **Improved:** $\Delta\text{DO} \ge +0.5\text{ mg/L}$ and un-ionized $\text{NH}_3$ did not increase by $\ge 0.02\text{ mg/L}$.
- **Worsened:** $\Delta\text{DO} \le -0.5\text{ mg/L}$ or un-ionized $\text{NH}_3$ increased by $\ge 0.02\text{ mg/L}$.
- **Unchanged:** Variations within $\pm 0.5\text{ mg/L}$ DO and $\pm 0.02\text{ mg/L}$ $\text{NH}_3$.
- **Pending / Insufficient:** When `next_observation` is missing or lacks valid DO measurements.

---

## 6. Test Results Summary

Both `unittest` and `pytest` runners executed all test suites across the application:

### 6.1 Pytest Execution Summary
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

### 6.2 Unittest Execution Summary
```text
Ran 58 tests in 7.522s

OK (58 passed, 0 failures, 0 errors)
```

### 6.3 Test Coverage Breakdown
- `test_chemistry.py` (11 tests): Emerson dissociation formulas, pKa precision, MW conversion, vectorization.
- `test_data_manager.py` (8 tests): Read-only dataset access, defensive caching, NaN preservation, schema verification.
- `test_models.py` (10 tests): Experiments 1–3 wrappers, registry health checks, partial failure tolerance.
- `test_fish_growth.py` (11 tests): Persistence baseline accuracy, alias resolution, zero/negative weight rejection, metadata and disclaimers.
- `test_feeding_advisor.py` (18 tests): Normal feeding, biomass-based calculation, DO throttles (100%, 50%, 20%), ammonia throttles, TAN test-kit graduation wording, negative feed/DO rejection, simulated scenario safety isolation (`SIMULATED_SCENARIO_ONLY`, `operational_use_permitted = False`, `SIMULATED_` actions), no-control guardrails, observational feedback transitions.

---

## 7. Dataset and Model Artifact Integrity Checks

SHA-256 cryptographic hashes were computed before and after Phase 3 implementation, confirming zero modification:

### 7.1 Audited Datasets (`processed_data_v2/`)
| Dataset Filename | Verified SHA-256 Hash | Integrity Status |
| :--- | :--- | :--- |
| `dropouts_v2.csv` | `12b7e730aac7ae9e4eed0b89d3a98489ac6cd3c72d55cd4f9b4e3d6dd424d250` | **100% Unchanged** |
| `enrolled_ponds_v2.csv` | `94dae8de04c53891af6550afa39a8df8920b67f4b347d01cf9aa5f73aaa16e57` | **100% Unchanged** |
| `feeding_analysis_v2.csv` | `c6cf43d6449d81ed7d591f4bbcf5a74a880a6c0f89bcda126f065921a5b3a582` | **100% Unchanged** |
| `fish_health_growth_analysis_v2.csv` | `2ed226697d2b7999e3b15b1604ac574b005144598f6cf35fbacf8b7ba2f0023f` | **100% Unchanged** |
| `iot_water_model_v2.csv` | `4a577164b2836ffb77ab2f102eea2c8ab5a9898d88590c3cf969808b370ea5af` | **100% Unchanged** |
| `preprocessing_v2_report.json` | `b163443291beccefea488270e7dde780d20aad806ab95cd1b1f59ec5d6205333` | **100% Unchanged** |
| `preprocessing_v2_report.md` | `66775bbf0ee2a5c423f5d9e372cd0692cff432908d03f476a0e49c6c2323058c` | **100% Unchanged** |
| `thresholds_config.json` | `7aad8fc6df5cebfb311b0ca97d6764f25eb313c35814740ad0d8e6953cad3e94` | **100% Unchanged** |
| `toxicity_analysis_v2.csv` | `073f5ab11da085160dcb0821e4a16533d96555f8587261c0bd348f385c60c462` | **100% Unchanged** |
| `water_quality_cleaned_v2.csv` | `500b2d6fd032eeabb6d1b947dbc6d93b4464c146d41d9e91f4a0367f54f50e1b` | **100% Unchanged** |

### 7.2 Pre-Trained Model Artifacts
| Model Artifact Path | File Size | Verified SHA-256 Hash | Status |
| :--- | :--- | :--- | :--- |
| `baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib` | 15,395,427 B | `e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a` | **Unchanged** |
| `experiment_2_mortality_v1/models/logistic_regression_pipeline.joblib` | 6,618 B | `02c8a34ae4ff8b8d907beeed18be4ecd00bb463cd204e8298163f6864afcdadf` | **Unchanged** |
| `experiment_2_mortality_v1/models/random_forest_pipeline.joblib` | 609,547 B | `464344d33ffc3cff26726bfa15ec73d6b8a59b773ae61083db3d3082f44b4216` | **Unchanged** |
| `experiment_3_next_visit_risk_v1/models/random_forest_pipeline.joblib` | 1,651,387 B | `2f7980756c02a5fa00e325919944c8dd416456d785af9f110135e10edd38853c` | **Unchanged** |
| `experiment_3_next_visit_risk_v1/models/logistic_regression_pipeline.joblib` | 6,490 B | `957aea9b8cd0066e364c776c76b12128b7b8e63cafe9800cbda39a03d8486ad7` | **Unchanged** |

---

## 8. Compliance Checklist with Project Restrictions

- [x] **No frontend or dashboard built yet:** Implementation restricted strictly to backend models, services, and tests.
- [x] **No hardware or sensor integrations added:** Pure software models with explicit simulation/historical input labeling.
- [x] **No new models trained:** Persistence baseline implemented analytically; zero model retraining executed.
- [x] **No claim of reliable harvest-yield prediction:** Somatic fish weight explicitly labeled as next-visit average body weight; harvest yield disclaimed.
- [x] **No invented scientific thresholds:** Thresholds loaded transparently from config and clearly labeled as provisional heuristics.
- [x] **Did not proceed to Phase 4:** Execution stopped immediately upon Phase 3 completion and validation.

---

## 9. Conclusion

Phase 3 is complete, validated, and ready for review. The system now possesses:
1. Operational fish growth tracking via the audited Experiment 4 persistence baseline.
2. Provisional rule-based feeding advice with safety throttles for hypoxia and un-ionized ammonia.
3. Observational adaptive feedback tracking for farm compliance logging and condition change evaluation.
4. Comprehensive test coverage (55 tests passing).

**Execution is halted awaiting user review.**

