# PHASE 5 STAGE 2.3 IMPLEMENTATION REPORT
**Next-Visit DO/Hypoxia Screening & Growth/Feeding Advisory Dashboards (Pages 3 & 4)**
*AI-Based Precision Aquaculture Toxicity and Yield Prediction System*
*Date: November 14, 2026*

---

## 1. Executive Summary

In **Phase 5 Stage 2.3**, we implemented two critical operational dashboard pages:
1. **Page 3: Next-Visit Morning DO and Hypoxia Screening** (`app/dashboard/pages/03_Next_Visit_DO_Hypoxia.py`)
2. **Page 4: Next-Visit Pond-Cohort Fish Weight Benchmark & Provisional Feeding Advisory** (`app/dashboard/pages/04_Growth_Feeding_Advisor.py`)
3. Authored dedicated page-level tests in `app/tests/test_dashboard_stage2_3.py`.

Both pages strictly enforce all scientific governance rules, negative scopes, and empirical benchmark findings established across Phases 1–4 and the approved `PHASE_5_DASHBOARD_DESIGN_PLAN.md`.

---

## 2. Page 3 Implementation Details: Next-Visit Morning DO and Hypoxia Screening

### 2.1 File Implemented
- `app/dashboard/pages/03_Next_Visit_DO_Hypoxia.py` (305 lines)
- Operational Category: `BENCHMARK` (Model Benchmark & Experimental Screening)

### 2.2 Core Architectural & Scientific Functions
1. **Primary Operational Point Regression Benchmark:**
   - **Method:** Historical Training Mean Baseline.
   - **Point Value:** **$3.50\text{ mg/L}$** (exact unconditional training mean: **$3.4984\text{ mg/L}$**; $N = 3,066$ training pairs, 2021–2024).
   - **Mandatory Scientific Notice:** Prominently communicates that this is a **constant historical benchmark, NOT a dynamic biological prediction**.
   - **Empirical Superiority Disclosure:** Explains that this unconditional historical mean achieved the lowest holdout prospective test error in Experiment 5 ($\text{MAE} = 0.3963\text{ mg/L}$, $\text{RMSE} = 0.6450\text{ mg/L}$), outperforming persistence ($\text{MAE} = 0.5334\text{ mg/L}$, $R^2 = -0.7071$, $p < 10^{-12}$) and complex ML regressors ($\text{RF MAE} = 0.4172\text{ mg/L}$, $\text{GBDT MAE} = 0.4260\text{ mg/L}$).
   - **Interactive Visualization:** Interactive Plotly bar chart visually comparing prospective holdout MAE across all four forecasting methods.

2. **Multi-Week Sampling Horizon & Morning Observation Protocol:**
   - **Revisit Interval:** Explicitly scoped to routine farm inspection visits scheduled **3 to 45 days apart (median ~21 days)**.
   - **Morning Window:** Telemetry is strictly collected during standard morning visits (**06:00–08:30 AM**).
   - **Mandatory Limitation:** Observations **are NOT verified pre-dawn daily minimum DO**.
   - **Real-Time Prohibition:** Strictly disclaims continuous streaming telemetry, diurnal cycling tracking, hourly forecasts, or overnight minimum DO prediction.

3. **Exploratory Moderate Hypoxia Screening ($< 3.0\text{ mg/L}$):**
   - **Model:** Gradient Boosting Classifier.
   - **Screening Role:** Risk-ranking score retained strictly for manual inspection queue prioritization, **NEVER an automated emergency alert or aerator trigger**.
   - **Audited False Alarm Burden Disclosure:** At the high-recall cutoff ($p^* = 0.090$), the classifier achieves $53.49\%$ recall ($92/172$ crises detected), but triggers an unsustainable **$50.25\%$ alarm rate** ($1,022/2,034$ visits) with a **$91.00\%$ False Discovery Rate** ($930$ false alarms out of $1,022$ alerts; $80$ false negatives). At the Max F1 cutoff ($p^* = 0.220$), recall collapses to $9.30\%$ ($16/172$ caught; $158$ false positives, $\text{FDR} = 90.80\%$).

4. **Transparent Rejection of Severe Hypoxia Classifier ($< 2.0\text{ mg/L}$):**
   - **Model:** Random Forest Severe Hypoxia Classifier.
   - **Status:** **REJECTED AS DEGENERATE / DISABLED BY GOVERNANCE**.
   - **Audit Disclosure:** At prospective cutoff $p = 0.10$, flagged **$99.56\%$ of test visits** ($2,025 / 2,034$) due to `class_weight='balanced'` probability inflation on severe class imbalance ($91$ positive vs. $1,943$ negative cases), destroying specificity ($0.0041$, generating $1,934$ false alarms). Permanently disabled in production.

---

## 3. Page 4 Implementation Details: Growth Benchmark & Provisional Feeding Advisory

### 3.1 File Implemented
- `app/dashboard/pages/04_Growth_Feeding_Advisor.py` (475 lines)
- Operational Category: `ADVISORY` (Model Benchmark & Provisional Advisory Heuristics)

### 3.2 Core Architectural & Scientific Functions
1. **Next-Visit Pond-Cohort Average Fish Weight Benchmark:**
   - **Model:** Operational Persistence Baseline ($\hat{W}_{t+1} = W_t$).
   - **Target Definition:** Somatic average body weight per fish at next routine visit ($\text{grams/fish}$).
   - **Strict Negative Scope:** Clearly warns that this is **NOT individual fish growth**, **NOT pond biomass growth**, and **NOT commercial harvest yield in kg/ha**. The dataset contains **0% total harvest yield labels**.
   - **Model Performance Disclosure:** Persistence baseline achieved **$\text{MAE} = 93.38\text{ g}$** ($\text{RMSE} = 196.48\text{ g}$, $R^2 = 0.7135$) on all-pairs commercial test data ($N = 1,689$). Machine learning regressors failed significantly ($\text{RF MAE} = 112.15\text{ g}$, $\text{GBDT MAE} = 127.34\text{ g}$, $p < 10^{-12}$) because ML assumes continuous growth and cannot foresee unrecorded commercial partial harvests, net thinning, disease culling, or cycle terminations. Retrospective target-leakage models ($\text{GBDT Clean MAE} = 57.22\text{ g}$) require unobservable future filtering and cannot be deployed operationally.
   - **Interactive Visualization:** Interactive Plotly bar chart comparing MAE across Persistence vs. Random Forest vs. Gradient Boosting.

2. **Provisional Rule-Based Feeding Advisory Engine:**
   - Evaluates morning DO, optional un-ionized $\text{NH}_3$ / TAN, water temperature, and feed/biomass.
   - **Adjustment Tiers:**
     - $\text{DO} < 2.0\text{ mg/L} \rightarrow 100\%\text{ cut}$ (`CEASE_FEEDING`, critical hypoxia heuristic).
     - $2.0 \le \text{DO} < 3.0\text{ mg/L} \rightarrow 50\%\text{ cut}$ (`SUBSTANTIAL_FEED_REDUCTION`, moderate hypoxia heuristic).
     - $3.0 \le \text{DO} < 4.0\text{ mg/L} \rightarrow 20\%\text{ cut}$ (`MODERATE_FEED_REDUCTION`).
     - $\text{NH}_3 \ge 0.10\text{ mg/L} \rightarrow 100\%\text{ cut}$; $\text{NH}_3 \ge 0.05\text{ mg/L} \rightarrow 50\%\text{ cut}$.
     - $\text{TAN} \ge 2.0\text{ mg/L} \rightarrow 50\%\text{ cut}$ (provisional heuristic based on test-kit graduation; **NOT a validated biological toxicity threshold**).
     - $\text{Temp} < 20^\circ\text{C}$ or $> 34^\circ\text{C} \rightarrow 20\%\text{ cut}$ (thermal stress heuristic).
   - **Causality & Verification Notice:** Feed reductions mitigate organic waste loading and biological oxygen demand, but **do NOT cause immediate water quality recovery** or cure hypoxia. All feeding adjustments are provisional decision-support heuristics requiring qualified human verification.
   - **Zero Automatic Actuation:** Confirms no automatic feeder or aerator commands are dispatched (`is_automatic_control = False`).

3. **Observational Feeding Feedback Tracker:**
   - Field recording form allowing technicians to log actual feed dispensed, compliance, and notes.
   - Connected to `ModelRegistry.record_feeding_feedback(...)`.
   - **Audit Notice:** Confirms this is an observational tracking log for retrospective review; **does NOT execute reinforcement learning, online retraining, or automatic parameter updates**.

4. **Operational vs. Simulated Quarantine:**
   - Supports switching between operational field entry and quarantined benchmark simulation mode (`status = "SIMULATED_SCENARIO_ONLY"`, `operational_use_permitted = False`).

---

## 4. Verification and Test Results

### 4.1 Page-Level Test Suite (`test_dashboard_stage2_3.py`)
Authored 9 comprehensive unit tests in `app/tests/test_dashboard_stage2_3.py`:
1. `test_page_03_compiles`: Bytecode compilation via `py_compile` without warnings or syntax errors.
2. `test_page_03_callable`: Confirms `render_page` is callable and exported.
3. `test_page_03_backend_do_hypoxia_integration`: Validates backend point benchmark ($3.50\text{ mg/L}$, exact $3.4984$), method description, and output schema.
4. `test_page_03_scientific_disclaimers_and_terminology`: Confirms mandatory scientific phrases, holdout statistics, and disclaimers in source code.
5. `test_page_04_compiles`: Bytecode compilation via `py_compile`.
6. `test_page_04_callable`: Confirms `render_page` is callable and exported.
7. `test_page_04_backend_fish_growth_integration`: Validates persistence prediction ($\hat{W}_{t+1} = W_t$) and negative scope metadata.
8. `test_page_04_backend_feeding_advisory_integration`: Validates rule-based throttling across normal, critical hypoxia, and moderate hypoxia tiers.
9. `test_page_04_scientific_disclaimers_and_negative_scope`: Confirms negative scope statements, 0% yield label disclaimers, test-kit graduation notes, and non-causal warnings in source code.

**Result:**
```
Ran 9 tests in 5.192s
OK
```

### 4.2 Full Regression Test Suite
Executed the entire project test suite across both `unittest` and `pytest`:
- **Unittest Discovery (`unittest discover -s app/tests -p "test_*.py"`):**
  ```
  Ran 120 tests in 11.627s
  OK
  ```
- **Pytest Discovery (`pytest app/tests/ -q`):**
  ```
  120 passed, 8994 warnings, 4 subtests passed in 13.26s
  ```

*Historical Test Growth:*
- Phase 4 acceptance baseline: 79 passed
- Phase 5 Stage 1 (Foundation): 95 passed (+16)
- Phase 5 Stage 2.1 (Pages 7 & 5): 103 passed (+8)
- Phase 5 Stage 2.2 (Page 2): 111 passed (+8)
- Phase 5 Stage 2.3 (Pages 3 & 4): **120 passed (+9)**

---

## 5. Cryptographic Immutability Audit

All 10 datasets in `processed_data_v2/` and all 9 pre-trained `.joblib` model artifacts were verified against audited baseline SHA-256 hashes. **100% of hashes matched with zero data or model drift.**

### 5.1 Dataset Checksums (`processed_data_v2/`)
| File | Audited SHA-256 Hash | Status |
|---|---|---|
| `dropouts_v2.csv` | `12b7e730aac7ae9e4eed0b89d3a98489ac6cd3c72d55cd4f9b4e3d6dd424d250` | **MATCH (Intact)** |
| `enrolled_ponds_v2.csv` | `94dae8de04c53891af6550afa39a8df8920b67f4b347d01cf9aa5f73aaa16e57` | **MATCH (Intact)** |
| `feeding_analysis_v2.csv` | `c6cf43d6449d81ed7d591f4bbcf5a74a880a6c0f89bcda126f065921a5b3a582` | **MATCH (Intact)** |
| `fish_health_growth_analysis_v2.csv` | `2ed226697d2b7999e3b15b1604ac574b005144598f6cf35fbacf8b7ba2f0023f` | **MATCH (Intact)** |
| `iot_water_model_v2.csv` | `4a577164b2836ffb77ab2f102eea2c8ab5a9898d88590c3cf969808b370ea5af` | **MATCH (Intact)** |
| `preprocessing_v2_report.json` | `b163443291beccefea488270e7dde780d20aad806ab95cd1b1f59ec5d6205333` | **MATCH (Intact)** |
| `preprocessing_v2_report.md` | `66775bbf0ee2a5c423f5d9e372cd0692cff432908d03f476a0e49c6c2323058c` | **MATCH (Intact)** |
| `thresholds_config.json` | `7aad8fc6df5cebfb311b0ca97d6764f25eb313c35814740ad0d8e6953cad3e94` | **MATCH (Intact)** |
| `toxicity_analysis_v2.csv` | `073f5ab11da085160dcb0821e4a16533d96555f8587261c0bd348f385c60c462` | **MATCH (Intact)** |
| `water_quality_cleaned_v2.csv` | `500b2d6fd032eeabb6d1b947dbc6d93b4464c146d41d9e91f4a0367f54f50e1b` | **MATCH (Intact)** |

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

## 6. Current Status & Next Steps

- **Completed in Stage 2.3:** Pages 3 and 4 fully implemented, integrated with backend services, and verified via 120 passing automated tests and hash integrity verification.
- **Git Remote:** Zero remote commits pushed to GitHub remote, honoring the strict user approval requirement.
- **Next Stage (Stage 2.4):**
  - Implement **Page 1: System Operational Overview & Daily Queue** (`01_Overview.py`).
  - Implement **Page 6: Simulation Sandbox & What-If Stress Testing** (`06_Simulation_Sandbox.py`).
  - Implement associated tests in `app/tests/test_dashboard_stage2_4.py`.

