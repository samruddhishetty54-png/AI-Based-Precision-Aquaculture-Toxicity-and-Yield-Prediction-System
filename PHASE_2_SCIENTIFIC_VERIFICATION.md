# Phase 2 Scientific Verification Report: Model Wrappers & Operational Benchmark Integrity

**Document ID:** `P2-SVR-AQUASYSTEM-2026-FINAL`  
**Date:** 2026-11-05  
**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System (BAI507P Mini Project)  
**Verification Scope:** Read-Only Scientific & Metric Audit of Phase 2 Wrappers (`app/models/`) Against Original Final Audit Reports  
**Status:** Read-Only Verification Completed (Zero Files Modified)  
**Author:** AI Technical Lead & Scientific Verification System  

---

## Executive Summary

This document performs an independent, read-only scientific verification of the Phase 2 model integration (`app/models/exp1_soft_sensor.py`, `app/models/exp2_mortality.py`, `app/models/exp3_ammonia_risk.py`, and `app/models/registry.py`) against the original final audit reports of Experiments 1, 2, and 3.

### Primary Audit Findings:
1. **Experiment 1 Warning Threshold Discrepancy (Critical Finding):**
   - In `app/models/exp1_soft_sensor.py`, the warning string states that the model underpredicted *"dangerous acute ammonia spikes (> 2.0 mg/L)"*.
   - **This 2.0 mg/L threshold is factually incorrect and unsupported by the scientific audit.** 2.0 mg/L is the TAN test-kit graduation, not an NH3 toxicity threshold. The un-ionized NH3 fraction depends on pH and temperature and is calculated using the Emerson equation.
   - Across audited NH3 concentration tiers ($\ge 0.05$ mg/L, $\ge 0.10$ mg/L, and $\ge 0.20$ mg/L), the model suffered high underprediction rates on the chronological holdout test set, including a **$100.0\%$ underprediction rate** at $\text{NH}_3 \ge 0.10$ mg/L and $\ge 0.20$ mg/L.
2. **Metric Substitution in Experiment 2 (Mortality Diagnostic):**
   - Phase 2 documentation cited $\text{ROC-AUC} = 0.771$ and $\text{PR-AUC} = 0.082$.
   - **Audit Correction:** These are **spatial GroupKFold cross-validation metrics** across all historical seasons. On the strict chronological holdout test set (2025–2026, $N = 2,600$, 44 mortalities), the audited performance drops to **$\text{ROC-AUC} = 0.5917$ and $\text{PR-AUC} = 0.0499$** for Logistic Regression.
3. **Metric Substitution in Experiment 3 (Next-Visit Ammonia Risk):**
   - Phase 2 documentation cited $\text{PR-AUC} = 0.346$ and $\text{ROC-AUC} = 0.814$.
   - **Audit Correction:** These are **spatial GroupKFold cross-validation metrics** across all 4,900 pairs. On the strict chronological holdout test set (2025–2026, $N = 2,034$ pairs, 57 events), ranking power compressed to **$\text{PR-AUC} = 0.0305$ (near no-skill baseline of $0.0280$) and $\text{ROC-AUC} = 0.5061$ (near random coin toss of $0.5000$)** due to test-kit protocol shifts.

---

## 1. Inspection of Experiment 1: Ammonia Soft-Sensor (`app/models/exp1_soft_sensor.py`)

### 1.1 Wrapper Code Inspection
Inspection of `app/models/exp1_soft_sensor.py` (lines 18–20, 75–79, 172–175) reveals the following docstrings, metadata, and runtime warning strings:
```python
# Lines 75-79:
"warning": (
    "EXPERIMENTAL SOFT-SENSOR ESTIMATE ONLY: Estimates un-ionized ammonia proxy "
    "from physical water quality parameters. Under chronological validation, it systematically "
    "underpredicted dangerous acute ammonia spikes (> 2.0 mg/L). It must NEVER be used as an "
    "independent safety alarm, regulatory compliance metric, or certified laboratory measurement."
)

# Lines 80-85:
"limitations": [
    "Target is a calculated equilibrium proxy, not an analytical chemistry laboratory standard.",
    "Systematically underpredicts acute high-concentration ammonia spikes (> 2.0 mg/L).",
    "Chronological validation showed significant performance degradation across unseen production seasons.",
    "Must be treated as an advisory soft-sensor, not an autonomous shutoff control."
]
```

### 1.2 Comparison Against Original Experiment 1 Final Audit Report
Reference: [`experiment_1_final_verification_v1/final_verification_report.md`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_final_verification_v1/final_verification_report.md)  
Deliverable Data: [`experiment_1_final_verification_v1/metrics/threshold_error_analysis.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_1_final_verification_v1/metrics/threshold_error_analysis.csv)

In Section 3 ("High-Ammonia Threshold Error Analysis"), the audit established the audited NH3 concentration tiers:
- **$\ge 0.05$ mg/L**: Elevated threshold tier.
- **$\ge 0.10$ mg/L**: High threshold tier.
- **$\ge 0.20$ mg/L**: Severe threshold tier.

The empirical error audit established the following quantitative performance:

#### Table 1: High-Ammonia Spike Error Analysis (Audit Table 3.1 & 3.2)
```
+-------------------------------------------------------------------------------------------------------------------------------+
|                                CHRONOLOGICAL HOLDOUT TEST SET (2025–2026, N = 2,600)                                          |
+---------------------+-------+------------+-------------+------------+--------------+------------+----------------+------------+
| Actual NH3 Cohort   | Count | Prevalence | Actual Mean | Pred Mean  | Mean Bias    | MAE (mg/L) | Underpredicted | Max Under  |
+---------------------+-------+------------+-------------+------------+--------------+------------+----------------+------------+
| All (>= 0.00 mg/L)  | 2,600 | 100.00%    | 0.01836     | 0.02639    | +0.00803     | 0.01694    | 32.31%         | 0.50540    |
| >= 0.05 mg/L        | 98    | 3.77%      | 0.10974     | 0.05603    | -0.05371     | 0.06664    | 79.59%         | 0.50540    |
| >= 0.10 mg/L        | 33    | 1.27%      | 0.19593     | 0.06235    | -0.13358     | 0.13358    | 100.00%        | 0.50540    |
| >= 0.20 mg/L        | 10    | 0.38%      | 0.29852     | 0.07509    | -0.22343     | 0.22343    | 100.00%        | 0.50540    |
+---------------------+-------+------------+-------------+------------+--------------+------------+----------------+------------+
|                                FULL DATASET OUT-OF-FOLD (GroupKFold, N = 6,945)                                               |
+---------------------+-------+------------+-------------+------------+--------------+------------+----------------+------------+
| All (>= 0.00 mg/L)  | 6,945 | 100.00%    | 0.02109     | 0.02172    | +0.00062     | 0.01454    | 40.35%         | 0.66251    |
| >= 0.05 mg/L        | 568   | 8.18%      | 0.11377     | 0.07255    | -0.04122     | 0.05489    | 83.45%         | 0.66251    |
| >= 0.10 mg/L        | 178   | 2.56%      | 0.21750     | 0.13195    | -0.08555     | 0.10235    | 83.71%         | 0.66251    |
| >= 0.20 mg/L        | 68    | 0.98%      | 0.34441     | 0.19401    | -0.15040     | 0.15593    | 92.65%         | 0.66251    |
+---------------------+-------+------------+-------------+------------+--------------+------------+----------------+------------+
```

### 1.3 Audit Finding: The "2.0 mg/L" Warning Threshold is Incorrect
- **Diagnosis:** The mention of `> 2.0 mg/L` in `app/models/exp1_soft_sensor.py` conflates **Total Ammonia Nitrogen (TAN)** with **un-ionized ammonia ($\text{NH}_3$)**.
- 2.0 mg/L is the TAN test-kit graduation, not an NH3 toxicity threshold. The un-ionized NH3 fraction depends on pH and temperature and is calculated using the Emerson equation. In the dataset, the maximum calculated NH3 value is 0.684 mg/L.
- **Correct Scientific Communication:** The wrapper must cite the audited NH3 concentration tiers:
  - At actual $\text{NH}_3 \ge 0.05$ mg/L: **$79.59\%$ underprediction rate** (Holdout bias: $-0.0537$ mg/L).
  - At actual $\text{NH}_3 \ge 0.10$ mg/L: **$100.00\%$ underprediction rate** (Holdout bias: $-0.1336$ mg/L).
  - At actual $\text{NH}_3 \ge 0.20$ mg/L: **$100.00\%$ underprediction rate** (Holdout bias: $-0.2234$ mg/L).

---

## 2. Inspection of Experiment 2: Fish Mortality Diagnostic (`app/models/exp2_mortality.py`)

### 2.1 Wrapper Code Inspection
In `app/models/exp2_mortality.py` (lines 17–20, 71–76), the wrapper describes:
- Low precision: $\text{PR-AUC} = 0.082$.
- Extreme class imbalance: $1.46\%$ positive prevalence ($67:1$ class ratio).
- Status: `ADVISORY_DIAGNOSTIC_ONLY`.

### 2.2 Comparison Against Original Experiment 2 Final Audit Report
Reference: [`experiment_2_mortality_v1/experiment_2_final_audit_report.md`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_2_mortality_v1/experiment_2_final_audit_report.md)  
Deliverable Data: [`experiment_2_mortality_v1/final_audit_metrics/threshold_selection_audit.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_2_mortality_v1/final_audit_metrics/threshold_selection_audit.csv)

The audit evaluated both **spatial GroupKFold cross-validation** ($N = 5,122$, 75 positives) and **chronological test holdout** (2025–2026, $N = 2,600$, 44 positives):

#### Table 2: Experiment 2 Metric Comparison (GroupKFold vs. Chronological Holdout)
```
+-----------------------------------+-----------------------------+------------------------------------+
| Performance Metric                | Spatial GroupKFold (OOF)    | Strict Chronological Holdout       |
|                                   | (N = 5,122, Prev = 1.46%)   | (2025–2026, N = 2,600, Prev=1.69%) |
+-----------------------------------+-----------------------------+------------------------------------+
| Logistic Regression ROC-AUC       | 0.7712                      | 0.5917                             |
| Logistic Regression PR-AUC (AP)   | 0.0821 (vs base 0.0146)     | 0.0499 (vs base 0.0169)            |
| Logistic Regression Recall        | 64.00%                      | 20.45% (9 / 44 mortalities)        |
| Logistic Regression Precision     | 4.62%                       | 3.81% (9 / 236 alarms)             |
| Logistic Regression F1-Score      | 0.0862                      | 0.0643                             |
| Logistic Regression False Alarms  | 989 FP                      | 227 FP                             |
+-----------------------------------+-----------------------------+------------------------------------+
| Random Forest ROC-AUC             | 0.8137                      | 0.7322                             |
| Random Forest PR-AUC (AP)         | 0.0934 (vs base 0.0146)     | 0.0648 (vs base 0.0169)            |
| Random Forest Recall (tau = 0.40) | 48.00%                      | 13.64% (6 / 44 mortalities)        |
| Random Forest Precision (tau=0.40)| 7.21%                       | 11.54% (6 / 52 alarms)             |
| Random Forest F1-Score (tau=0.40) | 0.1254                      | 0.1250                             |
+-----------------------------------+-----------------------------+------------------------------------+
```

### 2.3 Audit Finding: Metric Substitution in Documentation
- **Audit Diagnosis:** In `PHASE_2_IMPLEMENTATION_REPORT.md` (Section 6), the metrics listed for Experiment 2 were:
  `ROC-AUC = 0.771, PR-AUC = 0.082`.
- These values originate exclusively from the **spatial GroupKFold cross-validation**.
- On the **chronological holdout test set**, Logistic Regression's ranking discrimination drops to **$\text{ROC-AUC} = 0.5917$ and $\text{PR-AUC} = 0.0499$**, detecting only $9$ of $44$ mortalities ($20.45\%$ sensitivity) with $227$ false alarms ($3.81\%$ precision).
- **Correct Scientific Communication:** System documentation must state the chronological holdout metrics ($\text{ROC-AUC} = 0.5917, \text{PR-AUC} = 0.0499$) as the true operational temporal baseline, explicitly distinguishing them from the optimistic GroupKFold cross-validation results.

---

## 3. Inspection of Experiment 3: Next-Visit Ammonia Risk (`app/models/exp3_ammonia_risk.py`)

### 3.1 Wrapper Code Inspection
In `app/models/exp3_ammonia_risk.py` (lines 17–25, 78–84), the wrapper correctly identifies:
- Discrete multi-week revisit intervals ($3 \le \Delta t \le 45$ days, median 22 days).
- Explicit warning that this is **NOT an hourly or overnight forecast**.
- Chronological holdout performance was close to the no-skill baseline ($\text{PR-AUC} \approx 0.0305$ vs $0.0280$).

### 3.2 Comparison Against Original Experiment 3 Final Audit Report
Reference: [`experiment_3_next_visit_risk_v1/experiment_3_results_report.md`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_next_visit_risk_v1/experiment_3_results_report.md) & [`experiment_3_final_audit_report.md`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_next_visit_risk_v1/experiment_3_final_audit_report.md)  
Deliverable Data: [`experiment_3_next_visit_risk_v1/metrics/chronological_test_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_next_visit_risk_v1/metrics/chronological_test_metrics.csv)

The audit compared **spatial GroupKFold cross-validation** ($N = 4,900$, 314 positives, baseline $= 0.0641$) against the **strict chronological test holdout** (2025–2026, $N = 2,034$ pairs, 57 positives, baseline $= 0.0280$):

#### Table 3: Experiment 3 Metric Comparison (GroupKFold vs. Chronological Holdout)
```
+-----------------------------------+-----------------------------+------------------------------------+
| Performance Metric                | Spatial GroupKFold (OOF)    | Strict Chronological Holdout       |
|                                   | (N = 4,900, Prev = 6.41%)   | (2025–2026, N = 2,034, Prev=2.80%) |
+-----------------------------------+-----------------------------+------------------------------------+
| Random Forest PR-AUC (Primary)    | 0.3461 (5.4x over baseline) | 0.0305 (near no-skill 0.0280)      |
| Random Forest ROC-AUC             | 0.8137                      | 0.5061 (near coin toss 0.5000)     |
| Random Forest Recall              | 61.15% (192 / 314 events)   | 31.58% (18 / 57 events)            |
| Random Forest Precision           | 24.71%                      | 2.63% (18 / 684 alarms)            |
| Random Forest F1-Score            | 0.3520                      | 0.0486                             |
| Detection of New Onset Spikes     | 90 / 204 (44.1% sensitivity)| 15 / 54 (27.8% sensitivity)        |
+-----------------------------------+-----------------------------+------------------------------------+
| Logistic Regression PR-AUC        | 0.2893                      | 0.0309 (near no-skill 0.0280)      |
| Logistic Regression ROC-AUC       | 0.7876                      | 0.5010 (near coin toss 0.5000)     |
| Logistic Regression Recall        | 71.34% (224 / 314 events)   | 36.84% (21 / 57 events)            |
| Logistic Regression Precision     | 18.33%                      | 2.36% (21 / 889 alarms)            |
| Detection of New Onset Spikes     | 123 / 204 (60.3% sensitiv.) | 18 / 54 (33.3% sensitivity)        |
+-----------------------------------+-----------------------------+------------------------------------+
| Persistence Baseline (y_{t+1}=y_t)| Recall = 35.03%             | Recall = 5.26% (3 / 57 events)     |
| Persistence New Spike Sensitivity | 0 / 204 (0.0% [BLIND])      | 0 / 54 (0.0% [BLIND])              |
+-----------------------------------+-----------------------------+------------------------------------+
```

### 3.3 Audit Finding: Protocol Shift & GroupKFold vs. Chronological Distinction
- **Audit Diagnosis:** While the code in `app/models/exp3_ammonia_risk.py` correctly notes the near no-skill chronological performance, previous reports (`FINAL_INTEGRATION_READINESS_REPORT.md` and `PHASE_2_IMPLEMENTATION_REPORT.md`) repeatedly highlighted $\text{PR-AUC} = 0.346$ as the headline metric.
- $\text{PR-AUC} = 0.3461$ is strictly the **spatial cross-validation score** across historically pooled ponds.
- On the **unseen chronological holdout**, model ranking discrimination collapsed to **$\text{PR-AUC} = 0.0305$ and $\text{ROC-AUC} = 0.5061$**, driven by the 2026 test-kit protocol shift (where 57% of raw TAN readings collapsed to zero due to a 0.25 mg/L visual limit) and the cessation of Nellore monitoring.
- However, machine learning still provided a distinct operational advantage over the Persistence Baseline:
  - Persistence was **100% blind to newly developed spikes** (0/54, 0.0% sensitivity; 3 total true positives on persistent spikes).
  - Random Forest detected **18 total true positives**, successfully identifying **15 of the 54 newly developed spikes** ($27.8\%$ sensitivity) plus 3 persistent spikes, while Logistic Regression detected **21 total true positives** (identifying **18 of the 54 newly developed spikes**, $33.3\%$ sensitivity).

---

## 4. Synthesis of Audit Discrepancies & Recommendations

The table below summarizes the exact audit discrepancies identified during this read-only inspection:

```
+==================================================================================================================================+
|                                      PHASE 2 SCIENTIFIC VERIFICATION DISCREPANCY MATRIX                                          |
+------------+-------------------------------+-----------------------------------+-------------------------------------------------+
| Module     | Attribute Inspected           | Implemented in Phase 2            | Documented in Scientific Audits (Ground Truth)   |
+------------+-------------------------------+-----------------------------------+-------------------------------------------------+
| Exp 1      | Underpredicted Spike Threshold| "> 2.0 mg/L"                      | Audited NH3 concentration tiers:                |
|            |                               |                                   | >= 0.05 mg/L (79.6% underpredicted),            |
|            |                               |                                   | >= 0.10 mg/L (100.0% underpredicted),           |
|            |                               |                                   | >= 0.20 mg/L (100.0% underpredicted).           |
|            |                               |                                   | (2.0 mg/L is TAN test-kit graduation).          |
+------------+-------------------------------+-----------------------------------+-------------------------------------------------+
| Exp 2      | Reported Primary Metrics      | ROC-AUC = 0.771, PR-AUC = 0.082   | Chronological Holdout (N = 2,600):              |
|            |                               | (GroupKFold Spatial CV)           | ROC-AUC = 0.5917, PR-AUC = 0.0499 (LR).         |
|            |                               |                                   | (0.771 / 0.082 are spatial GroupKFold metrics). |
+------------+-------------------------------+-----------------------------------+-------------------------------------------------+
| Exp 3      | Headline PR-AUC Metric        | PR-AUC = 0.346                    | Chronological Holdout (N = 2,034):              |
|            |                               | (GroupKFold Spatial CV)           | PR-AUC = 0.0305, ROC-AUC = 0.5061 (RF).         |
|            |                               |                                   | (0.346 is pooled spatial GroupKFold PR-AUC).    |
+------------+-------------------------------+-----------------------------------+-------------------------------------------------+
```

---

## 5. Verification Checklist & Sign-Off

- [x] `app/models/exp1_soft_sensor.py` inspected and compared against `experiment_1_final_verification_v1/final_verification_report.md`.
- [x] Spike underprediction rates verified: $79.59\%$ at $\ge 0.05$ mg/L, $100.0\%$ at $\ge 0.10$ mg/L, and $100.0\%$ at $\ge 0.20$ mg/L on chronological holdout.
- [x] Identified that the 2.0 mg/L warning threshold is **incorrect**: 2.0 mg/L is the TAN test-kit graduation, not an NH3 toxicity threshold. The un-ionized NH3 fraction depends on pH and temperature and is calculated using the Emerson equation.
- [x] Experiment 2 chronological holdout metrics verified: $\text{ROC-AUC} = 0.5917, \text{PR-AUC} = 0.0499$ for Logistic Regression (reconciled against GroupKFold $\text{ROC-AUC} = 0.771, \text{PR-AUC} = 0.082$).
- [x] Experiment 3 chronological holdout metrics verified: $\text{PR-AUC} = 0.0305, \text{ROC-AUC} = 0.5061$ for Random Forest (reconciled against GroupKFold $\text{PR-AUC} = 0.3461$).
- [x] Zero code, model, dataset, or experiment files were modified.

---
*Report compiled and certified under strict read-only audit protocol.*

