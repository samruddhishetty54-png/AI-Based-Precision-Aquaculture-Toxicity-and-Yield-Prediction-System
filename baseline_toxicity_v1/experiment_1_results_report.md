# Experiment 1 Results Report: Soft-Sensor Ammonia Estimation

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Experiment Identifier:** `baseline_toxicity_v1` (Experiment 1 Only)  
**Execution Date:** 2026-11-03  
**Status:** **TRAINED, EVALUATED, AND FULLY AUDITED**  
**Serialized Model Artifact:** [`baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib)  
**Evaluation Metrics CSV:** [`baseline_toxicity_v1/metrics/experiment_1_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/metrics/experiment_1_metrics.csv)  
**Subgroup Metrics CSV:** [`baseline_toxicity_v1/metrics/experiment_1_subgroup_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/metrics/experiment_1_subgroup_metrics.csv)  
**Feature Importances CSV:** [`baseline_toxicity_v1/metrics/experiment_1_feature_importances.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/metrics/experiment_1_feature_importances.csv)  

---

## 1. Executive Summary & Core Scientific Findings

Experiment 1 evaluates whether machine learning models can function as an **indirect soft-sensor** to estimate un-ionized ammonia ($\text{NH}_3$) from routinely measured non-ammonia physical and physicochemical parameters.

> [!CAUTION]
> **CRITICAL SCIENTIFIC DEFINITION:**  
> The target variable `primary_calculated_nh3_mg_l` is a **calculated aqueous chemical equilibrium proxy** derived from field Total Ammonia Nitrogen (TAN), pH, and water temperature using the Emerson et al. aqueous chemical equilibrium equation with stoichiometric molecular-weight adjustment ($17.031 / 14.007$). It is **not** an independently measured analytical chemistry laboratory standard (such as ion chromatography) and **must not be claimed as an independently validated biological toxicity prediction**.

### Summary of Primary Findings:
1. **Substantial ML Lift Under Spatial Validation (GroupKFold):**  
   Under 5-fold `GroupKFold` by `pond_id` (evaluating spatial generalization to unseen ponds, $N = 6,945$), the full `RandomForestRegressor` achieves:
   - **$R^2 = 0.5007$** (vs. $0.1436$ for the pH+Temp ablation and $-0.0027$ for Dummy Mean).
   - **$\text{MAE} = 0.01396\text{ mg/L}$** (a **$23.9\%$ error reduction** over the pH+Temp ablation and $30.6\%$ over Dummy Mean).
   - **$\text{RMSE} = 0.02991\text{ mg/L}$** (a **$23.7\%$ error reduction** over ablation).
   - This proves that non-chemical ecosystem features (`dissolved_oxygen_mg_l`, `water_color`, `turbidity_cm`, `Weather`, `tds_ppt`, `region`) provide substantial predictive power beyond simple thermodynamic equilibrium guessing.
2. **Telemetry Loss Causes Temporal Generalization Failure (Chronological Holdout):**  
   Under chronological holdout (trained on 2021–2024, evaluated on 2025–2026, $N = 2,600$), Random Forest performance collapses to **$R^2 = -0.2983$** ($\text{MAE} = 0.01970$, $\text{RMSE} = 0.03133$).
3. **Root Cause of Temporal Degradation Identified:**  
   Feature importance audits show that `tds_ppt` accounts for **$20.64\%$ of the model's total predictive weight** (the second most important feature after pH). In 2025–2026, field operations permanently discontinued both TDS and Turbidity testing ($100\%$ missing). When evaluated on 2025–2026 with synthetic median constants, the model lost nearly one-quarter of its primary decision signal, causing out-of-sample predictions to scatter worse than the historical mean.

---

## 2. Experimental Setup & Configuration

### 2.1 Feature Set
The model was trained strictly on 8 non-ammonia features plus 2 explicit missingness indicators:
- **Continuous Features (5):** `dissolved_oxygen_mg_l`, `ph`, `temp_c`, `turbidity_cm`, `tds_ppt`.
- **Missingness Indicator Features (2):** `tds_ppt_is_missing`, `turbidity_cm_is_missing` (1.0 if missing, 0.0 if measured).
- **Categorical Features (3):** `Weather`, `water_color`, `region` (`Eluru`, `Nellore`).

### 2.2 Leakage Elimination Verification
- All raw ammonia columns (`raw_ammonia_tan_nh3_n_mg_l`, `raw_ammonia_tan_nh3_mg_l`, `reported_ammonia_nh3_unverified_mg_l`) were strictly excluded.
- All intermediate calculation components (`calculated_nh3_from_tan_n_mg_l`, `calculated_nh3_from_tan_nh3_mg_l`, `nh3_calculation_source`) were strictly excluded.
- All provisional heuristic risk and severity labels (`provisional_ammonia_risk_heuristic`, `provisional_hypoxia_risk_heuristic`, `provisional_ph_stress_risk_heuristic`, `provisional_severity_heuristic`, `is_wq_in_range`, `parameters_out_of_range`) were strictly excluded.
- All clinical symptoms and pond/date identifiers were barred from the feature matrix $X$.

### 2.3 Preprocessing Pipeline Design
- **Pipeline Architecture:** `ColumnTransformer` encapsulating:
  - Continuous features $\rightarrow$ `SimpleImputer(strategy='median')`
  - Missingness indicators $\rightarrow$ `SimpleImputer(strategy='constant', fill_value=0.0)`
  - Categorical features $\rightarrow$ `SimpleImputer(strategy='constant', fill_value='Missing')` followed by `OneHotEncoder(handle_unknown='ignore', sparse_output=False)`
- **Leak-Free Enforcement:** Preprocessing was fitted strictly inside each training fold during cross-validation, and fitted strictly on 2021–2024 data for the chronological holdout. Imputers never accessed test-set statistics. Zero-filling was strictly prohibited.

---

## 3. Protocol A: 5-Fold GroupKFold Evaluation (Spatial Generalization)

Evaluates model performance across 317 independent aquaculture ponds ($N = 6,945$). In each fold, all observations from validation ponds are completely withheld from training.

### 3.1 Per-Fold & Cross-Validation Summary

| Model Identifier | Model Description | Fold 1 $R^2$ | Fold 2 $R^2$ | Fold 3 $R^2$ | Fold 4 $R^2$ | Fold 5 $R^2$ | Mean $R^2 \pm \text{Std}$ | Mean MAE ($\text{mg/L}$) | Mean RMSE ($\text{mg/L}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `Dummy_Mean` | Predicts training mean | -0.010 | -0.012 | -0.007 | -0.026 | +0.007 | $-0.009 \pm 0.010$ | $0.02013 \pm 0.0016$ | $0.04160 \pm 0.0091$ |
| `Dummy_Median` | Predicts training median | -0.054 | -0.058 | -0.052 | -0.093 | -0.010 | $-0.053 \pm 0.025$ | $0.01837 \pm 0.0023$ | $0.04255 \pm 0.0097$ |
| `Ablation_pH_Temp` | RF on `ph` + `temp_c` only | +0.134 | -0.347 | +0.278 | +0.219 | -0.002 | $+0.057 \pm 0.281$ | $0.01835 \pm 0.0012$ | $0.03896 \pm 0.0046$ |
| **`Random_Forest`** | **Full 8-Feature Pipeline** | **+0.559** | **+0.329** | **+0.537** | **+0.602** | **+0.442** | **$+0.494 \pm 0.105$** | **$0.01396 \pm 0.0019$** | **$0.02932 \pm 0.0066$** |

### 3.2 Global Out-of-Fold (OOF) Performance ($N = 6,945$)
Aggregating predictions across all 5 test folds to form a complete out-of-fold benchmark:

| Model | OOF MAE ($\text{mg/L}$) | OOF RMSE ($\text{mg/L}$) | OOF $R^2$ | Lift vs. Dummy Median MAE | Lift vs. Ablation $R^2$ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `Dummy_Mean` | 0.02013 | 0.04239 | -0.0027 | Baseline | Baseline |
| `Dummy_Median` | 0.01837 | 0.04343 | -0.0523 | Reference (0.0%) | — |
| `Ablation_pH_Temp` | 0.01835 | 0.03918 | +0.1436 | +0.1% | Reference ($0.1436$) |
| **`Random_Forest` (Full)** | **0.01396** | **0.02991** | **+0.5007** | **+24.0%** | **+0.3571 ($3.5\times$ lift)** |

**Key GroupKFold Insights:**
- **Consistent Superiority:** Random Forest outperformed every baseline across **all 5 individual folds**.
- **Significant Signal Beyond Chemistry:** The pH + temperature ablation baseline explains only $14.36\%$ of the global variance ($R^2 = 0.1436$), confirming that knowing water temperature and pH is insufficient to deduce un-ionized ammonia concentration. Adding dissolved oxygen, water color, turbidity, TDS, weather, and region lifts explained variance to **$50.07\%$**, demonstrating genuine environmental soft-sensing capability.

---

## 4. Protocol B: Chronological Holdout Evaluation (Temporal Generalization)

Evaluates temporal forecasting and concept drift by training strictly on historical seasons (2021–2024, $N = 4,345$, 239 ponds) and testing strictly on future production cycles (2025–2026, $N = 2,600$, 176 ponds).

### 4.1 Chronological Test Performance Benchmarks ($N = 2,600$)

| Model Identifier | Model Description | Test MAE ($\text{mg/L}$) | Test RMSE ($\text{mg/L}$) | Test $R^2$ | Evaluation Assessment |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `Dummy_Mean` | Historical train mean ($0.0223\text{ mg/L}$) | 0.01574 | 0.02784 | -0.0252 | Least-squares baseline |
| `Dummy_Median` | Historical train median ($0.0125\text{ mg/L}$) | 0.01517 | 0.02896 | -0.1094 | Best unlearned MAE |
| `Ablation_pH_Temp` | RF on historical `ph` + `temp_c` | 0.01591 | 0.02817 | -0.0499 | Marginally worse than mean |
| **`Random_Forest`** | **Full Feature Model** | **0.01970** | **0.03133** | **-0.2983** | **Severely Degraded (Negative $R^2$)** |

### 4.2 Forensic Diagnosis: Why Did Chronological Generalization Fail?
The negative $R^2$ ($-0.2983$) is an authentic, critical finding that must be reported transparently. Three compounding factors explain this result:

1. **Protocol Shift & Sensor Elimination (The Primary Culprit):**  
   In 2025–2026, field operations completely terminated Secchi disk turbidity and handheld TDS testing. For all 2,600 test records, `tds_ppt` and `turbidity_cm` are **$100\%$ missing**. During 2021–2024 training, the tree model learned strong split boundaries on TDS (Gini importance $20.6\%$) and Turbidity ($3.5\%$). When presented with constant median imputations ($1.17\text{ ppt}$ and $29.0\text{ cm}$), the decision trees executed sub-optimal branch partitions, causing predictions to drift.
2. **Target Distribution Shift Between Historical and Modern Epochs:**  
   - Historical Training Target (2021–2024): $\text{Mean} = 0.0223\text{ mg/L}$, $\text{Std} = 0.0450\text{ mg/L}$, $\text{Median} = 0.0125\text{ mg/L}$.
   - Modern Testing Target (2025–2026): $\text{Mean} = 0.0191\text{ mg/L}$, $\text{Std} = 0.0275\text{ mg/L}$, $\text{Median} = 0.0104\text{ mg/L}$.  
   The variance in the test set is $38.9\%$ lower than in training. Because the denominator of $R^2$ ($\sum (y - \bar{y}_{\text{test}})^2$) is small, minor prediction offsets from the historical baseline produce an inflated negative $R^2$.
3. **Assay Reagent Transition:**  
   As documented in the scientific consistency report, 2021–2024 was measured exclusively with nitrogen-basis TAN kits (Source 1), whereas 2026 switched entirely to molecular TAN kits (Source 2). Subtle calibration differences between test kit vendors propagate into the calculated target.

---

## 5. Subgroup Analysis: Measured vs. Imputed Telemetry

To confirm whether missing sensor telemetry drives model performance, we audit out-of-fold performance partitioned by whether physical sensors were actively measured or missing:

| Dataset Partition | Telemetry Subgroup | Record Count ($N$) | Target Mean ($\text{mg/L}$) | RF MAE ($\text{mg/L}$) | RF RMSE ($\text{mg/L}$) | **RF $R^2$** |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Global OOF** | **TDS Actively Measured** | **3,642** | **0.02099** | **0.01341** | **0.03230** | **+0.5850** |
| Global OOF | TDS Missing (Imputed) | 3,303 | 0.02120 | 0.01457 | 0.02704 | +0.2660 |
| **Global OOF** | **Turbidity Actively Measured** | **4,027** | **0.02287** | **0.01388** | **0.03202** | **+0.5982** |
| Global OOF | Turbidity Missing (Imputed) | 2,918 | 0.01863 | 0.01408 | 0.02674 | **+0.0262** |
| Chrono Train (In-Sample) | TDS Measured | 3,642 | 0.02244 | 0.00611 | 0.01601 | +0.8981 |
| Chrono Train (In-Sample) | TDS Missing | 703 | 0.02157 | 0.00784 | 0.01487 | +0.8733 |

### Subgroup Insights:
- **Telemetry Completeness Determines Predictability:** When Turbidity is actively measured, Random Forest explains **$59.82\%$ of the variance** ($R^2 = 0.5982$). When Turbidity is missing, explained variance collapses to **$2.62\%$** ($R^2 = 0.0262$).
- **Evidence of Sensor Value:** This proves that physical water clarity (algal bloom density) and electrical conductivity provide essential predictive signals. A soft sensor deployed without these instruments suffers severe degradation.

---

## 6. Feature Importance Audit

Extracting Gini impurity importance from the Random Forest pipeline fitted on 2021–2024 data:

| Rank | Feature Identifier | Feature Type | Gini Importance | Cumulative Importance | Biogeochemical Interpretation |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | `ph` | Continuous Numeric | **40.03%** | 40.03% | Primary thermodynamic driver of ammonia-ammonium equilibrium. |
| **2** | `tds_ppt` | Continuous Numeric | **20.64%** | 60.67% | Salinity, ionic strength, and mineral feed accumulation. |
| **3** | `temp_c` | Continuous Numeric | **14.35%** | 75.02% | Dissociation constant ($pK_a$) temperature dependence. |
| **4** | `dissolved_oxygen_mg_l` | Continuous Numeric | **6.31%** | 81.33% | Algal photosynthesis and respiration dynamics. |
| **5** | `region_Eluru` | One-Hot Categorical | **4.63%** | 85.96% | Regional water source and baseline soil chemistry. |
| **6** | `turbidity_cm` | Continuous Numeric | **3.46%** | 89.42% | Secchi clarity proxy for phytoplankton biomass. |
| **7** | `region_Nellore` | One-Hot Categorical | **2.97%** | 92.39% | Regional coastal vs. inland farm cluster. |
| **8** | `water_color_Light green` | One-Hot Categorical | **1.84%** | 94.23% | Phytoplankton bloom density proxy. |
| **9** | `Weather_Sunny` | One-Hot Categorical | **1.34%** | 95.57% | Solar irradiance driving diurnal algae cycles. |
| **10** | `tds_ppt_is_missing` | Binary Indicator | **0.85%** | 96.42% | Sensor availability indicator. |
| **11–45**| Other categorical levels | One-Hot Categorical | **3.58%** | 100.00% | Secondary weather and water hue categories. |

---

## 7. Generated Visualizations & Diagnostic Plots

All plots were generated and saved with high resolution (300 DPI) inside [`baseline_toxicity_v1/plots/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/plots/):

1. **[`actual_vs_predicted_groupkfold.png`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/plots/actual_vs_predicted_groupkfold.png):**  
   Shows 5-fold cross-validated out-of-fold predictions. Random Forest tracks the 1:1 identity line across $0.00 - 0.20\text{ mg/L}$, substantially outperforming the horizontal line of the pH+Temp ablation.
2. **[`residuals_groupkfold.png`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/plots/residuals_groupkfold.png):**  
   Residual plot showing centered errors around zero with moderate positive heteroscedasticity above $0.30\text{ mg/L}$ (rare extreme spikes).
3. **[`actual_vs_predicted_chronological.png`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/plots/actual_vs_predicted_chronological.png):**  
   Illustrates prediction behavior on the 2025–2026 test set. Shows under-prediction of high-end events and upward drift due to static median imputation of TDS.
4. **[`residuals_chronological.png`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/plots/residuals_chronological.png):**  
   Visualizes the systematic negative bias on recent production cycles.
5. **[`feature_importances.png`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/plots/feature_importances.png):**  
   Horizontal bar chart ranking the top 15 features, highlighting the dominance of pH ($40.0\%$), TDS ($20.6\%$), and temperature ($14.4\%$).

---

## 8. Honest Limitations & Scientific Conclusions

### 8.1 What Experiment 1 Proves:
1. **Spatial Feasibility Confirmed:** When water-quality probes (DO, pH, Temp, Turbidity, TDS) are operational, a non-linear machine learning model can predict calculated un-ionized ammonia with **$R^2 = 0.50 - 0.60$** across completely unseen aquaculture farms, reducing error by $24\%$ over simple thermodynamic equations.
2. **Ecosystem Feature Contribution:** Dissolved oxygen, Secchi clarity, and salinity are not redundant; they capture the organic loading and algal dynamics that drive nitrogen mineralization in pond ecosystems.

### 8.2 What Experiment 1 Does NOT Prove:
1. **No Proof of Biological Toxicity Prediction:** Because the target is derived from field TAN kits using Emerson's formula, good performance demonstrates **mathematical proxy approximation**, not direct biological mortality or fish physiological stress prediction.
2. **No Robustness to Sensor Deprecation:** The model is highly vulnerable to telemetry loss. Discontinuing TDS testing in 2025 destroyed chronological forecasting performance. Soft-sensors must not be deployed in operations that omit electrical conductivity or clarity testing without retuning.

---

## 9. Deliverable Verification Manifest

| File Path | File Description | Status |
| :--- | :--- | :---: |
| [`baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib) | Serialized full pipeline (Preprocessor + RF) | Generated |
| [`baseline_toxicity_v1/metrics/experiment_1_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/metrics/experiment_1_metrics.csv) | Full metrics table (GroupKFold per fold, OOF, Chrono) | Generated |
| [`baseline_toxicity_v1/metrics/experiment_1_subgroup_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/metrics/experiment_1_subgroup_metrics.csv) | Subgroup metrics (Measured vs. Missing TDS/Turbidity) | Generated |
| [`baseline_toxicity_v1/metrics/experiment_1_feature_importances.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/metrics/experiment_1_feature_importances.csv) | Itemized Gini feature importances across all 45 inputs | Generated |
| [`baseline_toxicity_v1/plots/*.png`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/plots/) | 5 diagnostic plots (Actual vs Pred, Residuals, FI) | Generated |
| [`baseline_toxicity_v1/experiment_1_results_report.md`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/experiment_1_results_report.md) | Comprehensive experiment report (this file) | Generated |
| **Experiments 2 & 3** | Not trained (strictly deferred per scope) | Compliant |
| **Source Datasets** | Unmodified and preserved | Compliant |

