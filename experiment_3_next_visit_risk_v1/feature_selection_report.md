# Feature Selection & Anti-Leakage Report: Experiment 3 (Next-Visit Ammonia Risk)

**Date**: November 2026  
**Project**: AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Experiment Identifier**: `experiment_3_next_visit_risk_v1`  
**Dataset Analyzed**: Consecutive observation pairs constructed from [`processed_data_v2/toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv)  
**Evaluated Sample Size**: $N = 4,900$ valid temporal pairs ($3 \le \Delta t \le 45$ days) across 303 unique ponds  
**Target Variable**: Binary Next-Visit Ammonia Risk Flag ($y_{t+1}$): $314$ Positive ($6.41\%$), $4,586$ Negative ($93.59\%$)  

---

## 1. Selected Feature Inventory (12 Features)

For the next-visit ammonia toxicity risk prediction task, exactly **12 features** were selected. All 12 features represent environmental conditions, water chemistry, contextual observations, or scheduling metadata available strictly at or before the current sampling visit $t$.

| Feature Identifier | Time of Origin | Data Type | Missing Count ($N=4,900$) | Missing (%) | Min | Median | Mean | Max | Stated Unit | Biogeochemical & Operational Role in Long-Term Ammonia Accumulation |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :--- |
| `gap_days` | Known at visit $t$ | `float64` | 0 | 0.00% | 3.00 | 22.00 | 22.34 | 45.00 | $\text{days}$ | **Primary temporal modulator.** Governs elapsed microbial decomposition time, organic sludge accumulation, and uneaten feed breakdown between visits. |
| `curr_nh3` | Visit $t$ | `float64` | 0 | 0.00% | 0.0000 | 0.0134 | 0.0219 | 0.8387 | $\text{mg/L}$ | **Continuous chemical initial state.** Un-ionized ammonia concentration at visit $t$. Serves as continuous baseline condition for future risk. |
| `curr_do` | Visit $t$ | `float64` | 0 | 0.00% | 0.00 | 3.50 | 4.10 | 21.10 | $\text{mg/L}$ | Photosynthetic and aerobic health. Depleted oxygen suppresses nitrifying bacteria (*Nitrosomonas* and *Nitrobacter*), halting ammonia oxidation. |
| `curr_ph` | Visit $t$ | `float64` | 0 | 0.00% | 6.60 | 8.14 | 8.11 | 9.20 | pH scale | Chemical equilibrium driver ($\text{NH}_4^+ \rightleftharpoons \text{NH}_3 + \text{H}^+$). Higher pH drives greater molecular un-ionized toxicity. |
| `curr_temp` | Visit $t$ | `float64` | 0 | 0.00% | 21.40 | 29.10 | 28.84 | 35.60 | $^\circ\text{C}$ | Thermodynamic driver of equilibrium dissociation constant ($pK_a$) and bacterial metabolic rates. |
| `curr_turbidity` | Visit $t$ | `float64` | 1,845 | 37.65% | 0.00 | 29.00 | 29.08 | 89.00 | $\text{cm}$ | Secchi depth clarity. Low Secchi depths indicate dense phytoplankton blooms; senescent bloom collapse releases massive ammonia pulses. |
| `curr_tds` | Visit $t$ | `float64` | 2,121 | 43.29% | 0.01 | 1.17 | 3.55 | 936.00 | $\text{ppt}$ | Total dissolved solids capturing salinity, ionic strength, and osmoregulation dynamics. |
| `tds_is_missing` | Visit $t$ | `float64` | 0 | 0.00% | 0.0 | 0.0 | 0.433 | 1.0 | Binary | Informative missingness indicator capturing whether salinity/TDS testing was omitted by field technicians. |
| `turbidity_is_missing` | Visit $t$ | `float64` | 0 | 0.00% | 0.0 | 0.0 | 0.377 | 1.0 | Binary | Informative missingness indicator capturing whether Secchi disk clarity testing was omitted. |
| `curr_weather` | Visit $t$ | `object` | 179 | 3.65% | — | — | — | — | Categorical | Weather conditions (`Sunny`, `Cloudy`, `Rainy`, `Foggy`) modulating solar irradiance, photosynthesis, and convective water mixing. |
| `curr_color` | Visit $t$ | `object` | 205 | 4.18% | — | — | — | — | Categorical | Visual indicator of microalgal community composition (`Light green`, `Dark green`, `Saturated green`, `Brown`, etc.). |
| `region` | Metadata | `object` | 0 | 0.00% | — | — | — | — | Categorical | Geographical production zone (`Eluru` vs. `Nellore`) capturing regional climate, soil geochemistry, and baseline farm management practices. |

---

## 2. Itemized Audit of Excluded Features & Leakage Prevention

To guarantee strict temporal independence and prevent future outcome leakage, the following features were audited and barred from the model input matrix $X_t$:

| Excluded Variable Name | Time of Origin | Exclusion Classification | Technical & Scientific Reason for Exclusion |
| :--- | :---: | :---: | :--- |
| `next_risk` | Visit $t+1$ | **Target Variable** | The prediction target ($y_{t+1}$). Excluded from inputs to prevent trivial target identity leakage. |
| `next_nh3` | Visit $t+1$ | **Future Measurement** | Direct future calculated un-ionized ammonia measurement. Including this would allow the model to read the future outcome directly. |
| `next_datetime` | Visit $t+1$ | **Future Metadata** | Timestamp of next visit; used only to calculate `gap_days` and enforce temporal cutoff. |
| `curr_risk` | Visit $t$ | **Target Label Circularity** | The binary risk label at visit $t$. Excluded from the machine learning feature matrix to prevent label circularity and force models to learn from underlying physical and chemical features. Retained strictly as the operational input to the **Persistence Baseline**. |
| `curr_datetime` | Visit $t$ | **Temporal Tracking Key** | Sampling timestamp. Used strictly for chronological train/test partitioning and chronological sorting; barred from $X$ to prevent chronological memorization. |
| `pond_id` | Metadata | **Spatial Grouping Key** | Unique pond identifier. Used strictly as the grouping key for GroupKFold cross-validation; barred from $X$ to prevent farm memorization. |
| `raw_ammonia_tan_nh3_n_mg_l` | Visit $t$ | **Redundant Ammonia Pathway** | Raw TAN on nitrogen basis (monitored 2021–2024, missing in 2025–2026). Subsumed into `curr_nh3`. |
| `raw_ammonia_tan_nh3_mg_l` | Visit $t$ | **Redundant Ammonia Pathway** | Raw TAN on molecular basis (monitored 2025–2026, missing in 2021–2024). Subsumed into `curr_nh3`. |
| `reported_ammonia_nh3_unverified_mg_l` | Visit $t$ | **Unverified Ammonia Field** | Unverified raw field ammonia measurement; subsumed into `curr_nh3`. |
| `dead_fish_count` | Visit $t$ | **Biological Outcome** | Mortality tally; excluded to prevent biological confounding with water quality risk. |
| `air_gulping_count` | Visit $t$ | **Clinical Symptom** | Surface gasping behavior tally; clinical consequence, not an environmental predictive feature. |
| `tail_splashing_count` | Visit $t$ | **Clinical Symptom** | Erratic swimming behavior tally; clinical consequence, not an environmental predictive feature. |
| `provisional_severity_heuristic` | Visit $t$ | **Post-Hoc Heuristic Flag** | Post-hoc composite severity grade; barred to prevent rule-based circularity. |
| `is_wq_in_range` | Visit $t$ | **Post-Hoc Compliance Flag** | Operator audit compliance flag ("Yes"/"No"). |
| `parameters_out_of_range` | Visit $t$ | **Post-Hoc Compliance Flag** | Text string naming breached parameters. |

*Deliverable CSV*: [`feature_inventory.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_next_visit_risk_v1/metrics/feature_inventory.csv)

---

## 3. Preprocessing Pipeline Architecture

All feature preprocessing was implemented inside a unified `scikit-learn` `Pipeline` and fitted **strictly on training partitions only**:

1. **Continuous Predictors (`gap_days`, `curr_do`, `curr_ph`, `curr_temp`, `curr_turbidity`, `curr_tds`, `curr_nh3`)**:
   - `SimpleImputer(strategy='median')`: Missing values for turbidity and TDS are imputed using the training fold median.
   - `StandardScaler()`: Features are standardized to zero mean and unit variance for numerical stability in Logistic Regression.
2. **Missingness Indicator Predictors (`tds_is_missing`, `turbidity_is_missing`)**:
   - `SimpleImputer(strategy='constant', fill_value=0.0)`: Binary indicators pass through directly without numerical distortion.
3. **Categorical Predictors (`curr_weather`, `curr_color`, `region`)**:
   - `SimpleImputer(strategy='constant', fill_value='Missing')`: Missing categories are explicitly preserved as an informative `'Missing'` class level.
   - `OneHotEncoder(handle_unknown='ignore', sparse_output=False)`: Encodes categorical variables into binary dummy vectors while safely ignoring unseen levels during validation.

