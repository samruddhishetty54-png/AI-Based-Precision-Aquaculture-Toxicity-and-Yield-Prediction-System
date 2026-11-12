# Phase 5 Dashboard Design Plan: AI-Based Precision Aquaculture Decision-Support System

**Document ID:** `P5-DDP-AQUASYSTEM-2026-REVISED`  
**Date:** November 11, 2026 (Revised with Scientific Corrections)  
**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System (BAI507P Mini Project)  
**Deliverable Scope:** Phase 5 — Comprehensive Dashboard Architecture, Page Hierarchy, Categorized Navigation, Model Integration, Scientific Disclaimers, and Testing Strategy  
**Status:** Revised Design Plan Formulated — Awaiting User Approval (Zero Dashboard Code Implemented)  
**Author:** AI Technical Lead & UI/UX Systems Architect  

---

## Executive Summary

Phase 5 introduces the user-facing application interface for the **AI-Based Precision Aquaculture Toxicity and Yield Prediction System**. The objective is to provide a clean, professional, and scientifically rigorous **Streamlit dashboard** that assists commercial fish farmers, pond technicians, and aquaculture extension officers in reviewing pond conditions, exploring multi-week water quality trends, assessing biological risks, and receiving transparent decision-support advisories.

### Foundational Principles & Governance Rules

1. **Decision-Support Only (No Automated Control):** The dashboard is strictly an advisory decision-support interface. It executes **zero automated control commands** and does not interface with physical actuators, electronic feeding gates, or nocturnal aeration switches (`is_automatic_control = False`). All recommendations require qualified human inspection and verification.
2. **Clear Scientific Categorization (No Exaggerated Capabilities):** All dashboard views and components are explicitly partitioned into five distinct operational categories:
   - **Historical Field Observations:** Empirical records collected during routine multi-week commercial farm inspections.
   - **Model Benchmarks:** Analytical baselines (e.g. constant historical mean DO, somatic weight persistence) providing prospective reference standards.
   - **Experimental Screening Results:** Machine learning models with documented empirical limitations (e.g. soft-sensor underpredictions, high false discovery rates) used solely for inspection prioritization.
   - **Simulated Scenarios:** Synthetic or mathematical models used exclusively for offline demonstration and educational stress-testing.
   - **Provisional Advisories:** Rule-based decision-support heuristics requiring human review.
3. **Discrete Multi-Week Horizon (No Real-Time / Overnight Claims):** Field observations and prognostic models operate on scheduled routine farm visits ($3 \le \Delta t \le 45$ days; median ~21 days). Dissolved oxygen records represent **morning DO observations (06:00–08:30 AM)**, which are **NOT verified pre-dawn daily minimum DO**. The dashboard **explicitly disclaims** continuous real-time sensor streaming, diurnal cycling, hourly forecasts, or overnight predictions.
4. **Target Definition: Next-Visit Pond-Cohort Average Fish Weight (No Harvest Yield / Biomass Claims):** The Experiment 4 modeling target is strictly **next-visit pond-cohort average fish weight** (grams/fish). It is **NOT** individual fish growth, **NOT** harvest biomass, and **NOT** total commercial harvest yield in kg/ha. The reported $\text{MAE} = 93.38\text{ g}$ belongs strictly to the all-pairs chronological persistence baseline ($\hat{W}_{t+1} = W_t$). The dashboard transparently presents this baseline as an analytical reference benchmark, explaining that it is not a reliable dynamic biological growth predictor.
5. **Strict Physical and Visual Isolation of Simulated Data:** Real-world field inspection logs (`water_quality_cleaned_v2.csv`, etc.) and mathematical simulation models (`iot_water_model_v2.csv`) are strictly segregated. Any simulated input or scenario immediately triggers visible amber/orange warning banners, tags `status = "SIMULATED_SCENARIO_ONLY"`, and sets `operational_use_permitted = False`. Simulated data is barred from operational farm evaluation pages.
6. **Application Boundary Validations vs. Biological Safety Thresholds:** Application input-validation ranges (e.g. form entry constraints) represent software defensive boundary checks designed to reject unphysical entries, sensor failures, or numeric errors; they are **NEVER described as validated biological safety thresholds**.
7. **Provisional Feeding Heuristics (Human Verification Required):** All feeding adjustment rules are clearly labelled as **provisional decision-support heuristics requiring human verification**, based on empirical pond literature and test-kit graduations. Specifically, **TAN 2.0 mg/L is identified solely as a standard chemical test-kit graduation**, NOT a validated toxicological safety threshold.
8. **Zero Model Retraining & Absolute Immutability:** Pre-trained model artifacts, core chemistry equations, and cleaned datasets in `processed_data_v2/` remain 100% read-only and immutable.

---

## 1. System & Dashboard Architecture

### 1.1 Multi-Layer Architecture
The dashboard architecture cleanly separates user presentation from model inference, core chemistry, and dataset management:

```
+---------------------------------------------------------------------------------------------------+
|                                  PRESENTATION LAYER (Streamlit)                                   |
|  - Multi-Page Navigation & Session State Manager                                                  |
|  - Visual Dashboard Cards, Metric Badges, Condition Alerts, Interactive Plotly Visualizations     |
|  - Strict Simulation Watermarking & Machine-Readable Operational Gating Flags                     |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                  SERVICE COORDINATION LAYER                                       |
|  - app.models.registry.ModelRegistry (Central Singleton Coordinator)                              |
|  - Fault Isolation & Dynamic Health Checking (health_check(), list_models())                      |
|  - Domain Method Proxies (predict_ammonia_soft_sensor, predict_do_hypoxia, get_feeding_advisory)    |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                                     MODEL WRAPPER LAYER                                           |
|  ├── exp1_soft_sensor.py  : RF Un-ionized Ammonia Proxy (Tiered Underprediction Warnings)         |
|  ├── exp2_mortality.py    : Balanced LR Mortality Diagnostic (Chronological Benchmark)            |
|  ├── exp3_ammonia_risk.py : RF Next-Visit Multi-Week Toxicity Prognostic (Spike Breakdown)        |
|  ├── fish_growth.py       : Exp 4 Somatic Weight Persistence Baseline (W_t+1 = W_t)               |
|  ├── feeding_advisor.py   : Provisional Rule-Based Feeding Throttles & Observational Feedback     |
|  └── do_hypoxia.py        : Exp 5 Historical Mean DO Benchmark (3.50 mg/L) & GBDT Screening       |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                               CORE LOGIC & DATA MANAGEMENT LAYER                                  |
|  ├── app.core.chemistry.py    : Emerson Aqueous Ammonia Dissociation & MW Conversions             |
|  ├── app.core.data_manager.py : Defensive Cached Access to Audited Datasets (NaN Preservation)    |
|  └── app.config.py            : Paths, Chemical Constants, Threshold Configurations               |
+---------------------------------------------------------------------------------------------------+
                                                  │
                                                  ▼
+---------------------------------------------------------------------------------------------------+
|                               PERSISTENCE & ARTIFACT STORAGE LAYER                                |
|  ├── processed_data_v2/       : 10 Audited CSV/JSON Datasets (100% Read-Only, Cryptographically   |
|  │                              Verified SHA-256 Hashes)                                          |
|  └── *.joblib Artifacts       : 9 Audited Pre-Trained Model Pipelines (100% Read-Only)            |
+---------------------------------------------------------------------------------------------------+
```

### 1.2 Technology Stack
- **Web Application Framework:** Streamlit (>= 1.30.0). Provides a reactive, component-based user interface optimized for scientific and decision-support data applications.
- **Data Manipulation & Computation:** Pandas (>= 2.0.0), NumPy (>= 1.24.0).
- **Interactive Visualizations:** Plotly / Altair / native Streamlit charting. Interactive time series, threshold gauges, scatter plots, and distribution curves.
- **Model Orchestration:** Existing `app.models.registry.ModelRegistry` singleton (`get_model_registry()`).
- **Packaging Directory:** All dashboard components will reside cleanly under `app/dashboard/` with a top-level launcher `dashboard.py`, leaving all existing Phase 1–4 modules completely intact.

---

## 2. Page Structure, Navigation & Scientific Categorization

The dashboard is structured into **7 dedicated pages** accessible via Streamlit's native sidebar navigation. Each page title and header strictly adheres to scientific categorization without exaggerating model capabilities:

```
Dashboard Navigation Hierarchy:
├── 🏠 1. Pond Monitoring Overview & Model Status (`01_Overview.py`)
│   └── Category: Multi-Pond Field Status & Model Registry Health
├── 🧪 2. Water Quality Chemistry & Experimental Toxicity Screening (`02_Water_Quality_Toxicity.py`)
│   └── Category: Emerson Equilibrium Chemistry & Experimental Screening Models (Exp 1, 2, 3)
├── 🫁 3. Next-Visit Morning DO and Hypoxia Screening (`03_Next_Visit_DO_Hypoxia.py`)
│   └── Category: Model Benchmark (Historical Mean DO) & Experimental Screening (GBDT Hypoxia)
├── 🐟 4. Next-Visit Pond-Cohort Fish Weight Benchmark & Provisional Feeding Advisory (`04_Growth_Feeding_Advisor.py`)
│   └── Category: Model Benchmark (Persistence Baseline) & Provisional Advisory Heuristics
├── 📈 5. Historical Field Observations Explorer (`05_Historical_Data_Explorer.py`)
│   └── Category: Historical Field Observations (Logged Multi-Week Farm Inspections)
├── 🔬 6. Simulated Scenarios Sandbox (Non-Operational) (`06_Simulation_Sandbox.py`)
│   └── Category: Simulated Scenarios (Synthetic Benchmarking Environment)
└── 🛡️ 7. Model Registry Governance & Audit Benchmark Catalog (`07_Model_Registry_Governance.py`)
    └── Category: Audited Model Benchmarks, Scientific Disclaimers & Governance Controls
```

---

### Detailed Page Specifications

#### Page 1: Pond Monitoring Overview & Model Status (`01_Overview.py`)
* **Category:** Multi-Pond Field Status & Model Registry Health
* **Target Audience:** Farm managers, pond supervisors, and extension officers.
* **Core Functions:**
  1. **Executive Farm Field KPI Bar:** Summary metrics across monitored commercial ponds (active enrolled ponds, median morning DO, median pH, cohort average fish weight, current feeding rates).
  2. **Model Registry Health Banner:** Live visual status pill for all 6 registered models generated via `registry.health_check()`.
     - Displays `READY` (green) or `FAULT ISOLATED` (amber) for each model.
     - Confirms zero model retraining occurring at runtime.
  3. **Field Inspection Priority Queue:** Table ordering commercial ponds by latest morning DO reading and estimated un-ionized ammonia toxicity tier, highlighting ponds requiring immediate physical inspection.
  4. **System Governance Notice:** Persistent disclaimer emphasizing that all system outputs are decision-support aids requiring qualified human verification, with zero automated control of aeration, feeding, or water exchange (`is_automatic_control = False`).

---

#### Page 2: Water Quality Chemistry & Experimental Toxicity Screening (`02_Water_Quality_Toxicity.py`)
* **Category:** Emerson Equilibrium Chemistry & Experimental Screening Models
* **Target Audience:** Farm technicians and water quality specialists evaluating pond chemistry.
* **Core Functions:**
  1. **Field Water Quality Evaluator:** Form accepting morning physical readings: DO, pH, Temperature (°C), TAN (mg/L), Turbidity (cm), TDS (ppt). Form boundary limits are software validation checks, not biological safety limits.
  2. **Emerson Chemical Dissociation Engine:**
     - Computes dynamic dissociation constant ($pK_a$) using Emerson et al. (1975) equilibrium equation.
     - Computes toxic un-ionized ammonia fraction ($f$) and molecular $\text{NH}_3$ concentration (mg/L).
     - Clearly identifies TAN 2.0 mg/L as a standard test-kit graduation, NOT a validated biological toxicity threshold.
  3. **Experiment 1 Ammonia Soft-Sensor Card (Experimental Screening):**
     - Outputs estimated un-ionized $\text{NH}_3$ proxy from physical parameters.
     - **Mandatory Empirical Warning:** Highlights verified chronological holdout findings across audited concentration tiers:
       * Actual $\text{NH}_3 \ge 0.05\text{ mg/L}$: **79.59% underprediction** ($N = 98$).
       * Actual $\text{NH}_3 \ge 0.10\text{ mg/L}$: **100.00% underprediction** ($N = 33$).
       * Actual $\text{NH}_3 \ge 0.20\text{ mg/L}$: **100.00% underprediction** ($N = 10$).
       * Explicit prohibition against using the soft-sensor as an independent safety alarm.
  4. **Experiment 2 Fish Mortality Diagnostic Card (Experimental Diagnostic):**
     - Displays concurrent mortality probability score from balanced Logistic Regression.
     - Displays audited chronological holdout benchmarks: $\text{ROC-AUC} = 0.5917$, $\text{PR-AUC} = 0.0499$, $\text{Recall} = 20.45\%$, $\text{Precision} = 3.81\%$ ($227\text{ false alarms} / 236\text{ alerts}$).
     - Warning against automated mortality alarming due to extreme class imbalance and high false-positive rate.
  5. **Experiment 3 Next-Visit Multi-Week Ammonia Risk Card (Experimental Screening):**
     - Prognostic risk score for ammonia spike occurrence at the next routine visit ($3 \le \Delta t \le 45$ days).
     - Transparent detection breakdown: distinguishes 18 total true positives from 15 of 54 newly developed spikes detected ($27.8\%$ sensitivity).
     - Disclaims hourly or overnight forecasts.

---

#### Page 3: Next-Visit Morning DO and Hypoxia Screening (`03_Next_Visit_DO_Hypoxia.py`)
* **Category:** Model Benchmark & Experimental Screening
* **Target Audience:** Farm technicians and aquaculture planners reviewing pond oxygen status.
* **Core Functions:**
  1. **Historical Training Mean DO Benchmark:**
     - Point benchmark: audited training mean of **$3.50\text{ mg/L}$** (exact $3.4984\text{ mg/L}$).
     - **Explicit Scientific Disclaimer:** Clearly communicates that this is a **constant historical benchmark, not a dynamic biological prediction**.
     - Contextual performance disclosure: Explains that this unconditional constant historical mean achieved the lowest prospective test error in Experiment 5 ($\text{MAE} = 0.3963\text{ mg/L}$, $\text{RMSE} = 0.6450\text{ mg/L}$), outperforming persistence ($\text{MAE} = 0.5334\text{ mg/L}$) and complex ML regressors ($\text{RF MAE} = 0.4172\text{ mg/L}$, $\text{GBDT MAE} = 0.4260\text{ mg/L}$).
  2. **Multi-Week Sampling Horizon & Morning Observation Disclaimers:**
     - Revisit interval: **3–45 days** (routine farm inspection schedule; median ~21 days).
     - Sampling time: **Morning DO observation (06:00–08:30 AM)**.
     - **Mandatory Limitation Notice:** Explicitly states that these observations **are NOT verified pre-dawn daily minimum DO**.
     - **Prohibition of Real-Time Claims:** Strictly disclaims continuous sensor streaming, diurnal cycling, hourly forecasts, or overnight minimum DO prediction.
  3. **Exploratory Moderate Hypoxia Screening (< 3.0 mg/L):**
     - Risk-ranking score from Gradient Boosting Classifier.
     - **Strictly Exploratory Classification:** Maintained solely as an exploratory screening score for inspection queues, **NEVER an automated emergency alert**.
     - **Audited False Alarm Burden Disclosure:** At cutoff $p^* = 0.090$, GBDT triggers an unsustainable **50.25% alarm rate** ($1,022/2,034$ visits) with a **91.00% False Discovery Rate** (930 false positives, 92 true positives, 80 false negatives, recall 53.49%).
  4. **Transparent Rejection of Severe Hypoxia Classifier (< 2.0 mg/L):**
     - Full educational disclosure explaining why the Random Forest severe-hypoxia classifier was **REJECTED AS DEGENERATE** ($99.56\%$ alarm rate due to `class_weight='balanced'` probability distortion).

---

#### Page 4: Next-Visit Pond-Cohort Fish Weight Benchmark & Provisional Feeding Advisory (`04_Growth_Feeding_Advisor.py`)
* **Category:** Model Benchmark & Provisional Advisory Heuristics
* **Target Audience:** Pond feeding managers, field nutritionists, and farm supervisors.
* **Core Functions:**
  1. **Next-Visit Pond-Cohort Average Fish Weight Benchmark:**
     - Target definition: **Next-visit pond-cohort average fish weight** (grams/fish).
     - **Strict Negative Scope:** Clearly communicates that this is **NOT individual fish growth**, **NOT harvest biomass**, and **NOT commercial harvest yield in kg/ha**.
     - Persistence baseline: $\hat{W}_{t+1} = W_t$ (next-visit cohort weight equals current observed cohort weight).
     - Contextual performance disclosure: Reported **$\text{MAE} = 93.38\text{ g}$** belongs strictly to the all-pairs chronological persistence baseline. The dashboard clearly explains that the baseline is an analytical reference benchmark and **not a reliable dynamic growth predictor**.
  2. **Provisional Rule-Based Feeding Advisory Engine:**
     - Evaluates current morning DO, optional un-ionized $\text{NH}_3$ / TAN, water temperature, and feed/biomass.
     - **Heuristic Status:** Explicitly labelled as **provisional decision-support heuristics requiring human verification**, based on empirical extension literature and test-kit graduations.
     - Provisional adjustment tiers:
       * $\text{DO} < 2.0\text{ mg/L} \rightarrow 100\%\text{ cut}$ (`CEASE_FEEDING`, critical hypoxia heuristic).
       * $2.0 \le \text{DO} < 3.0\text{ mg/L} \rightarrow 50\%\text{ cut}$ (`SUBSTANTIAL_FEED_REDUCTION`, moderate hypoxia heuristic).
       * $3.0 \le \text{DO} < 4.0\text{ mg/L} \rightarrow 20\%\text{ cut}$ (`MODERATE_FEED_REDUCTION`).
       * $\text{NH}_3 \ge 0.10\text{ mg/L} \rightarrow 100\%\text{ cut}$; $\text{NH}_3 \ge 0.05\text{ mg/L} \rightarrow 50\%\text{ cut}$.
       * $\text{TAN} \ge 2.0\text{ mg/L} \rightarrow 50\%\text{ cut}$ (provisional heuristic based on test-kit graduation; NOT a validated biological toxicity threshold).
       * $\text{Temp} < 20^\circ\text{C}$ or $> 34^\circ\text{C} \rightarrow 20\%\text{ cut}$ (thermal stress heuristic).
     - **Causality Disclaimer:** Clearly explains that reducing feed reduces metabolic oxygen demand and prevents organic waste / BOD loading, but **does not cause immediate water-quality recovery** or cure hypoxia.
  3. **Observational Adaptive Feedback Tracker:**
     - Logging form to record actual feed dispensed and subsequent inspection readings.
     - Displays condition transition result (`improved`, `worsened`, `unchanged`, `insufficient_data`).
     - Persistent audit disclaimer: Logs observational data for human retrospective review; **does NOT execute reinforcement learning, automated parameter tuning, or causal learning**.

---

#### Page 5: Historical Field Observations Explorer (`05_Historical_Data_Explorer.py`)
* **Category:** Historical Field Observations
* **Target Audience:** Aquaculture extension officers, farm researchers, and data analysts.
* **Core Functions:**
  1. **Audited Dataset Selector:** Safe, cached access to `water_quality`, `toxicity_analysis`, `fish_health_growth`, `feeding_analysis`, `enrolled_ponds`, and `dropouts` via `app.core.data_manager`.
  2. **Longitudinal Pond Trajectory Viewer:** Interactive time series plots for individual commercial ponds across monitoring visits (DO trajectory, pH, temperature, cohort weight increments).
  3. **Inspection Context:** Emphasizes multi-week routine visits (3–45 days) and morning DO observations (06:00–08:30 AM).
  4. **Missingness & Data Integrity Visualizer:** Shows empirical missingness distributions (preserving NaNs; no silent zero-filling).
  5. **Strict Isolation from Simulation:** Explicitly notes that this explorer displays historical commercial field observations only.

---

#### Page 6: Simulated Scenarios Sandbox (Non-Operational) (`06_Simulation_Sandbox.py`)
* **Category:** Simulated Scenarios
* **Target Audience:** Researchers, students, and farm planners testing hypothetical scenarios.
* **Core Functions:**
  1. **Isolated Testing Environment:** Completely separated from commercial farm inspection workflows.
  2. **Synthetic Data Explorer:** Dedicated viewer for `iot_water_model_v2.csv` (hourly mathematical simulation model from `Data_Model_IoTMLCQ_2024.xlsx`).
  3. **What-If Scenario Simulator:** Allows users to inject extreme synthetic water conditions (e.g. zero DO, extreme ammonia spikes, thermal extremes) to observe model advisory responses.
  4. **Unambiguous Simulation Watermarking:**
     - High-visibility amber/orange banner across the entire page:
       > ⚠️ **SIMULATED SCENARIO ONLY (DEMONSTRATION):** All outputs generated on this page originate from synthetic or simulated data. Operational use is strictly prohibited (`operational_use_permitted = False`).

---

#### Page 7: Model Registry Governance & Audit Benchmark Catalog (`07_Model_Registry_Governance.py`)
* **Category:** Audited Model Benchmarks, Scientific Disclaimers & Governance Controls
* **Target Audience:** Scientific auditors, academic evaluators, and system administrators.
* **Core Functions:**
  1. **Complete Audited Benchmark Tables:** Full reference tables for Experiments 1, 2, 3, 4, and 5 from chronological holdout audits.
  2. **Chemical Formulations Reference:** Emerson dissociation formulas, pKa calculations, and molecular weight conversion rules.
  3. **Model Artifact Integrity Dashboard:** Live cryptographic SHA-256 verification status for all 10 datasets and 9 pre-trained model pipelines.
  4. **Operational Guardrail Summary:** Checklist verifying no automated actuators, no real-time IoT hardware claims, and no harvest yield claims.

---

## 3. Application Boundary Validations vs. Biological Safety Thresholds

### 3.1 Critical Governance Distinction
The numerical ranges defined below are **defensive software boundary constraints** intended solely to catch data-entry errors, unphysical sensor telemetry (e.g. negative concentrations or impossible pH), or numeric overflows. They are **NEVER to be interpreted or presented as validated biological safety thresholds or physiological tolerance limits**. Biological safety depends on species, life stage, temperature, and exposure duration.

```
+==================================================================================================================================+
|                                    APPLICATION BOUNDARY VALIDATION MATRIX (SOFTWARE DEFENSIVE BOUNDS)                            |
+--------------------------+-----------------------+---------------------+-------------------+-------------------------------------+
| Field Name               | Input Widget Type     | Supported Range     | Default Value     | Validation & Defensive Action       |
+--------------------------+-----------------------+---------------------+-------------------+-------------------------------------+
| Data Source Mode         | Radio Toggle          | [Field, Simulated]  | Field Inspection  | Toggles operational gating flags    |
| Dissolved Oxygen (DO)    | Number Input (mg/L)   | 0.00 to 25.00 mg/L  | 4.50 mg/L         | Software bound: rejects < 0 or > 25 |
| Water pH                 | Number Input (pH)     | 0.00 to 14.00 pH    | 7.80 pH           | Software bound: rejects < 0 or > 14 |
| Water Temperature        | Number Input (°C)     | 10.0 to 45.0 °C     | 28.0 °C           | Software bound: rejects <= -273.15  |
| Total Ammonia (TAN)      | Number Input (mg/L)   | 0.00 to 20.00 mg/L  | Optional (0.50)   | Software bound: rejects < 0.0       |
| Water Turbidity          | Number Input (cm)     | 0.0 to 150.0 cm     | Optional (NaN)    | Defensive handling (preserves NaN)  |
| Total Dissolved Solids   | Number Input (ppt)    | 0.0 to 50.0 ppt     | Optional (NaN)    | Defensive handling (preserves NaN)  |
| Current Fish Weight      | Number Input (g/fish) | > 0.0 to 5000.0 g   | 350.0 g           | Strictly enforces W > 0.0 g         |
| Current Daily Feed       | Number Input (kg/day) | >= 0.0 to 2000.0 kg | Optional (100.0)  | Software bound: rejects < 0.0 kg    |
| Pond Surface Area        | Number Input (acres)  | 0.10 to 50.0 acres  | Optional (2.5)    | Software bound: rejects <= 0.0      |
| Stocking Density         | Number Input (#/acre) | 100 to 100,000      | Optional (4,000)  | Software bound: rejects <= 0        |
| Revisit Horizon          | Slider / Number (days)| 3 to 45 days        | 21 days           | Warns if outside 3–45 day window    |
| Pond Identifier          | Selectbox / Text      | Alphanumeric string | "Pond_01"         | Required for feedback logging       |
+--------------------------+-----------------------+---------------------+-------------------+-------------------------------------+
```

---

## 4. Model Integration Architecture

The dashboard communicates exclusively with models via the central singleton:
`from app.models.registry import get_model_registry`

```
UI Component (Streamlit Page)
       │
       ▼
get_model_registry()
       │
       ├── predict_ammonia_soft_sensor(features)   --> AmmoniaSoftSensorModel (Exp 1 RF Screening)
       ├── predict_mortality_diagnostic(features)  --> FishMortalityDiagnosticModel (Exp 2 LR Diagnostic)
       ├── predict_next_visit_ammonia_risk(feats)  --> NextVisitAmmoniaRiskModel (Exp 3 RF Screening)
       ├── predict_fish_growth(features)           --> FishGrowthModel (Exp 4 Cohort Persistence Baseline)
       ├── predict_do_hypoxia(features)            --> DOHypoxiaModel (Exp 5 Hist Mean & GBDT Screening)
       ├── get_feeding_advisory(inputs)            --> FeedingAdvisorModel (Provisional Heuristic Engine)
       ├── record_feeding_feedback(...)            --> FeedingFeedbackTracker (Observational Logger)
       └── health_check()                          --> Dynamic Registry Status Dictionary
```

### Integration Guardrails
1. **Zero Direct File Deserialization:** The UI never calls `joblib.load()` or accesses `.joblib` files directly.
2. **Defensive Failure Handling:** If a model encounters an issue, `ModelRegistry` captures the exception. The UI displays an informative status alert (`⚠️ Model Unavailable`) while allowing all remaining models on the page to function seamlessly.
3. **Structured Payload Unpacking:** The UI unpacks standardized dictionary responses, binding status flags directly to UI badge colors (e.g., `status = "ADVISORY_GENERATED"` $\rightarrow$ Green badge, `status = "SIMULATED_SCENARIO_ONLY"` $\rightarrow$ Orange badge, `status = "INVALID_PHYSICAL_MEASUREMENT"` $\rightarrow$ Red alert).

---

## 5. Separation of Historical and Simulated Data

To prevent confusion between historical commercial pond data and synthetic simulations:

```
+---------------------------------------------------------------------------------------------------+
|                         DATASET & SCENARIO SEPARATION SPECIFICATION                               |
+--------------------------+------------------------------------+-----------------------------------+
| Attribute                | Historical Field Observations      | Synthetic Simulation Model        |
+--------------------------+------------------------------------+-----------------------------------+
| Source Dataset           | water_quality_cleaned_v2.csv       | iot_water_model_v2.csv            |
| Nature of Observations   | Real commercial fish ponds (AP)    | Mathematical simulation benchmark |
| Temporal Frequency       | Irregular visits (3 to 45 days)    | Continuous hourly artificial time |
| Missingness Profile      | Natural missing values (NaN)       | Artificially complete time series |
| Dashboard Page Role      | Pages 1, 2, 3, 4, 5                | Page 6 (Dedicated Sandbox Only)   |
| Operational Status       | ADVISORY_GENERATED (Provisional)   | SIMULATED_SCENARIO_ONLY           |
| Gating Boolean           | operational_use_permitted = True   | operational_use_permitted = False |
| Visual Styling           | Standard clean professional theme  | High-contrast amber/yellow banner |
+--------------------------+------------------------------------+-----------------------------------+
```

### Machine-Readable Enforcement
Whenever `is_simulated = True` or `data_source` contains `"simulat"` / `"synthetic"`:
- The UI renders a prominent warning header:
  > ⚠️ **DEMONSTRATION ONLY:** This calculation was performed using simulated benchmark data. It must NEVER be used to guide live fish feeding, pond aeration, or farm operations.
- The advisory action is visually prefixed with `SIMULATED_` (e.g., `SIMULATED_NORMAL_FEEDING`).
- The operational use badge is displayed as `OPERATIONAL USE: PROHIBITED (FALSE)`.

---

## 6. Defensive Error Handling & Fault Isolation Strategy

The dashboard implements comprehensive defensive patterns to guarantee 100% crash resilience:

1. **Input Pre-Validation:**
   - Every input widget enforces boundary minimums and maximums directly in Streamlit (`min_value`, `max_value`).
   - Manual text overrides are caught via `try...except ValueError` and surfaced as inline warnings (`st.warning()`), preventing unhandled Python tracebacks.
2. **Model Fault Isolation:**
   - Model calls are wrapped in defensive helper functions:
     ```python
     def safe_predict(predict_fn, payload):
         try:
             return predict_fn(payload)
         except Exception as exc:
             return {
                 "is_valid": False,
                 "status": "INFERENCE_ERROR",
                 "explanation": f"Model inference temporarily unavailable: {exc}",
                 "operational_use_permitted": False
             }
     ```
   - If an individual model encounters an issue, only its individual card displays an error state; the rest of the page remains fully operational.
3. **Session State Initialization:**
   - Streamlit session state keys (`feedback_history`, `selected_pond`, `current_inputs`) will be initialized with safe defaults on first load to prevent `KeyError` during rapid navigation.
4. **Graceful Dataset Loading:**
   - Dataset calls use `app.core.data_manager.load_dataset(..., use_cache=True)`. If a dataset fails schema verification, a clear notification is displayed without crashing the Streamlit server.

---

## 7. Testing Strategy for Phase 5

To ensure seamless integration without breaking existing functionality, Phase 5 will be verified through a 4-tier testing hierarchy:

```
TIER 1: Existing Regression Test Suites (79 tests across 6 modules)
        - Must pass 100% with zero regressions.
        - Preserves test_chemistry, test_data_manager, test_models, test_fish_growth,
          test_feeding_advisor, test_do_hypoxia.

TIER 2: Cryptographic Immutability Audit
        - Verifies that all 10 datasets in processed_data_v2/ remain 100% bit-for-bit unchanged.
        - Verifies that all 9 pre-trained .joblib model artifacts remain 100% bit-for-bit unchanged.

TIER 3: Dashboard Unit & Helper Function Tests (app/tests/test_dashboard_helpers.py)
        - Tests input formatting, alias resolution, status badge mapping, and error handling.
        - Tests simulation detection and operational gating flags.
        - Tests boundary validation helpers without requiring a live browser.

TIER 4: Streamlit Integration & Smoke Verification
        - Headless execution verification of main dashboard app and subpages (including 03_Next_Visit_DO_Hypoxia.py).
        - Validates that all 6 models can be invoked through the dashboard pipeline.
        - Validates that simulated inputs never produce operational_use_permitted = True.
```

---

## 8. Compliance Checklist with Project Restrictions

- [x] **Zero Model Retraining:** Models are loaded read-only from pre-existing `.joblib` artifacts or analytical baselines.
- [x] **Zero Dataset Modifications:** `processed_data_v2/` CSV and JSON files remain strictly read-only.
- [x] **DO Page Renamed & Categorized:** `03_Next_Visit_DO_Hypoxia.py` titled "Next-Visit Morning DO and Hypoxia Screening", communicating historical mean DO = 3.4984 mg/L as a constant historical benchmark, next-visit morning observations (06:00–08:30 AM), revisit interval 3–45 days, not verified pre-dawn daily minimum DO, no overnight/hourly/real-time claims, and GB moderate hypoxia kept exploratory only.
- [x] **Target Definition Corrected:** Experiment 4 target strictly defined as "Next-visit pond-cohort average fish weight" (grams/fish), explicitly disclaiming individual fish growth, harvest biomass, and harvest yield in kg/ha, with the 93.38 g MAE contextualized as an all-pairs chronological persistence baseline.
- [x] **Scientific Terminology Corrected:** "Morning nadir" replaced everywhere with "Morning DO observation (06:00–08:30 AM)". Input validation boundaries explicitly distinguished from biological safety thresholds.
- [x] **Provisional Feeding Heuristics Labelled:** Feeding rules labelled as provisional decision-support heuristics requiring human verification, with TAN 2.0 mg/L identified strictly as a test-kit graduation.
- [x] **Page Titles Reviewed & Categorized:** Five clear operational categories used across all views (Historical field observations, Model benchmarks, Experimental screening results, Simulated scenarios, Provisional advisories).
- [x] **No Automated Control:** Strictly decision-support advisory for human operators (`is_automatic_control = False`).
- [x] **Phases 1–4 Preservation:** Existing chemistry, data manager, model wrappers, and 79 unit tests remain 100% untouched.
- [x] **Phase 6 Not Started:** Execution halted immediately upon delivery of this updated design plan.

---

## 9. Conclusion & Next Steps

This revised design plan establishes an uncompromisingly rigorous, scientifically precise blueprint for the Phase 5 dashboard. It eliminates all exaggerated claims, establishes transparent operational categorization across all pages, and grounds all metrics in audited empirical reality.

**Deliverable Status: REVISED & COMPLETE.**  
**Action:** Awaiting user approval of `PHASE_5_DASHBOARD_DESIGN_PLAN.md` before proceeding with Phase 5 implementation.
