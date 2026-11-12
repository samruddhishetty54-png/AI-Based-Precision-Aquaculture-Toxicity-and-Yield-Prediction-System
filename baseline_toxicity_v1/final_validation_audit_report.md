# Final Pre-Training Validation Audit Report

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Audit Phase:** Pre-Modeling Final Verification & Feasibility Audit  
**Source Dataset:** [`processed_data_v2/toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv) ($N = 6,945$, 27 columns)  
**Deliverable Document:** `baseline_toxicity_v1/final_validation_audit_report.md`  
**Execution Status:** **AUDIT COMPLETED — ZERO MODELS TRAINED OR EXECUTED**  

---

## 1. Executive Summary

In accordance with strict pre-training verification guidelines, this document provides the final empirical validation of the three planned machine learning experiments before any model fitting begins:
1. **Experiment 1:** Continuous Soft-Sensor Ammonia Estimation
2. **Experiment 2:** Rare-Event Fish Mortality Classification (`dead_fish_count > 0`)
3. **Experiment 3:** Next-Visit High Ammonia Risk Forecasting ($3 \le \Delta t \le 45\text{ days}$)

All data checks, temporal boundaries, leakage restrictions, and baseline evaluations were calculated strictly on the frozen dataset. No model estimators were trained.

---

## 2. Experiment 1: Soft-Sensor Ammonia Estimation Audit

### 2.1 Feature Availability at Prediction Time
The model is granted access to exactly 8 non-ammonia features:
- `dissolved_oxygen_mg_l` (Continuous, 0.00% missing) — Field optical probe.
- `ph` (Continuous, 0.00% missing) — Field glass electrode probe.
- `temp_c` (Continuous, 0.00% missing) — Field thermistor probe.
- `turbidity_cm` (Continuous, 42.02% missing) — Field Secchi disk measurement.
- `tds_ppt` (Continuous, 47.56% missing) — Handheld conductivity/TDS meter.
- `Weather` (Categorical, 4.48% missing) — Field visual weather log.
- `water_color` (Categorical, 4.98% missing) — Field visual water hue log.
- `region` (Categorical, 0.00% missing) — Farm geographic location (`Eluru` vs. `Nellore`).

**Audit Finding:** All 8 features represent standard, field-accessible environmental and operational parameters available at water inspection time without chemical testing.

### 2.2 Leakage Verification & Target Component Elimination
A comprehensive scan of all 27 columns in `toxicity_analysis_v2.csv` verifies:
- **Raw Ammonia Excluded:** `raw_ammonia_tan_nh3_n_mg_l` (23.87% missing), `raw_ammonia_tan_nh3_mg_l` (76.11% missing), and `reported_ammonia_nh3_unverified_mg_l` (76.10% missing) are excluded from $X$.
- **Intermediate Formulas Excluded:** `calculated_nh3_from_tan_n_mg_l`, `calculated_nh3_from_tan_nh3_mg_l`, and `nh3_calculation_source` are excluded from $X$.
- **Heuristic Labels Excluded:** `provisional_ammonia_risk_heuristic`, `provisional_hypoxia_risk_heuristic`, `provisional_ph_stress_risk_heuristic`, `provisional_severity_heuristic`, `is_wq_in_range`, and `parameters_out_of_range` are excluded from $X$.
- **Clinical Symptoms Excluded:** `air_gulping_count`, `tail_splashing_count`, `dead_fish_count`, and `provisional_behavioral_distress_observed` are excluded from $X$.
- **Identifiers Excluded:** `pond_id` and `datetime` are barred from $X$.

**Audit Finding:** **Zero leakage.** There is no feature that directly or indirectly reveals the chemical nitrogen pool or mathematically derives the target.

### 2.3 Scientific Nature of the Target
> [!CAUTION]
> **TARGET DEFINITION BOUNDARY:**  
> The target variable `primary_calculated_nh3_mg_l` is a **calculated aqueous chemical equilibrium proxy**. It was computed by applying the Emerson et al. formula and the stoichiometric molecular weight ratio ($17.031 / 14.007$) to field Total Ammonia Nitrogen (TAN), pH, and water temperature. It is **not** an independently verified analytical laboratory measurement and **not** an independently measured biological toxicity ground truth. Field reagent and human titrator errors are embedded in the target.

---

## 3. Experiment 2: Mortality Classification Audit

### 3.1 Verification of Case Counts & Missingness
- **Dataset Total Rows:** 6,945
- **Unrecorded / Missing Rows:** 1,823 (26.25%)
- **Evaluated Non-Missing Rows ($N = 5,122$):**
  - **Negative Cases (`dead_fish_count == 0`):** **5,047 records** ($98.54\%$)
  - **Positive Cases (`dead_fish_count > 0`):** **75 records** ($1.46\%$)
- **Missing Data Policy Verification:**  
  Missing observations occurred during 2021 and 2022 when mortality tallies were not collected in field operations ($100\%$ unrecorded in 2021–2022). All 1,823 unrecorded visits are **strictly excluded** from mortality classification evaluation and **not zero-filled**. Zero-filling would invent unconfirmed survival labels.

### 3.2 Spatio-Temporal Distribution of Positive Cases
- **Pond Distribution:**
  - Evaluated unique ponds: 286 ponds.
  - Ponds with at least one mortality event: **53 unique ponds** ($18.53\%$ of evaluated ponds).
  - Ponds with 1 death event: 37 ponds.
  - Ponds with 2 death events: 10 ponds.
  - Ponds with 3 death events: 6 ponds.
  - Max positive count per pond: 3. No single pond dominates the positive class.
- **Annual Temporal Progression:**
  - **2021:** 0 evaluated (309 unrecorded).
  - **2022:** 0 evaluated (1,431 unrecorded).
  - **2023:** 999 evaluated $\rightarrow$ **17 positives** ($1.70\%$)
  - **2024:** 1,523 evaluated $\rightarrow$ **14 positives** ($0.92\%$)
  - **2025:** 1,563 evaluated $\rightarrow$ **29 positives** ($1.86\%$)
  - **2026:** 1,037 evaluated $\rightarrow$ **15 positives** ($1.45\%$)

Positive cases are distributed across multiple seasons and diverse ponds rather than concentrated in an isolated outbreak.

### 3.3 Evaluation Metrics Specification
Due to extreme class imbalance ($67.3 : 1$), standard accuracy ($98.54\%$ for majority class) is completely uninformative. Performance must be reported using:
1. **Precision-Recall AUC (PR-AUC / Average Precision)** — Primary ranking metric.
2. **Minority Class Recall (Sensitivity)** — Primary safety metric (proportion of fish kill events detected).
3. **Minority Class Precision & F1-Score** — False alarm rate control.
4. **Confusion Matrix ($2 \times 2$)** — Direct tally of true positives, false positives, true negatives, and false negatives.

---

## 4. Experiment 3: Next-Visit Ammonia Risk Audit

### 4.1 Consecutive Observation Pairing Verification
- **Pairing Criteria:** Consecutive observations sorted by `datetime` strictly within the same `pond_id`.
- **Intra-Pond Verification:** `(valid_pairs['pond_id'] == valid_pairs['next_pond_id']).all()` evaluated to **True**. Zero inter-pond pairs exist.
- **Sampling Interval ($\Delta t$):** Filtered strictly to $3.0 \le \Delta t \le 45.0\text{ days}$.
  - Min: 3.00 days
  - 25th percentile: 14.59 days
  - Median: 22.00 days
  - 75th percentile: 30.00 days
  - Max: 44.999 days
  - Mean: 22.34 days, Standard Deviation: 10.06 days.

### 4.2 Temporal Boundary & Anti-Leakage Rule
- Feature matrix $X_t$ is constructed **strictly from measurements recorded at time $t$** (current visit).
- Target $y_{t+1}$ is evaluated strictly at time $t+1$ (next visit).
- Re-visit gap $\Delta t$ is permitted as a current feature representing the scheduled visit latency.
- No future observation, weather forecast, or subsequent measurement from $t+1$ is accessible to $X_t$.

### 4.3 GroupKFold Group Isolation
Under 5-fold `GroupKFold` on the 303 unique ponds:
- **Pond Overlap across Train and Validation:** **0 ponds** (verified across all 5 folds).
- No pond appearing in a training fold ever appears in the corresponding validation fold.

### 4.4 Empirical Baseline Evaluation on Valid Pairs ($N = 4,900$)
Target at next visit: $314\text{ positive}$ ($6.41\%$) vs $4,586\text{ negative}$ ($93.59\%$).

| Metric | Majority-Class Baseline (Always Predict Safe: $\hat{y}_{t+1}=0$) | Same-as-Last-Visit Baseline (Persistence: $\hat{y}_{t+1}=y_t$) |
| :--- | :---: | :---: |
| **Accuracy** | **93.59%** | **90.84%** |
| **Recall (Sensitivity)** | **0.00%** ($0 / 314$) | **35.03%** ($110 / 314$) |
| **Precision** | **0.00%** | **30.99%** ($110 / 355$) |
| **F1-Score** | **0.0000** | **0.3288** |
| **PR-AUC** | **0.0641** | **0.1502** |
| **Confusion Matrix** | $\begin{bmatrix} 4586 & 0 \\ 314 & 0 \end{bmatrix}$ | $\begin{bmatrix} 4341 & 245 \\ 204 & 110 \end{bmatrix}$ |

**Key Diagnostic:** The Same-as-Last-Visit persistence baseline successfully captures 110 persistent high-risk states, but **fails completely on all 204 newly emerging risk spikes ($0 \rightarrow 1$)**. This highlights the exact operational value an ML model must provide: early detection of new onset spikes before they persist.

---

## 5. Chronological Validation Audit: 2021–2024 vs. 2025–2026

### 5.1 Partition Profile & Row Counts
A temporal cutoff at `2025-01-01 00:00:00` divides the longitudinal horizon into historical baseline vs. modern deployment:
- **Total Dataset:** 6,945 rows
- **Training Set (2021–2024):** **4,345 rows** ($62.56\%$) across 239 active ponds.
- **Testing Set (2025–2026):** **2,600 rows** ($37.44\%$) across 176 active ponds.

### 5.2 Target Breakdown across Chronological Partitions

| Experiment | Training Partition (2021–2024) | Testing Partition (2025–2026) |
| :--- | :--- | :--- |
| **Exp 1: Soft-Sensor NH3** | $N = 4,345$, Mean = $0.0223\text{ mg/L}$, Med = $0.0125$ | $N = 2,600$, Mean = $0.0191\text{ mg/L}$, Med = $0.0104$ |
| **Exp 2: Mortality ($N_{\text{eval}}$)** | $N_{\text{eval}} = 2,522$ (1,823 unrecorded excluded)<br>• Positive ($>0$): **31** ($1.23\%$)<br>• Negative ($==0$): **2,491** ($98.77\%$) | $N_{\text{eval}} = 2,600$ (0 unrecorded)<br>• Positive ($>0$): **44** ($1.69\%$)<br>• Negative ($==0$): **2,556** ($98.31\%$) |
| **Exp 3: Next-Visit Risk Pairs** | $N_{\text{pairs}} = 2,866$ (Current visit $< 2025$)<br>• Positive ($y_{t+1}=1$): **257** ($8.97\%$)<br>• Negative ($y_{t+1}=0$): **2,609** ($91.03\%$) | $N_{\text{pairs}} = 2,034$ (Current visit $\ge 2025$)<br>• Positive ($y_{t+1}=1$): **57** ($2.80\%$)<br>• Negative ($y_{t+1}=0$): **1,977** ($97.20\%$) |

### 5.3 Pond Overlap across Chronological Split
- Unique ponds in Train (2021–2024): 239
- Unique ponds in Test (2025–2026): 176
- **Overlapping Ponds:** **98 ponds** ($55.68\%$ of test ponds were also observed in the training period).
- **Novel Ponds in Test:** **78 ponds** ($44.32\%$ newly enrolled ponds).

### 5.4 Feature Missingness Comparison & The 2025–2026 Protocol Shift

| Feature | Train Missingness (2021–2024) | Test Missingness (2025–2026) | Operational & Biogeochemical Impact |
| :--- | :---: | :---: | :--- |
| `dissolved_oxygen_mg_l` | 0.00% | 0.00% | Stable core sensor; unaffected by protocol shift. |
| `ph` | 0.00% | 0.00% | Stable core sensor; unaffected by protocol shift. |
| `temp_c` | 0.00% | 0.00% | Stable core sensor; unaffected by protocol shift. |
| `turbidity_cm` | 7.32% | **100.00%** | **Sensor Terminated.** Field teams ceased Secchi disk collection in 2025. |
| `tds_ppt` | 16.18% | **100.00%** | **Sensor Terminated.** Field teams ceased handheld TDS collection in 2025. |
| `Weather` | 7.16% | 0.00% | Logging improved to 100% completeness in 2025–2026. |
| `water_color` | 7.96% | 0.00% | Logging improved to 100% completeness in 2025–2026. |
| `region` | 0.00% | 0.00% | Static metadata; 100% complete. |

**Impact Analysis of the Protocol Shift:**
In post-2024 operations, field teams eliminated turbidity and TDS testing. When evaluating models chronologically, `turbidity_cm` and `tds_ppt` in the test partition will be entirely filled with training median constants. This creates an authentic stress-test: it demonstrates whether model predictions depend primarily on DO, pH, temperature, weather, and color, or whether accuracy collapses when physical telemetry is degraded.

---

## 6. Remaining Risks & Technical Challenges

1. **Calculated Proxy Target (Experiment 1):**  
   The target is derived from TAN test kit readings using Emerson's formula. It is an aqueous chemical proxy, not an independently measured laboratory ground truth. Any field titrator noise is embedded in the target.
2. **Extreme Class Imbalance (Experiment 2):**  
   Mortality events occur in only $1.46\%$ of evaluated observations (75 / 5,122). Standard cross-entropy or mean squared error will collapse to predicting the majority class (98.54% accuracy, 0% recall). Models must incorporate `class_weight='balanced'` and probability threshold tuning to be practically viable.
3. **Severe Telemetry Loss (Chronological Generalization):**  
   The complete absence of TDS and Turbidity in 2025–2026 means any model that relies heavily on those two features will suffer degradation in recent seasons.
4. **Positive Risk Prevalence Shift (Experiment 3):**  
   Next-visit high-risk prevalence drops from $8.97\%$ in 2021–2024 to $2.80\%$ in 2025–2026, indicating either improved farmer management or unobserved seasonal dampening.

---

## 7. Recommendation: Which Experiment Should Be Trained First?

### **Recommendation: Train Experiment 1 (Soft-Sensor Ammonia Estimation) FIRST.**

### Justification:
1. **Unbroken Data Completeness:** Experiment 1 possesses complete target coverage across all $6,945\text{ rows}$ ($0\text{ missing}$ target values), whereas Experiment 2 has 1,823 unrecorded visits ($26.25\%$) that must be quarantined.
2. **Foundational Biogeochemical Signal:** Establishing whether basic physical parameters (DO, pH, temperature, visual color, weather) can model aqueous ammonia is the scientific core of the entire precision aquaculture project.
3. **Direct Baseline Proof:** The clear progression from Dummy Mean $\rightarrow$ Dummy Median $\rightarrow$ pH+Temp Ablation $\rightarrow$ Random Forest Regressor provides an unambiguous, step-by-step demonstration of true machine learning lift above simple equilibrium guessing.
4. **Downstream Value:** Continuous un-ionized ammonia estimates from Experiment 1 directly inform the risk thresholds used in Experiment 2 (Mortality) and Experiment 3 (Next-Visit Risk).

