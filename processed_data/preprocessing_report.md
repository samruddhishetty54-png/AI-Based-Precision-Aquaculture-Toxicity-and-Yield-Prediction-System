# AI-Based Precision Aquaculture Data Preprocessing Report

**Status:** Preprocessing Completed  
**ML Models Trained:** None (Awaiting user confirmation)  
**Output Directory:** `processed_data/`  
**Original Datasets:** Intact and unmodified in `dataset/`

---

## 1. Executive Summary Table

| Dataset / Analytical File | Original Rows | Final Rows | Original Cols | Final Cols | Duplicates Handled | Missing Cells (Before) | Missing Cells (After) | Cleaning Strategy |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`water_quality.csv`** | 12,431 | 12,399 | 53 | 30 | 4 | 364,516 | 74,761 | Removed 100% empty cols & notes/actions; dropped 30 missing sensor vitals; preserved ammonia & feeding/growth metrics without zero-fill. |
| **`enrolled_ponds.csv`** | 324 | 323 | 20 | 20 | 2 | 1,278 | 46 | Deduplicated pond `ara2_f33085c0`; preserved uninvented pond area; categorized missing categorical fields as `'Unknown'`/`'None'`. |
| **`dropouts.csv`** | 128 | 128 | 8 | 8 | 0 | 29 | 0 | Preserved all 128 dropout records; filled missing tenancy and descriptive reasons cleanly. |
| **`Data_Model_IoTMLCQ_2024.xlsx`** | 4,383 | 4,383 | 28 | 29 | 0 | 0 | 0 | Preserved complete records; formatted ISO 8601 datetimes; standardized degree symbols and numeric types. |

---

## 2. Dedicated Domain-Specific Prepared Datasets

As requested for precision aquaculture modelling, three specialized datasets were extracted and engineered from the verified observations:

| Task Dataset | Output Path | Rows | Columns | Missing Values | Domain Focus & Scientific Rationale |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Toxicity Analysis** | [`toxicity_analysis.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data/toxicity_analysis.csv) | **6,945** | 24 | 31,717 | Focused strictly on verified ammonia monitoring events (`Ammonia—TAN (NH3-N)`, `Ammonia—TAN (NH3)`, `Ammonia—NH3`), complete DO, pH, and Temperature. Computes un-ionized toxic ammonia ($\text{NH}_3$) using the Emerson equation. Derives multi-factor risk flags (`hypoxia_risk`, `ph_stress_risk`, `ammonia_toxicity_risk`, `behavioral_distress_observed`, `toxicity_severity_level`). |
| **Fish Health & Growth Analysis** | [`fish_health_growth_analysis.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data/fish_health_growth_analysis.csv) | **9,422** | 16 | 7,033 | Focused on fish biomass, weight growth, and health distress symptoms (`Individuals air gulping`, `Individuals tail splashing`, `Dead fish`). Weight is strictly preserved as measured (5,566 direct weight records flagged with `has_weight_measurement`) and never filled with zero. Enriched with pond area, depth, and feed type. |
| **Feeding Analysis** | [`feeding_analysis.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data/feeding_analysis.csv) | **6,752** | 16 | 8,938 | Captures active feeding events (`Feed amount (kg) > 0`) correlated with water quality vitals (`DO`, `pH`, `Temp`, `Ammonia`). Enriched with pond dimensions, stocking density, feed brand, and normalized `feed_per_acre_kg`. Never filled with zero. |

---

## 3. Detailed Preprocessing Decisions by Dataset

### A. [`water_quality.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/dataset/water_quality.csv)
1. **Datetime Alignment & Chronological Ordering:**
   - Synthesized timestamp from `Date of data collection` and `Time of data collection`.
   - Sorted chronologically per pond (`pond_id`, `datetime`).
2. **Duplicate Deduplication:**
   - Identified 4 duplicate timestamp records across ponds `ara2_5a3d15dd` and `ara2_407f70f7`.
   - Retained the primary record containing verified, non-null sensor vitals.
3. **Columns Removed (23 Columns):**
   - **Completely Empty (100% missing):** `Alkalinity (mg/L)`, `Hardness (mg/L)`.
   - **Free-Text, Observers, & Corrective Action Intervention Fields:**
     `Observer`, `Is follow up possible`, `Reason follow up not possible`, `Corrective actions requested`, `Corrective actions requested (other)`, `Corrective actions amount requested`, `Corrective actions implemented`, `Corrective actions implementation date`, `Corrective actions taken`, `Corrective actions taken (other)`, `Corrective actions taken (details)`, `Non-prescribed corrective actions taken`, `Reason not implemented`, `Water quality improved after corrective actions`, `Corrective action notes`, `Notes (mortalities)`, `Self-initiated corrective actions taken`, `Self-initiated corrective actions implemented on (exact date)`, `Self-initiated corrective actions implemented (date range)`, `Self-initiated corrective actions notes`, `Notes`, `Corrective actions`.
4. **Sensor Vitals Missing Values (DO, pH, Temp):**
   - 30 records were missing vital signs (pH, DO, or Temp). Because DO, pH, and Temperature are non-negotiable triage parameters in aquaculture, these 30 rows were excluded from the modeling master to avoid sensor hallucination.
   - Result: 12,399 rows remain with 100% verified sensor measurements.
5. **Ammonia Handling:**
   - Strictly preserved actual measurements without blind imputation.
6. **Feed, Weight, and Survival Values:**
   - One impossible `0.0g` weight and one `0.0 kg` feed value were converted to `NaN`. No missing feed, weight, or survival values were filled with zero.
7. **Target & Behavioral Indicators:**
   - `Parameters out of range` filled with `'None'` when water quality was in range.

### B. [`enrolled_ponds.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/dataset/enrolled_ponds.csv)
1. **Pond Identity & Deduplication:**
   - Pond `ara2_f33085c0` had two records (an early enrollment on 2022 with missing area and an updated 2026 record with 41.0 acres). Retained the complete 41.0-acre profile, bringing unique enrolled ponds to 323.
2. **Preserving Physical Dimensions:**
   - In accordance with instructions (*"Do not invent pond measurements"*), the 46 missing `Pond area in acres` values were left as `NaN` without synthetic imputation.
3. **Categorical Imputation:**
   - `Enrollment mechanism`: 44 missing $\rightarrow$ `'Unknown'`
   - `Added by`: 23 missing $\rightarrow$ `'Unknown'`
   - `Status`: 4 missing $\rightarrow$ `'Unknown'`
   - `Culture change`: 253 missing $\rightarrow$ `'None Reported'`
   - `Equipment`, `Existing practices`: missing $\rightarrow$ `'Standard/Unspecified'`
   - `Fertilizers used`, `Feed type`, `Feed source`, `Feed brand`, `Fish source`: missing $\rightarrow$ `'Unspecified'` / `'None'`
   - Free-text notes: missing $\rightarrow$ `'None'`

### C. [`dropouts.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/dataset/dropouts.csv)
1. **Preservation:**
   - All 128 dropout records preserved intact.
2. **Missing Descriptive Fields:**
   - `Tenancy type`: 27 missing (21.09%) $\rightarrow$ `'Unknown'`
   - `Further details on reason`: 2 missing (1.56%) $\rightarrow$ `'None recorded'`

### D. [`Data_Model_IoTMLCQ_2024.xlsx`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/dataset/Data_Model_IoTMLCQ_2024.xlsx)
1. **Preservation & Formatting:**
   - Original 4,383 records preserved without record deletion or artificial alteration.
   - Parsed Excel serial timestamps (`45292.0` $\rightarrow$ `2024-01-01 00:00:00`) and stored as `datetime_iso`.
   - Cast 21 continuous and discrete sensor features to `float64` / `int64`.
   - Verified zero missing values, zero duplicates, and physical sanity across all features.

### E. Retracted Dataset Exclusion
- [`water_quality_nellore_retracted.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/dataset/water_quality_nellore_retracted.csv) was explicitly excluded from all training pipelines and prepared datasets as instructed.

---

## 4. Interpolation and Leakage-Prevention Constraints
- **Temporal Interpolation Guardrail:** Implemented in `safe_time_interpolate()`. Interpolation is strictly confined to the *same pond* and ordered chronologically, with an explicit rejection threshold for gaps $> 4$ hours.
- **Leakage-Free Imputation Protocol:** Implemented in `fit_imputer_on_train_only()`. For downstream ML feature pipelines, all statistics (medians, means, scalers) are fit strictly on the training partition and transformed on test sets.

