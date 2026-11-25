# Phase 2 Final Wording & Terminology Audit Report

**Document ID:** `P2-FWA-AQUASYSTEM-2026-FINAL`  
**Date:** 2026-11-06  
**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System (BAI507P Mini Project)  
**Scope:** Verification of Precise Scientific Terminology Across Application Model Wrappers, Test Suites, and Phase 2 Documentation  
**Status:** Audit Complete & Fully Verified (Zero Models Retrained, Zero Datasets Modified)  
**Author:** AI Technical Lead & Scientific Verification System  

---

## Executive Summary

This report documents the final wording and scientific terminology refinements implemented across the application models (`app/models/`), test suite (`app/tests/`), and Phase 2 verification and correction reports (`PHASE_2_CORRECTION_REPORT.md` and `PHASE_2_SCIENTIFIC_VERIFICATION.md`). 

All five specific user directives were executed with exact precision:
1. **Audited NH3 Concentration Tiers:** Replaced "verified biological stress thresholds" with "audited NH3 concentration tiers". Removed the unverified biological consequence labels "sublethal stress", "severe distress", and "critical lethal".
2. **Physical Chemistry Mechanism:** Removed blanket "1–10%" statements. Explicitly documented that the un-ionized $\text{NH}_3$ fraction depends on pH and temperature and is calculated using the Emerson equation ($pK_a = 0.09018 + 2729.92 / T_K$).
3. **Field Kit Graduation Clarification:** Eliminated ambiguous "TAN (N=1 in 2026)" phrasing. Explicitly stated that 2.0 mg/L is the TAN test-kit graduation, not an $\text{NH}_3$ toxicity threshold.
4. **Experiment 3 True Positive vs. New Spike Distinction:** Clearly distinguished the 18 total true positives from the 15 of 54 newly developed spikes detected by Random Forest (with 3 persistent spikes detected), both in module docstrings and structured metadata dictionaries.
5. **Comprehensive Codebase Audit:** Scanned all user-facing messages, docstrings, metadata dictionaries, and Phase 2 reports to ensure zero remaining occurrences of unverified terminology.

---

## 1. Itemized Wording Changes and Exact Modifications

### 1.1 Item 1: Audited NH3 Concentration Tiers vs. Unverified Biological Labels
- **Directive:** Replace "verified biological stress thresholds" with "audited NH3 concentration tiers". Remove the unverified labels "sublethal stress", "severe distress", and "critical lethal".
- **Files Modified:**
  - `app/models/exp1_soft_sensor.py`
  - `app/tests/test_models.py`
  - `PHASE_2_CORRECTION_REPORT.md`
  - `PHASE_2_SCIENTIFIC_VERIFICATION.md`

#### Comparison in `app/models/exp1_soft_sensor.py`:
```python
# BEFORE (Inaccurate biological labels):
- Chronological Holdout Findings (2025–2026, N = 2,600):
  * Actual NH3 >= 0.05 mg/L (Sublethal stress): 79.59% underpredicted (N = 98, bias = -0.0537 mg/L).
  * Actual NH3 >= 0.10 mg/L (Severe distress): 100.00% underpredicted (N = 33, bias = -0.1336 mg/L).
  * Actual NH3 >= 0.20 mg/L (Critical lethal): 100.00% underpredicted (N = 10, bias = -0.2234 mg/L).

"limitations": [
    "Target is a calculated equilibrium proxy, not an analytical chemistry laboratory standard.",
    "100% underprediction failure during critical lethal spikes (NH3 >= 0.10 and >= 0.20 mg/L).",
    ...
]

# AFTER (Audited NH3 concentration tiers):
- Chronological Holdout Findings Across Audited NH3 Concentration Tiers (2025–2026, N = 2,600):
  * Actual NH3 >= 0.05 mg/L: 79.59% underpredicted (N = 98, bias = -0.0537 mg/L).
  * Actual NH3 >= 0.10 mg/L: 100.00% underpredicted (N = 33, bias = -0.1336 mg/L).
  * Actual NH3 >= 0.20 mg/L: 100.00% underpredicted (N = 10, bias = -0.2234 mg/L).

"limitations": [
    "Target is a calculated equilibrium proxy, not an analytical chemistry laboratory standard.",
    "100% underprediction failure across elevated NH3 concentration tiers (NH3 >= 0.10 and >= 0.20 mg/L).",
    ...
]
```

---

### 1.2 Item 2: Un-ionized NH3 Fraction Depends on pH and Temperature (Emerson Equation)
- **Directive:** Explain that the un-ionized $\text{NH}_3$ fraction depends on pH and temperature and is calculated using the Emerson equation. Remove the blanket 1–10% statement.
- **Files Modified:**
  - `app/models/exp1_soft_sensor.py`
  - `PHASE_2_CORRECTION_REPORT.md`
  - `PHASE_2_SCIENTIFIC_VERIFICATION.md`

#### Comparison in `app/models/exp1_soft_sensor.py`:
```python
# BEFORE:
- Physical Chemistry Boundary: Molecular un-ionized ammonia (NH3) is distinct from Total
  Ammonia Nitrogen (TAN). Do NOT confuse the 2.00 mg/L visual test-kit TAN limit with NH3.

# AFTER:
- Physical Chemistry Boundary: Molecular un-ionized ammonia (NH3) is distinct from Total
  Ammonia Nitrogen (TAN). The un-ionized NH3 fraction depends on pH and temperature and is
  calculated using the Emerson equation. 2.0 mg/L is the TAN test-kit graduation, not an
  NH3 toxicity threshold.
```

#### Comparison in `PHASE_2_CORRECTION_REPORT.md`:
```markdown
<!-- BEFORE (Blanket 1-10% statement): -->
...whereas un-ionized molecular ammonia ($\text{NH}_3$) is only $1\%\text{--}10\%$ of TAN.

<!-- AFTER (Rigorous chemical explanation): -->
The un-ionized $\text{NH}_3$ fraction depends on pH and temperature and is calculated using the Emerson equation. $2.0\text{ mg/L}$ is the TAN test-kit graduation, not an $\text{NH}_3$ toxicity threshold.
```

---

### 1.3 Item 3: Clarification of 2.0 mg/L Field Kit Graduation
- **Directive:** Correct the ambiguous "TAN (N=1 in 2026)" wording. State that 2.0 mg/L is the TAN test-kit graduation, not an $\text{NH}_3$ toxicity threshold.
- **Files Modified:**
  - `app/models/exp1_soft_sensor.py`
  - `app/tests/test_models.py`
  - `PHASE_2_CORRECTION_REPORT.md`
  - `PHASE_2_SCIENTIFIC_VERIFICATION.md`

#### Comparison in `app/models/exp1_soft_sensor.py` (`get_metadata()["chronological_underprediction_audit"]`):
```python
# BEFORE:
"note": "2.00 mg/L represents a discrete TAN test-kit scale limit, NOT an un-ionized NH3 threshold."

# AFTER:
"note": (
    "2.0 mg/L is the TAN test-kit graduation, not an NH3 toxicity threshold. "
    "The un-ionized NH3 fraction depends on pH and temperature and is calculated using the Emerson equation."
)
```

---

### 1.4 Item 4: Experiment 3 Distinction — Total True Positives vs. Newly Developed Spikes
- **Directive:** In Experiment 3, distinguish 18 total true positives from 15 of 54 newly developed spikes detected by Random Forest.
- **Files Modified:**
  - `app/models/exp3_ammonia_risk.py`
  - `app/tests/test_models.py`
  - `PHASE_2_CORRECTION_REPORT.md`
  - `PHASE_2_SCIENTIFIC_VERIFICATION.md`

#### Comparison in `app/models/exp3_ammonia_risk.py`:
```python
# BEFORE (Conflated total TP with new spike sensitivity):
  * Random Forest (Primary Model):
    - Recall: 31.58% (detected 18 of 57 events)
    - Precision: 2.63% (18 true positives out of 684 alarms; 666 false alarms)
    - F1-Score: 0.0486
    - New Spike Sensitivity: Detected 15 of 54 new onset spikes (27.8%)

"random_forest": {
    "pr_auc": 0.0305,
    "roc_auc": 0.5061,
    "recall": 0.3158,
    "precision": 0.0263,
    "f1_score": 0.0486,
    "true_positives": 18,
    "false_positives": 666,
    "new_spikes_detected": "15 / 54 (27.8%)"
}

# AFTER (Explicitly distinguished total true positives from newly developed spikes):
  * Random Forest (Primary Model):
    - PR-AUC: 0.0305 (close to no-skill baseline of 0.0280)
    - ROC-AUC: 0.5061 (near random coin toss of 0.5000)
    - Recall: 31.58% (detected 18 of 57 events)
    - Precision: 2.63% (18 total true positives out of 684 alarms; 666 false alarms)
    - F1-Score: 0.0486
    - Detection Breakdown: 18 total true positives (consisting of 15 of 54 newly developed spikes detected [27.8% sensitivity] plus 3 persistent spikes detected)

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
}
```

---

## 2. Codebase Audit Search Verification

A comprehensive automated text scan was conducted across all files in `app/` and the Phase 2 reports for the prohibited phrases:
- `"biological stress"`
- `"sublethal stress"`
- `"severe distress"`
- `"critical lethal"`
- `"1–10%"` / `"1-10%"` / `"1%–10%"` / `"1%--10%"`
- `"N=1 in 2026"` / `"N = 1 in 2026"`

**Audit Scan Result:**
```text
Scan target files:
- app/models/exp1_soft_sensor.py
- app/models/exp2_mortality.py
- app/models/exp3_ammonia_risk.py
- app/models/registry.py
- app/tests/test_models.py
- PHASE_2_CORRECTION_REPORT.md
- PHASE_2_SCIENTIFIC_VERIFICATION.md
- PHASE_2_IMPLEMENTATION_REPORT.md

Matches Found: ZERO (0 occurrences). All files cleanly pass terminology verification.
```

---

## 3. Test Suite Verification Results

Both `unittest` and `pytest` test suites were run on the updated code.

### 3.1 Unittest Results
```text
Ran 29 tests in 18.779s

OK (29 passed, 0 failures, 0 errors)
```

### 3.2 Pytest Results
```text
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.7.0 -- C:\Python314\python.exe
rootdir: D:\AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System
collected 29 items

app/tests/test_chemistry.py ...........                                  [ 37%]
app/tests/test_data_manager.py ........                                  [ 65%]
app/tests/test_models.py ..........                                      [100%]

====================== 29 passed, 7564 warnings in 5.87s ======================
```

---

## 4. Dataset and Model Integrity Verification

All dataset files and trained model artifacts were hashed using SHA-256 to confirm zero tampering, modification, or retraining:

### 4.1 Audited Datasets (`processed_data_v2/`)
| Filename | Computed SHA-256 Hash | Status |
| :--- | :--- | :--- |
| `dropouts_v2.csv` | `12b7e730aac7ae9e4eed0b89d3a98489ac6cd3c72d55cd4f9b4e3d6dd424d250` | **Verified Intact** |
| `enrolled_ponds_v2.csv` | `94dae8de04c53891af6550afa39a8df8920b67f4b347d01cf9aa5f73aaa16e57` | **Verified Intact** |
| `feeding_analysis_v2.csv` | `c6cf43d6449d81ed7d591f4bbcf5a74a880a6c0f89bcda126f065921a5b3a582` | **Verified Intact** |
| `fish_health_growth_analysis_v2.csv` | `2ed226697d2b7999e3b15b1604ac574b005144598f6cf35fbacf8b7ba2f0023f` | **Verified Intact** |
| `iot_water_model_v2.csv` | `4a577164b2836ffb77ab2f102eea2c8ab5a9898d88590c3cf969808b370ea5af` | **Verified Intact** |
| `preprocessing_v2_report.json` | `b163443291beccefea488270e7dde780d20aad806ab95cd1b1f59ec5d6205333` | **Verified Intact** |
| `preprocessing_v2_report.md` | `66775bbf0ee2a5c423f5d9e372cd0692cff432908d03f476a0e49c6c2323058c` | **Verified Intact** |
| `thresholds_config.json` | `7aad8fc6df5cebfb311b0ca97d6764f25eb313c35814740ad0d8e6953cad3e94` | **Verified Intact** |
| `toxicity_analysis_v2.csv` | `073f5ab11da085160dcb0821e4a16533d96555f8587261c0bd348f385c60c462` | **Verified Intact** |
| `water_quality_cleaned_v2.csv` | `500b2d6fd032eeabb6d1b947dbc6d93b4464c146d41d9e91f4a0367f54f50e1b` | **Verified Intact** |

### 4.2 Serialized Model Artifacts
| Model Artifact Path | File Size | Computed SHA-256 Hash | Status |
| :--- | :--- | :--- | :--- |
| `baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib` | 15,395,427 B | `e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a` | **Verified Intact** |
| `experiment_2_mortality_v1/models/logistic_regression_pipeline.joblib` | 6,618 B | `02c8a34ae4ff8b8d907beeed18be4ecd00bb463cd204e8298163f6864afcdadf` | **Verified Intact** |
| `experiment_2_mortality_v1/models/random_forest_pipeline.joblib` | 609,547 B | `464344d33ffc3cff26726bfa15ec73d6b8a59b773ae61083db3d3082f44b4216` | **Verified Intact** |
| `experiment_3_next_visit_risk_v1/models/random_forest_pipeline.joblib` | 1,651,387 B | `2f7980756c02a5fa00e325919944c8dd416456d785af9f110135e10edd38853c` | **Verified Intact** |
| `experiment_3_next_visit_risk_v1/models/logistic_regression_pipeline.joblib` | 6,490 B | `957aea9b8cd0066e364c776c76b12128b7b8e63cafe9800cbda39a03d8486ad7` | **Verified Intact** |

---

## 5. Conclusion & Operational Sign-Off

All wording updates have been executed strictly in place without altering any datasets, feature definitions, target variables, model pipelines, or serialized `.joblib` weights. Both unittest and pytest suites pass with 100% compliance.

Execution is stopped per prompt instructions. The system is fully aligned and ready for subsequent project phases upon user approval.

