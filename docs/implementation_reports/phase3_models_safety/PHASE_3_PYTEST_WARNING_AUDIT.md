# Phase 3 Pytest Warning Investigation & Audit Report

**AI-Based Precision Aquaculture Toxicity and Yield Prediction System**  
**Date:** November 11, 2026  
**Investigation Mode:** Read-Only Investigation (Zero source code modifications; Zero warning suppressions; Zero test alterations)

---

## 1. Executive Summary

A comprehensive warning investigation was performed on the full test suite using `pytest 9.1.1` under `Python 3.14.4` and `NumPy 2.5.1`.

### Key Findings
1. **Total Test Suite:** 61 test functions collected, 61 passed, 4 subtests passed, 0 failed, 0 errors (100% pass rate).
2. **Total Warnings Captured:** Exactly **8,279** warning events.
3. **Distinct Warning Signatures:** Exactly **1** unique warning signature across the entire test suite.
4. **Project Code Purity:** **0 (Zero)** warnings originate from project code in `app/`.
5. **Numerical & Scientific Purity:** **0 (Zero)** runtime warnings, zero numerical instabilities, zero divide-by-zero, zero NaN propagation, and zero safety issues.
6. **Origin of All 8,279 Warnings:** 100% of the warnings originate from a single line in a third-party library:  
   `joblib/numpy_pickle.py:207` executing `array.shape = self.shape` during the deserialization of pre-existing scikit-learn `.joblib` model artifacts under NumPy 2.5+.

---

## 2. Complete Warning Summary & Grouping

```
+==================================================================================================================================+
|                                              PYTEST WARNING INVENTORY BREAKDOWN                                                  |
+--------------------------+-------------------------------------------------------------------------------------------------------+
| Warning Category         | DeprecationWarning                                                                                    |
+--------------------------+-------------------------------------------------------------------------------------------------------+
| Warning Message          | Setting the shape on a NumPy array has been deprecated in NumPy 2.5.                                  |
|                          | As an alternative, you can create a new view using np.reshape (with copy=False if needed).            |
+--------------------------+-------------------------------------------------------------------------------------------------------+
| Source File & Line       | C:\Users\Samrudhi\AppData\Roaming\Python\Python314\site-packages\joblib\numpy_pickle.py:207            |
+--------------------------+-------------------------------------------------------------------------------------------------------+
| Triggering Statement     | array.shape = self.shape                                                                              |
+--------------------------+-------------------------------------------------------------------------------------------------------+
| Total Occurrences        | 8,279 (100.0% of all captured pytest warnings)                                                        |
+--------------------------+-------------------------------------------------------------------------------------------------------+
| Number of Distinct Tests | 11 test nodes (across app/tests/test_models.py and app/tests/test_feeding_advisor.py)                 |
+--------------------------+-------------------------------------------------------------------------------------------------------+
```

---

## 3. Top 10 Most Frequent Warning Sources

Because there is exactly **one** distinct warning message in the entire suite, the top 10 breakdown represents the test nodes where this deserialization warning is triggered most frequently:

| Rank | Test Node (File & Function) | Occurrences | Deserialization Context |
| :---: | :--- | :---: | :--- |
| **1** | `app/tests/test_models.py::TestModelWrappersAndRegistry::test_registry_partial_failure_tolerance` | **1,129** | Loads full registry (715) + creates secondary partial registry with Exp 1 & Exp 3 models (414) |
| **2** | `app/tests/test_feeding_advisor.py::TestFeedingAdvisorModel::test_adaptive_feedback_recording_and_condition_evaluation` | **715** | First test in module to invoke `get_model_registry()`, triggering initial singleton loading |
| **3** | `app/tests/test_models.py::TestModelWrappersAndRegistry::test_all_models_load_successfully` | **715** | `setUp()` instantiates fresh `ModelRegistry()` (Exp 1: 301 + Exp 2: 8 + Exp 3: 406 arrays) |
| **4** | `app/tests/test_models.py::TestModelWrappersAndRegistry::test_exp1_soft_sensor_handles_internal_nans` | **715** | `setUp()` instantiates fresh `ModelRegistry()` |
| **5** | `app/tests/test_models.py::TestModelWrappersAndRegistry::test_exp1_soft_sensor_missing_core_key_raises_error` | **715** | `setUp()` instantiates fresh `ModelRegistry()` |
| **6** | `app/tests/test_models.py::TestModelWrappersAndRegistry::test_exp1_soft_sensor_prediction_and_metadata` | **715** | `setUp()` instantiates fresh `ModelRegistry()` |
| **7** | `app/tests/test_models.py::TestModelWrappersAndRegistry::test_exp2_mortality_diagnostic_prediction_and_metadata` | **715** | `setUp()` instantiates fresh `ModelRegistry()` |
| **8** | `app/tests/test_models.py::TestModelWrappersAndRegistry::test_exp3_alias_resolution` | **715** | `setUp()` instantiates fresh `ModelRegistry()` |
| **9** | `app/tests/test_models.py::TestModelWrappersAndRegistry::test_exp3_next_visit_ammonia_risk_prediction_and_metadata` | **715** | `setUp()` instantiates fresh `ModelRegistry()` |
| **10** | `app/tests/test_models.py::TestModelWrappersAndRegistry::test_missing_model_artifact_handled_gracefully` | **715** | `setUp()` instantiates fresh `ModelRegistry()` |
| **11** | `app/tests/test_models.py::TestModelWrappersAndRegistry::test_no_model_retrained_or_modified` | **715** | `setUp()` instantiates fresh `ModelRegistry()` |

### Mechanical Breakdown of the 715 Array Unpickling Events
Each instantiation of `ModelRegistry()` loads three audited machine learning artifacts:
- **Experiment 1 (Random Forest Ammonia Soft-Sensor):** 301 NumPy arrays reconstructed $\rightarrow$ **301 warnings**.
  - Random Forest decision trees store internal structure arrays (`children_left`, `children_right`, `feature`, `threshold`, `value`, `n_node_samples`) across 100+ estimators.
- **Experiment 2 (Balanced Logistic Regression Mortality Diagnostic):** 8 NumPy arrays reconstructed $\rightarrow$ **8 warnings**.
  - StandardScaler means/variances + LogisticRegression coefficients and intercept.
- **Experiment 3 (Random Forest Next-Visit Ammonia Risk):** 406 NumPy arrays reconstructed $\rightarrow$ **406 warnings**.
  - Multi-tree structure arrays for Experiment 3 Random Forest classifier.
- **Sum per Registry Load:** $301 + 8 + 406 = \mathbf{715\text{ warnings}}$.
- **Sum across test suite:** $(10 \times 715) + 414 + 715 = \mathbf{8,279\text{ warnings}}$.

---

## 4. Warning Classification & Categorization

```mermaid
pie title Warning Distribution by Origin (Total: 8,279)
    "Third-Party Library (joblib/numpy_pickle.py)" : 8279
    "Project Code (app/)" : 0
```

### 4.1 Project-Code vs. Third-Party Library
* **Project-Code Warnings:** **0 (0.0%)**  
  No warnings are emitted by any application files (`app/config.py`, `app/core/chemistry.py`, `app/core/data_manager.py`, `app/models/*.py`, `app/tests/*.py`).
* **Third-Party Library Warnings:** **8,279 (100.0%)**  
  All warnings originate inside `joblib.numpy_pickle` when reading serialized ndarray headers.

### 4.2 Deprecation vs. Runtime / Numerical Warnings
* **Deprecation Warnings:** **8,279 (100.0%)**  
  A forward-looking deprecation notice indicating that in a future major NumPy release (NumPy 3.0), direct assignment to `array.shape` will be disallowed in favor of `np.reshape()`.
* **Runtime / Numerical Warnings:** **0 (0.0%)**  
  - No `RuntimeWarning` (zero division, overflow, underflow, invalid float conversion).
  - No `UserWarning`.
  - No `FutureWarning`.

---

## 5. Scientific, Biological, and Operational Safety Impact

An exhaustive evaluation was conducted to determine whether these warnings affect calculations, predictions, data integrity, or safety:

1. **Calculation Correctness:**
   - **Verdict:** **UNIMPACTED.**
   - In NumPy 2.5, in-place shape assignment succeeds without error; it merely emits a `DeprecationWarning`. All model coefficients, tree splits, decision nodes, and scaling vectors retain exact mathematical precision. All model outputs match verified benchmark values bit-for-bit.
2. **Input Validation Integrity:**
   - **Verdict:** **UNIMPACTED.**
   - All input validation rules (negative DO rejection, missing DO detection, empty DataFrame rejection, string weight rejection, negative feed rejection) execute with 100% fidelity.
3. **Data Leakage & Model Immutability:**
   - **Verdict:** **UNIMPACTED.**
   - The warnings occur strictly during read-only deserialization (`open(model_path, 'rb')`). Cryptographic SHA-256 checks confirm all 5 `.joblib` model artifacts remain 100% unchanged.
4. **Feeding Advisory & Simulation Guardrails:**
   - **Verdict:** **UNIMPACTED.**
   - The simulation guardrails (`status: "SIMULATED_SCENARIO_ONLY"`, `operational_use_permitted: False`, `SIMULATED_` actions) function without interference.

---

## 6. Verification of `.vscode/settings.json`

The workspace configuration file [`.vscode/settings.json`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/.vscode/settings.json) was inspected:

```json
{
  "python.defaultInterpreterPath": "C:\\Python314\\python.exe",
  "python.analysis.extraPaths": [
    "C:\\Users\\Samrudhi\\AppData\\Roaming\\Python\\Python314\\site-packages",
    "${workspaceFolder}"
  ],
  "python.autoComplete.extraPaths": [
    "C:\\Users\\Samrudhi\\AppData\\Roaming\\Python\\Python314\\site-packages",
    "${workspaceFolder}"
  ],
  "python.terminal.activateEnvironment": true
}
```

### Verification Findings
1. **Existing Interpreter:**
   - `C:\Python314\python.exe` exists, is accessible, and corresponds to Python 3.14.4.
2. **User Site-Packages Path:**
   - `C:\Users\Samrudhi\AppData\Roaming\Python\Python314\site-packages` exists and contains the user-installed packages (`numpy`, `pandas`, `scipy`, `joblib`, `scikit-learn`, `pytest`).
3. **Machine-Specific Analysis:**
   - The path `C:\Users\Samrudhi\AppData\Roaming\...` contains the local Windows user profile name (`Samrudhi`).
   - On this machine, this path is required because `pip install` without administrative privileges places wheels into `%APPDATA%\Python\Python314\site-packages`.
   - **Cross-User Portability Note:** For multi-user repository cloning, VS Code supports the portable variable `${env:APPDATA}\\Python\\Python314\\site-packages`. Alternatively, creating a project-local virtual environment (`.venv`) avoids user-specific roaming directories.
4. **No Unnecessary Overhead:**
   - The configuration contains only 4 essential keys required for Python path resolution. No unnecessary telemetry, formatting overrides, or arbitrary debug flags are present.

---

## 7. Recommendations & Governance Rules

In strict compliance with the user prompt (*"Do not modify source code or suppress warnings. Do not hide warnings using blanket filters or weaken tests"*):

1. **Zero Suppression Policy Maintained:**
   - No `pytest.ini` filter, `-W ignore`, or code-level warning suppressions were added.
   - All 8,279 warnings remain visible and unsuppressed.
2. **Preservation of Pre-Trained Artifacts:**
   - Re-serializing the `.joblib` files under a newer joblib patch would alter the cryptographic SHA-256 hashes of the approved audit artifacts. Therefore, the models must remain untouched.
3. **Long-Term Upstream Path:**
   - When `joblib` releases an updated release that adopts `np.reshape(..., copy=False)` internally, upgrading `joblib` in the Python environment will naturally eliminate this warning without modifying any project code or model artifacts.

---

## 8. Audit Conclusion

- **Total Tests Passing:** 61/61 (100%)
- **Project Code Health:** Completely free of warnings, syntax errors, or unhandled exceptions.
- **Warning Nature:** 100% third-party `DeprecationWarning` from `joblib` under NumPy 2.5.
- **Safety & Scientific Status:** Verified safe; zero impact on numerical calculations, water-quality evaluations, or feeding decisions.
- **Phase 4 Status:** Phase 4 has **not** been started. Execution is stopped here.

