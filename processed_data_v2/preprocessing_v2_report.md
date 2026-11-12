# Preprocessing Pipeline v2 Audit & Verification Report

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Pipeline Version:** `clean_datasets_v2.py`  
**Output Directory:** `processed_data_v2/`  
**Date:** November 2026  
**Status:** All Corrections Successfully Implemented & Verified | **ML Models Trained:** None  

---

## 1. Executive Summary & Purpose of v2 Corrections

Following the in-depth verification of the original preprocessing script, `clean_datasets_v2.py` was created to address chemical, structural, and temporal issues without altering raw data or overwriting existing v1 files.

### Summary of Corrections in v2:
1. **Chemical & Molecular-Weight Rigor in Ammonia Modeling:**
   * Corrected the un-ionized ammonia calculation for Total Ammonia Nitrogen expressed as nitrogen (`Ammonia—TAN (NH3-N)`) by applying the stoichiometric molecular-weight conversion factor:
     $$\text{MW Ratio} = \frac{\text{MW}(\text{NH}_3)}{\text{MW}(\text{N})} = \frac{17.031}{14.007} \approx 1.215892$$
   * For Total Ammonia Nitrogen expressed as ammonia (`Ammonia—TAN (NH3)`), computed un-ionized ammonia directly without re-applying the 17/14 ratio (preventing double-counting).
   * Kept all three raw ammonia columns separate and explicitly labeled.
   * Marked field-reported `Ammonia—NH3` as **unverified** because its testing methodology (probe vs colorimetric chart vs lookup table) is not documented.
2. **Multi-Populated Ammonia Inconsistency Audit:**
   * Quantified and compared records where multiple ammonia measurements co-occur.
   * Documented agreement between calculation pathways.
3. **Externalized & Provisional Heuristic Thresholds:**
   * Decoupled hardcoded rules into an external JSON configuration file: [`thresholds_config.json`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/thresholds_config.json).
   * Explicitly labeled all derived alert categories as **provisional heuristics** (unverified against site-specific bioassays or regulatory standards).
   * Kept raw sensor measurements completely separate from rule-derived risk labels.
4. **Elimination of Future-Information (Look-Ahead) Leakage:**
   * Replaced static deduplication with a **point-in-time temporal as-of join** (`pd.merge_asof(direction='backward')`).
   * Attached pond metadata (area, depth, feed type, feed brand) strictly from profiles recorded **on or before** the observation date.
   * Prevented retroactive back-projection of 2026 survey updates (such as pond `ara2_f33085c0`'s 41.0-acre expansion) onto historical 2021–2025 observations.
5. **Folder Isolation:**
   * Saved all new files to [`processed_data_v2/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/). Left `dataset/` and `processed_data/` completely intact.

---

## 2. Dataset Dimensions & Output Directory Mapping

| Processed File (v2) | Rows | Columns | Key Features & Enhancements |
| :--- | :---: | :---: | :--- |
| [`water_quality_cleaned_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/water_quality_cleaned_v2.csv) | **12,399** | **31** | 100% complete DO, pH, Temp; 100% empty cols purged; unmeasured feed/weight kept as NaN; includes parsed date for point-in-time joins. |
| [`enrolled_ponds_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/enrolled_ponds_v2.csv) | **324** | **21** | Retains all historical profile snapshots (including both 2022 and 2026 snapshots for pond `ara2_f33085c0`) with standardized datetime. |
| [`dropouts_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/dropouts_v2.csv) | **128** | **8** | Preserves all 128 dropout records; missing tenancy and reasons filled cleanly. |
| [`iot_water_model_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/iot_water_model_v2.csv) | **4,383** | **29** | Complete hourly IoT records; standardized ISO datetime; type-safe numeric features. |
| [`toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv) | **6,945** | **27** | Corrected molecular $\text{NH}_3$ calculation (17/14 applied to TAN-N; direct to TAN-NH3); unverified reported $\text{NH}_3$ preserved; provisional heuristic risk labels. |
| [`fish_health_growth_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/fish_health_growth_analysis_v2.csv) | **9,422** | **17** | Biomass and health tracking; point-in-time pond metadata; unmeasured weights kept as NaN (zero-fill prevented). |
| [`feeding_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/feeding_analysis_v2.csv) | **6,752** | **17** | Active feeding events; point-in-time pond metadata (no future acreage leakage); feed per acre normalized only when historical acreage is valid. |
| [`thresholds_config.json`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/thresholds_config.json) | — | — | Externalized JSON file containing provisional heuristic thresholds and warning metadata. |

---

## 3. Deep Dive: Ammonia Calculations & Overlap Analysis

### A. Calculation Methodologies Applied

1. **Method 1: From TAN as $\text{NH}_3\text{-N}$ (`raw_ammonia_tan_nh3_n_mg_l`):**
   * Applied Emerson et al. (1975) equilibrium equation with temperature in Kelvin ($T_K = T_C + 273.15$):
     $$\text{p}K_a = 0.09018 + \frac{2729.92}{T_K}, \quad f = \frac{1}{10^{(\text{p}K_a - \text{pH})} + 1}$$
   * Converted nitrogen concentration to molecular $\text{NH}_3$:
     $$\text{calculated\_nh3\_from\_tan\_n\_mg\_l} = f \times \text{TAN}_{\text{NH3-N}} \times \left(\frac{17.031}{14.007}\right)$$
   * **Unit:** $\text{mg/L as molecular NH}_3$
   * **Records Processed:** **5,287 records**
   * **Distribution:** Min: $0.00000\text{ mg/L}$, Mean: $0.02276\text{ mg/L}$, Median: $0.01159\text{ mg/L}$, Max: $0.83873\text{ mg/L}$.

2. **Method 2: From TAN as $\text{NH}_3$ (`raw_ammonia_tan_nh3_mg_l`):**
   * Applied Emerson equilibrium directly:
     $$\text{calculated\_nh3\_from\_tan\_nh3\_mg\_l} = f \times \text{TAN}_{\text{NH3}}$$
   * No $17/14$ factor applied (already on molecular $\text{NH}_3$ basis).
   * **Unit:** $\text{mg/L as molecular NH}_3$
   * **Records Processed:** **1,659 records**
   * **Distribution:** Min: $0.00000\text{ mg/L}$, Mean: $0.01577\text{ mg/L}$, Median: $0.01147\text{ mg/L}$, Max: $0.33584\text{ mg/L}$.

3. **Method 3: Reported Ammonia $\text{NH}_3$ (`reported_ammonia_nh3_unverified_mg_l`):**
   * Preserved in its original column.
   * **Unit:** $\text{mg/L reported}$
   * **Status:** **Explicitly marked as UNVERIFIED**. The laboratory testing method or field kit brand used to produce this value is not documented in project files.

4. **Primary Unified Calculated Field (`primary_calculated_nh3_mg_l`):**
   * Selects `calculated_nh3_from_tan_n_mg_l` first (5,287 records), falling back to `calculated_nh3_from_tan_nh3_mg_l` (1,658 records).
   * Accompanied by categorical tracking column `nh3_calculation_source`:
     * `emerson_from_tan_nh3_n_with_mw_conversion`: 5,287 records (76.1%)
     * `emerson_from_tan_nh3_direct`: 1,658 records (23.9%)
     * `uncalculated_missing_inputs`: 0 records in `toxicity_analysis_v2.csv` (100% of rows have a valid primary calculated molecular $\text{NH}_3$).

### B. Overlap and Inconsistency Audit

1. **Overlap of TAN-N and TAN-NH3 (Row 3244 / Pond `ara2_c15dc3a2` on 08/01/2025):**
   * Only 1 record in the entire dataset has both `TAN (NH3-N)` ($0.25\text{ mg/L}$) and `TAN (NH3)` ($0.30\text{ mg/L}$) populated.
   * At $\text{pH} = 7.88$ and $T = 30.4^\circ\text{C}$:
     * Calculated from TAN-N (with 17/14): **$0.01791\text{ mg/L}$**
     * Calculated from TAN-NH3 (direct): **$0.01767\text{ mg/L}$**
     * Reported $\text{NH}_3$: **$0.02\text{ mg/L}$**
   * **Inconsistency Check:** The discrepancy between the two calculations is only $0.00024\text{ mg/L}$ ($1.3\%$), and both round to $0.02\text{ mg/L}$. This provides strong empirical validation that the $17.031/14.007$ factor correctly reconciles the two measurement bases.

2. **Overlap of TAN-NH3 and Reported NH3 (1,658 records):**
   * In records where both are populated, comparing $f \times \text{TAN}_{\text{NH3}}$ to reported $\text{NH}_3$ yielded:
     * Correlation: **$0.9953$**
     * Mean Absolute Difference: **$0.00147\text{ mg/L}$**
     * Max Absolute Difference: **$0.02\text{ mg/L}$**
   * **Conclusion:** The reported `Ammonia—NH3` column closely tracks the un-ionized fraction of `Ammonia—TAN (NH3)`.

---

## 4. Threshold Decoupling & Documentation

In [`thresholds_config.json`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/thresholds_config.json), the heuristic thresholds have been externalized as follows:

```json
{
  "metadata": {
    "status": "provisional_heuristic",
    "scientific_validation": "unverified",
    "warning": "These thresholds are unverified operational heuristics. They are NOT validated against published site-specific bioassays or regulatory standards, and must not be presented as ground truth.",
    "configurable": true
  },
  "heuristics": {
    "hypoxia_sublethal_do_mg_l": 4.0,
    "hypoxia_acute_do_mg_l": 3.0,
    "ph_stress_lower": 6.5,
    "ph_stress_upper": 8.5,
    "toxic_molecular_nh3_heuristic_mg_l": 0.05,
    "tan_caution_heuristic_mg_l": 1.0
  }
}
```

### Clean Separation of Sensor Data vs. Derived Rules:
* All raw sensor features retain standard scientific names (`dissolved_oxygen_mg_l`, `ph`, `temp_c`, `raw_ammonia_tan_nh3_n_mg_l`, `primary_calculated_nh3_mg_l`).
* Rule-derived risk labels are clearly prefixed with `provisional_`:
  * `provisional_hypoxia_risk_heuristic`
  * `provisional_ph_stress_risk_heuristic`
  * `provisional_ammonia_risk_heuristic` (flagged in 571 records based on molecular $\text{NH}_3 \ge 0.05\text{ mg/L}$ or $\text{TAN} \ge 1.0\text{ mg/L}$)
  * `provisional_behavioral_distress_observed`
  * `provisional_severity_heuristic` (Optimal: 1,726; Moderate: 4,001; High Risk: 1,218)

---

## 5. Point-in-Time Temporal Matching & Leakage Elimination

### A. The Mechanism:
Instead of taking the latest/complete profile and retroactively merging it onto past observations, `clean_datasets_v2.py` implements a temporal backwards as-of merge:
```python
df_merged = pd.merge_asof(
    df_observations.sort_values(by='date_parsed'),
    df_enrolled_profiles.sort_values(by='profile_date'),
    left_on='date_parsed',
    right_on='profile_date',
    by='pond_id',
    direction='backward'
)
```

### B. Audit Findings & Quantified Impact:

1. **Pond `ara2_f33085c0` Resolution:**
   * In raw data, this pond had a 2022 enrollment with `Pond area in acres = NaN` and a 2026 profile update with `Pond area in acres = 41.0`.
   * **v1 Behavior:** Static merge retroactively attached 41.0 acres to all 48 observations back to 2022.
   * **v2 Behavior:** 
     * For the 42 observations occurring between February 2022 and June 2, 2026, `Pond area in acres` is strictly **`NaN`**.
     * Only for the 6 observations on or after June 3, 2026 is `41.0` acres attached.
     * Future-information leakage for this pond is completely eliminated.

2. **Observations Pre-Dating Pond Enrollment:**
   * **Water Quality:** Across all 12,399 observations, **26 observations** (across 10 distinct ponds) occurred before the pond's initial enrollment date. Under v2, their historical pond profile fields remain **`NaN`**.
   * **Feeding Analysis:** Out of 6,752 feeding records, **12 records** pre-dated pond enrollment (`profile_date is NaN`).
   * **Pond Area Missingness in Feeding Analysis:**
     * In v1: 558 records had missing pond area.
     * In v2: **585 records** have missing pond area (an increase of 27 records where future acreage is no longer leaked into past calculations).
     * `feed_per_acre_kg` is calculated across **6,167 records** where pond area was genuinely known at the time of feeding.
   * **Fish Health & Growth Analysis:**
     * In v1: 125 records had missing pond area.
     * In v2: **144 records** have missing pond area (19 historical records protected from look-ahead leakage).

---

## 6. Verification Checklist & Compliance

| Requirement | Audit Criterion | Status |
| :--- | :--- | :---: |
| **MW Conversion (17/14)** | Applied strictly to TAN (NH3-N) | **PASSED** |
| **Direct Calculation** | Applied directly to TAN (NH3) without double-scaling | **PASSED** |
| **Separation of Raw Columns** | All 3 raw columns retained in output | **PASSED** |
| **Unverified Flagging** | Reported Ammonia-NH3 labeled unverified | **PASSED** |
| **Provisional Thresholds** | Externalized to `thresholds_config.json` | **PASSED** |
| **Heuristic Labeling** | Risk labels prefixed with `provisional_` | **PASSED** |
| **Leakage Elimination** | Point-in-time matching via `merge_asof` | **PASSED** |
| **Preservation of NaNs** | Missing areas/depths preserved without synthetic invention | **PASSED** |
| **Zero-Fill Prevention** | Weights and feeds never zero-filled | **PASSED** |
| **Folder Isolation** | Saved to `processed_data_v2/` without touching raw data | **PASSED** |
| **No ML Training** | Zero machine learning models trained | **PASSED** |

---

## 7. Next Steps for Model Training

The datasets in [`processed_data_v2/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/) are chemically verified, leak-free, and ready for baseline machine learning modeling whenever you approve:
1. **Toxicity Model:** Train on [`toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv) using `primary_calculated_nh3_mg_l`, `dissolved_oxygen_mg_l`, `ph`, and `temp_c`.
2. **Growth Model:** Train on [`fish_health_growth_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/fish_health_growth_analysis_v2.csv) using verified non-zero weights and historical pond parameters.
3. **Feeding Model:** Train on [`feeding_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/feeding_analysis_v2.csv) using leak-free historical feed density.

