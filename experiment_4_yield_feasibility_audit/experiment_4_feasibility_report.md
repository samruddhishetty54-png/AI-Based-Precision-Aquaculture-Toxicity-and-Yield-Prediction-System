# Experiment 4 Feasibility Audit: Fish Growth & Yield Prediction

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Audit Scope:** Data Feasibility and Target Defensibility Audit for Experiment 4  
**Audit Date:** November 3, 2026  
**Status:** Audit Complete — Pre-Training Feasibility Assessment  
**Audit Directory:** `experiment_4_yield_feasibility_audit/`  
**Referenced Datasets:**  
- Farm Water Quality & Survey Dataset: [`water_quality.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/dataset/water_quality.csv) ($N = 12,431$)
- Enrolled Ponds Profile: [`enrolled_ponds_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/enrolled_ponds_v2.csv) ($N = 324$)
- Dropout Registry: [`dropouts_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/dropouts_v2.csv) ($N = 128$)
- Curated Fish Health & Growth Dataset: [`fish_health_growth_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/fish_health_growth_analysis_v2.csv) ($N = 9,422$)
- Curated Feeding Dataset: [`feeding_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/feeding_analysis_v2.csv) ($N = 6,752$)
- IoT Sensor Benchmark: [`iot_water_model_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/iot_water_model_v2.csv) ($N = 4,383$)

---

## Executive Summary

Before undertaking model development for **Experiment 4: Fish Growth and Yield Prediction**, a comprehensive data feasibility audit was conducted across all raw and processed project datasets. 

This audit investigates whether the available data can scientifically support:
1. End-of-cycle agricultural harvest yield prediction (e.g., metric tons per acre),
2. Total living harvest biomass prediction (e.g., total kilograms harvested), or
3. Dynamic fish growth and somatic weight gain prediction across routine farm observation intervals.

### Critical Feasibility Conclusions
1. **Genuine Harvest Yield Prediction is SCIENTIFICALLY INFEASIBLE:**  
   Across all 12,431 farm records, 324 enrolled pond profiles, and 128 dropout records, there are **EXACTLY ZERO (0) RECORDS of actual harvested biomass, harvest yield, stocking dates, or harvest dates**. Calculating "synthetic yield" by multiplying sample fish weight by stocking density and pond area would create an unvalidated mathematical simulation lacking empirical ground truth, in direct violation of scientific integrity standards.
2. **Days of Culture (DOC) CANNOT be reliably calculated:**  
   No stocking date was recorded during farm enrollment. Ponds were enrolled at arbitrary, heterogeneous stages of their production cycles: on their very first recorded visit, **74.8% of ponds already had fish weighing $> 100\text{ g}$, and 32.7% had fish weighing $> 500\text{ g}$**. Assuming the enrollment or first observation date is Day 0 (stocking) introduces massive, irrecoverable temporal errors.
3. **Pond-Level Fish Growth Prediction is CONDITIONALLY FEASIBLE:**  
   There are **5,569 non-null fish weight measurements** across 265 unique farm ponds. When aggregated by visit date and paired across consecutive routine farm visits ($3 \le \Delta t \le 45$ days), there exist **2,497 valid temporal observation pairs** across 240 unique ponds. Over an average revisit interval of 23.5 days, mean weight gain is $+41.16\text{ g}$, corresponding to an average daily growth rate of $1.68\text{ g/day}$, which aligns precisely with established commercial Indian major carp aquaculture bioenergetics.
4. **Best Recommended Prediction Target:**  
   The most scientifically defensible, empirically grounded target is **Next-Visit Average Fish Weight ($W_{t+1}$ in grams)** or **Interval Weight Gain ($\Delta W$ in grams)** over scheduled 3–45 day revisit windows, conditioned on initial body weight ($W_t$), elapsed days ($\Delta t$), feeding rates, stocking density, pond area, and water quality parameters.

---

## 1. Available Dataset Inventory & Variable Mapping

Every dataset in the repository was comprehensively audited for variables related to fish weight, fish counts, stocking dates, harvest dates, species, pond area, stocking density, feed, mortality, and yield. The complete column mapping is exported as [`yield_data_inventory.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_yield_feasibility_audit/yield_data_inventory.csv) and summarized below in Table 1.

### Table 1: Comprehensive Variable Inventory for Growth and Yield Modeling

| Category | Column Name | Source Table | Data Type | Populated / Total | Coverage | Analytical Role & Feasibility |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| **Fish Weight** | `Weight` | `water_quality.csv` | `float64` | 5,569 / 12,431 | 44.80% | **Available Ground Truth:** Measured average body weight of sampled fish in grams from pond cast-netting. |
| **Fish Weight** | `average_fish_weight_g` | `fish_health_growth_analysis_v2.csv` | `float64` | 5,566 / 9,422 | 59.07% | Cleaned average fish weight merged with pond area and profile history. |
| **Fish Weight** | `Average Fish Weight (g)` | `iot_water_model_v2.csv` | `float64` | 4,383 / 4,383 | 100.00% | **Synthetic/Benchmark Only:** Hourly single-sensor series without pond IDs; fish weight decreases linearly from March to May (286.5g down to 262.05g). Incompatible with multi-farm models. |
| **Stocking Date** | *[ABSENT IN ALL TABLES]* | None | `datetime` | **0 / 12,431** | **0.00%** | **Fatal Deficiency:** Calendar stocking date was never recorded. Prevents calculation of true Days of Culture (DOC). |
| **Harvest Date** | *[ABSENT IN ALL TABLES]* | None (31 text notes only) | `datetime` | **0 / 12,431** | **0.00%** | **Fatal Deficiency:** Structured harvest date does not exist. 31 informal free-text notes explain missed follow-up visits due to harvest. |
| **Harvested Biomass** | *[ABSENT IN ALL TABLES]* | None | `float64` | **0 / 12,431** | **0.00%** | **Fatal Deficiency:** Actual total harvested mass (kg or metric tons) was never recorded. |
| **Harvest Yield** | *[ABSENT IN ALL TABLES]* | None | `float64` | **0 / 12,431** | **0.00%** | **Fatal Deficiency:** Area-normalized harvest yield (tons/acre) does not exist. |
| **Stocking Density** | `Stocking density (per acre)` | `water_quality.csv` | `float64` | 9,780 / 12,431 | 78.67% | **Available Feature:** Number of fish stocked per acre. Key crowding and carrying-capacity covariate. |
| **Fish Species** | `Species` | `water_quality.csv` | `object` | 8,650 / 12,431 | 69.58% | **Available Feature:** Cultured species mix. 90.6% polyculture of Catla (*Catla catla*) and Rohu (*Labeo rohita*). |
| **Pond Area** | `Pond area in acres` | `enrolled_ponds_v2.csv` | `float64` | 277 / 324 | 85.49% | **Available Feature:** Surface water area. Mean = 14.26 acres (range: 0.13 to 54.0 acres). Merged to 98.5% of health records. |
| **Pond Depth** | `Depth in meters` | `enrolled_ponds_v2.csv` | `float64` | 324 / 324 | 100.00% | **Available Feature:** Operating pond depth. Mean = 2.05 m. |
| **Feed Quantity** | `Feed amount (kg)` | `water_quality.csv` | `float64` | 6,756 / 12,431 | 54.35% | **Available Feature:** Daily feed quantity in kg. Mean = 565.3 kg (median = 350 kg). Primary somatic energy source. |
| **Feed Frequency** | *[ABSENT AS EXPLICIT COL]* | None | `int` | **0 / 12,431** | **0.00%** | Feeding frequency per day not recorded; feeding practices captured under categorical `Existing practices`. |
| **Fish Mortality** | `Dead fish` | `water_quality.csv` | `float64` | 8,523 / 12,431 | 68.56% | **Available Feature:** Daily observed floating mortalities during field officer visits. Mean = 2.03 dead fish. |
| **Observation Date** | `Date of data collection` | `water_quality.csv` | `object` | 12,431 / 12,431 | 100.00% | **Available Index:** Temporal anchor for chronological ordering and revisit interval calculation. |

---

## 2. Granular Data Quality & Anomaly Analysis

All relevant candidate predictive features and target variables were audited for missingness, distribution properties, truncation, and data anomalies. The complete audit matrix is exported as [`yield_data_quality_report.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_yield_feasibility_audit/yield_data_quality_report.csv) and summarized below in Table 2.

### Table 2: Data Quality, Distribution, and Anomaly Audit

| Variable | Populated ($N$) | Missing (%) | Min | P25 | Median | Mean | P75 | Max | Quality Findings & Anomalies |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`Weight` (g)** | 5,569 | 55.20% | 0.0 | 250.0 | 500.0 | 548.8 | 800.0 | 2,000.0 | Exactly 1 record with $0\text{g}$; rounded to nearest 25g/50g/100g bins; 144 revisit pairs show apparent negative delta due to partial harvest thinning. |
| **`Feed amount (kg)`** | 6,756 | 45.65% | 0.0 | 100.0 | 350.0 | 565.3 | 900.0 | 3,300.0 | 1 record with $0\text{kg}$; 5 records $\ge 3,000\text{kg}$ representing bulk farm feeding deliveries rather than single ration. |
| **`Stocking density (/acre)`**| 9,780 | 21.33% | 0.0 | 2,285.0 | 2,791.0 | 8,654.2 | 5,059.0 | 235,294.0 | 5 records with $0$; 10 records $\ge 200,000$ (nursery/fingerling rearing ponds rather than standard commercial grow-out ponds). |
| **`Dead fish`** | 8,523 | 31.44% | 0.0 | 0.0 | 0.0 | 2.03 | 0.0 | 2,717.0 | 89.8% of visits report 0 dead fish; 1 catastrophic mass mortality event of 2,717 dead fish in pond `ara2_fe1074da`. |
| **`Pond area in acres`** | 277 | 14.51% | 0.13 | 3.44 | 9.07 | 14.26 | 21.50 | 54.00 | 47 enrolled ponds missing area in profile; highly skewed commercial distribution. |
| **`DO (mg/L)`** | 12,412 | 0.15% | 0.20 | 3.60 | 5.20 | 5.75 | 7.60 | 20.00 | 364 records with acute hypoxia ($< 1.0\text{ mg/L}$); 158 afternoon supersaturation records ($> 15\text{ mg/L}$). |
| **`pH`** | 12,412 | 0.15% | 5.10 | 7.61 | 7.85 | 7.88 | 8.13 | 9.90 | Alkaline spikes ($> 9.0$) in 73 records; acid stress ($< 6.5$) in 48 records. |
| **`Temp (in °C)`** | 12,410 | 0.17% | 17.5 | 26.2 | 27.5 | 27.7 | 29.3 | 38.6 | Biologically valid seasonal temperature range for Andhra Pradesh aquaculture. |
| **`Stocking date`** | **0** | **100.0%** | — | — | — | — | — | — | **FATAL:** 100% missing across all farm tables. |
| **`Harvested biomass`** | **0** | **100.0%** | — | — | — | — | — | — | **FATAL:** 100% missing across all farm tables. |
| **`Harvest yield`** | **0** | **100.0%** | — | — | — | — | — | — | **FATAL:** 100% missing across all farm tables. |

---

## 3. In-Depth Scientific Investigation of Feasibility Questions

### 3.1 Are individual fish weights available?
**NO.** Individual tagged fish weight trajectories do not exist.  
The values in `Weight` represent **pond-level aggregate sample body weights** obtained by farm field officers via cast netting or farmer interview. In standard commercial practice in Andhra Pradesh, 5 to 10 fish are captured in a cast net, weighed collectively, and the average gram weight per fish is recorded.

### 3.2 Are stocking dates available, and can Days of Culture (DOC) be calculated?
**NO. Stocking dates are completely absent, and DOC cannot be reliably derived.**
- An initial hypothesis was evaluated: *Could the first recorded observation date or the pond profile enrollment date be used as a proxy for the stocking date (Day 0)?*
- To test this, the initial observed fish weight on the very first recorded visit was evaluated for all 266 ponds with weight data:
  - Ponds starting with true fry/fingerlings ($\le 50\text{ g}$): **Only 35 ponds (13.2%)**
  - Ponds starting with advanced juveniles ($50\text{ g} < W \le 100\text{ g}$): **32 ponds (12.0%)**
  - Ponds starting with sub-adult fish ($100\text{ g} < W \le 500\text{ g}$): **112 ponds (42.1%)**
  - Ponds starting with market-size adult fish ($> 500\text{ g}$): **87 ponds (32.7%)** (several ponds first record fish at $1,500\text{ g}$ to $2,000\text{ g}$).
- **Scientific Implication:** Farm ponds were enrolled opportunistically at arbitrary times during ongoing culture operations. Setting $\text{DOC} = 0$ at the first visit would falsely equate a $500\text{ g}$ sub-adult fish with a newly stocked $5\text{ g}$ fingerling. Therefore, **Days of Culture (DOC) cannot be used as an independent feature or temporal index**.

### 3.3 Are fish weights measured repeatedly for the same pond?
**YES. Substantial repeated longitudinal measurements exist.**
- **265 unique ponds** have at least one weight measurement.
- Observation count distribution per pond:
  - Mean: $21.0$ weight visits per pond (Median: $16$, IQR: $[6, 30]$, Maximum: $83$ visits).
  - Ponds with $\ge 5$ weight visits: **209 ponds (78.9%)**.
  - Ponds with $\ge 20$ weight visits: **110 ponds (41.5%)**.
- When observations are aggregated to distinct daily visits and paired across consecutive visits within a realistic commercial window ($3 \le \Delta t \le 45$ days):
  - **Total Valid Revisit Pairs:** **2,497 pairs across 240 unique ponds**.
  - **Mean Revisit Interval:** $23.47\text{ days}$ (Median: $24.0\text{ days}$, IQR: $[15.0, 31.0]\text{ days}$).

### 3.4 Biological Plausibility of Observed Growth Trajectories
Analyzing the 2,497 consecutive revisit pairs reveals a clear biological signal:
- Initial Visit Weight ($W_t$): Mean = $532.89\text{ g}$ (Median: $500.0\text{ g}$).
- Next Visit Weight ($W_{t+1}$): Mean = $574.05\text{ g}$ (Median: $550.0\text{ g}$).
- Observed Weight Gain ($\Delta W = W_{t+1} - W_t$): Mean = **$+41.16\text{ g}$** (Median: $+50.0\text{ g}$).
- Average Daily Growth Rate ($\text{ADG} = \Delta W / \Delta t$): Mean = **$1.68\text{ g/day}$** (Median: $1.72\text{ g/day}$, IQR: $[0.00, 4.55]\text{ g/day}$).
  - In Indian carp commercial aquaculture, Catla and Rohu typically exhibit growth rates between $1.5\text{ g/day}$ and $3.0\text{ g/day}$. The empirical mean of $1.68\text{ g/day}$ confirms strong alignment with domain reality.

### 3.5 Dissection of Growth Trajectory Noise & Anomalies
While 59.95% of revisit pairs exhibit positive weight gain, two distinct noise patterns were identified:
1. **Apparent Weight Loss ($\Delta W < 0$, 144 pairs, 5.77%):**
   - In commercial Andhra Pradesh carp farming, farmers perform **partial harvesting** (also called "intermittent thinning"): when fish reach 1–1.5 kg, large individuals are netted and sold to reduce biomass density, leaving smaller fish to grow. When cast netting occurs after partial harvesting, the average sampled body weight drops abruptly (e.g., from $1,200\text{ g}$ down to $700\text{ g}$).
   - Cycle transitions: Over 2 years of observation, ponds complete a cycle and are drained, dried, and restocked with new fingerlings, causing weight to reset from $> 1,000\text{ g}$ to $< 300\text{ g}$.
   - Polyculture sampling variation: Catla grows substantially faster than Rohu. If cast netting captures more Rohu on visit $t+1$ than on visit $t$, recorded weight may fluctuate.
2. **Zero Weight Delta ($\Delta W = 0$, 856 pairs, 34.28%):**
   - Field officers visually round fish weights to coarse increments ($250\text{ g}, 500\text{ g}, 750\text{ g}, 800\text{ g}, 1,000\text{ g}$). If the true somatic growth over a short 14-day window is $+25\text{ g}$, the observer frequently records the same rounded value (e.g., $500\text{ g} \rightarrow 500\text{ g}$).

### 3.6 Can fish counts and mortality data support biomass estimation?
**NO. Biomass cannot be estimated with scientific rigor.**
- To compute total pond biomass, one requires:
  $$\text{Biomass} = \text{Average Fish Weight} \times \text{Initial Stocked Count} \times (1 - \text{Cumulative Mortality})$$
- We only have:
  - `Stocking density (per acre)` (recorded statically at enrollment or intermittently).
  - `Pond area in acres`.
  - `Dead fish` (observed daily floating mortalities on visit day, e.g. mean 2 fish).
- The true cumulative survival rate is completely unobserved (unobserved cannibalism, benthic decomposition, bird predation, and disease die-offs are not captured by daily floating counts).
- Multiplying static stocking density by pond area assumes near-100% survival, which would overestimate living biomass by $30\% - 70\%$ at harvest.
- Furthermore, the user instructions explicitly prohibit:
  > *"Do not manufacture target values or claim that estimated biomass is actual harvest yield."*

---

## 4. Evaluation of Four Candidate Prediction Targets

A comparative feasibility evaluation of the four candidate targets requested by the user is exported as [`yield_target_feasibility.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_yield_feasibility_audit/yield_target_feasibility.csv) and detailed below.

### Target A: Concurrent / Instantaneous Fish Weight ($W_t$)
- **Model Task:** Predict fish weight ($W_t$ in grams) from contemporaneous water quality, pond metadata, and feed on visit day $t$.
- **Available Sample Count:** 5,569 raw observations (or 3,402 daily pond visits) across 265 ponds.
- **Scientific Defensibility: Deficient / Unsound.**
  - Fish body mass is an *accumulated biological state variable* governed by months of nutrition, thermal degree-days, genetics, and age.
  - Predicting body weight from today's dissolved oxygen or pH has no biological causality. Any correlation learned by an ML model would be a spurious artifact of sampling schedules (e.g., ponds enrolled in July happening to have older fish).
- **Feasibility Verdict:** **NOT RECOMMENDED**.

### Target B: Next-Visit Fish Weight ($W_{t+1}$) or Interval Weight Gain ($\Delta W$)
- **Model Task:** Predict fish weight ($W_{t+1}$) or interval weight gain ($\Delta W = W_{t+1} - W_t$) at scheduled revisit $t+1$, conditioned on initial weight ($W_t$), revisit interval ($\Delta t = 3\text{--}45\text{ days}$), daily feeding rate, stocking density, pond area, and water quality parameters at visit $t$.
- **Available Sample Count:** **2,497 consecutive revisit pairs across 240 unique ponds**.
- **Scientific Defensibility: High / Methodologically Sound.**
  - Solves the absence of stocking dates: initial weight $W_t$ acts as the empirical baseline state variable, anchoring the growth curve.
  - Aligns with aquaculture bioenergetics: environmental covariates (temperature, dissolved oxygen, pH) and inputs (feed amount per acre, stocking density) modulate the rate of biomass accumulation over the elapsed duration $\Delta t$.
  - Allows rigorous baseline benchmarking against domain baselines:
    1. **Null / Persistence Baseline:** $W_{t+1} = W_t$ ($\Delta W = 0$).
    2. **Species Mean Daily Growth Rate Baseline:** $\hat{W}_{t+1} = W_t + (1.68\text{ g/day} \times \Delta t)$.
  - Fully evaluable under strict chronological partitioning (Train: pairs before 2025; Test: pairs starting in 2025–2026) and GroupKFold cross-validation by `pond_id`.
- **Feasibility Verdict:** **FEASIBLE & RECOMMENDED TARGET**.

### Target C: Total Harvest Biomass (kg)
- **Model Task:** Predict total harvested wet biomass of fish in kg at cycle end.
- **Available Sample Count:** **0 (Zero ground-truth records)**.
- **Scientific Defensibility: Inviable.**
  - Actual harvested biomass was never collected. Synthesizing biomass through uncalibrated mathematical multiplication violates strict scientific integrity constraints and creates an ungrounded target.
- **Feasibility Verdict:** **INFEASIBLE (FATAL DATA DEFICIENCY)**.

### Target D: End-of-Cycle Agricultural Yield (kg/acre or tons/acre)
- **Model Task:** Predict total farm yield per acre at commercial harvest.
- **Available Sample Count:** **0 (Zero ground-truth records)**.
- **Scientific Defensibility: Inviable.**
  - Neither harvest weight nor cycle completion markers exist.
- **Feasibility Verdict:** **INFEASIBLE (FATAL DATA DEFICIENCY)**.

---

## 5. Recommended Target & Feature Specifications

Based on the empirical evidence, the **only scientifically defensible and empirically evaluable target** for Experiment 4 is:

$$\text{Primary Target: } W_{t+1} \quad (\text{Average Fish Weight in grams at next visit } t+1)$$
$$\text{Alternative Target: } \Delta W = W_{t+1} - W_t \quad (\text{Interval Weight Gain in grams})$$

### Supporting Feature Inventory
The recommended target can be supported by the following structured variables present in the dataset:

1. **Dynamic Initial State Features (at visit $t$):**
   - `curr_weight`: Fish weight at visit $t$ ($W_t$ in grams) — *mandatory dynamic baseline*.
   - `gap_days`: Elapsed time between routine visits ($\Delta t = t_{t+1} - t_t$ in fractional days, $3.0 \le \Delta t \le 45.0$).
2. **Feeding & Nutritional Features (at visit $t$):**
   - `feed_amount_kg`: Daily supplementary feed applied (kg).
   - `feed_per_acre_kg`: Feed amount normalized by pond area ($\text{kg/acre}$).
3. **Pond Scale & Biological Environment Features:**
   - `stocking_density_per_acre`: Number of fish stocked per acre.
   - `Pond area in acres`: Surface water area.
   - `Depth in meters`: Operating water depth.
   - `species`: Cultured fish species mix (polyculture categories).
   - `region`: Farming district (`Eluru` vs. `Nellore`).
4. **Physicochemical Water Quality Features (at visit $t$):**
   - `dissolved_oxygen_mg_l`: Morning DO level (metabolic oxygen driver).
   - `ph`: Water pH (carbonate equilibrium and chemical stress).
   - `temp_c`: Water temperature (ectothermic metabolic rate determinant).
5. **Fish Distress & Health Covariates (at visit $t$):**
   - `dead_fish_count`: Floating dead fish count.
   - `air_gulping_count`: Surface hypoxia distress behavior count.
   - `tail_splashing_count`: Behavioral agitation count.

---

## 6. Critical Limitations to Address Before Model Development

Before constructing features or training models, five specific limitations must be explicitly handled in the modeling protocol:

1. **Partial Harvesting & Restocking Outlier Filtering:**  
   The 144 pairs (5.77%) exhibiting negative weight delta ($\Delta W < 0$) must be treated systematically. In growth modeling, an apparent weight loss exceeding $-100\text{ g}$ over 20 days represents an unrecorded partial harvest event or a new cycle restocking, not negative biological growth. The protocol must specify whether these pairs are excluded as cycle breaks or flagged with an indicator.
2. **Measurement Granularity / Zero-Growth Bins:**  
   Because field officers round weights to coarse 50g/100g bins, 34.28% of revisit pairs have $\Delta W = 0$. Regression models will predict continuous fractional growth (e.g. $+28.4\text{ g}$), which may yield non-zero residuals against rounded ground truth. Evaluation metrics must include MAE, RMSE, and comparison against the Persistence Baseline ($W_{t+1} = W_t$).
3. **Pond Area Missingness (14.5%):**  
   47 enrolled ponds lack `Pond area in acres`. Imputation must be fit strictly on training partitions to prevent data leakage.
4. **Strict GroupKFold by `pond_id`:**  
   Because ponds have up to 83 repeated measurements, pairs from the same pond are strongly autocorrelated. Standard random cross-validation would cause severe spatial data leakage. Validation must strictly use **GroupKFold by `pond_id`**.
5. **Strict Chronological Holdout:**  
   Temporal generalization must be evaluated by splitting pairs chronologically based on visit date $t$ (e.g. Training: pairs before 2025; Testing: pairs on or after 2025-01-01), mirroring the rigorous protocol established in Experiments 1, 2, and 3.

---

## Summary of Core Feasibility Questions

1. **Is genuine fish growth prediction possible?**  
   **YES, conditionally feasible at the pond-cohort level as Next-Visit Fish Weight ($W_{t+1}$) or Interval Weight Gain ($\Delta W$) across 2,497 temporal observation pairs**, but NOT as individual-tagged fish tracking, and NOT across entire culture cycles from stocking to harvest.
2. **Is genuine harvest yield prediction possible?**  
   **NO, SCIENTIFICALLY INFEASIBLE.** There are exactly zero records of actual harvested biomass, harvest yield, stocking dates, or harvest dates in the dataset. Any calculation of harvest yield would be an entirely ungrounded mathematical simulation lacking empirical ground truth.
3. **What is the best recommended target?**  
   **Next-Visit Average Fish Weight ($W_{t+1}$ in grams)** over a 3–45 day revisit window, conditioned on initial body weight ($W_t$), elapsed interval ($\Delta t$), feeding rates, stocking density, pond area, and water quality parameters.
4. **What exact dataset columns can support it?**  
   `Weight` (target at $t+1$ and baseline feature at $t$), `Date of data collection` ($\Delta t$), `Feed amount (kg)`, `Stocking density (per acre)`, `Pond area in acres`, `Depth in meters`, `Species`, `region`, `DO (mg/L)`, `pH`, `Temp (in °C)`, `dead_fish_count`, `air_gulping_count`, and `tail_splashing_count`.
5. **What limitations must be addressed before model development?**  
   Partial harvest/thinning weight-loss outliers (5.77%), coarse visual measurement rounding (34.28% zero delta), pond area missingness (14.5%), spatial autocorrelation requiring GroupKFold by `pond_id`, and strict chronological holdout partitioning.

> [!IMPORTANT]
> **Model Training Hold:** No machine learning model has been trained, fit, or evaluated. All analyses were conducted in read-only audit mode. Model development will proceed only upon user review and approval of this feasibility audit.

