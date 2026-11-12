# Phase 1 Implementation Report: Backend Foundation & Data Integration

**Document ID:** `P1-IR-AQUASYSTEM-2026-FINAL`  
**Date:** 2026-11-05  
**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System (BAI507P Mini Project)  
**Status:** Phase 1 Successfully Completed & Fully Verified  
**Scope:** Phase 1 Only (Backend Foundation, Chemistry Engine, Data Loaders, and Test Suite)  

---

## Executive Summary

Phase 1 of the **AI-Based Precision Aquaculture Toxicity and Yield Prediction System** has been implemented and verified in strict accordance with the approved architecture in `FINAL_INTEGRATION_READINESS_REPORT.md` and project instructions.

All deliverables were created inside an isolated `app/` folder. **No existing project scripts, datasets, or experiment artifacts were modified, renamed, moved, or overwritten.** All 10 audited v2 dataset files in `processed_data_v2/` were verified before and after implementation; SHA-256 content hashes confirm 100% data integrity with zero file mutation.

A comprehensive unit test suite covering Emerson chemistry calculations, schema integrity, safe missingness handling, and separation of simulation data from field observation logs achieved a **100% pass rate (19 of 19 tests passed)** in both `unittest` and `pytest`.

---

## 1. Files Created

The following 8 files were created in the new `app/` directory:

| File Path | Purpose | Key Responsibilities |
|---|---|---|
| `app/__init__.py` | Package Initializer | Exports version (`1.0.0`) and defines application package root. |
| `app/config.py` | Configuration & Constants | Centralizes project paths, loads `thresholds_config.json`, establishes Emerson chemistry constants. |
| `app/core/__init__.py` | Core Subpackage Initializer | Marks `app.core` as a Python module for scientific engines. |
| `app/core/chemistry.py` | Ammonia Equilibrium Engine | Implements audited v2 Emerson et al. (1975) equilibrium calculations with molecular weight conversion. |
| `app/core/data_manager.py` | Data Access & Schema Layer | Safe, cached loaders for all 7 audited v2 datasets with schema checks and simulation metadata. |
| `app/tests/__init__.py` | Test Subpackage Initializer | Marks `app.tests` as a Python test package. |
| `app/tests/test_chemistry.py` | Chemistry Unit Tests | 11 unit tests verifying Emerson formula, molecular weight conversion, edge cases, and missing value safety. |
| `app/tests/test_data_manager.py` | Data Manager Unit Tests | 8 unit tests verifying dataset loading, schema enforcement, cache isolation, and simulation separation. |

---

## 2. Implementation Details

### A. System Configuration (`app/config.py`)
- **Reliable Relative Paths:** Anchored to `PROJECT_ROOT = Path(__file__).resolve().parent.parent`, ensuring resilience regardless of invocation working directory.
- **Audited Thresholds Loading:** Safely parses `processed_data_v2/thresholds_config.json` via `load_thresholds_config()`. Preserves provisional heuristic status, warnings, and descriptions without inventing new thresholds.
- **Central Dataset Registry:** Maps canonical dataset keys (`water_quality`, `toxicity_analysis`, `fish_health_growth`, `feeding_analysis`, `enrolled_ponds`, `dropouts`, `iot_water_model`) to their exact filesystem paths.
- **Chemical Constants:** Defines explicit double-precision constants for the Emerson equation:
  - `EMERSON_PKA_INTERCEPT = 0.09018`
  - `EMERSON_PKA_SLOPE = 2729.92`
  - `ABSOLUTE_ZERO_CELSIUS = -273.15`
  - `MW_NH3 = 17.031` g/mol
  - `MW_N = 14.007` g/mol
  - `MW_RATIO_NH3_N = 17.031 / 14.007 ≈ 1.2158919`

### B. Ammonia Dissociation Chemistry Engine (`app/core/chemistry.py`)
- **Dissociation Constant ($pK_a$):**
  $$pK_a = 0.09018 + \frac{2729.92}{T_C + 273.15}$$
  Safely handles non-physical temperatures ($\le -273.15^\circ\text{C}$ or $> 100^\circ\text{C}$) by returning `np.nan`.
- **Un-ionized Fraction ($f$):**
  $$f = \frac{1}{10^{(pK_a - \text{pH})} + 1}$$
  Safely clamps numerical overflows on extreme pH exponents ($<-50 \rightarrow 1.0$, $>+50 \rightarrow 0.0$) and rejects out-of-range pH values ($< 0$ or $> 14$).
- **Dual Basis Handling:**
  1. **TAN reported as Nitrogen (`calculate_nh3_from_tan_n`):** Applies $(17.031 / 14.007)$ **exactly once**:
     $$\text{NH}_3 = f \times \text{TAN-N} \times \left(\frac{17.031}{14.007}\right)$$
  2. **TAN reported as Molecular Ammonia (`calculate_nh3_from_tan_nh3`):** Applies fraction directly **without** conversion:
     $$\text{NH}_3 = f \times \text{TAN-NH}_3$$
- **Unified Interface (`calculate_ammonia_toxicity`):** Accepts reporting basis explicitly (`'TAN_N'` or `'TAN_NH3'`) and returns a structured dictionary with metadata, calculation transparency, and standard scientific disclaimers.
- **Series Vectorization (`calculate_nh3_series`):** Supports batch calculation over pandas Series.
- **Strict Prohibition of Zero-Filling:** Missing inputs (`NaN`, `None`, empty string) explicitly return `np.nan` and never 0.0.

### C. Dataset Manager & Schema Validation (`app/core/data_manager.py`)
- **Audited Dataset Loaders:** Dedicated loaders for all 7 v2 datasets:
  - `load_water_quality_data()` ($N = 12,399$ rows)
  - `load_toxicity_analysis_data()` ($N = 6,945$ rows)
  - `load_fish_health_growth_data()` ($N = 9,422$ rows)
  - `load_feeding_analysis_data()` ($N = 6,752$ rows)
  - `load_enrolled_ponds_data()` ($N = 324$ rows)
  - `load_dropouts_data()` ($N = 128$ rows)
  - `load_iot_water_model_data()` ($N = 4,383$ rows)
- **Schema & Missingness Integrity:** Key column presence is validated at load time; missing values are preserved as `NaN`.
- **Defensive In-Memory Caching:** Internal cache stores deep copies (`df.copy(deep=True)`) to ensure caller mutations do not corrupt subsequent calls or the cache.
- **Strict Simulation Quarantine:** `load_iot_water_model_data()` tags the dataframe with `attrs["is_simulation"] = True` and attaches an explicit disclaimer that the data represents mathematical model outputs from `Data_Model_IoTMLCQ_2024.xlsx`, not live pond telemetry.

---

## 3. Chemistry Verification Results

To confirm numerical consistency with the audited `clean_datasets_v2.py` pipeline, the implementation was benchmarked across standard reference points:

| Scenario | Input Parameters | Formula Applied | Expected Output | Actual Output | Verification Result |
|---|---|---|---|---|---|
| **Commercial Pond Benchmark** | $\text{TAN}=1.5$ mg/L, $\text{pH}=8.2$, $T=28.5^\circ\text{C}$ | TAN-N with MW ratio $(17/14)$ | `0.18778` mg/L | `0.18778` mg/L | **EXACT MATCH** |
| **Direct Molecular Basis** | $\text{TAN}=1.5$ mg/L, $\text{pH}=8.2$, $T=28.5^\circ\text{C}$ | TAN-$\text{NH}_3$ direct fraction | `0.15444` mg/L | `0.15444` mg/L | **EXACT MATCH** |
| **Molecular Weight Ratio** | Identical inputs ($T=27^\circ\text{C}, \text{pH}=8.0, \text{TAN}=1.5$) | $\text{Result}_{\text{N}} / \text{Result}_{\text{NH}_3}$ | $1.2158919$ | $1.2158919$ | **EXACT MATCH** |
| **Standard Emerson Reference** | $T=25.0^\circ\text{C}$ | $pK_a = 0.09018 + \frac{2729.92}{298.15}$ | $9.2464$ | $9.2464$ | **EXACT MATCH** |
| **Half-Dissociation Equivalence** | $\text{pH} = pK_a$, $T=25.0^\circ\text{C}$ | Fraction $f = \frac{1}{10^0 + 1}$ | $0.50000$ | $0.50000$ | **EXACT MATCH** |
| **Missing TAN Input** | $\text{TAN}=\text{NaN}$, $\text{pH}=8.0$, $T=25.0^\circ\text{C}$ | Missing input check | `np.nan` (Not 0.0) | `np.nan` | **PASS (No zero-fill)** |
| **Negative TAN Input** | $\text{TAN}=-1.0$, $\text{pH}=8.0$, $T=25.0^\circ\text{C}$ | Physical validity check | `np.nan` | `np.nan` | **PASS (Unphysical rejected)** |
| **Sub-Absolute Zero Temp** | $\text{TAN}=1.0$, $\text{pH}=8.0$, $T=-300.0^\circ\text{C}$ | Temperature validity check | `np.nan` | `np.nan` | **PASS (Unphysical rejected)** |

---

## 4. Dataset Loading & Schema Verification Results

All 7 audited v2 datasets were verified for row count, column structure, missingness preservation, and read-only integrity:

| Dataset Key | Target File | Rows | Columns | Verified Key Schema | Missing Values Preserved |
|---|---|---|---|---|---|
| `water_quality` | `water_quality_cleaned_v2.csv` | 12,399 | 31 | `pond_id`, `DO (mg/L)`, `pH`, `Temp (in °C)`, `datetime` | Yes (84,796 missing preserved) |
| `toxicity_analysis` | `toxicity_analysis_v2.csv` | 6,945 | 27 | `pond_id`, `dissolved_oxygen_mg_l`, `ph`, `temp_c`, `primary_calculated_nh3_mg_l` | Yes (37,003 missing preserved) |
| `fish_health_growth` | `fish_health_growth_analysis_v2.csv` | 9,422 | 17 | `pond_id`, `datetime`, `species`, `average_fish_weight_g` | Yes (7,062 missing preserved) |
| `feeding_analysis` | `feeding_analysis_v2.csv` | 6,752 | 17 | `pond_id`, `datetime`, `species`, `feed_amount_kg` | Yes (9,040 missing preserved) |
| `enrolled_ponds` | `enrolled_ponds_v2.csv` | 324 | 21 | `pond_id`, `region`, `Pond area in acres` | Yes (588 missing preserved) |
| `dropouts` | `dropouts_v2.csv` | 128 | 8 | `pond_id`, `Date of drop out`, `Reason` | Yes (0 missing) |
| `iot_water_model` | `iot_water_model_v2.csv` | 4,383 | 29 | `Datetime`, `Dissolved Oxygen (mg/L)`, `pH`, `Temperature (°C)`, `datetime_iso` | Yes (0 missing; simulation flag attached) |

---

## 5. Test Suite Execution Results

All 19 tests passed with zero failures and zero errors.

### Pytest Execution Summary
```text
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.7.0
rootdir: D:\AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System
collected 19 items

app/tests/test_chemistry.py::TestAmmoniaChemistry::test_invalid_inputs_handled_safely PASSED [  5%]
app/tests/test_chemistry.py::TestAmmoniaChemistry::test_missing_values_handled_safely PASSED [ 10%]
app/tests/test_chemistry.py::TestAmmoniaChemistry::test_no_silent_zero_replacement PASSED [ 15%]
app/tests/test_chemistry.py::TestAmmoniaChemistry::test_numerical_consistency_with_audited_v2 PASSED [ 21%]
app/tests/test_chemistry.py::TestAmmoniaChemistry::test_pka_calculation PASSED [ 26%]
app/tests/test_chemistry.py::TestAmmoniaChemistry::test_ratio_between_tan_n_and_tan_nh3 PASSED [ 31%]
app/tests/test_chemistry.py::TestAmmoniaChemistry::test_tan_n_applies_mw_conversion_once PASSED [ 36%]
app/tests/test_chemistry.py::TestAmmoniaChemistry::test_tan_nh3_does_not_apply_mw_conversion PASSED [ 42%]
app/tests/test_chemistry.py::TestAmmoniaChemistry::test_unified_toxicity_interface PASSED [ 47%]
app/tests/test_chemistry.py::TestAmmoniaChemistry::test_unionized_fraction PASSED [ 52%]
app/tests/test_chemistry.py::TestAmmoniaChemistry::test_vectorized_series_calculation PASSED [ 57%]
app/tests/test_data_manager.py::TestDataManager::test_all_v2_datasets_load_successfully PASSED [ 63%]
app/tests/test_data_manager.py::TestDataManager::test_defensive_caching_prevents_mutation PASSED [ 68%]
app/tests/test_data_manager.py::TestDataManager::test_historical_and_simulated_datasets_remain_separate PASSED [ 73%]
app/tests/test_data_manager.py::TestDataManager::test_missing_dataset_key_raises_keyerror PASSED [ 78%]
app/tests/test_data_manager.py::TestDataManager::test_missing_file_raises_filenotfound PASSED [ 84%]
app/tests/test_data_manager.py::TestDataManager::test_missing_values_remain_missing PASSED [ 89%]
app/tests/test_data_manager.py::TestDataManager::test_source_csv_files_unmodified PASSED [ 94%]
app/tests/test_data_manager.py::TestDataManager::test_specialized_loaders PASSED [100%]

============================= 19 passed in 1.88s ==============================
```

---

## 6. Confirmation of Source Data & Artifact Immutability

SHA-256 hashes of all files in `processed_data_v2/` were computed prior to implementation and re-verified following all test runs:

| File Name | SHA-256 Hash (Prefix) | Pre-Implementation | Post-Implementation | Status |
|---|---|---|---|---|
| `dropouts_v2.csv` | `12b7e730aac7ae9e` | `12b7e730aac7ae9e` | `12b7e730aac7ae9e` | **Unchanged** |
| `enrolled_ponds_v2.csv` | `94dae8de04c53891` | `94dae8de04c53891` | `94dae8de04c53891` | **Unchanged** |
| `feeding_analysis_v2.csv` | `c6cf43d6449d81ed` | `c6cf43d6449d81ed` | `c6cf43d6449d81ed` | **Unchanged** |
| `fish_health_growth_analysis_v2.csv` | `2ed226697d2b7999` | `2ed226697d2b7999` | `2ed226697d2b7999` | **Unchanged** |
| `iot_water_model_v2.csv` | `4a577164b2836ffb` | `4a577164b2836ffb` | `4a577164b2836ffb` | **Unchanged** |
| `preprocessing_v2_report.json` | `b163443291beccef` | `b163443291beccef` | `b163443291beccef` | **Unchanged** |
| `preprocessing_v2_report.md` | `66775bbf0ee2a5c4` | `66775bbf0ee2a5c4` | `66775bbf0ee2a5c4` | **Unchanged** |
| `thresholds_config.json` | `7aad8fc6df5cebfb` | `7aad8fc6df5cebfb` | `7aad8fc6df5cebfb` | **Unchanged** |
| `toxicity_analysis_v2.csv` | `073f5ab11da08516` | `073f5ab11da08516` | `073f5ab11da08516` | **Unchanged** |
| `water_quality_cleaned_v2.csv` | `500b2d6fd032eeab` | `500b2d6fd032eeab` | `500b2d6fd032eeab` | **Unchanged** |

All raw datasets in `dataset/`, experiment scripts (`train_experiment_*.py`, `clean_datasets_v2.py`, etc.), and existing audit deliverables remain 100% untouched.

---

## 7. Issues to Address Before Phase 2

1. **Pre-Trained Pipeline Verification for Water-Quality & Toxicity Models:**
   - In Phase 2, we will wrap pre-trained `.joblib` pipelines for Experiment 1 (`baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib`), Experiment 2 (`experiment_2_mortality_v1/models/`), and Experiment 3 (`experiment_3_next_visit_risk_v1/models/`).
   - We must verify that `scikit-learn` pipeline feature names match incoming dictionaries and handle missing categorical indicators gracefully without crashing.
2. **Explicit Exploratory Flagging:**
   - All Phase 2 inference wrappers must attach explicit metadata flags:
     - Exp 1: Experimental soft-sensor only; cannot serve as independent safety alarm.
     - Exp 2: Advisory severity diagnostic flag; cannot trigger automated alarms.
     - Exp 3: Experimental multi-week trend warning; cannot trigger operational alarms.

---

## 8. Conclusion & Sign-Off

Phase 1 has established an audited, robust backend foundation. The application structure, configuration, Emerson chemistry engine, and dataset access layer are operational, fully tested, and strictly decoupled from existing research deliverables.

**Phase 1 is complete. Awaiting user review and authorization before proceeding to Phase 2.**

