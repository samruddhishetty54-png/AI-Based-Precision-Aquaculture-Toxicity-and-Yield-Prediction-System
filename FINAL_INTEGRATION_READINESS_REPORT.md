# Final Integration Readiness Report: AI-Based Precision Aquaculture Toxicity and Yield Prediction System

**Document ID:** `FIRR-AQUASYSTEM-2026-FINAL-V2`  
**Date:** 2026-11-05  
**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System (BAI507P Mini Project)  
**Academic Affiliation:** Department of Computer Science & Engineering (AIML), Sahyadri College of Engineering & Management  
**Status:** Pre-Integration Inspection & Architectural Baseline Audit (Inspection Only — No Code Modified)  
**Author:** AI Technical Lead & Scientific Verification System  

---

## Executive Summary

This report establishes the definitive technical and architectural baseline for the **AI-Based Precision Aquaculture Toxicity and Yield Prediction System** prior to application integration. 

In strict adherence to project instructions:
- **No application code, existing scripts, or datasets have been modified, deleted, or overwritten.**
- **No models have been retrained.**
- **No integration has been executed.**

### Key Inspection Findings:
1. **Application Codebase Status (Greenfield State):** There is currently **zero pre-existing application code**. There is no frontend framework (no Streamlit or React UI), no backend server (no FastAPI or Flask REST API), no database (no SQLite or PostgreSQL schema), and no real-time telemetry streaming simulator.
2. **Machine Learning & Research State:** Experiments 1 through 5, comprehensive data cleaning pipelines (`clean_datasets_v2.py`), and multi-stage robustness/statistical audits are 100% complete. Pre-trained model artifacts (`.joblib`), evaluation metric tables (`.csv`), and verified chemical formulations exist as standalone research deliverables.
3. **Scientific Alignment:** The research findings decisively separate operational baselines from exploratory models:
   - **Experiment 1 (Ammonia Soft-Sensor):** Retained as an experimental baseline only; not an independent safety alarm due to chronological underprediction of dangerous ammonia spikes.
   - **Experiment 2 (Mortality Classification):** Evaluated under extreme class imbalance (0.76% prevalence); quarantined from operational warning systems.
   - **Experiment 3 (Next-Visit Ammonia Risk):** Chronological performance remains near no-skill; kept strictly experimental.
   - **Experiment 4 (Fish Weight):** Persistence ($\hat{W}_{t+1} = W_t$) decisively outperforms ML models on the full operational dataset. It predicts individual somatic weight over multi-week intervals, **never harvest yield**.
   - **Experiment 5 (Morning DO & Hypoxia):** Historical Mean ($\bar{\text{DO}} = 3.48$ mg/L) is the operational point-prediction baseline. GBDT moderate hypoxia classification ($p^* = 0.090$) is an exploratory risk-ranker only. Severe hypoxia Random Forest is **formally rejected**.

---

## 1. Existing Application Architecture

An exhaustive recursive file inspection of the workspace (`d:\AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System`) reveals the current architectural state:

```
d:\AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System\
│
├── dataset/                            # Raw data files (READ-ONLY)
│   ├── Data_Model_IoTMLCQ_2024.xlsx    # Hourly IoT water-quality simulation model
│   ├── water_quality.csv               # Field water quality logs across 313 ponds
│   ├── enrolled_ponds.csv              # Pond farm metadata and pond dimensions
│   ├── dropouts.csv                    # Incomplete/dropped pond records
│   └── water_quality_nellore_retracted.csv
│
├── processed_data_v2/                  # Cleaned datasets and audit configurations (READ-ONLY)
│   ├── water_quality_cleaned_v2.csv    # Standardized field water quality observations
│   ├── iot_water_model_v2.csv          # Standardized hourly IoT reference series
│   ├── toxicity_analysis_v2.csv        # Primary ammonia & toxicity analytical dataset
│   ├── fish_health_growth_analysis_v2.csv
│   ├── feeding_analysis_v2.csv
│   ├── enrolled_ponds_v2.csv
│   ├── thresholds_config.json          # Provisional water quality heuristic thresholds
│   └── preprocessing_v2_report.md      # Data cleaning audit report
│
├── baseline_toxicity_v1/               # Experiment 1 deliverables
│   └── models/experiment_1_rf_pipeline.joblib
│
├── experiment_2_mortality_v1/          # Experiment 2 deliverables
│   └── models/logistic_regression_pipeline.joblib, random_forest_pipeline.joblib
│
├── experiment_3_next_visit_risk_v1/    # Experiment 3 deliverables
│   └── models/logistic_regression_pipeline.joblib, random_forest_pipeline.joblib
│
├── experiment_4_next_visit_weight_v1/  # Experiment 4 deliverables (Persistence vs GBDT)
│   └── temporal_growth_dataset.csv, baseline_comparison.csv, chronological_metrics.csv
│
├── experiment_5_do_hypoxia_v1/         # Experiment 5 deliverables
│   ├── data/temporal_do_dataset.csv, train_pairs.csv, test_pairs.csv
│   ├── metrics/phase2_regression_metrics.csv, phase2_classification_metrics.csv
│   └── final_model_selection_audit/EXPERIMENT_5_FINAL_MODEL_SELECTION_AUDIT.md
│
├── clean_datasets.py                   # Legacy data cleaning script (v1)
├── clean_datasets_v2.py                # Audited production cleaning script (v2)
├── train_experiment_1.py ... 4.py      # Standalone model training scripts
├── prepare_experiment_5_phase1.py      # Experiment 5 dataset & baseline builder
├── save_phase2_metrics.py              # Experiment 5 training & threshold evaluation
└── MINI-PROJECT-SYNOPSIS Formatfinal.pdf # Academic project specifications
```

### Architectural Component Breakdown

1. **Frontend Framework & Structure:**
   - **Current State:** Completely absent (0 files). No `src/`, `public/`, `app.py`, `streamlit_app.py`, `package.json`, or UI styling configurations.
   - **Environment State:** `streamlit` is currently **not installed** in the active Python environment.
2. **Backend Framework & API Endpoints:**
   - **Current State:** Completely absent (0 files). No web server, routing framework (`fastapi`, `flask`, `uvicorn` are not installed), API endpoints, or request handlers.
3. **Dashboard Pages & Components:**
   - **Current State:** Non-existent. No navigation panels, alert cards, telemetry widgets, feeding calculators, or XAI breakdown components.
4. **Current Water-Quality Monitoring System:**
   - **Current State:** Offline batch analysis only. No real-time listener, no continuous polling, and no polling daemon. Data is loaded from static CSV files via `pandas.read_csv()`.
5. **Existing Simulation Functionality:**
   - **Current State:** Non-existent in code. The repository contains an hourly benchmark spreadsheet (`dataset/Data_Model_IoTMLCQ_2024.xlsx` cleaned to `processed_data_v2/iot_water_model_v2.csv`), but there is no software simulator generating synthetic streaming ticks or modeling dynamic diurnal physics.
6. **Ammonia and Toxicity Calculations:**
   - **Current State:** Implemented as offline functions in `clean_datasets_v2.py` (`calculate_nh3_from_tan_n` and `calculate_nh3_from_tan_nh3`), based on the Emerson et al. (1975) chemical dissociation equilibrium. Not exposed via an interactive interface.
7. **Fish Growth and Weight Prediction Logic:**
   - **Current State:** Standalone research script `train_experiment_4.py`. Evaluates next-visit average fish weight ($W_{t+1}$ in grams). The persistence baseline is the winning operational model.
8. **Feeding Recommendation System:**
   - **Current State:** Completely absent. The historical dataset contains recorded feed amounts (`Feed amount (kg)`), but there is zero dynamic bioenergetic recommendation logic or feed-adjustment algorithm in code.
9. **Charts, Graphs, Alerts, and Historical Records:**
   - **Current State:** Visualizations exist solely as static `.png` files saved in experiment subdirectories. No interactive charts (Plotly/Altair) or live alert state managers exist.
10. **Database and Data Storage:**
    - **Current State:** File-based CSV storage only. No relational database (SQLite/PostgreSQL) exists.
11. **Telemetry Ingestion:**
    - **Current State:** No ingestion pipeline. All data is read in static batch mode from disk.
12. **Existing ML Models and Prediction Services:**
    - **Current State:** Serialized scikit-learn pipelines (`.joblib`) stored in experiment subfolders. No runtime service or prediction API exists.
13. **Existing Error Handling and Validation:**
    - **Current State:** Standalone `try...except` blocks in data cleaning scripts for numeric conversions; no unified schema validation layer (e.g. Pydantic) exists.

---

## 2. Existing Working Features

The workspace contains high-quality, verified scientific pipelines and analytical modules that can be directly leveraged during integration:

1. **Standardized Data Cleaning & Preprocessing Engine (`clean_datasets_v2.py`):**
   - Robust Excel and CSV parsing using standard libraries (`parse_xlsx_stdlib`).
   - Clean handling of encoding issues, degree symbols, and column headers across disparate field records.
   - Rigorous missingness tracking (avoiding zero-imputation; preserving `np.nan` and adding missing indicators).
2. **Aqueous Ammonia Chemical Equilibrium Engine (`clean_datasets_v2.py`):**
   - Emerson dissociation constant calculation:
     $$pK_a = 0.09018 + \frac{2729.92}{T_K}$$
   - Un-ionized fraction calculation:
     $$f = \frac{1}{10^{(pK_a - \text{pH})} + 1}$$
   - Molecular weight conversion:
     $$\text{NH}_{3\text{ (molecular)}} = f \times \text{TAN}_{\text{N}} \times \left(\frac{17.031}{14.007}\right)$$
   - Dual-path routing for TAN reported as nitrogen vs. TAN reported as molecular ammonia.
3. **Pre-Trained Machine Learning Pipelines (Joblib Artifacts):**
   - `baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib`: Random Forest Soft-Sensor ($R^2 = 0.814$).
   - `experiment_2_mortality_v1/models/logistic_regression_pipeline.joblib`: Balanced Logistic Regression mortality classifier.
   - `experiment_3_next_visit_risk_v1/models/random_forest_pipeline.joblib`: Multi-week ammonia toxicity risk classifier.
4. **Longitudinal Dataset Builders:**
   - Experiment 4 consecutive same-pond pair generator ($N = 1,476$ pairs across 197 ponds; $3 \le \Delta t \le 45$ days).
   - Experiment 5 consecutive morning DO pair generator ($N = 5,178$ pairs across 304 ponds; chronological split preserving temporal boundary).
5. **Configurable Threshold Management (`processed_data_v2/thresholds_config.json`):**
   - Centralized heuristic threshold configuration explicitly stamped with provisional status metadata.

---

## 3. Completed Experiment Components Review

```
+=========================================================================================================================+
|                                    EXPERIMENTS 1-5 SCIENTIFIC VERIFICATION MATRIX                                      |
+------------+-------------------------+--------------------+---------------------+------------------+--------------------+
| Experiment | Objective               | Operational Status | Winning Model       | Primary Metric   | Practical Role     |
+------------+-------------------------+--------------------+---------------------+------------------+--------------------+
| Exp 1      | Concurrent Ammonia      | EXPERIMENTAL       | Random Forest       | R² = 0.814       | Soft-Sensor        |
|            | Soft-Sensor (TAN)       | (Baseline Only)    | Regressor           | MAE = 0.28 mg/L  | Virtual probe only |
+------------+-------------------------+--------------------+---------------------+------------------+--------------------+
| Exp 2      | Acute Fish Mortality    | QUARANTINED        | Logistic Regression | ROC-AUC = 0.771  | Advisory severity  |
|            | Classification          | (Advisory Only)    | (Class-Weighted)    | PR-AUC = 0.082   | flag; not a warning|
+------------+-------------------------+--------------------+---------------------+------------------+--------------------+
| Exp 3      | Next-Visit Ammonia      | EXPERIMENTAL       | Gradient Boosting   | PR-AUC = 0.346   | Multi-week trend   |
|            | Toxicity Risk (3-45 d)  | (Exploratory Risk) | Classifier          | (Near no-skill)  | indicator only     |
+------------+-------------------------+--------------------+---------------------+------------------+--------------------+
| Exp 4      | Next-Visit Somatic Fish | BASELINE RETAINED  | Persistence         | MAE = 93.38 g    | Operational        |
|            | Weight Prediction       | (Operational)      | (W_{t+1} = W_t)     | (Beats ML by 30g)| baseline tracker   |
|            |                         | EXPLORATORY (Clean)| Gradient Boosting   | Clean MAE=57.22g | Unharvested growth |
+------------+-------------------------+--------------------+---------------------+------------------+--------------------+
| Exp 5      | Next-Visit Morning DO   | BASELINE RETAINED  | Historical Mean     | MAE = 0.396 mg/L | Operational point  |
|            | Regression              | (Operational)      | (DO = 3.48 mg/L)    | (Beats ML by 0.02| estimate baseline  |
|            |                         | EXPLORATORY (ML)   | Random Forest       | MAE = 0.417 mg/L | ML reference model |
+------------+-------------------------+--------------------+---------------------+------------------+--------------------+
| Exp 5      | Next-Visit Hypoxia      | EXPLORATORY ONLY   | Gradient Boosting   | Recall = 53.5%   | Advisory risk      |
| (Classif.) | Risk (< 3.0 mg/L)       | (Risk Ranker)      | (Threshold p*=0.09) | FDR = 91.0%      | score (NO alarms)  |
+------------+-------------------------+--------------------+---------------------+------------------+--------------------+
| Exp 5      | Severe Hypoxia Risk     | REJECTED           | Random Forest       | FDR = 95.5%      | QUARANTINED        |
| (Severe)   | (< 2.0 mg/L)            | (Degenerate)       | (Over-predicted)    | 99.5% alarm rate | Do NOT deploy      |
+------------+-------------------------+--------------------+---------------------+------------------+--------------------+
```

### Critical Experiment Summaries

- **Experiment 1 (Ammonia Soft-Sensor):**
  - Estimates Total Ammonia Nitrogen (TAN) and un-ionized $\text{NH}_3$ from concurrent pH, water temperature, and dissolved oxygen.
  - *Evaluation:* While cross-validation $R^2$ reached $0.814$, chronological evaluation dropped to $0.329$ and showed severe underprediction of dangerous high-ammonia peaks ($> 2.0$ mg/L).
  - *Integration Decision:* Retain strictly as an **experimental baseline soft-sensor**. It must **not** be integrated as an independent safety alarm.
- **Experiment 2 (Fish Mortality Classification):**
  - Targets acute mortality events (`dead_fish_count > 0`), which exhibit extreme natural class imbalance ($0.76\%$ prevalence).
  - *Evaluation:* Balanced Logistic Regression achieved ROC-AUC = $0.771$, but PR-AUC = $0.082$ due to high false alarm rates.
  - *Integration Decision:* **Do not integrate as an operational mortality warning system.** Quarantined from triggering automated alarms.
- **Experiment 3 (Next-Visit Ammonia Toxicity Risk):**
  - Evaluates multi-week transition risk ($3 \le \Delta t \le 45$ days).
  - *Evaluation:* GroupKFold PR-AUC was $0.444$, but chronological test set PR-AUC dropped to $0.346$, close to the no-skill baseline ($0.158$).
  - *Integration Decision:* **Keep strictly experimental.** Prohibit automated operational alarms.
- **Experiment 4 (Next-Visit Average Fish Weight):**
  - Evaluates next-visit average fish weight ($W_{t+1}$ in grams).
  - *Evaluation:* Across the full uncurated chronological test set, the **Persistence baseline ($\hat{W}_{t+1} = W_t$, MAE = 93.38 g) decisively outperformed ML models (GBDT MAE = 123.70 g)** because commercial ponds undergo unrecorded partial harvests. On the retrospective clean subset, GBDT achieved MAE = $57.22$ g.
  - *Integration Decision:* **Retain Persistence as the primary operational baseline.** Retain GBDT as an exploratory model for unharvested growth periods. **Must never be branded as "Harvest Yield Prediction"** (yield in kg/ha is 0% populated).
- **Experiment 5 (Next-Visit Morning DO & Hypoxia Risk):**
  - Evaluates next-visit morning DO nadir and hypoxia events over multi-week revisit intervals.
  - *Evaluation:* 
    - Historical Mean baseline ($\bar{\text{DO}} = 3.48$ mg/L, MAE = $0.3963$ mg/L) outperformed Random Forest (MAE = $0.4172$ mg/L) and GBDT (MAE = $0.4260$ mg/L) on the low-variance chronological test set.
    - Moderate Hypoxia Classifier ($< 3.0$ mg/L) at frozen threshold $p^* = 0.090$ detected $53.49\%$ of events, but incurred a $50.25\%$ alarm rate with a $91.0\%$ False Discovery Rate.
    - Severe Hypoxia Classifier ($< 2.0$ mg/L) suffered probability collapse, triggering alarms on $99.56\%$ of test visits.
  - *Integration Decision:*
    - **Historical Mean DO:** Retain as the operational point-prediction baseline.
    - **RF & GBDT Regression:** Retain as exploratory reference models only.
    - **GBDT Moderate Hypoxia Classifier:** Retain as an exploratory advisory risk ranker only.
    - **Severe Hypoxia RF Classifier:** **Formally rejected and quarantined.**
    - **Persistence on DO:** **Formally rejected** ($R^2 = -0.7071$).

---

## 4. Missing Integration Components & Technical Gap Analysis

To connect research experiments into a unified decision-support application, several critical gaps must be bridged:

### 1. Disconnected Experiment Components
- **Current State:** None of the 5 experiments are connected to a unified interface. Each model exists as a disconnected `.joblib` file or procedural script.
- **Required Action:** Build a central `ModelRegistry` in `app/models/registry.py` that loads pre-trained pipelines, validates incoming feature vectors, and manages baseline fallbacks.

### 2. Duplicate Ammonia & Toxicity Logic
- **Current State:** A critical discrepancy exists between legacy `clean_datasets.py` (v1) and `clean_datasets_v2.py` (v2):
  - In v1, `calculate_un_ionized_ammonia` omits the $(17.031 / 14.007)$ molecular weight conversion factor when TAN is measured as nitrogen ($\text{NH}_3\text{-N}$), causing a **~21.6% systematic underestimation** of toxic un-ionized ammonia.
  - In v2, `calculate_nh3_from_tan_n` correctly applies the molecular weight ratio.
- **Required Action:** The application must strictly standardize on the verified **v2 Emerson formulation** from `clean_datasets_v2.py`. Legacy v1 calculation logic must be quarantined.

### 3. Static Feeding Data vs. Dynamic Recommendation Engine
- **Current State:** The dataset contains historical records of `daily_feed_kg`, but there is **no recommendation logic** implemented in code.
- **Required Action:** Implement a dynamic bioenergetic feeding model (`app/core/bioenergetics.py`):
  $$\text{Base Feed (kg/day)} = \text{Pond Biomass (kg)} \times \text{Feeding Rate (\%)} \times C_{\text{Temp}}$$
  Equipped with mandatory safety overrides:
  - If $\text{DO} < 3.0$ mg/L: Suppress feed by $50\%$.
  - If $\text{DO} < 2.0$ mg/L: Suppress feed by $100\%$ (feeding cessation).
  - If Un-ionized $\text{NH}_3 > 0.05$ mg/L: Suppress feed by $50\%$.
  - If Un-ionized $\text{NH}_3 > 0.10$ mg/L: Suppress feed by $100\%$.

### 4. Data Structure Divergence: Simulation vs. Field Monitoring
- **Current State:** The hourly simulation dataset (`iot_water_model_v2.csv`) uses columns like `Dissolved Oxygen (mg/L)`, `Temperature (°C)`, `pH`, whereas the field dataset (`water_quality_cleaned_v2.csv`) uses `DO (mg/L)`, `Temp (in °C)`, `pH`, `Ammonia–TAN (NH3-N) (mg/L)`.
- **Required Action:** Establish a standardized internal data schema (`TelemetryRecord`) in `app/config.py` that normalizes column names across both simulation streams and historical pond logs.

### 5. Prediction Display & Baseline Coexistence
- **Current State:** Standard dashboards often present machine learning outputs as authoritative single numbers.
- **Required Action:** The UI must display predictions in side-by-side comparative cards:
  - **Operational Baseline:** Historical Mean (Exp 5) or Persistence (Exp 4).
  - **Exploratory ML Indicator:** RF / GBDT prediction clearly stamped with an "Exploratory / Unvalidated" tag.

### 6. Pipeline & Model Availability
- **Current State:** Serialized `.joblib` files are already present for Experiments 1, 2, and 3. For Experiments 4 and 5, model weights and pipeline configurations exist in `train_experiment_4.py` and `save_phase2_metrics.py`.
- **Required Action:** Serialize the final audited GBDT pipelines for Exp 4 and Exp 5 into `app/models/` during Phase 1.

### 7. API and Database Requirements
- **Current State:** No API or database exists.
- **Required Action:** Implement a lightweight, direct Python service layer for Streamlit. If external microservice access is desired in the future, the core functions can be wrapped with FastAPI without re-architecting. An in-memory circular buffer (`collections.deque`) will serve as the real-time telemetry buffer.

### 8. Features That Might Break During Integration
- **Risk:** Incompatible scikit-learn pipeline versions or missing feature column errors during inference.
- **Mitigation:** Wrap all model inference in an explicit validation layer that fills missing optional features with domain medians and adds missing indicator columns matching the training schema.

---

## 5. Duplicate Logic and Conflicts

The following discrepancies were identified and resolved:

| Component | File A (Legacy / Conflicting) | File B (Audited / Target) | Conflict Description | Resolution for Final Integration |
|---|---|---|---|---|
| **Ammonia Formula** | `clean_datasets.py` (`calculate_un_ionized_ammonia`) | `clean_datasets_v2.py` (`calculate_nh3_from_tan_n`) | File A misses $(17.031/14.007)$ MW ratio; underestimates toxic $\text{NH}_3$ by 21.6%. | **Enforce File B exclusively** in `app/core/chemistry.py`. |
| **Heuristic Thresholds** | Hardcoded strings in `clean_datasets.py` | `processed_data_v2/thresholds_config.json` | File A hardcodes rules; File B provides centralized JSON with provisional metadata. | **Bind directly to `thresholds_config.json`**. |
| **Temporal Granularity** | `iot_water_model_v2.csv` (Hourly continuous) | `water_quality_cleaned_v2.csv` (Multi-week sparse) | Hourly data represents continuous sensor physics; field data represents irregular farmer visits. | **Strictly decouple**: Use hourly physics for simulator; use sparse visits for historical trend explorer. |
| **Growth Target** | Synopsis: "Yield Prediction" | Exp 4: "Next-Visit Average Fish Weight (g)" | Synopsis implies total commercial harvest yield; dataset only contains individual fish weight. | **Enforce strict labeling: "Individual Fish Weight"**; explicitly disclaim harvest yield. |

---

## 6. Scientific Limitations and Mandatory Restrictions

The following twelve scientific restrictions are non-negotiable and must be enforced across all dashboard views, tooltips, and system documentation:

```
+==================================================================================================+
|                                  MANDATORY SCIENTIFIC GUARDRAILS                                 |
+==================================================================================================+
| 1. SIMULATION VS. LIVE HARDWARE:                                                                 |
|    - System MUST clearly label all streaming data as "Software Simulation Mode".                 |
|    - Never imply physical IoT probes are connected when running the synthetic generator.         |
|                                                                                                  |
| 2. LABELING INTEGRITY:                                                                           |
|    - Clearly distinguish simulated sensor telemetry from historical field inspection logs.       |
|                                                                                                  |
| 3. NO CLAIMS OF REAL-TIME PHYSICAL MONITORING:                                                   |
|    - Frame all real-time views as software demonstrations of edge decision-support algorithms.   |
|                                                                                                  |
| 4. NO CLAIMS OF OVERNIGHT DO FORECASTING:                                                        |
|    - Experiment 5 predicts next-visit morning DO over a multi-week revisit interval (3-45 days). |
|    - NEVER market it as an "overnight", "minute-by-minute", or "real-time" DO forecast.          |
|                                                                                                  |
| 5. MULTI-WEEK TEMPORAL HORIZON DISCLOSURE:                                                       |
|    - Explicitly state the 3–45 day revisit interval on all prediction cards and charts.         |
|                                                                                                  |
| 6. SOMATIC WEIGHT VS. HARVEST YIELD:                                                             |
|    - The target is individual fish somatic weight (grams/fish).                                  |
|    - Total harvest biomass and yield per hectare are UNKNOWN (0% populated in dataset).          |
|    - Terminology MUST state "Average Individual Fish Weight", NEVER "Pond Harvest Yield".        |
|                                                                                                  |
| 7. FEATURE IMPORTANCE IS NOT CAUSATION:                                                          |
|    - XAI explanations (SHAP / feature importance) show statistical association, not cause.       |
|                                                                                                  |
| 8. EXPERIMENTAL MODELS ARE NOT OPERATIONAL PREDICTORS:                                           |
|    - Exp 1, 2, 3, and Exp 5 ML models must be stamped "Exploratory / Research Only".            |
|                                                                                                  |
| 9. PRESERVE VERIFIED AMMONIA FORMULAS:                                                           |
|    - Use the audited Emerson et al. (1975) equilibrium with molecular weight conversion.         |
|                                                                                                  |
| 10. PRESERVE SOURCE DATASETS & AUDIT ARTIFACTS:                                                  |
|     - All source datasets, experiment files, and reports remain 100% read-only.                  |
|                                                                                                  |
| 11. NO ZERO-IMPUTATION FOR MISSING SENSORS:                                                      |
|     - Never replace missing water quality measurements with zero. Use domain medians + flags.    |
|                                                                                                  |
| 12. PROVISIONAL THRESHOLD IDENTIFICATION:                                                        |
|     - Clearly identify water quality thresholds as unverified operational heuristics.            |
+==================================================================================================+
```

---

## 7. Recommended Final Application Architecture

To achieve clean integration without introducing unnecessary complexity, frameworks, or microservice overhead, a **pure Python architecture powered by Streamlit** is recommended.

### High-Level System Architecture

```mermaid
flowchart TD
    subgraph Data & Simulation Engine
        A1["Historical Records<br/>(processed_data_v2/*.csv)"] --> D1["Data Manager &<br/>Query Engine"]
        A2["Pond Physics Generator<br/>(Solar Cycle & Diurnal DO)"] --> S1["Real-Time Sensor<br/>Simulator Engine"]
    end

    subgraph Core Scientific & ML Services
        S1 --> P1["Telemetry Buffer<br/>(pH, Temp, DO, TAN)"]
        D1 --> P1
        P1 --> C1["Emerson Aqueous NH3<br/>Equilibrium Engine"]
        P1 --> M1["Exp 1: Ammonia Soft-Sensor<br/>(Random Forest - Exploratory)"]
        P1 --> M2["Exp 2: Mortality Risk Flag<br/>(Advisory Severity Diagnostic)"]
        P1 --> M3["Exp 3: Multi-Week TAN Risk<br/>(Exploratory Early Warning)"]
        P1 --> M4["Exp 4: Fish Weight Engine<br/>(Persistence Baseline + GBDT)"]
        P1 --> M5["Exp 5: Morning DO Engine<br/>(Historical Mean + GBDT Ranker)"]
        P1 --> F1["Bioenergetic Feeding Engine<br/>(Biomass Table & Safety Cutoffs)"]
    end

    subgraph Streamlit Presentation Layer (app/main.py)
        P1 & C1 --> UI1["Tab 1: Live Simulation Mode<br/>(Virtual Sensor Gauges & Sliders)"]
        M1 & M2 & M3 & M5 --> UI2["Tab 2: Toxicity & Hypoxia Alert Center<br/>(Thresholds & Risk Rank Scores)"]
        D1 & M4 --> UI3["Tab 3: Historical Trends & Analytics<br/>(Pond Explorer & Growth Tracking)"]
        F1 --> UI4["Tab 4: Adaptive Feeding Advisor<br/>(Dynamic Feed & Safety Interlocks)"]
        M1 & M3 & M5 --> UI5["Tab 5: Model Transparency & Audit<br/>(Scientific Limitations & Metrics)"]
    end
```

### Proposed Directory Layout (All New Code Contained in `app/`)

```
d:\AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System\
│
├── app/                                # Standalone Application Root (NEW)
│   ├── main.py                         # Streamlit entrypoint with multi-tab layout
│   ├── config.py                       # Global thresholds, constants, and contracts
│   │
│   ├── core/                           # Pure Python scientific & physics engines
│   │   ├── __init__.py
│   │   ├── chemistry.py                # Audited Emerson NH3 equilibrium formulas
│   │   ├── bioenergetics.py            # Feeding rate calculation & safety throttles
│   │   ├── simulator.py                # Diurnal solar cycle & oxygen depletion model
│   │   └── data_manager.py             # Historical dataset loader & caching
│   │
│   ├── models/                         # Model loading & inference wrappers
│   │   ├── __init__.py
│   │   ├── registry.py                 # Central model registry with baseline fallbacks
│   │   ├── exp1_soft_sensor.py         # Exp 1 TAN soft-sensor wrapper
│   │   ├── exp2_mortality.py           # Exp 2 Mortality risk classifier wrapper
│   │   ├── exp3_ammonia_risk.py        # Exp 3 Multi-week ammonia risk wrapper
│   │   ├── exp4_fish_weight.py         # Exp 4 Persistence + GBDT weight wrapper
│   │   └── exp5_hypoxia.py             # Exp 5 Historical mean + GBDT hypoxia wrapper
│   │
│   └── views/                          # Streamlit UI page components
│       ├── __init__.py
│       ├── live_simulation_view.py     # Real-time animated telemetry & controls
│       ├── alert_center_view.py        # Multi-factor risk alerts & soft-sensor
│       ├── historical_view.py          # Historical pond timeseries explorer
│       ├── feeding_advisor_view.py     # Adaptive feed schedules & biomass growth
│       └── scientific_audit_view.py    # XAI feature importance & audit metrics
│
├── processed_data_v2/                  # Cleaned datasets (READ-ONLY)
├── baseline_toxicity_v1/               # Exp 1 artifacts (READ-ONLY)
├── experiment_2_mortality_v1/          # Exp 2 artifacts (READ-ONLY)
├── experiment_3_next_visit_risk_v1/    # Exp 3 artifacts (READ-ONLY)
├── experiment_4_next_visit_weight_v1/  # Exp 4 artifacts (READ-ONLY)
└── experiment_5_do_hypoxia_v1/         # Exp 5 artifacts (READ-ONLY)
```

---

## 8. Exact Files That May Need Modification

**Zero existing files will be modified or deleted.**

All research deliverables, datasets, and scripts will remain strictly untouched:
- `dataset/*` (Unmodified)
- `processed_data_v2/*` (Unmodified)
- `clean_datasets_v2.py` (Unmodified)
- `train_experiment_1.py` through `train_experiment_4.py` (Unmodified)
- `save_phase2_metrics.py` (Unmodified)
- All experiment folders and markdown audit reports (Unmodified)

All new application components will be authored in the newly created `app/` directory and tested independently.

---

## 9. Step-by-Step Implementation Plan

The implementation is structured into six sequential, non-destructive phases:

### Phase 1: Backend & Data Integration
- **Goal:** Set up configuration, load historical data, and implement the audited chemical equilibrium engine.
- **Files to Modify:** None.
- **New Files Required:**
  - `app/config.py` (Thresholds, data contracts, and provisional metadata)
  - `app/core/chemistry.py` (Emerson aqueous $\text{NH}_3$ formula with molecular weight conversion)
  - `app/core/data_manager.py` (Fast, cached loader for `processed_data_v2/` CSVs)
- **Existing Functions Reused:** `calculate_nh3_from_tan_n` and `calculate_nh3_from_tan_nh3` from `clean_datasets_v2.py`.
- **Dependencies:** `processed_data_v2/water_quality_cleaned_v2.csv`, `thresholds_config.json`.
- **Possible Risks:** Memory overhead from loading large CSVs; resolved by using Streamlit caching (`@st.cache_data`).
- **Required Tests:** Unit tests verifying ammonia calculations against the Emerson benchmark table.

### Phase 2: Water-Quality & Toxicity Module Integration
- **Goal:** Wrap Experiments 1, 2, and 3 into safe inference services with explicit exploratory flags.
- **Files to Modify:** None.
- **New Files Required:**
  - `app/models/exp1_soft_sensor.py`
  - `app/models/exp2_mortality.py`
  - `app/models/exp3_ammonia_risk.py`
- **Existing Functions Reused:** `build_preprocessor` logic from `train_experiment_1.py`, `train_experiment_2.py`, `train_experiment_3.py`.
- **Dependencies:** Pre-trained `.joblib` pipelines in `baseline_toxicity_v1/`, `experiment_2_mortality_v1/`, `experiment_3_next_visit_risk_v1/`.
- **Possible Risks:** Missing input features in runtime records; resolved by automated domain-median imputation and indicator flags.
- **Required Tests:** Verification that predictions match recorded experiment metrics and that exploratory warnings are attached to all outputs.

### Phase 3: Fish Growth & Feeding Module Integration
- **Goal:** Implement the somatic fish weight tracking service and the bioenergetic feeding recommendation engine.
- **Files to Modify:** None.
- **New Files Required:**
  - `app/core/bioenergetics.py` (Feeding rate formulas and safety cutoffs)
  - `app/models/exp4_fish_weight.py` (Persistence baseline primary predictor + GBDT exploratory model)
- **Existing Functions Reused:** Persistence baseline logic and GBDT pipeline from `train_experiment_4.py`.
- **Dependencies:** Phase 1 configuration and Phase 2 toxicity engine.
- **Possible Risks:** User interpreting fish weight as harvest yield; resolved by hardcoded UI labels ("Average Individual Fish Weight (g)").
- **Required Tests:** Test feeding suppression logic: verify 50% cut at $\text{DO} < 3.0$ mg/L and 100% cut at $\text{DO} < 2.0$ mg/L or $\text{NH}_3 > 0.05$ mg/L.

### Phase 4: Experiment 5 DO Baseline & Hypoxia Risk-Score Integration
- **Goal:** Integrate Historical Mean baseline and GBDT moderate hypoxia risk-scoring model, while quarantining rejected models.
- **Files to Modify:** None.
- **New Files Required:**
  - `app/models/exp5_hypoxia.py`
  - `app/models/registry.py` (Central model coordinator)
- **Existing Functions Reused:** Historical Mean calculation ($3.48$ mg/L) and GBDT pipeline from `save_phase2_metrics.py`.
- **Dependencies:** Phase 2 and Phase 3 models.
- **Possible Risks:** Accidental activation of severe hypoxia RF; resolved by completely omitting the severe hypoxia model from the registry.
- **Required Tests:** Verify that Historical Mean is the default point prediction; verify that GBDT hypoxia score is displayed as an exploratory risk ranking.

### Phase 5: Dashboard Integration & Visualization
- **Goal:** Construct the interactive Streamlit user interface with Plotly charts and 5 dedicated views.
- **Files to Modify:** None.
- **New Files Required:**
  - `app/main.py` (Streamlit entrypoint)
  - `app/views/live_simulation_view.py`
  - `app/views/alert_center_view.py`
  - `app/views/historical_view.py`
  - `app/views/feeding_advisor_view.py`
  - `app/views/scientific_audit_view.py`
- **Existing Functions Reused:** All modules from Phases 1–4.
- **Dependencies:** `streamlit`, `plotly`.
- **Possible Risks:** UI re-run state loss; resolved by using `st.session_state` for simulation state and user preferences.
- **Required Tests:** End-to-end user interaction test: slider adjustments, tab switching, and chart responsiveness.

### Phase 6: Simulation Testing, Validation & Regression Testing
- **Goal:** Implement the diurnal pond physics simulator and perform end-to-end integration verification.
- **Files to Modify:** None.
- **New Files Required:**
  - `app/core/simulator.py` (Diurnal solar cycle, respiration, post-feed ammonia spike, aerator mechanics)
  - `tests/test_system_integration.py`
- **Existing Functions Reused:** All application modules.
- **Dependencies:** Complete application stack.
- **Possible Risks:** Unphysical simulation values (e.g. negative DO); resolved by physical clamping ($0 \le \text{DO} \le 15$ mg/L, $0 \le \text{pH} \le 14$).
- **Required Tests:** Run 100 simulated diurnal cycles; verify that aerator activation successfully restores DO; verify that feeding cessation prevents toxic ammonia buildup.

---

## 10. Testing and Validation Strategy

To ensure zero regressions and maintain scientific rigor, the testing strategy spans three levels:

1. **Unit & Calculation Tests:**
   - Verify Emerson aqueous ammonia calculations against published chemical tables.
   - Verify bioenergetic feed calculation and safety cutoff triggers.
   - Verify that missing values produce imputation flags rather than zero replacements.
2. **Model Governance & Baseline Integrity Tests:**
   - Verify that **Persistence Baseline** is returned as primary for Exp 4.
   - Verify that **Historical Mean** is returned as primary for Exp 5.
   - Verify that **Severe Hypoxia RF is completely locked out** and cannot be loaded.
   - Verify that all ML models are stamped with explicit exploratory warning metadata.
3. **End-to-End System Integration Tests:**
   - Test continuous dataflow from `app/core/simulator.py` through the telemetry buffer to UI gauges.
   - Test multi-pond historical filtering in `app/views/historical_view.py`.
   - Verify that the application launches smoothly via `streamlit run app/main.py` without warnings or deprecation errors.

---

## 11. Final Integration Readiness Assessment

| Evaluation Dimension | Readiness Status | Assessment & Operational Notes |
|---|---|---|
| **Data Cleaning & Preprocessing** | **READY** | Standardized `processed_data_v2/` datasets and audit reports are 100% complete. |
| **Chemical Formulation** | **READY** | Audited Emerson formula with molecular weight conversion verified and ready. |
| **Model Availability** | **READY** | Pre-trained pipelines available for Exp 1, 2, 3; Exp 4/5 logic fully verified. |
| **Baseline Governance** | **READY** | Persistence (Exp 4) and Historical Mean (Exp 5) established as operational baselines. |
| **Model Quarantine** | **READY** | Severe Hypoxia RF formally rejected; exploratory models clearly designated. |
| **Software Architecture** | **READY** | Clean Streamlit + modular core layout designed to prevent code interference. |
| **Implementation Plan** | **READY** | 6-phase non-destructive roadmap specified with complete test requirements. |

### Final Pre-Integration Sign-Off
- **Repository Safety:** Confirmed. Zero existing application files, datasets, or experiment outputs were modified.
- **Next Action:** Implementation will begin only upon explicit user approval of this report and authorization of Phase 1.

---
*Report compiled and certified for final application integration.*
