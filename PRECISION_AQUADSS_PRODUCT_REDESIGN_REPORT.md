# Precision AquaDSS — Organization-Facing Product Redesign Report

**Date:** 2026-11-25  
**Scope:** Organization-facing aquaculture decision-support application redesign (9-page navigation, Farm & Pond Overview landing page, CSV Dataset Import & Analysis Workspace, and strict model-compatibility gating).  
**Status:** Implemented & Verified (`149 passed, 4 subtests passed` in pytest; live Streamlit server running on `http://127.0.0.1:8501`).

---

## 1. Application Architecture & 9-Page Navigation

The application is structured in [dashboard.py](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/dashboard.py) for aquaculture organizations, fisheries departments, farm management companies, and research monitoring teams:

| Section | Page Title | Source File | Purpose |
| :--- | :--- | :--- | :--- |
| **Farm & Monitoring** | Farm Overview *(Default)* | [08_Farm_Overview.py](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/dashboard/pages/08_Farm_Overview.py) | Organization-level regional/pond summary, latest historical observation date, water-quality trends, quick actions |
| **Farm & Monitoring** | Pond Monitoring | [01_Overview.py](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/dashboard/pages/01_Overview.py) | Pond inspection priority queue & central model registry health |
| **Data Management** | Import & Analyse | [09_Import_Dataset.py](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/dashboard/pages/09_Import_Dataset.py) | Central CSV upload, schema mapping, unit confirmation, validation, compatibility audit, batch execution, CSV export |
| **Water Quality & Risk** | Water Quality | [02_Water_Quality_Toxicity.py](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/dashboard/pages/02_Water_Quality_Toxicity.py) | Emerson (1975) chemistry calculator + Exp 1, 2, 3 experimental screening |
| **Water Quality & Risk** | DO & Hypoxia | [03_Next_Visit_DO_Hypoxia.py](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/dashboard/pages/03_Next_Visit_DO_Hypoxia.py) | Exp 5 constant historical mean DO benchmark (`3.50 mg/L`) & hypoxia screening limitations |
| **Growth & Feeding** | Growth & Feeding | [04_Growth_Feeding_Advisor.py](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/dashboard/pages/04_Growth_Feeding_Advisor.py) | Exp 4 persistence baseline (`W_{t+1} = W_t`), provisional feeding advisory, observational feedback |
| **Analytics** | Historical Reports | [05_Historical_Data_Explorer.py](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/dashboard/pages/05_Historical_Data_Explorer.py) | Longitudinal historical field explorer & missingness profiles |
| **Analytics** | Simulation Lab | [06_Simulation_Sandbox.py](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/dashboard/pages/06_Simulation_Sandbox.py) | Quarantined synthetic IoT benchmark sandbox (`operational_use_permitted = False`) |
| **System** | Model & System Status | [07_Model_Registry_Governance.py](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/dashboard/pages/07_Model_Registry_Governance.py) | SHA-256 artifact audit, benchmark catalog, governance controls |

### Data Separation & Hierarchy Integrity
- **No Invented Hierarchies:** Audited historical datasets (`enrolled_ponds_v2.csv`, `toxicity_analysis_v2.csv`) record `region` and `pond_id` without a corporate farm parent table. The UI groups strictly by actual recorded `region` and `pond_id`.
- **Three-Way Isolation:** Historical field records (`processed_data_v2/`), user-uploaded CSVs (`st.session_state["uploaded_analysis_state"]`), and simulated scenarios (`iot_water_model_v2.csv`) remain strictly separated.

---

## 2. Dataset Upload Workflow

Implemented in [upload_processor.py](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/dashboard/utils/upload_processor.py) and [09_Import_Dataset.py](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/dashboard/pages/09_Import_Dataset.py):

1. **CSV Upload:** Accepts `.csv` (UTF-8 / Latin-1). Excel `.xlsx` is explicitly disabled because `openpyxl` is not installed in the environment.
2. **Preview & Integrity Profile:** Displays row/column counts, first 15 rows, column dtypes, exact missing-value (`NaN`) counts/percentages, and exact duplicate row counts. Missing values are **never** zero-filled.
3. **Canonical Column Mapping & Unit Confirmation:** Suggests mappings for exact aliases and flags ambiguous column names (e.g., `temp`, `ammonia`, `tan`) for explicit user unit confirmation before mapping.
4. **Validation:** Checks duplicate mappings, non-numeric values in numeric columns, software defensive bounds (`DEFENSIVE_BOUNDS`), unparsable dates (preserved as `NaT`), duplicate `(pond_id, datetime)` pairs, and simulation filename markers.
5. **Pond Selection:** Allows filtering by `pond_id` when mapped; never invents pond IDs or dates when absent.
6. **Model Compatibility Gate & Run Analysis:** Enables **Run Analysis** only when validation passes and at least one compatible module is selected.
7. **Results Workspace & Export:** Organizes outputs into Water Quality, Toxicity Screening, DO Benchmark, Growth Persistence, and Feeding Advisory, showing unavailable outputs explicitly and providing a downloadable CSV report.

---

## 3. Model Compatibility Audit

| Module / Model | Required Inputs | Output & Interpretation | Governance / Limitations |
| :--- | :--- | :--- | :--- |
| **Emerson (1975) NH3** | `ph`, `temp_c`, explicit `tan_n_mg_l` or `tan_nh3_mg_l` | Theoretical equilibrium un-ionized `NH3` (mg/L) | Equilibrium proxy, not laboratory assay |
| **Exp 1: Ammonia Soft-Sensor (RF)** | `dissolved_oxygen_mg_l`, `ph`, `temp_c` | Estimated `NH3` proxy (mg/L) | **Experimental only**; trained on AP ponds; underpredicts `NH3 >= 0.05 mg/L` |
| **Exp 2: Mortality Diagnostic (LR)** | `dissolved_oxygen_mg_l`, `ph`, `temp_c` | Mortality risk score (0–1) | **Weak chronological holdout** (3.81% precision); not a reliable mortality predictor |
| **Exp 3: Next-Visit NH3 Risk (RF)** | `curr_do`, `curr_ph`, `curr_temp`, `gap_days` (3–45d) | Multi-week transition risk score | **Exploratory** (PR-AUC 0.0305 vs 0.0280 no-skill); not hourly/overnight |
| **Exp 4: Cohort Weight (Persistence)** | `average_fish_weight_g` (> 0) | `W(t+1) = W(t)` (MAE 93.38 g) | Somatic pond-cohort avg weight only; **NOT harvest yield** |
| **Exp 5: Morning DO Benchmark** | `dissolved_oxygen_mg_l` | Constant historical mean (`3.50 mg/L`) | Constant benchmark, **NOT dynamic forecast**; GBDT classifier has 91% FDR |
| **Provisional Feeding Advisory** | `dissolved_oxygen_mg_l` + (`feed_amount_kg` or biomass) | Provisional feed rate adjustment | Unverified heuristic; `is_automatic_control = False` |

---

## 4. Files Changed

### Created
- `app/dashboard/utils/upload_processor.py`
- `app/dashboard/pages/08_Farm_Overview.py`
- `app/dashboard/pages/09_Import_Dataset.py`
- `app/tests/test_upload_and_product_redesign.py`
- `PRECISION_AQUADSS_PRODUCT_REDESIGN_REPORT.md`

### Modified
- `dashboard.py` (9-page organization-facing navigation & branding)
- `app/dashboard/components/banners.py` (added `render_uploaded_context_notice`)
- `app/dashboard/pages/01_Overview.py` (integrated uploaded context notice)
- `app/dashboard/pages/02_Water_Quality_Toxicity.py` (integrated uploaded context notice)
- `app/dashboard/pages/03_Next_Visit_DO_Hypoxia.py` (integrated uploaded context notice)
- `app/dashboard/pages/04_Growth_Feeding_Advisor.py` (integrated uploaded context notice)
- `app/dashboard/pages/05_Historical_Data_Explorer.py` (integrated uploaded context notice)

---

## 5. Verification & Test Results

- **Full Pytest Suite:** `.\.venv\Scripts\python.exe -m pytest app/tests/ -q` → **149 passed, 4 subtests passed** in 7.08s (includes all 139 existing tests + 10 new upload & product redesign tests).
- **Pipeline Verification on `toxicity_analysis_v2.csv`:** Verified parsing, mapping, validation (`317` ponds detected), compatibility assessment, and batch execution.
- **Live Server Check:** Streamlit Uvicorn server running on `http://127.0.0.1:8501` returning HTTP `200`.
- **Browser Screenshots:** Automated headless Chrome/Edge screenshot capture is unavailable in this Windows host environment (`DevToolsActivePort` not available and no Playwright/Selenium installed); manual visual inspection in a local browser at `http://127.0.0.1:8501` is recommended.

---

## 6. Remaining Limitations

- **Excel (`.xlsx`) Upload:** Not supported without installing `openpyxl`.
- **Batch Row Cap:** Interactive batch execution in `09_Import_Dataset.py` defaults to evaluating up to `500` rows per run to keep the web UI responsive.
- **Organization/User Accounts:** Multi-user authentication, staff RBAC, and cloud database synchronization are not implemented; uploaded datasets live in browser session memory (`st.session_state`).
- **Model Domain:** Pre-trained ML artifacts (Exp 1–3) reflect Andhra Pradesh commercial pond distributions and morning inspection protocols (06:00–08:30 AM, 3–45 day intervals).
