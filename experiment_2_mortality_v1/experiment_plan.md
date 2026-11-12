# Experiment 2 Plan: Fish Mortality Classification

**Date**: November 2026  
**Project**: AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Experiment Identifier**: `experiment_2_mortality_v1`  
**Dataset Source**: [`processed_data_v2/toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv) ($N = 6,945$)  
**Target Variable**: Binary Mortality Occurrence:
$$\text{Target} = \begin{cases} 1 & \text{if } \text{dead\_fish\_count} > 0 \\ 0 & \text{if } \text{dead\_fish\_count} == 0 \end{cases}$$

---

## 1. Executive Summary & Objective

The objective of **Experiment 2** is to develop and rigorously benchmark machine learning classification models to predict the occurrence of fish mortality events at routine pond water-quality sampling visits. 

Fish mortality in commercial aquaculture represents an acute biological disaster resulting from environmental hypoxia, chemical toxicity (such as un-ionized ammonia), infectious pathogens, extreme pH swings, or management failures. This experiment evaluates whether routine physical, physicochemical, and contextual water-quality parameters alone carry sufficient predictive signal to anticipate mortality events across unseen ponds and subsequent production years.

---

## 2. Target Variable & Data Audit

### 2.1 Target Definition & Missingness Policy
- **Target Column**: `dead_fish_count` in `toxicity_analysis_v2.csv`.
- **Target Binary Transformation**: Positive class ($1$) if $\text{dead\_fish\_count} > 0$; Negative class ($0$) if $\text{dead\_fish\_count} == 0$.
- **Strict Exclusion of Unrecorded Observations**:
  - Across the 6,945 rows in `toxicity_analysis_v2.csv`, exactly **1,823 rows (26.25%)** have missing mortality counts (`NaN`).
  - An audit of data provenance confirms that during 2021 and 2022, farm technicians did not record dead fish tallies (100% missing in 2021 and 2022; 83 missing in early 2023). Regular mortality monitoring commenced in mid-2023.
  - **MANDATORY POLICY**: Missing mortality observations are **strictly excluded**, not zero-filled. Assuming unrecorded ponds had zero mortality would introduce severe historical bias and distort the true epidemiological baseline.
- **Evaluated Sample Size**: Exactly **$N = 5,122$** records.

### 2.2 Class Distribution & Imbalance
On the 5,122 evaluated records:
- **Negative Class ($0$, No Dead Fish Observed)**: $5,047\text{ records}$ ($98.54\%$)
- **Positive Class ($1$, Dead Fish Observed $> 0$)**: $75\text{ records}$ ($1.46\%$)
- **Class Imbalance Ratio**: **$67.29 : 1$** (Extreme class imbalance).

### 2.3 Distribution by Monitoring Year
| Monitoring Year | Raw Total Records | Missing Mortality | Evaluated Records | Negative Cases ($0$) | Positive Cases ($1$) | Positive Prevalence (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2021** | 309 | 309 | 0 | 0 | 0 | 0.00% |
| **2022** | 1,431 | 1,431 | 0 | 0 | 0 | 0.00% |
| **2023** | 1,082 | 83 | 999 | 982 | 17 | 1.70% |
| **2024** | 1,523 | 0 | 1,523 | 1,509 | 14 | 0.92% |
| **2025** | 1,563 | 0 | 1,563 | 1,534 | 29 | 1.86% |
| **2026** | 1,037 | 0 | 1,037 | 1,022 | 15 | 1.45% |
| **Total** | **6,945** | **1,823** | **5,122** | **5,047** | **75** | **1.46%** |

### 2.4 Distribution Across Ponds and Regions
- **Ponds Evaluated**: 286 unique ponds across the 5,122 evaluated rows.
- **Ponds with $\ge 1$ Positive Mortality Case**: **53 unique ponds** ($18.53\%$ of evaluated ponds).
  - 6 ponds experienced 3 mortality events.
  - 10 ponds experienced 2 mortality events.
  - 37 ponds experienced 1 mortality event.
  - 233 ponds experienced 0 mortality events ($81.47\%$).
- **Regional Breakdown**:
  - **Eluru**: 4,121 evaluated records, **73 positive cases** ($1.77\%$ prevalence).
  - **Nellore**: 1,001 evaluated records (monitored in 2023–2024), **2 positive cases** ($0.20\%$ prevalence).

---

## 3. Feature Space & Anti-Leakage Constraints

### 3.1 Selected Feature Inventory (11 Features)
Models are trained strictly on physical, physicochemical, and contextual features available at or before water sampling:
1. `dissolved_oxygen_mg_l` (continuous, DO in mg/L)
2. `ph` (continuous, pH scale)
3. `temp_c` (continuous, water temperature in °C)
4. `turbidity_cm` (continuous, Secchi disk visibility in cm)
5. `tds_ppt` (continuous, Total Dissolved Solids in ppt)
6. `tds_ppt_is_missing` (binary missingness indicator)
7. `turbidity_cm_is_missing` (binary missingness indicator)
8. `Weather` (categorical: Sunny, Cloudy, Rainy, Foggy)
9. `water_color` (categorical: Light green, Dark green, Saturated green, Brown, etc.)
10. `region` (categorical: Eluru, Nellore)
11. `primary_calculated_nh3_mg_l` (continuous, calculated un-ionized ammonia in mg/L; key environmental toxicant)

### 3.2 Strictly Excluded Features
To prevent methodological failure, data leakage, and post-hoc outcome confounding, the following categories are strictly barred:
- **Direct Target Source**: `dead_fish_count` (the raw outcome).
- **Clinical Behavioral Symptoms**: `air_gulping_count`, `tail_splashing_count`, and `provisional_behavioral_distress_observed`. These are clinical symptoms of dying fish (respiratory gasping and central nervous distress). Including them causes downstream symptom leakage rather than environmental prediction.
- **Post-Hoc Heuristic Compliance Flags**: `provisional_severity_heuristic` (which directly bins dead fish count into categories), `provisional_hypoxia_risk_heuristic`, `provisional_ph_stress_risk_heuristic`, `provisional_ammonia_risk_heuristic`, `is_wq_in_range`, and `parameters_out_of_range`.
- **Spatial & Temporal Identifiers**: `pond_id` and `datetime` are barred from the feature matrix $X$ to prevent memorization of specific farms or dates.

---

## 4. Dual Validation Strategy

### 4.1 Protocol 1: 5-Fold GroupKFold by `pond_id` (Spatial Generalization)
- **Goal**: Evaluate out-of-fold generalization to completely unseen ponds.
- **Grouping**: Grouped strictly on `pond_id`.
- **Constraint**: Strict verification that $\text{Ponds}_{\text{train}} \cap \text{Ponds}_{\text{val}} = \emptyset$ in all 5 folds.
- **Positive Allocation**: Each fold contains between 12 and 18 positive cases, ensuring every validation fold has statistical support.

### 4.2 Protocol 2: Chronological Holdout (Temporal Generalization)
- **Goal**: Evaluate generalization across future years (2025–2026) using models trained strictly on historical data (2021–2024).
- **Temporal Cutoff**: `2025-01-01 00:00:00`.
- **Training Set (2021–2024 Evaluated)**: $N = 2,522$ records, **31 positive cases** ($1.23\%$).
- **Test Set (2025–2026 Evaluated)**: $N = 2,600$ records, **44 positive cases** ($1.69\%$).
- **Strict Protocol**: Preprocessing pipelines (imputers, scalers, encoders) fitted strictly on the training partition. **Zero tuning on the chronological test set**.

---

## 5. Candidate Baselines & Machine Learning Models

### 5.1 Baseline 2.1: Dummy Classifier (`Dummy_Prior`)
- Always predicts probabilities equal to training class prevalence and predicts the majority class ($0$).
- Establishes the no-skill baseline ($\text{PR-AUC} = 0.0169$, $\text{Recall} = 0.0$).

### 5.2 Model 2.2: Logistic Regression (`Logistic_Regression`)
- Linear baseline with inverse class weighting (`class_weight='balanced'`).
- StandardScaler applied to continuous features; median imputation for numericals; OneHotEncoder for categoricals.

### 5.3 Model 2.3: Random Forest Classifier (`Random_Forest`)
- Non-linear ensemble baseline (100 estimators, `min_samples_leaf=5`, `class_weight='balanced'`).
- Handles complex non-linear interactions between temperature, dissolved oxygen, pH, and ammonia.

---

## 6. Evaluation Metrics

Because the target exhibits a $67 : 1$ class imbalance, **Accuracy is barred from primary decision-making** (a naive model predicting all zeros achieves $98.54\%$ accuracy while missing $100\%$ of mortalities).

Models are evaluated on:
1. **PR-AUC (Average Precision)**: Primary metric for imbalanced classification.
2. **Recall (Sensitivity)**: Proportion of true mortality events detected ($\frac{\text{TP}}{\text{TP} + \text{FN}}$).
3. **Precision (Positive Predictive Value)**: Proportion of mortality alarms that are genuine ($\frac{\text{TP}}{\text{TP} + \text{FP}}$).
4. **F1-Score**: Harmonic mean of Precision and Recall.
5. **Confusion Matrix**: Full tally of $\text{TP}, \text{FP}, \text{FN}, \text{TN}$.
6. **ROC-AUC**: Secondary discrimination metric.

