# Feature Selection & Data Inspection Report: Experiment 2 (Mortality Classification)

**Date**: November 2026  
**Project**: AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Experiment Identifier**: `experiment_2_mortality_v1`  
**Dataset Analyzed**: [`processed_data_v2/toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv) ($N = 6,945$, 27 columns)  
**Evaluated Sample Size**: $N = 5,122$ records (1,823 missing mortality records strictly excluded)  
**Target Variable**: Binary Mortality Flag derived from `dead_fish_count > 0` ($75$ positive, $5,047$ negative)  

---

## 1. Selected Feature Inventory

For the mortality classification task, exactly **11 features** were selected. These comprise 6 continuous water quality and chemical parameters, 2 binary missingness indicators, and 3 categorical contextual variables. All 11 features represent environmental and operational measurements available at the time of water sampling, prior to post-hoc biological evaluations.

| Feature Identifier | Data Type | Missing Count (Eval $N=5,122$) | Missing (%) | Min | Median (50%) | Mean | Max | Stated Unit | Biological & Environmental Role in Aquaculture Mortality |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `dissolved_oxygen_mg_l` | `float64` | 0 | 0.00% | 0.00 | 3.50 | 3.74 | 21.10 | $\text{mg/L}$ | **Primary mortality driver.** Acute hypoxia ($< 2.0\text{ mg/L}$) suffocates shrimp and fish, impairing cardiac function and cellular respiration. |
| `ph` | `float64` | 0 | 0.00% | 6.60 | 8.15 | 8.13 | 9.20 | pH scale | Direct chemical modulator of un-ionized ammonia equilibrium; extreme acidosis ($< 7.0$) or alkalosis ($> 9.0$) causes gill epithelial necrosis. |
| `temp_c` | `float64` | 0 | 0.00% | 21.40 | 28.90 | 28.60 | 35.60 | $^\circ\text{C}$ | Metabolic accelerator; increases oxygen consumption, accelerates bacterial proliferation, and increases ammonia toxicity via thermodynamic dissociation. |
| `primary_calculated_nh3_mg_l` | `float64` | 0 | 0.00% | 0.0000 | 0.0157 | 0.0210 | 0.8387 | $\text{mg/L}$ | **Primary chemical toxicant.** Un-ionized ammonia passes freely across gill membranes, inducing central nervous systemic toxicity and convulsions. |
| `turbidity_cm` | `float64` | 1,109 | 21.65% | 0.00 | 29.00 | 29.13 | 89.00 | $\text{cm}$ | Secchi depth clarity. Low Secchi depths indicate dense cyanobacterial blooms or suspended clay; sudden collapse signals mass phytoplankton mortality. |
| `tds_ppt` | `float64` | 1,544 | 30.14% | 0.01 | 1.21 | 2.27 | 143.00 | $\text{ppt}$ | Total Dissolved Solids reflecting salinity, osmoregulation stress, and ionic balance. |
| `tds_ppt_is_missing` | `float64` | 0 | 0.00% | 0.0 | 0.0 | 0.301 | 1.0 | Binary | Informative missingness indicator capturing whether salinity/TDS testing was omitted by field technicians. |
| `turbidity_cm_is_missing` | `float64` | 0 | 0.00% | 0.0 | 0.0 | 0.217 | 1.0 | Binary | Informative missingness indicator capturing whether Secchi disk clarity testing was omitted. |
| `Weather` | `object` | 237 | 4.63% | — | — | — | — | Categorical | Weather conditions (`Sunny`, `Cloudy`, `Rainy`, `Foggy`) modulating solar irradiance, photosynthesis, and convective water mixing. |
| `water_color` | `object` | 267 | 5.21% | — | — | — | — | Categorical | Visual indicator of microalgal community composition (`Light green`, `Dark green`, `Saturated green`, `Brown`, etc.). |
| `region` | `object` | 0 | 0.00% | — | — | — | — | Categorical | Geographical production zone (`Eluru` vs. `Nellore`) capturing regional climate, soil geochemistry, and baseline farm management practices. |

---

## 2. Itemized Audit of Excluded Features

To ensure strict scientific rigor and avoid circularity, data leakage, or clinical symptom confounding, all non-selected columns from `processed_data_v2/toxicity_analysis_v2.csv` were audited and excluded.

The table below documents every excluded column, its raw missing count, and the technical rationale for its exclusion:

| Excluded Column Name | Data Type | Missing Count (Raw $N=6,945$) | Missing (%) | Exclusion Classification | Technical & Scientific Rationale for Exclusion |
| :--- | :---: | :---: | :---: | :--- | :--- |
| `dead_fish_count` | `float64` | 1,823 | 26.25% | **Target Source** | **Direct Target Leakage.** The binary classification target is defined as $\text{dead\_fish\_count} > 0$. Retaining this column would result in direct identity leakage. |
| `air_gulping_count` | `float64` | 1,792 | 25.80% | **Clinical Symptom Leakage** | **Downstream Behavioral Distress Symptom.** Surface air gulping is a terminal clinical response to branchial damage, acute hypoxia, or severe ammonia poisoning. Including behavioral symptoms would allow the model to predict mortality from symptoms of dying fish rather than from environmental water quality. |
| `tail_splashing_count` | `float64` | 1,790 | 25.77% | **Clinical Symptom Leakage** | **Downstream Behavioral Distress Symptom.** Erratic swimming and violent surface splashing represent acute neurotoxic distress. Excluded to prevent clinical outcome leakage. |
| `provisional_behavioral_distress_observed` | `int64` | 0 | 0.00% | **Clinical Symptom Leakage** | Binary flag aggregating observed fish distress behaviors (`air_gulping_count > 0` or `tail_splashing_count > 0`). Downstream consequence, not an environmental predictor. |
| `provisional_severity_heuristic` | `object` | 0 | 0.00% | **Direct Circular Label Leakage** | **Severe Target Leakage.** This heuristic rule label explicitly incorporates `dead_fish_count > 0` to assign high and critical risk grades. Including it would allow the model to cheat by reading the target encoded in the label. |
| `provisional_hypoxia_risk_heuristic` | `int64` | 0 | 0.00% | **Confounded Heuristic Rule** | Heuristic rule thresholded on $\text{DO} \le 3.0\text{ mg/L}$. Redundant transformation of the continuous `dissolved_oxygen_mg_l` input feature. |
| `provisional_ph_stress_risk_heuristic` | `int64` | 0 | 0.00% | **Confounded Heuristic Rule** | Heuristic rule thresholded on $\text{pH} < 7.5$ or $\text{pH} > 8.5$. Redundant transformation of the continuous `ph` input feature. |
| `provisional_ammonia_risk_heuristic` | `int64` | 0 | 0.00% | **Confounded Heuristic Rule** | Binary flag thresholded on $\text{NH}_3 \ge 0.05\text{ mg/L}$. Redundant duplicate of `primary_calculated_nh3_mg_l`. |
| `is_wq_in_range` | `object` | 0 | 0.00% | **Operational Post-Hoc Flag** | Operator audit flag ("Yes"/"No") indicating compliance across all parameters. Post-hoc summary flag. |
| `parameters_out_of_range` | `object` | 5,547 | 79.87% | **Operational Post-Hoc Flag** | Text field explicitly listing out-of-range parameters (e.g., "Ammonia", "Dissolved Oxygen"). Redundant post-hoc indicator. |
| `pond_id` | `object` | 0 | 0.00% | **Identifier / Group Key** | Unique pond identifier. Used strictly as the grouping key for GroupKFold to enforce spatial cross-validation; barred from feature matrix $X$ to prevent farm memorization. |
| `datetime` | `datetime64` | 0 | 0.00% | **Identifier / Temporal Key** | Sampling timestamp. Used strictly for chronological partitioning and temporal alignment; barred from feature matrix $X$ to prevent chronological memorization. |
| `raw_ammonia_tan_nh3_n_mg_l` | `float64` | 1,658 | 23.87% | **Redundant Ammonia Pathway** | Raw TAN on nitrogen basis (monitored 2021–2024, missing in 2025–2026). Subsumed into the standardized `primary_calculated_nh3_mg_l` feature. |
| `raw_ammonia_tan_nh3_mg_l` | `float64` | 5,286 | 76.11% | **Redundant Ammonia Pathway** | Raw TAN on molecular basis (monitored 2025–2026, missing in 2021–2024). Subsumed into `primary_calculated_nh3_mg_l`. |
| `reported_ammonia_nh3_unverified_mg_l` | `float64` | 5,285 | 76.10% | **Unverified Ammonia Field** | Unverified raw field ammonia measurement. Subsumed into `primary_calculated_nh3_mg_l`. |
| `calculated_nh3_from_tan_n_mg_l` | `float64` | 1,658 | 23.87% | **Intermediate Pathway** | Intermediate calculation pathway from TAN-N; subsumed into `primary_calculated_nh3_mg_l`. |
| `calculated_nh3_from_tan_nh3_mg_l` | `float64` | 5,286 | 76.11% | **Intermediate Pathway** | Intermediate calculation pathway from TAN-NH3; subsumed into `primary_calculated_nh3_mg_l`. |
| `nh3_calculation_source` | `object` | 0 | 0.00% | **Ammonia Metadata Flag** | Categorical flag identifying calculation formula; excluded to prevent formula-cohort confounding. |

*Deliverable CSV*: [`feature_inventory.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_2_mortality_v1/metrics/feature_inventory.csv)

---

## 3. Preprocessing and Imputation Architecture

To eliminate data leakage, all preprocessing components are encapsulated within an end-to-end `scikit-learn` `Pipeline` and fitted strictly on training data:

1. **Continuous Features (`dissolved_oxygen_mg_l`, `ph`, `temp_c`, `turbidity_cm`, `tds_ppt`, `primary_calculated_nh3_mg_l`)**:
   - `SimpleImputer(strategy='median')`: Imputes missing turbidity and TDS using the training fold medians.
   - `StandardScaler()`: Standardizes features to zero mean and unit variance for numerical stability in Logistic Regression.
2. **Missingness Indicator Features (`tds_ppt_is_missing`, `turbidity_cm_is_missing`)**:
   - `SimpleImputer(strategy='constant', fill_value=0.0)`: Passes through binary missingness flags without transformation.
3. **Categorical Features (`Weather`, `water_color`, `region`)**:
   - `SimpleImputer(strategy='constant', fill_value='Missing')`: Labels missing weather and water color observations explicitly as a distinct categorical level.
   - `OneHotEncoder(handle_unknown='ignore', sparse_output=False)`: Encodes categorical variables while ignoring previously unseen categories during validation.

