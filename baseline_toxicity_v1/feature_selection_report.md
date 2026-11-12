# Feature Selection & Data Inspection Report

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Experiment Identifier:** `baseline_toxicity_v1`  
**Dataset Analyzed:** [`processed_data_v2/toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv) ($N = 6,945$, 27 columns)  
**Deliverable Directory:** [`baseline_toxicity_v1/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/)  

---

## 1. Selected Feature Inventory

For the Soft-Sensor Ammonia Estimation task (Experiment 1), exactly **8 predictive features** have been selected. All 8 features represent non-ammonia physical, physicochemical, or visual properties that can be obtained in the field without using chemical ammonia test kits.

| Feature Identifier | Data Type | Non-Null Count | Missing Count | Missing (%) | Min | Median (50%) | Mean | Max | Stated Unit | Domain & Biogeochemical Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| `dissolved_oxygen_mg_l` | `float64` | 6,945 | 0 | 0.00% | 0.00 | 3.50 | 4.11 | 21.10 | $\text{mg/L}$ | Photosynthetic activity, algal bloom density, and aerobic respiration. |
| `ph` | `float64` | 6,945 | 0 | 0.00% | 6.60 | 8.14 | 8.11 | 9.20 | pH scale | Direct chemical equilibrium driver ($\text{NH}_4^+ \rightleftharpoons \text{NH}_3 + \text{H}^+$). |
| `temp_c` | `float64` | 6,945 | 0 | 0.00% | 21.40 | 29.10 | 28.86 | 35.60 | $^\circ\text{C}$ | Thermodynamic driver of the dissociation constant ($pK_a$). |
| `turbidity_cm` | `float64` | 4,027 | 2,918 | 42.02% | 0.00 | 29.00 | 29.07 | 89.00 | $\text{cm}$ | Secchi depth clarity; proxy for suspended algae and particulate matter. |
| `tds_ppt` | `float64` | 3,642 | 3,303 | 47.56% | 0.01 | 1.16 | 3.52 | 936.00 | $\text{ppt}$ | Total dissolved solids reflecting salinity, ion balance, and conductivity. |
| `Weather` | `object` | 6,634 | 311 | 4.48% | — | — | — | — | Text label | Meteorological conditions driving solar irradiance and water heating. |
| `water_color` | `object` | 6,599 | 346 | 4.98% | — | — | — | — | Text label | Visual proxy for predominant phytoplankton community. |
| `region` | `object` | 6,945 | 0 | 0.00% | — | — | — | — | Text label | Farming district (`Eluru` vs. `Nellore`) capturing soil/water baseline. |

*Target variable:* `primary_calculated_nh3_mg_l` (`float64`, 6,945 non-null, 0 missing, 0.00%, range $0.000$ to $0.8387\text{ mg/L}$, mean $0.0211\text{ mg/L}$, median $0.0116\text{ mg/L}$).

---

## 2. Itemized Audit of Excluded Columns

Across the 27 columns present in `processed_data_v2/toxicity_analysis_v2.csv`, all **19 non-selected columns** are excluded from the input feature matrix $X$. The table below documents every excluded column, its data type, exact missingness count and percentage, and the specific reason for exclusion:

| Excluded Column Name | Data Type | Missing Count | Missing (%) | Exclusion Category | Specific Technical & Scientific Reason for Exclusion |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `raw_ammonia_tan_nh3_n_mg_l` | `float64` | 1,658 | 23.87% | Raw Ammonia Measurement | Raw TAN (nitrogen basis). Including raw TAN trivializes the soft-sensor task into a direct inversion of the Emerson formula rather than indirect estimation. |
| `raw_ammonia_tan_nh3_mg_l` | `float64` | 5,286 | 76.11% | Raw Ammonia Measurement | Raw TAN (molecular basis). Direct input leakage defeating the soft-sensor objective. |
| `reported_ammonia_nh3_unverified_mg_l` | `float64` | 5,285 | 76.10% | Raw Ammonia Measurement | Raw reported ammonia column from field testing. Measurement methodology unverified; direct predictor leakage. |
| `calculated_nh3_from_tan_n_mg_l` | `float64` | 1,658 | 23.87% | Intermediate Target Pathway | Intermediate calculation derived directly from TAN-N. Direct mathematical identity with the target (target leakage). |
| `calculated_nh3_from_tan_nh3_mg_l` | `float64` | 5,286 | 76.11% | Intermediate Target Pathway | Intermediate calculation derived directly from TAN-NH3. Direct mathematical identity with the target (target leakage). |
| `nh3_calculation_source` | `object` | 0 | 0.00% | Target Metadata | Categorical label identifying which formula pathway was used to compute the target. Correlates with data collection cohort and target magnitude. |
| `provisional_ammonia_risk_heuristic` | `int64` | 0 | 0.00% | Circular Label Leakage | Binary heuristic thresholded directly on the target (`primary_calculated_nh3_mg_l >= 0.05`). Using this to predict the target is completely circular. |
| `provisional_hypoxia_risk_heuristic` | `int64` | 0 | 0.00% | Confounded Rule Label | Heuristic rule thresholded directly on `dissolved_oxygen_mg_l <= 3.0`. Redundant duplicate of an existing continuous input feature. |
| `provisional_ph_stress_risk_heuristic` | `int64` | 0 | 0.00% | Confounded Rule Label | Heuristic rule thresholded on `ph < 7.5` or `ph > 8.5`. Redundant transformation of an existing continuous input feature. |
| `provisional_severity_heuristic` | `object` | 0 | 0.00% | Circular Multi-Class Label | Categorical risk grade aggregating ammonia, DO, and mortality thresholds. Introduces severe target and label leakage. |
| `is_wq_in_range` | `object` | 0 | 0.00% | Operational Compliance Flag | Binary operator compliance field ("Yes"/"No") indicating whether all measured parameters satisfied thresholds. |
| `parameters_out_of_range` | `object` | 5,547 | 79.87% | Operational Compliance Flag | Text string explicitly naming out-of-range parameters (e.g., "Ammonia", "Dissolved Oxygen"). Directly leaks target breach events. |
| `provisional_behavioral_distress_observed` | `int64` | 0 | 0.00% | Clinical Symptom | Binary indicator of fish distress. A biological outcome of acute stress, not an environmental physical predictor. |
| `air_gulping_count` | `float64` | 1,792 | 25.80% | Clinical Symptom | Observed tally of fish gasping at the water surface due to acute branchial damage or anoxia. Downstream clinical symptom. |
| `tail_splashing_count` | `float64` | 1,790 | 25.77% | Clinical Symptom | Observed tally of erratic swimming behavior. Downstream symptom of central nervous systemic ammonia toxicity. |
| `dead_fish_count` | `float64` | 1,823 | 26.25% | Mortality Outcome | Mortality tally. Target variable for Experiment 2; excluded from inputs to prevent downstream outcome confounding. |
| `pond_id` | `object` | 0 | 0.00% | Spatial Grouping Key | Unique pond identifier. Preserved strictly for group splitting and longitudinal tracking; barred from $X$ to prevent farm memorization. |
| `datetime` | `datetime64` | 0 | 0.00% | Temporal Tracking Key | Sampling timestamp. Preserved strictly for chronological splitting and interval calculation; barred from $X$ to prevent temporal memorization. |
| `primary_calculated_nh3_mg_l` | `float64` | 0 | 0.00% | Target Variable | Continuous target variable for Experiment 1; cannot be present in the feature matrix $X$. |

---

## 3. TDS Outlier Investigation: Separation of Observed Evidence from Suspected Hypotheses

### 3.1 Observed Numerical & Physical Evidence
The dataset contains a column labeled `TDS (ppt)` with the following empirical properties:
- **Distribution Quantiles:**
  - Min: $0.010\text{ ppt}$
  - 25th Percentile: $0.880\text{ ppt}$
  - Median (50th): $1.160\text{ ppt}$
  - 75th Percentile: $1.860\text{ ppt}$
  - 90th Percentile: $3.780\text{ ppt}$
  - 99th Percentile: $8.790\text{ ppt}$
  - **Maximum:** **$936.000\text{ ppt}$**
- **Top 10 Highest Values:**
  - $936.0\text{ ppt}$ (Pond `ara2_20dd0295`, `2022-04-01 07:57`)
  - $923.0\text{ ppt}$ (Pond `ara2_bd32b7fb`, `2021-09-20 06:10`)
  - $795.0\text{ ppt}$ (Pond `ara2_a2d65cb4`, `2022-10-27 06:55`)
  - $795.0\text{ ppt}$ (Pond `ara2_bd32b7fb`, `2021-09-20 18:25`)
  - $781.0\text{ ppt}$ (Pond `ara2_01463d19`, `2022-10-17 07:10`)
  - $781.0\text{ ppt}$ (Pond `ara2_2d4cda6c`, `2022-10-17 17:17`)
  - $555.0\text{ ppt}$ (Pond `ara2_87661414`, `2022-10-17 17:43`)
  - $543.0\text{ ppt}$ (Pond `ara2_87661414`, `2022-10-27 07:58`)
  - $143.0\text{ ppt}$ (Pond `ara2_a0d5d74d`, `2023-12-15 06:36`)
  - $98.0\text{ ppt}$ (Pond `ara2_b77a0d03`, `2023-04-12 06:23`)
- **Physical Impossibility in Water:**  
  By standard definition, $1\text{ ppt} = 1\text{ g/kg} = 1,000\text{ mg/L} = 1,000\text{ ppm}$.  
  Typical freshwater pond water ranges between $0.1$ and $1.0\text{ ppt}$; brackish aquaculture water ranges between $1.0$ and $10.0\text{ ppt}$; ocean seawater is $\approx 35\text{ ppt}$; the Dead Sea is $\approx 300\text{ ppt}$; and saturated salt brine at $25^\circ\text{C}$ is $\approx 357\text{ ppt}$.  
  A reading of $936.0\text{ ppt}$ would imply that $93.6\%$ of the pond volume consists of solid dissolved mineral mass by weight, which is physically impossible in liquid water under ambient conditions.

### 3.2 Longitudinal Pond Observations
Tracking the time series of specific ponds surrounding these dates reveals isolated spikes:
- **Pond `ara2_20dd0295`:**
  - `2022-03-17`: $0.888\text{ ppt}$
  - `2022-04-01`: **$936.000\text{ ppt}$** *(isolated single-visit spike)*
  - `2022-04-18`: $1.398\text{ ppt}$
- **Pond `ara2_01463d19`:**
  - `2022-10-04`: $0.874\text{ ppt}$
  - `2022-10-17`: **$781.000\text{ ppt}$**
  - `2022-11-10`: $0.835\text{ ppt}$

### 3.3 Suspected Unit Mismatch Hypothesis (Unconfirmed)
- **The Hypothesis:** Handheld digital conductivity/TDS meters commonly output in parts per million ($\text{ppm} = \text{mg/L}$) for readings under $1,000\text{ ppm}$. It is widely suspected that field personnel recorded the meter's raw numerical display (e.g. $936$, $781$, $555$) directly into a form column whose header specified "TDS (ppt)", omitting the required division by $1,000$ ($936\text{ ppm} = 0.936\text{ ppt}$).
- **Status of Evidence:** **UNCONFIRMED HYPOTHESIS.** Because the original physical field notebook sheets, instrument manuals, and technician SOPs are unavailable, this unit mismatch explanation cannot be stated as a confirmed fact. It must remain labeled as an unverified operational hypothesis.
- **Handling Protocol:**
  - All raw values are maintained **strictly unmodified** in the data files.
  - In tree-based models (`RandomForestRegressor`), splits depend on rank order ($X_{\text{tds}} \le c$). Because monotonic rank order is preserved, extreme positive values are isolated into the upper split without corrupting decision boundaries across standard ranges ($0.1 - 10\text{ ppt}$).
  - In preprocessing pipelines, median imputation ($1.17\text{ ppt}$ in training) is employed rather than mean imputation ($3.62\text{ ppt}$) to prevent outlier distortion.

---

## 4. Missingness Pattern Analysis & 2025–2026 Temporal Regime Shift

### 4.1 Systematic Sensor Cessation Post-2024
A cross-tabulation of feature non-null counts by monitoring year uncovers an abrupt protocol shift in data collection:

| Sampling Year | Total Records | `tds_ppt` Present Count | `tds_ppt` Missing (%) | `turbidity_cm` Present Count | `turbidity_cm` Missing (%) |
| :---: | :---: | :---: | :---: | :---: | :---: |
| **2021** | 309 | 277 | 10.36% | 195 | 36.89% |
| **2022** | 1,431 | 1,339 | 6.43% | 1,423 | 0.56% |
| **2023** | 1,082 | 1,082 | **0.00%** | 1,076 | 0.55% |
| **2024** | 1,523 | 944 | 38.02% | 1,333 | 12.48% |
| **2025** | 1,563 | **0** | **100.00%** | **0** | **100.00%** |
| **2026** | 1,037 | **0** | **100.00%** | **0** | **100.00%** |

> [!WARNING]
> **OPERATIONAL IMPLICATION OF POST-2024 MISSINGNESS:**  
> - For the 2,600 records collected across 2025 and 2026, **neither TDS nor Turbidity was recorded** ($100\%$ missing).  
> - In any forward-looking operational deployment or chronological evaluation spanning 2025–2026, models utilizing `tds_ppt` and `turbidity_cm` will operate entirely on training-set median-imputed values.  
> - A model must be verified to ensure it degrades gracefully when these two physical features are absent.

### 4.2 Target Distribution Conditioned on Missingness
To verify whether missingness in these features is informative or biased relative to un-ionized ammonia toxicity:

| Feature | Missing Status | Row Count | Target Mean ($\text{NH}_3\text{ mg/L}$) | Target Median ($\text{NH}_3\text{ mg/L}$) |
| :--- | :---: | :---: | :---: | :---: |
| `tds_ppt` | **Missing** | 3,303 | $0.02120$ | $0.01625$ |
|  | **Present** | 3,642 | $0.02099$ | $0.00710$ |
| `turbidity_cm` | **Missing** | 2,918 | $0.01863$ | $0.01521$ |
|  | **Present** | 4,027 | $0.02287$ | $0.00886$ |

The global target mean is nearly identical between missing ($0.02120$) and present ($0.02099$) subsets for TDS. Missingness in TDS does not indicate a selective bias toward acute toxicity.

---

## 5. Summary & Verification Status

1. Exactly 8 features are selected for Experiment 1; all 19 other columns are audited and excluded.
2. The 936 ppt TDS outlier is documented with observed evidence separated from unconfirmed hypotheses.
3. The 100% missingness of TDS and Turbidity in 2025–2026 is fully quantified.
4. No data modification has been conducted; preprocessing pipelines will enforce leak-free imputation fitted strictly on training data.
