# Data Split Summary: Experiment 2 (Mortality Classification)

**Date**: November 2026  
**Project**: AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Experiment Identifier**: `experiment_2_mortality_v1`  
**Dataset Analyzed**: [`processed_data_v2/toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv)  
**Evaluated Sample Size**: Exactly **$N = 5,122$** records (1,823 unrecorded mortality records strictly excluded)  

---

## 1. Data Audit & Cohort Filtering

### 1.1 Complete Dataset Accounting
- **Total Records in Toxicity Dataset**: $6,945$ records across 317 unique ponds.
- **Unrecorded Mortality Records (`dead_fish_count.isna()`)**: **$1,823$ records (26.25%)**.
  - 2021: 309 records (100% missing)
  - 2022: 1,431 records (100% missing)
  - 2023 (Jan–Feb): 83 records (7.67% of 2023 missing)
  - 2024–2026: 0 records missing (100% complete)
- **Mandatory Handling**: Following the strict scientific audit protocol, these 1,823 unrecorded records are **strictly excluded**. They are **not zero-filled**, ensuring that no unobserved historical periods distort the positive mortality prevalence.
- **Final Evaluated Dataset**: **$N = 5,122$ records** across 286 unique ponds.

### 1.2 Target Class Balance Summary
- **Negative Class ($0$, No Dead Fish Observed)**: $5,047\text{ records}$ ($98.54\%$)
- **Positive Class ($1$, Dead Fish Observed $> 0$)**: $75\text{ records}$ ($1.46\%$)
- **Class Imbalance Ratio**: **$67.29 : 1$**

---

## 2. Validation Protocol 1: 5-Fold GroupKFold by `pond_id`

To test whether models generalize to **completely unseen aquaculture ponds**, 5-fold cross-validation was grouped on `pond_id`.

### 2.1 Group Independence Verification
In each fold, the training ponds and validation ponds were verified to have **strictly zero overlap**:
$$\text{Ponds}_{\text{train}} \cap \text{Ponds}_{\text{val}} = \emptyset \quad (\text{Overlap Count} = 0 \text{ for all 5 folds})$$

### 2.2 Fold Partitioning Table

| Fold Index | Training Samples | Validation Samples | Training Positives ($1$) | Validation Positives ($1$) | Training Ponds | Validation Ponds | Validation Positive Prevalence (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fold 1** | 4,097 | 1,025 | 63 | 12 | 229 | 57 | 1.17% |
| **Fold 2** | 4,097 | 1,025 | 62 | 13 | 228 | 58 | 1.27% |
| **Fold 3** | 4,098 | 1,024 | 57 | 18 | 229 | 57 | 1.76% |
| **Fold 4** | 4,098 | 1,024 | 59 | 16 | 229 | 57 | 1.56% |
| **Fold 5** | 4,098 | 1,024 | 59 | 16 | 229 | 57 | 1.56% |
| **Total / OOF** | — | **5,122** | — | **75** | — | **286** | **1.46%** |

*Verification Finding*: Every fold contains between 12 and 18 positive cases, ensuring adequate support for minority-class performance estimation in each validation split.

---

## 3. Validation Protocol 2: Chronological Holdout Validation

To test whether models generalize to **subsequent production years**, data were split chronologically using the approved project cutoff date:
$$\text{Cutoff Date} = \text{2025-01-01 00:00:00}$$

### 3.1 Partitioning Structure

| Partition | Time Interval | Total Evaluated Records | Negative Cases ($0$) | Positive Cases ($1$) | Positive Prevalence (%) | Unique Ponds | Monitored Regions |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Training Set** | 2023-03-01 to 2024-12-31 | **2,522** | 2,491 | **31** | **1.23%** | 240 | Eluru (1,521), Nellore (1,001) |
| **Test Set** | 2025-01-01 to 2026-06-30 | **2,600** | 2,556 | **44** | **1.69%** | 162 | Eluru (2,600) |
| **Full Evaluated** | 2023-03-01 to 2026-06-30 | **5,122** | 5,047 | **75** | **1.46%** | 286 | Eluru (4,121), Nellore (1,001) |

### 3.2 Regional Distribution Across Splits
- **Training Set (2023–2024)**:
  - **Eluru**: 1,521 records, 29 positive cases ($1.91\%$ prevalence).
  - **Nellore**: 1,001 records, 2 positive cases ($0.20\%$ prevalence).
- **Test Set (2025–2026)**:
  - **Eluru**: 2,600 records, 44 positive cases ($1.69\%$ prevalence).
  - **Nellore**: 0 records (Nellore was not monitored in 2025–2026).

---

## 4. Temporal Alignment & Leakage Prevention Audit

1. **Temporal Alignment**: All physical water quality measurements (`dissolved_oxygen_mg_l`, `ph`, `temp_c`, `turbidity_cm`, `tds_ppt`, `Weather`, `water_color`, `region`, and `primary_calculated_nh3_mg_l`) and biological observations (`dead_fish_count`) were recorded synchronously at sampling visit $t$. The prediction task evaluates:
   $$\hat{y}_t = f(X_t) \quad \text{where } y_t = \mathbb{I}(\text{dead\_fish\_count}_t > 0)$$
2. **Future Information Isolation**: Feature matrix $X_t$ contains strictly current-visit measurements. No readings from subsequent visits ($t+1$) or future dates are accessible.
3. **Preprocessing Pipeline Isolation**: All imputation values (median turbidity, median TDS) and scaling parameters were fitted strictly on the training partition ($t < 2025$). The test set was transformed using frozen training statistics.
4. **Zero Test Tuning**: No hyperparameters, decision thresholds, or model configurations were tuned on the chronological test set.

