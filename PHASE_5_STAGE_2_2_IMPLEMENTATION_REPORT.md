# PHASE 5 STAGE 2.2 IMPLEMENTATION REPORT
**Water Quality Chemistry & Experimental Toxicity Screening Dashboard (Page 2)**
*AI-Based Precision Aquaculture Toxicity and Yield Prediction System*
*Date: November 14, 2026*

---

## 1. Executive Summary

In **Phase 5 Stage 2.2**, we implemented **Page 2: Water Quality Chemistry & Experimental Toxicity Screening** (`app/dashboard/pages/02_Water_Quality_Toxicity.py`) and authored dedicated page-level tests (`app/tests/test_dashboard_stage2_2.py`).

All implementations adhere strictly to the approved `PHASE_5_DASHBOARD_DESIGN_PLAN.md` and the governance rules established across Phases 1–4:
1. **Emerson Chemistry Integration:** Implements the audited Emerson et al. (1975) aqueous dissociation equilibrium formulation, dynamically calculating equilibrium $pK_a$, un-ionized fraction $f$, and molecular toxic $\text{NH}_3$.
2. **Explicit Basis Handling:** Distinguishes between `TAN-N` (nitrogen basis, requiring the $17.031 / 14.007 \approx 1.21589$ molecular weight conversion factor) and `TAN-NH3` (molecular basis, applying fraction $f$ directly without conversion).
3. **Test-Kit Graduation Disclaimer:** Explicitly labels 2.0 mg/L TAN as a chemical test-kit graduation mark, NOT a validated biological toxicity threshold.
4. **Experiment 1 Soft-Sensor Transparency:** Presents the Random Forest soft-sensor as an experimental proxy with prominent holdout underprediction warnings ($79.59\%$ underpredicted at actual $\text{NH}_3 \ge 0.05\text{ mg/L}$, $100\%$ at $\ge 0.10\text{ mg/L}$, $100\%$ at $\ge 0.20\text{ mg/L}$).
5. **Experiment 2 Mortality Diagnostic Transparency:** Displays the balanced Logistic Regression diagnostic with documented holdout precision ($3.81\%$, 227 false alarms on 236 alerts) and explicitly prohibits automated alarm dispatch.
6. **Experiment 3 Next-Visit Risk Transparency:** Conveys the multi-week prognostic risk ($3 \le \Delta t \le 45$ days) with audited spike sensitivity breakdown ($15$ of $54$ newly developed spikes detected / $27.8\%$ sensitivity), disclaiming continuous hourly or overnight forecasts.
7. **Simulated Data Isolation:** Supports simulated scenario testing with an unambiguous isolation quarantine banner (`status = "SIMULATED_SCENARIO_ONLY"`, `operational_use_permitted = False`).
8. **Defensive Boundaries:** Enforces software input validations while explicitly documenting that numeric clamps are defensive integrity checks, NOT biological safety limits.

---

## 2. Implemented Components & Architecture

### 2.1 File Implemented
- `app/dashboard/pages/02_Water_Quality_Toxicity.py` (367 lines)
- `app/tests/test_dashboard_stage2_2.py` (164 lines)

### 2.2 Page Structure and UI Layout
The page is organized into four intuitive, scientifically rigorous sections:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ Page Header: Water Quality Chemistry & Experimental Toxicity Screening      │
│ Operational Category: EXPERIMENTAL (Screening Proxies & Chemical Equil.)   │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Operating Mode & Scenario Quarantine Selector                            │
│    • Manual Field Inspection Entry (Operational Field Telemetry)            │
│    • Simulated Benchmark Scenario (Quarantined Synthetic Demonstration)     │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. Water Quality Telemetry Input Panel                                      │
│    • DO (0–25 mg/L), pH (0–14), Water Temp (10–45 °C), Revisit (3–45 days)  │
│    • TAN (0–20 mg/L) with Reporting Basis (TAN-N vs TAN-NH3)                │
│    • Optional Secchi Turbidity (cm) and TDS (ppt)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. Emerson (1975) Aqueous Ammonia Dissociation Calculator                   │
│    • Equilibrium pKa, Un-ionized Fraction (f), Molecular Toxic NH3 (mg/L)   │
│    • Test-kit note: TAN 2.0 mg/L is a kit mark, NOT a biological limit      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. Experimental ML Screening Models Panel                                   │
│    ├─ Exp 1: RF Ammonia Soft-Sensor Proxy (MAE 0.0528 mg/L + Warnings)     │
│    ├─ Exp 2: Balanced LR Mortality Diagnostic (3.81% Precision Warning)    │
│    └─ Exp 3: RF Next-Visit Ammonia Risk (3–45 Days Revisit Horizon)        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Scientific & Mathematical Implementation

### 3.1 Emerson Ammonia Equilibrium Formulation
The page consumes the audited backend `app.core.chemistry` functions:
- Temperature-dependent dissociation constant:
  $$pK_a = 0.09018 + \frac{2729.92}{T_C + 273.15}$$
- Un-ionized fraction:
  $$f = \frac{1}{10^{pK_a - \text{pH}} + 1}$$
- Molecular un-ionized ammonia calculation:
  - If basis is `TAN-N (Ammonia-Nitrogen, NH3-N)`:
    $$\text{NH}_3\text{ (mg/L)} = f \times \text{TAN-N} \times \frac{17.031}{14.007}$$
  - If basis is `TAN-NH3 (Molecular Ammonia)`:
    $$\text{NH}_3\text{ (mg/L)} = f \times \text{TAN-NH}_3$$

Missing, negative, or unphysical inputs return `np.nan` (never silently converted to `0.0`).

### 3.2 Heuristic Toxicity Tiering
A provisional heuristic tiering helper is defined to support visual categorization:
- **Optimal:** $\text{NH}_3 < 0.02\text{ mg/L}$ (Normal operation)
- **Caution:** $0.02 \le \text{NH}_3 < 0.05\text{ mg/L}$ (Routine monitoring)
- **Elevated:** $0.05 \le \text{NH}_3 < 0.10\text{ mg/L}$ (Reduce feed 50% / Monitor)
- **Critical:** $0.10 \le \text{NH}_3 < 0.20\text{ mg/L}$ (Cease feeding / Aerate)
- **Extreme:** $\text{NH}_3 \ge 0.20\text{ mg/L}$ (Emergency physical inspection)

> **Scientific Notice:** All displayed tiers are explicitly tagged as *unverified operational heuristics*, requiring human verification and never presented as certified biological standards.

### 3.3 Audited Model Metrics Displayed

| Model Wrapper | Algorithm | Primary Role | Audited Holdout Performance Displayed |
|---|---|---|---|
| **Experiment 1** | Random Forest Regressor | Empirical Soft-Sensor Proxy | Chronological Holdout MAE: **0.0528 mg/L**.<br>Underprediction: **79.59%** at $\ge 0.05$, **100%** at $\ge 0.10$, **100%** at $\ge 0.20$ mg/L. |
| **Experiment 2** | Balanced Logistic Regression | Concurrent Mortality Screening Diagnostic | Chronological Holdout Precision: **3.81%** (227 false alarms on 236 alerts).<br>ROC-AUC: **0.7818**; Holdout Event Rate: **1.69%**. |
| **Experiment 3** | Random Forest Classifier | Next-Visit Ammonia Toxicity Risk ($3\text{--}45$ days) | Chronological Holdout PR-AUC: **0.0305** (no-skill: **0.0280**).<br>Spike Sensitivity: **15 of 54 (27.8%)** newly developed spikes detected. |

---

## 4. Verification and Test Results

### 4.1 Page-Level Test Suite (`test_dashboard_stage2_2.py`)
Authored 8 dedicated unit tests in `app/tests/test_dashboard_stage2_2.py`:
1. `test_page_02_compiles`: Bytecode compilation via `py_compile` without warnings or syntax errors.
2. `test_page_02_callable`: Confirms `render_page` is properly exported and callable.
3. `test_emerson_chemistry_accuracy_and_basis_distinction`: Validates $pK_a$ accuracy, un-ionized fraction bounds, double-precision molecular ratio ($17.031 / 14.007$), and NaN handling on missing inputs.
4. `test_ammonia_toxicity_heuristic_classification`: Verifies heuristic classification across all concentration tiers and missing input resilience.
5. `test_exp1_soft_sensor_integration`: Verifies soft-sensor inference, output fields, and mandatory underprediction disclaimers.
6. `test_exp2_mortality_diagnostic_integration`: Verifies mortality diagnostic inference, probability bounds ($0.0 \le p \le 1.0$), and low-precision warnings.
7. `test_exp3_ammonia_risk_integration`: Verifies next-visit risk inference and multi-week revisit horizon propagation ($3\text{--}45$ days).
8. `test_page_02_scientific_disclaimers_and_terminology`: Confirms mandatory scientific phrases, holdout statistics, and disclaimers are present in page source text.

**Result:**
```
Ran 8 tests in 5.699s
OK
```

### 4.2 Full Regression Test Suite
Ran the entire project test suite across both `unittest` and `pytest`:
- **Unittest Discovery:**
  ```
  Ran 111 tests in 7.774s
  OK
  ```
- **Pytest Discovery:**
  ```
  111 passed, 9061 warnings, 4 subtests passed in 8.91s
  ```

*Summary of test growth:*
- Baseline Phase 4 tests: 79 passed
- Phase 5 Stage 1 foundation tests: 95 passed (+16)
- Phase 5 Stage 2.1 tests: 103 passed (+8)
- Phase 5 Stage 2.2 tests: **111 passed (+8)**

---

## 5. Cryptographic Immutability Audit

All datasets and trained model artifacts were checked against their audited baseline SHA-256 hashes. **Zero modifications or hash drifts occurred.**

### 5.1 Dataset Checksums (`processed_data_v2/`)
| File | Audited SHA-256 Hash | Status |
|---|---|---|
| `dropouts_v2.csv` | `12b7e730aac7ae9e4eed0b89d3a98489ac6cd3c72d55cd4f9b4e3d6dd424d250` | **MATCH (Intact)** |
| `enrolled_ponds_v2.csv` | `94dae8de04c53891af6550afa39a8df8920b67f4b347d01cf9aa5f73aaa16e57` | **MATCH (Intact)** |
| `feeding_analysis_v2.csv` | `c6cf43d6449d81ed7d591f4bbcf5a74a880a6c0f89bcda126f065921a5b3a582` | **MATCH (Intact)** |
| `fish_health_growth_analysis_v2.csv` | `2ed226697d2b7999e3b15b1604ac574b005144598f6cf35fbacf8b7ba2f0023f` | **MATCH (Intact)** |
| `iot_water_model_v2.csv` | `4a577164b2836ffb77ab2f102eea2c8ab5a9898d88590c3cf969808b370ea5af` | **MATCH (Intact)** |
| `toxicity_analysis_v2.csv` | `073f5ab11da085160dcb0821e4a16533d96555f8587261c0bd348f385c60c462` | **MATCH (Intact)** |
| `water_quality_cleaned_v2.csv` | `500b2d6fd032eeabb6d1b947dbc6d93b4464c146d41d9e91f4a0367f54f50e1b` | **MATCH (Intact)** |
| `thresholds_config.json` | `7aad8fc6df5cebfb311b0ca97d6764f25eb313c35814740ad0d8e6953cad3e94` | **MATCH (Intact)** |

### 5.2 Trained Model Artifact Checksums (`.joblib`)
| Model File Path | Audited SHA-256 Hash | Status |
|---|---|---|
| `baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib` | `e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a` | **MATCH (Intact)** |
| `experiment_1_sensor_ablation_v1/models/model_a_rf_pipeline.joblib` | `e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a` | **MATCH (Intact)** |
| `experiment_1_sensor_ablation_v1/models/model_b_rf_pipeline.joblib` | `08907e58a01036eaadb44b6c10370e0219b920ddaa07279504b6e101a0f4a281` | **MATCH (Intact)** |
| `experiment_2_mortality_v1/models/dummy_prior_pipeline.joblib` | `c6259edd0a0908614ba93b3faa78256359098c4461576ec08d40ae46714985fa` | **MATCH (Intact)** |
| `experiment_2_mortality_v1/models/logistic_regression_pipeline.joblib` | `02c8a34ae4ff8b8d907beeed18be4ecd00bb463cd204e8298163f6864afcdadf` | **MATCH (Intact)** |
| `experiment_2_mortality_v1/models/random_forest_pipeline.joblib` | `464344d33ffc3cff26726bfa15ec73d6b8a59b773ae61083db3d3082f44b4216` | **MATCH (Intact)** |
| `experiment_3_next_visit_risk_v1/models/dummy_prior_pipeline.joblib` | `2a51e871bbf2fa4d0d5f7a3c1f0dcbfc49499418383cc887514112bf8fa0de8b` | **MATCH (Intact)** |
| `experiment_3_next_visit_risk_v1/models/logistic_regression_pipeline.joblib` | `957aea9b8cd0066e364c776c76b12128b7b8e63cafe9800cbda39a03d8486ad7` | **MATCH (Intact)** |
| `experiment_3_next_visit_risk_v1/models/random_forest_pipeline.joblib` | `2f7980756c02a5fa00e325919944c8dd416456d785af9f110135e10edd38853c` | **MATCH (Intact)** |

---

## 6. Next Steps

With Phase 5 Stage 2.2 successfully verified:
- **Status:** Phase 5 Stage 2.2 complete and fully verified.
- **Git Remote:** No changes pushed to GitHub remote, honoring explicit user approval requirement.
- **Upcoming Stage (Stage 2.3):**
  - Implement **Page 3: Next-Visit DO & Hypoxia Early Warning** (`03_Next_Visit_DO_Hypoxia.py`).
  - Implement **Page 4: Growth Monitoring & Feeding Decision Advisor** (`04_Growth_Feeding_Advisor.py`).
  - Implement associated tests in `app/tests/test_dashboard_stage2_3.py`.

