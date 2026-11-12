# Experiment 3 Plan: Next-Visit Ammonia Toxicity Risk Prediction

**Date**: November 2026  
**Project**: AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Experiment Identifier**: `experiment_3_next_visit_risk_v1`  
**Dataset Source**: [`processed_data_v2/toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv) ($N = 6,945$)  
**Target Variable**: Provisional Ammonia Toxicity Risk at Next Routine Farm Visit ($t+1$):
$$y_{t+1} = \mathbb{I}\left(\text{primary\_calculated\_nh3\_mg\_l}_{t+1} \ge 0.05\text{ mg/L} \ \lor \ \text{raw\_ammonia\_tan\_nh3\_n\_mg\_l}_{t+1} \ge 1.0\text{ mg/L}\right)$$

---

## 1. Executive Summary & Task Scope

The primary objective of **Experiment 3** is to determine whether environmental water-quality measurements collected during a routine farm inspection visit at time $t$ can forecast whether that same pond will be in a high-risk un-ionized ammonia state ($\text{NH}_3 \ge 0.05$ mg/L) at its next scheduled farm visit at time $t+1$ ($3$ to $45$ days later).

> [!IMPORTANT]
> **Explicit Scope Boundary: Next-Visit Prediction vs. Real-Time/Hourly Forecasting**:
> - This task is **strictly a next-visit prognostic classification task** on discrete monitoring visits separated by intervals of **3 to 45 days** (median sampling interval: **$22.0$ days**).
> - This task is **NOT** a real-time, continuous, hourly, or diurnal forecasting system. Continuous hourly ammonia dynamics depend on diurnal photosynthetic cycles, midnight aeration runs, and daily feeding rates, which are not logged in routine discrete field monitoring visits.

---

## 2. Target Derivation & Operational Risk Thresholds

### 2.1 Chemistry-Based Derivation of the Target
The target variable is based on the un-ionized ammonia concentration calculated via Emerson's equilibrium formula:
$$\text{NH}_3 = \text{TAN} \times \left(1 + 10^{\text{pK}_a(T) - \text{pH}}\right)^{-1}$$
where $\text{pK}_a(T) = \frac{2729.92}{T + 273.15} + 0.09018$, and $\text{TAN}$ is Total Ammonia Nitrogen ($\text{NH}_4^+ + \text{NH}_3$).

### 2.2 Operational Risk Threshold (`thresholds_config.json`)
As formally configured in [`processed_data_v2/thresholds_config.json`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/thresholds_config.json):
- `"toxic_molecular_nh3_heuristic_mg_l": 0.05` mg/L.
- `"tan_caution_heuristic_mg_l": 1.0` mg/L.
- The binary flag `provisional_ammonia_risk_heuristic` evaluates to $1$ when calculated molecular $\text{NH}_3 \ge 0.05$ mg/L or raw TAN-N $\ge 1.0$ mg/L.

> [!WARNING]
> **Provisional Nature of the Risk Label**:
> The $0.05$ mg/L threshold is an unverified operational heuristic standard commonly adopted in warm-water Penaeid shrimp and cyprinid farming. It is **NOT an independently confirmed laboratory toxicity bioassay** (such as a 96-hour $\text{LC}_{50}$ mortality test). It must not be presented as absolute biological ground truth, but rather as an operational warning benchmark.

---

## 3. Temporal Pair Construction Methodology

To evaluate longitudinal risk forecasting without temporal leakage, observation pairs $(t, t+1)$ were constructed following five strict rules:

1. **Intra-Pond Ordering**: Records were grouped strictly by `pond_id` and sorted chronologically by sampling timestamp (`datetime`).
2. **Consecutive Pairing**: Observation at index $i$ (time $t$) is paired strictly with the immediate next observation at index $i+1$ (time $t+1$).
3. **Sampling Interval Window ($3 \le \Delta t \le 45$ days)**:
   - Pairs with $\Delta t < 3.0$ days are **excluded** to eliminate trivial auto-correlation from immediate re-sampling or diurnal duplicate visits.
   - Pairs with $\Delta t > 45.0$ days are **excluded** to prevent pairing across production crop cycles or fallow pond dry-out phases.
4. **Target Availability**: Both current and next observations must contain valid water quality and calculated ammonia records (no pairs with missing target values).
5. **No Future Measurements in $X_t$**: Features are constructed strictly from readings recorded at time $t$.

### Pair Construction Accounting
- **Total Raw Observations**: $6,945$ records across 317 ponds.
- **Valid Temporal Pairs ($3 \le \Delta t \le 45$ days)**: **$4,900$ pairs** across **303 unique ponds** ($95.58\%$ of all ponds).
- **Target Distribution at Next Visit ($t+1$)**:
  - Safe ($0$, $\text{NH}_3 < 0.05$ mg/L): **$4,586$ pairs ($93.59\%$)**.
  - High Risk ($1$, $\text{NH}_3 \ge 0.05$ mg/L): **$314$ pairs ($6.41\%$)**.
  - Class Imbalance Ratio: **$14.61 : 1$**.

### State Transition Dynamics ($t \rightarrow t+1$)
| Current Visit State ($t$) | Next Visit State ($t+1$) | Biogeochemical Meaning | Pair Count | Percentage (%) |
| :---: | :---: | :--- | :---: | :---: |
| **0 (Safe)** | **0 (Safe)** | Stable Quiescent Water Quality | **4,341** | **88.59%** |
| **0 (Safe)** | **1 (High Risk)** | **New Onset Risk Spike (Acute Surge)** | **204** | **4.16%** |
| **1 (High Risk)** | **0 (Safe)** | Mitigation / Environmental Recovery | **245** | **5.00%** |
| **1 (High Risk)** | **1 (High Risk)** | Persistent Toxic Chronic State | **110** | **2.24%** |
| **Total** | — | — | **4,900** | **100.00%** |

*Critical Dynamic*: Notice that out of $314$ total positive next-visit risk events, **$204$ events ($65.0\%$) represent new onset spikes ($0 \rightarrow 1$)**, where the pond was safe at visit $t$ but crossed into toxic hazard by visit $t+1$.

---

## 4. Feature Selection & Anti-Leakage Constraints

### 4.1 Permitted Features at Visit $t$ (12 Features)
Models are trained strictly on observations available at the current visit $t$, plus the scheduled revisit interval:
1. `gap_days`: Scheduled revisit interval ($\Delta t$ in days, $3.0$ to $45.0$). Modulates microbial kinetics, nutrient buildup, and organic matter decay time.
2. `curr_do`: Dissolved oxygen at visit $t$ (mg/L).
3. `curr_ph`: Water pH at visit $t$.
4. `curr_temp`: Water temperature at visit $t$ (°C).
5. `curr_turbidity`: Secchi depth at visit $t$ (cm).
6. `curr_tds`: Total dissolved solids at visit $t$ (ppt).
7. `tds_is_missing`: Missingness flag for current TDS probe.
8. `turbidity_is_missing`: Missingness flag for current Secchi disc.
9. `curr_weather`: Current meteorological condition (`Sunny`, `Cloudy`, `Rainy`, `Foggy`).
10. `curr_color`: Current algal bloom visual color.
11. `region`: Geographic farming district (`Eluru` vs. `Nellore`).
12. `curr_nh3`: Continuous un-ionized ammonia concentration at visit $t$ (mg/L).

### 4.2 Strictly Excluded Features
- **Next-Visit Measurements**: `next_nh3`, `next_do`, `next_ph`, `next_temp`, `next_datetime` (all future measurements at $t+1$ are barred).
- **Target Labels**: `next_risk` (the target variable). `curr_risk` is barred from the ML feature matrix to avoid circular label leakage; it is used strictly as the input for the Persistence Baseline.
- **Identifiers**: `pond_id` is barred from feature matrix $X$ to prevent memorizing farm baselines.

---

## 5. Dual Validation Protocols

### 5.1 Protocol 1: 5-Fold GroupKFold by `pond_id` (Spatial Generalization)
- **Goal**: Evaluate out-of-fold generalization to completely unseen ponds.
- **Grouping**: Grouped strictly on `pond_id` across the 4,900 pairs.
- **Independence**: Verified $\text{Ponds}_{\text{train}} \cap \text{Ponds}_{\text{val}} = \emptyset$ in all 5 folds.
- **Positive Allocation**: Each fold contains between 56 and 76 positive next-visit risk cases.

### 5.2 Protocol 2: Strict Chronological Validation (Temporal Generalization)
- **Cutoff Date**: `2025-01-01 00:00:00`.
- **Training Set**: Both visits occurred before cutoff (`curr_datetime < 2025-01-01` and `next_datetime < 2025-01-01`).  
  $N = 2,788$ pairs, **$257$ positives ($9.22\%$ prevalence)**.
- **Cross-Cutoff Exclusion**: Pairs straddling the 2025 boundary (`curr_datetime < 2025-01-01` but `next_datetime >= 2025-01-01`) are **strictly excluded ($N = 78$ pairs)** to ensure no observation from the test period leaks into training.
- **Test Set**: Current visit occurred after cutoff (`curr_datetime >= 2025-01-01`).  
  $N = 2,034$ pairs, **$57$ positives ($2.80\%$ prevalence)**.
- **Strict Protocol**: Preprocessing pipelines fitted strictly on training data. Zero hyperparameter tuning on the test set.

---

## 6. Candidate Models & Benchmarking Hierarchy

1. **Dummy Baseline (`Dummy_Prior`)**: Always predicts probabilities equal to training positive prevalence and predicts class $0$. Establishes the no-skill baseline.
2. **Persistence Baseline**: Predicts that the risk state at visit $t+1$ equals the risk state at visit $t$ ($\hat{y}_{t+1} = y_t$). Serves as the primary heuristic competitor.
3. **Logistic Regression (Balanced)**: Linear baseline with inverse class weighting (`class_weight='balanced'`).
4. **Random Forest (Balanced)**: Non-linear tree ensemble baseline (100 estimators, `min_samples_leaf=5`, `class_weight='balanced'`).

---

## 7. Primary Evaluation Metrics

Because the target exhibits class imbalance ($14.6 : 1$), **Accuracy is barred from primary decision-making**:
1. **PR-AUC (Average Precision)**: Primary ranking metric. Evaluated against the exact positive prevalence of each evaluation set ($0.0641$ for GroupKFold, $0.0280$ for Chronological Test).
2. **ROC-AUC**: Secondary discrimination metric.
3. **Recall (Sensitivity)**: Evaluated overall and specifically on **new onset spikes ($0 \rightarrow 1$)**.
4. **Precision (Positive Predictive Value)**.
5. **F1-Score**.
6. **Confusion Matrix (TP, FP, FN, TN)**.

