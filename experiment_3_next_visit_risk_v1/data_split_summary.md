# Data Split Summary: Experiment 3 (Next-Visit Ammonia Risk)

**Date**: November 2026  
**Project**: AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Experiment Identifier**: `experiment_3_next_visit_risk_v1`  
**Dataset Analyzed**: [`processed_data_v2/toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv) ($N = 6,945$)  
**Valid Pairs Evaluated**: Exactly **$N = 4,900$ pairs** ($3 \le \Delta t \le 45$ days) across 303 unique ponds  

---

## 1. Temporal Pair Construction & Window Accounting

### 1.1 Complete Pairing Accounting
- **Total Observations in Source Dataset**: $6,945$ records across 317 unique ponds.
- **Maximum Possible Consecutive Pairs**: $\sum (N_{\text{visits}} - 1) = 6,945 - 317 = 6,628$ theoretical pairs.
- **Pairing Constraints Applied**:
  - Minimum gap: $\ge 3.0$ days (eliminates diurnal/duplicate visits).
  - Maximum gap: $\le 45.0$ days (eliminates inter-crop fallow dry-outs).
  - Valid targets: Both visits contain valid calculated ammonia readings.
- **Pairs Excluded**:
  - Gaps $< 3.0$ days: $23$ pairs (immediate re-measurements).
  - Gaps $> 45.0$ days: $1,705$ pairs (extended fallow periods, seasonal pond drying, or abandoned monitoring).
- **Final Valid Consecutive Pairs**: Exactly **$N = 4,900$ observation pairs**.
- **Unique Ponds Represented**: **$303$ unique ponds** ($95.58\%$ of all 317 monitored ponds).

### 1.2 Revisit Interval ($\Delta t$, Gap Days) Distribution
| Statistic | Stated Value (Days) | Operational Interpretation |
| :--- | :---: | :--- |
| **Minimum Interval** | **3.00 days** | Intensive emergency follow-up re-sampling. |
| **25th Percentile (Q1)** | **14.59 days** | Bi-weekly routine farm inspection cycle. |
| **50th Percentile (Median)** | **21.99 days ($\approx 22$ days)** | Standard 3-week routine extension visit. |
| **Mean Interval** | **22.34 days** | Average inter-visit sampling duration across the farm network. |
| **75th Percentile (Q3)** | **30.00 days** | Monthly routine farm inspection cycle. |
| **Maximum Interval** | **44.99 days** | Maximum allowable within-crop monitoring gap. |

*Deliverable CSV*: [`gap_days_distribution.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_next_visit_risk_v1/metrics/gap_days_distribution.csv)

### 1.3 Target Class Distribution and State Transitions
- **Negative Target ($0$, Safe Next Visit)**: **$4,586$ pairs ($93.59\%$)**.
- **Positive Target ($1$, High Risk Next Visit)**: **$314$ pairs ($6.41\%$)**.
- **Class Imbalance Ratio**: **$14.61 : 1$**.

#### The State Transition Matrix
| Current Visit State ($t$) | Next Visit State ($t+1$) | Transition Category | Pair Count | Percentage (%) |
| :---: | :---: | :--- | :---: | :---: |
| **0 (Safe)** | **0 (Safe)** | Stable Quiescent Water Quality | **4,341** | **88.59%** |
| **0 (Safe)** | **1 (High Risk)** | **New Onset Risk Spike (Acute Surge)** | **204** | **4.16%** |
| **1 (High Risk)** | **0 (Safe)** | Environmental Recovery / Mitigation | **245** | **5.00%** |
| **1 (High Risk)** | **1 (High Risk)** | Persistent Toxic Chronic State | **110** | **2.24%** |
| **Total** | — | — | **4,900** | **100.00%** |

*Deliverable CSV*: [`state_transition_matrix.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_next_visit_risk_v1/metrics/state_transition_matrix.csv)

---

## 2. Validation Protocol 1: 5-Fold GroupKFold by `pond_id`

To test whether prognostic models generalize to **completely unseen aquaculture ponds**, 5-fold cross-validation was grouped strictly on `pond_id`.

### 2.1 Group Independence Verification
In each fold, the training ponds and validation ponds were verified to have **strictly zero overlap**:
$$\text{Ponds}_{\text{train}} \cap \text{Ponds}_{\text{val}} = \emptyset \quad (\text{Overlap Count} = 0 \text{ across all 5 folds})$$

### 2.2 Fold Partitioning Table

| Fold Index | Training Pairs | Validation Pairs | Training Positives ($1$) | Validation Positives ($1$) | Training Ponds | Validation Ponds | Validation Positive Prevalence (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fold 1** | 3,920 | 980 | 251 | 63 | 243 | 60 | 6.43% |
| **Fold 2** | 3,920 | 980 | 258 | 56 | 243 | 60 | 5.71% |
| **Fold 3** | 3,920 | 980 | 256 | 58 | 242 | 61 | 5.92% |
| **Fold 4** | 3,920 | 980 | 253 | 61 | 242 | 61 | 6.22% |
| **Fold 5** | 3,920 | 980 | 238 | 76 | 242 | 61 | 7.76% |
| **Total / OOF** | — | **4,900** | — | **314** | — | **303** | **6.41%** |

*Verification Finding*: Every validation fold contains between 56 and 76 positive next-visit risk events, providing robust statistical support for out-of-sample evaluation.

---

## 3. Validation Protocol 2: Strict Chronological Validation

To evaluate how models generalize across **subsequent production years**, pairs were partitioned chronologically using the approved cutoff:
$$\text{Cutoff Date} = \text{2025-01-01 00:00:00}$$

### 3.1 Strict Partitioning Rules & Cross-Cutoff Elimination
To prevent temporal leakage, pairs that straddled the cutoff date were identified and partitioned according to strict causality rules:

1. **Training Partition ($N = 2,788$ pairs)**:
   - Defined strictly as pairs where **BOTH** the current visit and next visit occurred before the cutoff:
     $$\text{curr\_datetime} < \text{2025-01-01} \quad \land \quad \text{next\_datetime} < \text{2025-01-01}$$
   - Positive next-visit risk cases: **$257$ pairs ($9.22\%$ prevalence)**.
2. **Cross-Cutoff Straddling Pairs ($N = 78$ pairs, STRICTLY EXCLUDED)**:
   - Defined as pairs where the current visit occurred in late 2024, but the next visit occurred in early 2025:
     $$\text{curr\_datetime} < \text{2025-01-01} \quad \land \quad \text{next\_datetime} \ge \text{2025-01-01}$$
   - **MANDATORY POLICY**: These 78 pairs are **strictly excluded from training**. If included in training, the model would be trained on outcomes occurring in the test period (2025), creating direct temporal leakage.
3. **Test Partition ($N = 2,034$ pairs)**:
   - Defined strictly as pairs where the current visit occurred after the cutoff:
     $$\text{curr\_datetime} \ge \text{2025-01-01}$$
   - Positive next-visit risk cases: **$57$ pairs ($2.80\%$ prevalence)**.

### 3.2 Chronological Partitioning Summary Table

| Partition | Time Window | Total Pairs | Negative Cases ($0$) | Positive Cases ($1$) | Positive Prevalence (%) | Unique Ponds | Regional Breakdown |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Training Set** | 2021-08-01 to 2024-12-31 | **2,788** | 2,531 | **257** | **9.22%** | 258 | Eluru (1,847), Nellore (941) |
| **Cross-Cutoff (Excluded)** | 2024-11-20 to 2025-01-28 | **78** | 78 | **0** | **0.00%** | 78 | Eluru (78) |
| **Test Set** | 2025-01-01 to 2026-06-30 | **2,034** | 1,977 | **57** | **2.80%** | 162 | Eluru (2,034) |
| **Total Accounts** | — | **4,900** | **4,586** | **314** | **6.41%** | **303** | — |

### 3.3 Cause of Positive Prevalence Drop in Test Set (9.22% to 2.80%)
A critical biogeochemical and operational audit explains why positive risk prevalence dropped from $9.22\%$ in training to $2.80\%$ in the test set:
1. **The 2026 Field-Kit Protocol Transition**: As documented in the Experiment 1 Verification Audit, 100% of 2026 ammonia measurements switched to a 5-step visual comparator disc kit ($0.00, 0.25, 0.50, 1.00, 2.00$ mg/L). In 2026, **$57.09\%$ of all raw TAN measurements collapsed to exact zeros ($0.00$ mg/L)** due to the $0.25$ mg/L field detection floor. Because $\text{TAN} = 0.00$ forces $\text{NH}_3 = 0.000$, far fewer ponds exceeded the $0.05$ mg/L risk threshold in 2026.
2. **Regional Composition Shift**: Nellore (which accounted for 941 pairs in training) was completely unmonitored in 2025–2026. The test set represents Eluru exclusively.
3. **No Test Tuning**: Preprocessing statistics were frozen from the training partition; no hyperparameters or decision thresholds were tuned on the test set.

