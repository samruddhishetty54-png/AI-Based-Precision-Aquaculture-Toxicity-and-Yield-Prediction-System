# Final Independent Validation Audit: Experiment 2 (Fish Mortality Classification)

**Audit Date**: November 2026  
**Project**: AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Audit Target**: [`experiment_2_mortality_v1/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_2_mortality_v1)  
**Dataset Evaluated**: [`processed_data_v2/toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv) ($N = 6,945$ total, $N = 5,122$ evaluated)  
**Target Variable**: Binary Mortality Flag ($\text{dead\_fish\_count} > 0$)  
**Audit Deliverables Directory**: [`experiment_2_mortality_v1/final_audit_metrics/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_2_mortality_v1/final_audit_metrics)  

---

## Executive Summary

This independent validation audit provides a rigorous review of **Experiment 2 (Fish Mortality Classification)**. The audit examined five specific methodological criteria: threshold selection integrity, evaluation consistency, feature leakage and operational availability, scientific claims boundaries, and metric validity.

All existing Experiment 2 files, models, plots, and source datasets were preserved without modification. No models were retrained. All recalculated verification metrics are archived in [`experiment_2_mortality_v1/final_audit_metrics/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_2_mortality_v1/final_audit_metrics).

---

## 1. Threshold Selection Audit

### 1.1 Provenance of the Random Forest $\tau = 0.20$ Threshold
- **Audit Finding**: In the initial report ([`experiment_2_results_report.md`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_2_mortality_v1/experiment_2_results_report.md), Section 2.1), a threshold of $\tau = 0.20$ was reported with $\text{Recall} = 59.09\%$ and $\text{Precision} = 5.94\%$.
- **Mechanism of Selection**: An inspection of the execution trajectory confirms that this $\tau = 0.20$ threshold was **NOT** selected using cross-validation on the training set (2021–2024). Instead, it was identified by evaluating a post-hoc grid of candidate thresholds directly on the 2025–2026 chronological holdout test set.
- **Formal Audit Classification**: 
  > [!WARNING]
  > **Exploratory Post-Hoc Analysis**: The reported metrics at $\tau = 0.20$ on the chronological test set **must be designated strictly as an exploratory post-hoc sensitivity analysis**, NOT as an independent out-of-sample evaluation. Because test results directly influenced the choice of $\tau = 0.20$, reporting this number as the primary model performance constitutes mild test-set selection bias.

### 1.2 Independent Test Evaluation at Default Pipeline Threshold ($\tau = 0.50$)
The true independent, un-tuned evaluation metric for Random Forest on the chronological holdout is the pre-specified default decision boundary ($\tau = 0.50$):
- **True Positives (TP)**: $0$
- **False Negatives (FN)**: $44$
- **False Positives (FP)**: $6$
- **True Negatives (TN)**: $2,550$
- **Recall**: **$0.0000$ ($0.0\%$)**
- **Precision**: **$0.0000$ ($0.0\%$)**
- **F1-Score**: **$0.0000$**

### 1.3 Training-Only Threshold Tuning Benchmark ($\tau = 0.40$)
To determine what threshold *would* be selected without test leakage, a 5-fold cross-validation grid search was executed strictly on the 2021–2024 training partition ($N = 2,522$, $31$ positive cases):
- **Optimal Training OOF Threshold**: **$\tau = 0.40$** (maximizing training OOF $\text{F1} = 0.0631$, with training $\text{Recall} = 22.58\%$ and $\text{Precision} = 3.66\%$).
- **Independent Application to Chronological Test Set (Zero Test Leakage)**:
  - **TP**: $6$ (detected $6$ of $44$ mortalities)
  - **FN**: $38$ (missed $38$ of $44$ mortalities)
  - **FP**: $46$
  - **TN**: $2,510$
  - **Recall**: **$13.64\%$**
  - **Precision**: **$11.54\%$**
  - **F1-Score**: **$0.1250$**

### 1.4 Logistic Regression Threshold Integrity
- **Audit Finding**: In contrast to Random Forest, the Logistic Regression threshold was applied via the default decision function ($\text{logit} \ge 0$, probability $\ge 0.50$).
- **Imbalance Handling**: The `class_weight='balanced'` parameter computed class inverse weights strictly from the training partition:
  $$w_0 = \frac{2522}{2 \times 2491} \approx 0.506, \quad w_1 = \frac{2522}{2 \times 31} \approx 40.677$$
- **Verification**: This parameter shifted the decision boundary using training class frequencies alone. No test data influenced Logistic Regression's threshold. Its reported test metrics ($\text{Recall} = 20.45\%$, $\text{Precision} = 3.81\%$, $\text{F1} = 0.0643$) are **fully independent and verified**.

*Deliverable CSV*: [`threshold_selection_audit.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_2_mortality_v1/final_audit_metrics/threshold_selection_audit.csv)

---

## 2. Evaluation Consistency & Metric Verification

All confusion matrices and performance metrics were recalculated independently from source arrays and validated against existing report values.

### 2.1 Positive-Class Definition & Prevalence Accounting
- **Positive Class ($1$)**: $\text{dead\_fish\_count} > 0$.
- **Negative Class ($0$)**: $\text{dead\_fish\_count} == 0$.
- **Prevalence Baselines**:
  - **GroupKFold OOF ($N = 5,122$)**: $75$ positives $\rightarrow$ **$1.464\%$ ($0.0146$)**.
  - **Chronological Training ($N = 2,522$)**: $31$ positives $\rightarrow$ **$1.229\%$ ($0.0123$)**.
  - **Chronological Test ($N = 2,600$)**: $44$ positives $\rightarrow$ **$1.692\%$ ($0.0169$)**.

### 2.2 Chronological Test Performance Audit ($N = 2,600$, Positives = 44)

| Model Configuration | Decision Threshold ($\tau$) | Derivation Protocol / Status | Recall | Precision | F1-Score | PR-AUC (AP) | ROC-AUC | TP | FN | FP | TN | No-Skill Baseline |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dummy (Prior)** | 0.50 | Majority Class Baseline | 0.0000 | 0.0000 | 0.0000 | 0.0169 | 0.5000 | 0 | 44 | 0 | 2,556 | 0.0169 |
| **Logistic Regression** | 0.50 | Training-fitted balanced weights | **0.2045** | 0.0381 | 0.0643 | 0.0499 | 0.5917 | **9** | 35 | 227 | 2,329 | 0.0169 |
| **Random Forest (Default)** | 0.50 | Independent Pipeline Default | 0.0000 | 0.0000 | 0.0000 | **0.0648** | **0.7322** | 0 | 44 | **6** | 2,550 | 0.0169 |
| **Random Forest (Train-Tuned)** | 0.40 | 5-Fold CV on 2021–2024 Train only | 0.1364 | **0.1154** | **0.1250** | **0.0648** | **0.7322** | 6 | 38 | 46 | 2,510 | 0.0169 |
| **Random Forest (Exploratory)** | 0.20 | *POST-HOC (Inspected test set)* | *0.5909* | *0.0594* | *0.1079* | *0.0648* | *0.7322* | *26* | *18* | *412* | *2,144* | 0.0169 |

*Verification Finding*:
- The reported Average Precision ($\text{PR-AUC} = 0.0648$ for RF, $0.0499$ for LR) and $\text{ROC-AUC} = 0.7322$ are threshold-independent ranking metrics. Both are mathematically verified and use the correct test prevalence baseline ($0.0169$).
- Random Forest ranks positive cases higher than negative cases (mean probability $0.2371$ vs. $0.1408$).

### 2.3 GroupKFold Out-of-Fold Performance Audit ($N = 5,122$, Positives = 75)

| Model Architecture | Recall | Precision | F1-Score | PR-AUC (AP) | ROC-AUC | TP | FN | FP | TN | No-Skill Baseline |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dummy (Prior)** | 0.0000 | 0.0000 | 0.0000 | 0.0134 | 0.4593 | 0 | 75 | 0 | 5,047 | 0.0146 |
| **Logistic Regression** | **0.5467** | 0.0363 | 0.0680 | 0.0577 | 0.6923 | **41** | 34 | 1,090 | 3,957 | 0.0146 |
| **Random Forest** | 0.3200 | **0.0743** | **0.1206** | **0.0939** | **0.7607** | 24 | 51 | 299 | 4,748 | 0.0146 |

*Verification Finding*: All GroupKFold confusion matrices and summary metrics are confirmed identical to the report.

*Deliverable CSVs*: [`recalculated_chronological_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_2_mortality_v1/final_audit_metrics/recalculated_chronological_metrics.csv), [`recalculated_groupkfold_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_2_mortality_v1/final_audit_metrics/recalculated_groupkfold_metrics.csv)

---

## 3. Feature Leakage & Operational Workflow Audit

### 3.1 Verification of Excluded Variables
The feature matrix and preprocessing pipelines were audited for leakage:
- **Mortality Counts**: `dead_fish_count` is excluded (used solely to construct $y$).
- **Clinical Distress Symptoms**: `air_gulping_count`, `tail_splashing_count`, and `provisional_behavioral_distress_observed` are strictly barred.
- **Post-Hoc Heuristics**: `provisional_severity_heuristic` (which directly bins dead fish count), `provisional_hypoxia_risk_heuristic`, `provisional_ph_stress_risk_heuristic`, `provisional_ammonia_risk_heuristic`, `is_wq_in_range`, and `parameters_out_of_range` are strictly barred.
- **Identifiers**: `pond_id` and `datetime` are barred from $X$.
- **Temporal Alignment**: All inputs and targets are recorded at the same visit $t$; no future observations enter the models.

### 3.2 Operational Limitation: Chemical Dependency of `primary_calculated_nh3_mg_l`
> [!IMPORTANT]
> **Operational Dependency Disclosed**:
> `primary_calculated_nh3_mg_l` was selected as a key input feature and ranked as the **second most important predictor ($15.3\%$ Gini importance)**.
> However, `primary_calculated_nh3_mg_l` is calculated via Emerson's formula from `raw_ammonia_tan_nh3_mg_l` (or TAN-N), pH, and temperature.
> 
> **Workflow Impact**:
> 1. In a **pure software-only / IoT automated monitoring workflow** where manual chemical test kits are absent, `primary_calculated_nh3_mg_l` is **UNAVAILABLE at prediction time**. Standard optical or electrochemical IoT probes do not measure Total Ammonia Nitrogen.
> 2. If Experiment 1's soft-sensor model (Model B) is substituted to estimate un-ionized ammonia, Model B's own prediction errors (negative $R^2$ on the chronological holdout and $100\%$ under-prediction of ammonia spikes $\ge 0.10$ mg/L) would cascade directly into the mortality classifier.
> 3. Therefore, Experiment 2 as evaluated represents a **hybrid workflow** requiring manual chemical TAN test-kit inputs, not an autonomous software-only sensor system.

*Deliverable CSV*: [`feature_availability_audit.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_2_mortality_v1/final_audit_metrics/feature_availability_audit.csv)

---

## 4. Scientific Claims and Statistical Rigor

### 4.1 Measured Statistical Facts vs. Interpretive Hypotheses
The following distinction is strictly enforced:
- **Measured Statistical Facts**:
  - Low dissolved oxygen and elevated ammonia correlate with recorded dead fish counts ($p < 0.01$).
  - Random Forest achieves $\text{ROC-AUC} = 0.7322$ and $\text{PR-AUC} = 0.0648$ on the chronological test holdout.
  - Across 5,122 evaluated visits, exactly 75 positive mortality events were recorded ($1.46\%$).
  - In 2021 and 2022, 1,823 records lacked mortality monitoring ($100\%$ unmonitored).
- **Interpretive Hypotheses (Unmeasured in Dataset)**:
  - Speculations that viral outbreaks (WSSV, AHPND) or midnight aerator electrical blackouts caused the undetected mortalities are plausible domain explanations, but cannot be verified from the dataset.

### 4.2 Prohibited Claims
1. **No Causal Claims**: The audit confirms that water quality cannot be claimed as the sole proximate cause of mortality. Environmental stress predisposes aquatic organisms to disease, but clinical mortality is multifactorial.
2. **No Claim of Reliable Operational Deployment**: The audit confirms that Experiment 2 **cannot be recommended for standalone autonomous farm alarms**. At acceptable sensitivity levels ($\ge 50\%$), precision remains $\le 8\%$, producing more than $12$ false alarms for every genuine mortality event.

---

## 5. Audit Conclusion & Final Verdict

```
+--------------------------------------------------------------------------------------------------+
|                                    EXPERIMENT 2 AUDIT VERDICT                                    |
+--------------------------------------------------------------------------------------------------+
| Evaluation Protocol        | Validated Primary Metric                | Operational Verdict        |
| :------------------------- | :-------------------------------------- | :------------------------- |
| GroupKFold by pond_id      | PR-AUC = 0.0939, ROC-AUC = 0.7607       | VALID (Spatial Ranking)     |
| Chronological Holdout      | PR-AUC = 0.0648, ROC-AUC = 0.7322       | VALID (Temporal Ranking)    |
| RF Default Threshold (0.5) | Recall = 0.0%, Precision = 0.0%         | VALID (Independent Baseline)|
| RF Train-Tuned Thresh(0.4) | Recall = 13.6%, Precision = 11.5%       | VALID (Independent Tuned)  |
| RF Exploratory Thresh(0.2) | Recall = 59.1%, Precision = 5.9%        | EXPLORATORY ONLY (Test-Bias)|
| Feature Anti-Leakage       | Zero target/clinical symptom leakage    | FULLY COMPLIANT            |
| Software-Only Deployment   | Requires manual TAN chemical test kit   | RESTRICTED (Hybrid Only)   |
+--------------------------------------------------------------------------------------------------+
```

### Final Statement
- **Validity**: The Experiment 2 ranking and comparative baseline results are **methodologically valid and mathematically sound**.
- **Trusted Thresholds**: For independent evaluation, only the default pipeline thresholds ($\tau = 0.50$) and the training-only tuned threshold ($\tau = 0.40$) can be cited. The $\tau = 0.20$ metrics must be explicitly cited as exploratory sensitivity analysis.
- **Disclosed Boundaries**: The system requires external chemical ammonia testing, suffers from severe minority-class sparsity ($75$ events), misses early-year historical records, and cannot serve as an autonomous early-warning mortality system.

