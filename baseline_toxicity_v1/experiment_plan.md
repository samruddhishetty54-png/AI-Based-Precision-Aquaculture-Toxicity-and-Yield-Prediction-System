# Experiment Plan: Baseline Toxicity Modeling Suite (`baseline_toxicity_v1`)

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Experiment Identifier:** `baseline_toxicity_v1`  
**Execution Phase:** Pre-Modeling Formulation & Documentation Phase  
**Source Dataset:** [`processed_data_v2/toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv) ($N = 6,945$, 27 columns)  
**Status:** **AWAITING USER APPROVAL — NO MODELS TRAINED OR EVALUATED**  

---

## 1. Suite Overview & Operational Context

In commercial pond aquaculture, un-ionized ammonia ($\text{NH}_3$) and severe oxygen depletion are primary drivers of acute toxic stress, respiratory distress, and mass mortality. However, continuous chemical reagent monitoring for ammonia is logistically difficult and costly. 

To address this challenge within rigorous scientific boundaries, this experiment suite defines three distinct, complementary machine learning formulations:
1. **Experiment 1 (Continuous Soft-Sensor):** Indirect estimation of calculated un-ionized ammonia from non-ammonia physical and physicochemical sensors.
2. **Experiment 2 (Mortality Classification):** Detection of acute mortality events (`dead_fish_count > 0`) using non-lethal water-quality indicators.
3. **Experiment 3 (Next-Visit Ammonia Risk):** Forecasting whether a pond will enter a high-risk ammonia state ($\text{NH}_3 \ge 0.05\text{ mg/L}$) at the next scheduled farm visit (3 to 45 days ahead).

> [!CAUTION]
> **MANDATORY SCIENTIFIC & PRACTICAL BOUNDARY:**  
> - **Calculated Proxy, Not Biological Ground Truth:**  
>   The un-ionized ammonia target (`primary_calculated_nh3_mg_l`) was derived mathematically from Total Ammonia Nitrogen (TAN), pH, and water temperature using the Emerson et al. aqueous chemical equilibrium formula adjusted by the stoichiometric molecular weight ratio ($17.031 / 14.007$). It is an aqueous chemical proxy, **not an independently measured analytical chemistry laboratory standard** (e.g., ion chromatography) and **not an independently validated biological toxicity indicator**.  
> - **Field Kit Error Propagation:**  
>   Because the target was derived from field-level TAN measurements, any inaccuracies, reagent degradation, or human observer biases in the raw field test kits propagate directly into the target.  
> - **Zero Execution Policy:**  
>   No machine learning models have been fitted, evaluated, or saved during this preparation phase.

---

## 2. Experiment 1: Soft-Sensor Ammonia Estimation

### 2.1 Task Formulation
- **Objective:** Estimate un-ionized ammonia concentration from routinely monitored water-quality parameters without requiring chemical ammonia test kits.
- **Task Type:** Supervised Continuous Regression.
- **Target Variable:** `primary_calculated_nh3_mg_l` ($\text{mg/L}$).
- **Target Distribution:** $N = 6,945$, non-negative continuous, right-skewed ($\text{skew} = +7.84$, $\text{min} = 0.000$, $\text{median} = 0.0116$, $\text{mean} = 0.0211$, $\text{max} = 0.8387\text{ mg/L}$).

### 2.2 Selected Input Features ($X$)
The model is restricted to exactly **8 predictive features**:
1. `dissolved_oxygen_mg_l` (Continuous, $\text{mg/L}$, 0.00% missing): Biological activity and photosynthesis indicator.
2. `ph` (Continuous, pH units, 0.00% missing): Primary thermodynamic driver of ammonia-ammonium chemical equilibrium.
3. `temp_c` (Continuous, $^\circ\text{C}$, 0.00% missing): Primary thermodynamic driver of the dissociation constant ($pK_a$).
4. `turbidity_cm` (Continuous, $\text{cm}$, 42.02% missing): Water clarity inversely related to algal biomass and suspended solids.
5. `tds_ppt` (Continuous, $\text{ppt}$, 47.56% missing): Total dissolved solids reflecting salinity and ionic strength.
6. `Weather` (Categorical, 4.48% missing): Meteorological condition influencing solar irradiance and temperature.
7. `water_color` (Categorical, 4.98% missing): Visual proxy for phytoplankton bloom type and organic density.
8. `region` (Categorical, 0.00% missing): Geographic cluster (`Eluru` vs. `Nellore`) capturing regional water chemistry and climate.

### 2.3 Excluded Columns & Leakage Prevention
To ensure methodological validity, **19 columns** are excluded from model inputs (see [`feature_selection_report.md`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/baseline_toxicity_v1/feature_selection_report.md) for the complete 19-row itemized audit table):
- **Raw Ammonia Columns:** `raw_ammonia_tan_nh3_n_mg_l` (23.87% missing), `raw_ammonia_tan_nh3_mg_l` (76.11% missing), and `reported_ammonia_nh3_unverified_mg_l` (76.10% missing). *Reason:* Including raw TAN turns the soft-sensor task into a trivial mathematical inversion of the Emerson formula.
- **Calculated Ammonia Pathways:** `calculated_nh3_from_tan_n_mg_l` (23.87% missing), `calculated_nh3_from_tan_nh3_mg_l` (76.11% missing), and `nh3_calculation_source` (0.00% missing). *Reason:* Direct mathematical identity with target (target leakage).
- **Provisional Heuristic Labels:** `provisional_ammonia_risk_heuristic`, `provisional_hypoxia_risk_heuristic`, `provisional_ph_stress_risk_heuristic`, `provisional_severity_heuristic`, `is_wq_in_range`, and `parameters_out_of_range`. *Reason:* Circular label leakage.
- **Clinical Symptoms & Outcomes:** `dead_fish_count` (26.25% missing), `air_gulping_count` (25.80% missing), `tail_splashing_count` (25.77% missing), and `provisional_behavioral_distress_observed` (0.00% missing). *Reason:* Post-hoc clinical consequences, not predictor variables.
- **Identifiers:** `pond_id` and `datetime` (0.00% missing). *Reason:* Barred from feature matrix $X$ to prevent memorizing individual pond baselines.

### 2.4 Candidate Baselines & Main Model
- **Baseline 1.1 (Dummy Mean):** Constant prediction equal to $\bar{y}_{\text{train}}$ ($0.02173\text{ mg/L}$). Provides the least-squares lower bound ($R^2 = 0.0$).
- **Baseline 1.2 (Dummy Median):** Constant prediction equal to $\text{median}(y_{\text{train}})$ ($0.01197\text{ mg/L}$). Provides the non-parametric lower bound for MAE.
- **Baseline 1.3 (pH + Temperature-Only Ablation Baseline):** Regressor trained strictly on `ph` and `temp_c`. Because un-ionized $\text{NH}_3$ fraction depends thermodynamically on pH and temperature, this ablation isolates how much target variance can be captured from thermodynamic dissociation alone without any indirect ecosystem signals.
- **Main Model:** `RandomForestRegressor(n_estimators=100, min_samples_leaf=2, random_state=42)`.
- **Evaluation Metrics:** Mean Absolute Error (MAE), Root Mean Squared Error (RMSE), Coefficient of Determination ($R^2$).

---

## 3. Experiment 2: Mortality Classification

### 3.1 Task Formulation
- **Objective:** Predict the occurrence of fish mortality events at the time of water sampling using environmental water-quality measurements.
- **Task Type:** Supervised Binary Classification.
- **Target Variable Definition:** Binary flag derived from `dead_fish_count`:
  $$\text{Mortality Observed} = \begin{cases} 1 & \text{if } \text{dead\_fish\_count} > 0 \\ 0 & \text{if } \text{dead\_fish\_count} == 0 \end{cases}$$

### 3.2 Target Distribution, Missingness & Class Imbalance
- **Dataset-Level Missingness:** In `toxicity_analysis_v2.csv`, `dead_fish_count` has **1,823 missing values (26.25%)**.
  - A temporal audit shows that during 2021 and 2022, `dead_fish_count` was **100% unrecorded** (technicians did not collect mortality tallies).
  - Regular collection commenced in mid-2023 and continued through 2026.
- **Class Counts on Evaluated Records ($N = 5,122$ with recorded mortality):**
  - **Negative Class (0 - No dead fish observed):** $5,047\text{ records}$ ($98.54\%$)
  - **Positive Class (1 - Mortality observed, 1 to 200+ fish):** $75\text{ records}$ ($1.46\%$)
  - **Class Imbalance Ratio:** **$67.3 : 1$** (Extreme class imbalance).
- If unrecorded 2021–2022 records are assumed zero, $N = 6,945$, with $6,870$ negative ($98.92\%$) and $75$ positive ($1.08\%$), yielding an imbalance of $91.6 : 1$.

### 3.3 Feature Space & Exclusion Rules
- **Permitted Features:** The 8 non-lethal water-quality parameters (`dissolved_oxygen_mg_l`, `ph`, `temp_c`, `turbidity_cm`, `tds_ppt`, `Weather`, `water_color`, `region`).
- **Strictly Excluded Features:**
  - `dead_fish_count` (direct target source).
  - Any notes or text referencing mortality (`Notes (mortalities)`).
  - Clinical symptom indicators (`air_gulping_count`, `tail_splashing_count`, `provisional_behavioral_distress_observed`) to evaluate whether chemical/physical parameters alone can anticipate mortality.
  - All provisional severity labels (`provisional_severity_heuristic`) which directly incorporate dead fish count.

### 3.4 Baselines, Modeling & Validation Strategy
- **Baseline 2.1 (Majority-Class Classifier):** Always predicts negative class (0). Achieves an uninformative accuracy of **$98.54\%$** while detecting zero mortality events ($\text{Recall} = 0.0$, $\text{F1} = 0.0$).
- **Suitable Validation Strategy:** GroupKFold by `pond_id` (5 folds). Because the positive class is rare (75 cases), GroupKFold allocates between 6 and 19 positive cases per fold. Every fold contains positive cases (no fold lacks positive cases).
- **Evaluation Metrics:** Accuracy must **not** be used as a primary decision metric. Evaluation must rely on:
  - Precision-Recall AUC (PR-AUC / Average Precision)
  - Minority Class Recall (Sensitivity)
  - Minority Class Precision and F1-Score
  - Balanced Accuracy

---

## 4. Experiment 3: Next-Visit Ammonia Risk

### 4.1 Task Formulation
- **Objective:** Forecast whether a pond will enter or remain in a high-risk un-ionized ammonia state ($\text{primary\_calculated\_nh3\_mg\_l} \ge 0.05\text{ mg/L}$) at the next routine farm visit, using only observations available at the current visit.
- **Task Type:** Temporal Lagged Binary Classification.
- **Pairing Criteria:** Consecutive observations from the **same pond** where the sampling interval $\Delta t = t_{\text{next}} - t_{\text{current}}$ satisfies:
  $$3\text{ days} \le \Delta t \le 45\text{ days}$$
  Pairs with $\Delta t < 3\text{ days}$ are excluded to avoid trivial diurnal auto-correlation; pairs with $\Delta t > 45\text{ days}$ are excluded to avoid spanning across production crop cycles.

### 4.2 Sample Size & Sufficiency Audit
- **Total Rows in Toxicity Dataset:** $6,945$
- **Total Valid Consecutive Pairs ($3 \le \Delta t \le 45\text{ days}$):** **$4,900\text{ pairs}$**
- **Unique Ponds Represented:** $303\text{ ponds}$ (out of 317, representing $95.58\%$ of all ponds).
- **Target Distribution at Next Visit ($t_{\text{next}}$):**
  - Next Visit Safe ($\text{NH}_3 < 0.05\text{ mg/L}$): $4,586\text{ pairs}$ ($93.59\%$)
  - Next Visit High Risk ($\text{NH}_3 \ge 0.05\text{ mg/L}$): $314\text{ pairs}$ ($6.41\%$)

### 4.3 State Transition Matrix & Dynamics
Analyzing state transitions between current visit ($t$) and next visit ($t+1$):

| Current Visit State ($t$) | Next Visit State ($t+1$) | Transition Description | Pair Count | Percentage (%) |
| :---: | :---: | :--- | :---: | :---: |
| **0 (Safe)** | **0 (Safe)** | Stable Safe Baseline | **4,341** | **88.59%** |
| **0 (Safe)** | **1 (High Risk)** | **New Risk Onset / Spike** | **204** | **4.16%** |
| **1 (High Risk)** | **0 (Safe)** | Recovery / Mitigation | **245** | **5.00%** |
| **1 (High Risk)** | **1 (High Risk)** | **Persistent High Risk** | **110** | **2.24%** |
| **Total** | — | — | **4,900** | **100.00%** |

### 4.4 Sufficiency Assessment
> [!NOTE]
> **FEASIBILITY DETERMINATION: EXPERIMENT 3 IS VIABLE.**  
> - With **4,900 valid consecutive observation pairs** and **314 positive next-visit high-risk cases** (including 204 new onset spikes), sample size is sufficient for training and cross-validating machine learning models.  
> - Under 5-fold GroupKFold by `pond_id`, each test fold contains between 56 and 76 positive risk events, providing sufficient statistical support for out-of-sample evaluation.

### 4.5 Strict Temporal Leakage Elimination
- **Current-Time Feature Constraint:** Feature matrix $X_t$ must be constructed **strictly from measurements recorded at time $t$** (or historical visits $\le t$).  
- **Prohibited Information:** No water-quality reading, weather observation, or operational action from $t+1$ may enter $X_t$. The sampling interval ($\Delta t$ in days) may be included as a current feature representing the scheduled re-visit interval.

### 4.6 Baselines & Evaluation Metrics
- **Baseline 3.1 (Same-as-Last-Visit Persistence Baseline):** Predicts that the next state equals the current state ($\hat{y}_{t+1} = y_t$).  
  - Correct on stable safe ($4,341$) and persistent risk ($110$) = $4,451 / 4,900 = \mathbf{90.84\%}$ accuracy.  
  - Fails completely on all 204 new risk spikes ($0 \rightarrow 1$) and all 245 recovery events ($1 \rightarrow 0$).
- **Baseline 3.2 (Majority-Class Baseline):** Always predicts safe ($\hat{y}_{t+1} = 0$). Accuracy = **$93.59\%$** ($4,586 / 4,900$).
- **Evaluation Metrics:** PR-AUC, F1-score on the positive class ($y_{t+1}=1$), and specifically Recall on the new spike subset ($0 \rightarrow 1$).

---

## 5. Consolidated Master Baselines List

To ensure consistent benchmarking, the candidate baselines across all three experiments are consolidated below:

| Experiment | Baseline Identifier | Baseline Name | Mechanism / Rule | Target Metric Benchmark |
| :--- | :--- | :--- | :--- | :--- |
| **Exp 1: Soft-Sensor** | `B1.1` | Dummy Regressor (Mean) | Always predicts $\bar{y}_{\text{train}} = 0.02173\text{ mg/L}$ | Establishes $R^2 = 0.000$; upper bound for RMSE |
| **Exp 1: Soft-Sensor** | `B1.2` | Dummy Regressor (Median) | Always predicts $\text{median}(y_{\text{train}}) = 0.01197\text{ mg/L}$ | Establishes minimum MAE without feature learning |
| **Exp 1: Soft-Sensor** | `B1.3` | pH + Temp Ablation Baseline | Regressor trained strictly on `ph` and `temp_c` | Isolates thermodynamic equilibrium contribution |
| **Exp 2: Mortality** | `B2.1` | Majority-Class Classifier | Always predicts 0 (No dead fish observed) | Achieves 98.54% accuracy; sets baseline Recall = 0.000 |
| **Exp 3: Next Risk** | `B3.1` | Same-as-Last-Visit Baseline | Predicts $\hat{y}_{t+1} = y_t$ (persistence heuristic) | Achieves 90.84% accuracy; fails on all new spikes (0→1) |
| **Exp 3: Next Risk** | `B3.2` | Majority-Class Classifier | Always predicts 0 (Safe next visit) | Achieves 93.59% accuracy; sets baseline Recall = 0.000 |

---

## 6. Execution Protocol & Verification Summary

1. **Model Training Status:** **FROZEN.** No training scripts have been executed.
2. **Prepared Data Files Status:** As reported in Section 7 of the Data Split Summary, `train_toxicity_v1.csv` and `test_toxicity_v1.csv` are existing holdout split files that remain completely unmodified.
3. **Approval Requirement:** Modeling will proceed only after user review and explicit authorization.
