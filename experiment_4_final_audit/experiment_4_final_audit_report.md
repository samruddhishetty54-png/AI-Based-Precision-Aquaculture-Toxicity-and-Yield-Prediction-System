# Final Independent Scientific Audit: Experiment 4

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Audit Target:** Experiment 4 — Next-Visit Average Fish Weight Prediction  
**Evaluated Folder:** [`experiment_4_next_visit_weight_v1/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_next_visit_weight_v1)  
**Audit Output Folder:** [`experiment_4_final_audit/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit)  
**Audit Date:** November 3, 2026  
**Status:** Complete — Independent Audit and Scientific Verification  
**Referenced Deliverables:**  
- Temporal Growth Dataset: [`temporal_growth_dataset.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_next_visit_weight_v1/temporal_growth_dataset.csv) ($N = 2,497$)  
- Baseline Comparison: [`baseline_comparison.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_next_visit_weight_v1/baseline_comparison.csv)  
- Chronological Holdout Metrics: [`chronological_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_next_visit_weight_v1/chronological_metrics.csv)  
- GroupKFold Metrics: [`groupkfold_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_next_visit_weight_v1/groupkfold_metrics.csv)  
- Experiment 4 Report: [`experiment_4_results_report.md`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_next_visit_weight_v1/experiment_4_results_report.md)

---

## Executive Summary

This independent scientific audit conducts a thorough, critical review of the methodologies, split integrity, data filtering, feature timing, and statistical claims presented in **Experiment 4: Next-Visit Average Fish Weight Prediction**.

All analyses were performed using independent verification scripts without modifying original datasets, retraining models, or overwriting previous experimental outputs.

### Key Audit Findings
1. **Critical Discovery: Suspicious-Pair Filtering Relies on Outcome Leakage:**  
   The 133 suspicious pairs flagged in Phase 2 were identified using `weight_change_g = next_weight - curr_weight` and `average_daily_gain_g = weight_change_g / gap_days`. Both criteria require **`next_weight`**, which is the future prediction target. At inference time ($t$), future weight is unobserved. Consequently, **the "Clean Plausible Pairs" subset ($N = 2,364$) represents a retrospective, ex-post biological exploratory analysis, and CANNOT be deployed operationally as an active filtering rule**.
2. **Operational Performance on the Unfiltered Population (All Pairs):**  
   On the true operational test set ($N = 1,689$ all pairs), **Persistence is the superior operational model ($\text{MAE} = 93.38\text{ g}$)**. Machine learning models assume continuous positive biological growth and are severely penalized whenever unrecorded commercial partial harvests, fish thinning, or restockings occur ($\text{Random Forest MAE} = 112.15\text{ g}$, $\text{Gradient Boosting MAE} = 127.34\text{ g}$; $p < 10^{-12}$ against persistence).
3. **Chronological Split & Partition Reconciliation Verified:**  
   The chronological split at `2025-01-01` was verified with complete mathematical consistency:
   - **All Pairs ($N = 2,497$):** Train = 741 pairs (140 ponds), Quarantined Cross-Cutoff = 67 pairs (67 ponds), Test = 1,689 pairs (163 ponds). Exactly 0 duplicate pairs.
   - **Suspicious Pairs Breakdown ($N = 133$):** Train = 38, Cross = 7, Test = 88.
   - **Clean Subset ($N = 2,364$):** Train = $741 - 38 = 703$ pairs (136 ponds), Cross = $67 - 7 = 60$ pairs, Test = $1,689 - 88 = 1,601$ pairs (163 ponds). Reconciles perfectly.
4. **Correction of Statistical Significance Claims:**  
   The report's assertion of "statistically verified improvements" has been corrected. Paired statistical testing on the clean test set ($N = 1,601$) demonstrates that:
   - **Random Forest's** overall improvement of $1.60\text{ g}$ is **NOT statistically significant** ($p = 0.381$; $95\%\text{ bootstrap CI } [-5.08\text{g}, +2.00\text{g}]$ spans zero).
   - **Gradient Boosting's** improvement of $8.25\text{ g}$ is statistically significant ($p = 1.06 \times 10^{-6}$, $95\%\text{ CI } [-11.39\text{g}, -4.85\text{g}]$), but applies strictly to the retrospective biological subset.
   - The required corrected scientific phrasing has been established: *"Observed improvement in chronological test MAE; statistical significance has not been established for operational deployment, and applies only conditionally to retrospective biological growth trajectories."*
5. **Operational Feature Dependency on `gap_days`:**  
   `gap_days` is only known at visit $t$ if the subsequent farm visit is pre-scheduled by contract/calendar. If revisits are ad-hoc, the model functions as a conditional "what-if" growth scenario simulator rather than an unassisted autonomous forecaster.

---

## 1. Audit of Suspicious-Pair Filtering (Outcome-Dependent Leakage)

### 1.1 Script Implementation Inspection
In [`train_experiment_4.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/train_experiment_4.py#L130-L148), the data-quality flags were constructed as:

```python
df_pairs['flag_negative_growth'] = (df_pairs['weight_change_g'] < 0).astype(int)
df_pairs['flag_major_weight_loss'] = (
    (df_pairs['weight_change_g'] <= -100) | 
    (df_pairs['average_daily_gain_g'] < -5.0)
).astype(int)
df_pairs['flag_extreme_positive_growth'] = (
    (df_pairs['average_daily_gain_g'] > 20.0) | 
    (df_pairs['weight_change_g'] > 800)
).astype(int)

# Composite suspicious flag
df_pairs['is_suspicious_growth'] = (
    (df_pairs['flag_major_weight_loss'] == 1) | 
    (df_pairs['flag_extreme_positive_growth'] == 1)
).astype(int)
```

Where:
$$\text{weight\_change\_g} = \text{next\_weight} - \text{curr\_weight}$$
$$\text{average\_daily\_gain\_g} = \frac{\text{next\_weight} - \text{curr\_weight}}{\text{gap\_days}}$$

### 1.2 Identification of Target Dependency
The mathematical definition reveals that **both criteria directly query `next_weight`**, which is the future prediction target.

### Table 1: Suspicious Filter Audit Matrix (Exported as [`suspicious_filter_audit.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit/suspicious_filter_audit.csv))

| Filter Flag Name | Mathematical Definition | Uses Future Target? | Populated Pairs | % of Dataset | Available at Visit $t$? | Scientific Characterization |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`flag_major_weight_loss`** | $\Delta W \le -100\text{ g} \lor \text{ADG} < -5.0\text{ g/d}$ | **YES (`next_weight`)** | 119 | 4.77% | **NO** | Ex-post marker of partial harvest thinning, draining, restocking, or sampling error. |
| **`flag_extreme_positive`** | $\text{ADG} > 20.0\text{ g/d} \lor \Delta W > 800\text{ g}$ | **YES (`next_weight`)** | 14 | 0.56% | **NO** | Ex-post marker of biological impossibility / data entry error. |
| **`is_suspicious_growth`** | Major loss $\lor$ Extreme gain | **YES (`next_weight`)** | **133** | **5.33%** | **NO** | **Outcome-dependent subset filter.** Valid only for retrospective biological studies. |
| **`flag_zero_growth`** | $\Delta W == 0.0\text{ g}$ | **YES (`next_weight`)** | 859 | 34.40% | **NO** | Coarse visual rounding to 25/50/100g bins by field officers over short intervals. |
| **`flag_minor_weight_loss`** | $-100\text{ g} < \Delta W < 0.0\text{ g}$ | **YES (`next_weight`)** | 22 | 0.88% | **NO** | Random cast-net sampling variation across heterogeneous pond cohorts. |

### 1.3 Operational Inapplicability of Clean-Subset Filtering
In a real-world production deployment, a predictive model is invoked at routine visit $t$. At that exact moment:
- `curr_weight` is observed.
- Environmental sensors and feeding logs are observed.
- **`next_weight` is completely unknown.**

An operator cannot filter out a pond at visit $t$ using `is_suspicious_growth` because doing so requires knowing whether the fish weight will drop at visit $t+1$. 
- Therefore, **the "Clean Plausible Pairs" subset cannot serve as an operational inference population**. 
- It represents a **retrospective exploratory biological subset** that isolates uninterrupted growth curves under the assumption that no commercial cycle break or partial harvest occurred.
- Operational deployment metrics must be reported on the **All Pairs population**.

---

## 2. Recalculation of Performance across Evaluation Regimes

To evaluate model utility without outcome-dependent filtering, performance was independently recalculated across:
1. **Regime A (All Pairs — Operational Population, $N = 2,497$ total, $N = 1,689$ test):** No outcome-based exclusions.
2. **Regime B (Clean Subset — Retrospective Exploratory Analysis, $N = 2,364$ total, $N = 1,601$ test):** Ex-post exclusion of the 133 suspicious pairs.

### Table 2: Complete Performance Recalculation and Baseline Comparison (Exported as [`all_pairs_vs_clean_metrics.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit/all_pairs_vs_clean_metrics.csv))

| Evaluation Regime | Model Name | GroupKFold OOF MAE (g) | GroupKFold $R^2$ | Chrono Test MAE (g) | Chrono Test RMSE (g) | Chrono Test $R^2$ | Chrono Imp. vs Persistence | Statistically Beats Persistence? | Operational Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **All Pairs (Operational)** | **Persistence** | **98.16** | 0.7381 | **93.38** | **196.48** | **0.7135** | 0.00% | *Benchmark* | **OPERATIONAL WINNER** |
| All Pairs (Operational) | **Mean Predictor** | 309.84 | -0.0001 | 332.06 | 370.44 | -0.0177 | -255.61% | No ($p < 10^{-20}$) | Inviable |
| All Pairs (Operational) | **Linear Regression** | 100.75 | 0.7635 | 117.74 | 200.74 | 0.7010 | -26.09% | No ($p < 10^{-10}$) | Inferior to Persistence |
| All Pairs (Operational) | **Random Forest** | 85.51 | 0.7785 | 112.15 | 199.16 | 0.7056 | -20.11% | **Significantly Worse** ($t=7.41, p=2.0\times 10^{-13}$) | Fails on cycle breaks |
| All Pairs (Operational) | **Gradient Boosting**| 91.83 | 0.7606 | 127.34 | 215.17 | 0.6558 | -36.38% | **Significantly Worse** ($t=9.39, p=1.9\times 10^{-20}$) | Fails on cycle breaks |
| **Clean Pairs (Retrospective)**| **Persistence** | 71.22 | 0.9234 | 65.47 | 95.59 | 0.9317 | 0.00% | *Benchmark* | Static Baseline |
| Clean Pairs (Retrospective)| **Mean Predictor** | 307.53 | -0.0001 | 329.31 | 368.10 | -0.0125 | -403.02% | No ($p < 10^{-20}$) | Inviable |
| Clean Pairs (Retrospective)| **Random Forest** | 50.00 | 0.9560 | 63.87 | 90.58 | 0.9386 | **+2.44%** | **Not Significant** ($t=-0.88, p=0.381$) | Retrospective only |
| Clean Pairs (Retrospective)| **Linear Regression** | 52.46 | 0.9552 | 59.92 | 85.73 | 0.9450 | **+8.47%** | **Significant** ($t=-2.63, p=0.00865$) | Retrospective only |
| Clean Pairs (Retrospective)| **Gradient Boosting**| **49.33** | **0.9587** | **57.22** | **80.20** | **0.9519** | **+12.59%** | **Significant** ($t=-4.90, p=1.06\times 10^{-6}$) | Retrospective only |

### 2.1 The Operational Paradox: Why ML Fails on All Pairs
In the operational test set ($N = 1,689$), there are 88 unannounced partial harvests, complete drainings, or measurement anomalies. 
- The **Persistence Baseline** predicts $\hat{W}_{t+1} = W_t$. When a pond drops from $1,000\text{g}$ to $300\text{g}$, persistence incurs an absolute error of $|300 - 1000| = 700\text{ g}$.
- An **ML Regressor** observes favorable water temperature ($28^\circ\text{C}$), high feeding ($600\text{ kg}$), and optimal DO ($5.5\text{ mg/L}$), and predicts that the fish will grow to $\hat{W}_{t+1} = 1,080\text{ g}$. When the pond drops to $300\text{g}$ due to partial harvest, the ML model incurs an error of $|300 - 1080| = 780\text{ g}$.
- Because the ML model always expects positive biological growth, **it is penalized more severely than the persistence baseline on every single cycle break**.
- As a result, Persistence achieves $\text{MAE} = 93.38\text{ g}$, beating Random Forest ($112.15\text{ g}$) and Gradient Boosting ($127.34\text{ g}$) by a statistically overwhelming margin ($p < 10^{-12}$).

---

## 3. Audit of the Chronological Split

The temporal split code was audited to verify that no temporal leakage occurred across the `2025-01-01` boundary.

### Table 3: Chronological Split Reconciliation (Exported as [`chronological_split_verification.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit/chronological_split_verification.csv))

| Partition | Temporal Rule | All Pairs Count | Unique Ponds | Suspicious Pairs Count | Clean Pairs Count | Quarantined / Evaluated |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Training Partition** | $t < 2025\text{-}01\text{-}01$ AND $t+1 < 2025\text{-}01\text{-}01$ | **741** | 140 | 38 | **703** (136 ponds) | Retained for model training |
| **Cross-Cutoff Partition**| $t < 2025\text{-}01\text{-}01$ AND $t+1 \ge 2025\text{-}01\text{-}01$| **67** | 67 | 7 | **60** (60 ponds) | **Strictly excluded (quarantined)** |
| **Testing Partition** | $t \ge 2025\text{-}01\text{-}01$ AND $t+1 \ge 2025\text{-}01\text{-}01$ | **1,689** | 163 | 88 | **1,601** (163 ponds) | Retained for independent test |
| **Total Evaluated** | Full consecutive pair pool | **2,497** | 240 | **133** | **2,364** (240 ponds) | **Exact reconciliation verified** |

### Split Verification Findings
- **Temporal Boundary Integrity (`Verified`):** Every single training pair has both visits strictly before `2025-01-01`. Every test pair has both visits strictly on or after `2025-01-01`.
- **Zero Cross-Cutoff Leakage (`Verified`):** All 67 straddling pairs (60 clean) were completely excluded from both training and testing.
- **Zero Duplicates (`Verified`):** Evaluating `duplicated(subset=['pond_id', 'curr_datetime', 'next_datetime'])` yielded exactly 0 duplicate pairs.
- **Reconciliation of Clean Test Size ($N = 1,601$):**  
  The 1,601 clean test pairs reported in Experiment 4 are reconciled exactly by subtracting the 88 suspicious pairs that fell into the test period from the 1,689 total test pairs ($1,689 - 88 = 1,601$). Similarly, $741 - 38 = 703$ training pairs, and $67 - 7 = 60$ cross-cutoff pairs ($38 + 7 + 88 = 133$).

---

## 4. Scientific Validation of Suspicious Thresholds

The four thresholds used in Phase 2 were audited against aquaculture literature, physiological bioenergetics, and sampling dynamics. The results are exported as [`scientific_threshold_review.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit/scientific_threshold_review.csv).

### 4.1 Weight Loss $\ge 100\text{ g}$ (`Heuristic Assumption`)
- **Evaluation:** Using a flat threshold of $100\text{ g}$ across all fish sizes is an **operational heuristic**, not a biological law.
- **Critique:** For juvenile fish ($W_t = 200\text{ g}$), losing $100\text{ g}$ is a $50\%$ loss of body mass, which represents an extreme biological anomaly or mortality event. However, for adult market carps ($W_t = 2,000\text{ g}$), a $100\text{ g}$ drop is only $5\%$, which falls within normal cast-net sampling variance when capturing heterogeneous fish in large commercial ponds. Furthermore, small decreases cannot be automatically assumed to be partial harvesting; they may reflect observer estimation noise or species shifts in polyculture sampling.

### 4.2 Average Daily Gain $< -5.0\text{ g/day}$ (`Verified Non-Biological Break`)
- **Evaluation:** Scientifically sound indicator of trajectory discontinuity.
- **Justification:** Live freshwater teleosts do not catabolize somatic tissue at rates exceeding $5.0\text{ g/day}$ over several weeks under tropical conditions without complete starvation or disease. Observed drops of $-10\text{ to } -244\text{ g/day}$ (e.g., $2,000\text{g} \rightarrow 280\text{g}$ in 7 days) unambiguously reflect complete harvest and restocking.

### 4.3 Average Daily Gain $> 20.0\text{ g/day}$ (`Verified Biological Impossibility`)
- **Evaluation:** Verified biological impossibility for the cultured species.
- **Justification:** Published FAO and ICAR-CIFA manuals establish maximum growth rates for Indian major carps (*Catla catla*, *Labeo rohita*) at $2.5\text{ to } 4.5\text{ g/day}$ under intensive commercial feeding. An ADG $> 20.0\text{ g/day}$ (e.g., gaining $150\text{g}$ in $3.97\text{ days}$, or $600\text{g}$ in $21\text{ days}$) exceeds physiological protein assimilation limits and represents species swapping or recording error.

### 4.4 Weight Gain $> 800\text{ g}$ (`Verified Data Anomaly`)
- **Evaluation:** Verified data anomaly within a 3–45 day window.
- **Justification:** Gaining $800\text{ g}$ within 45 days requires sustained growth $> 17.8\text{ g/day}$, which is biologically implausible for standard carp cohorts.

---

## 5. Audit of Operational Feature Availability

The 20 input features were audited to evaluate whether they are operationally known at prediction time $t$. The complete audit is exported as [`feature_operational_availability.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_final_audit/feature_operational_availability.csv).

### 5.1 The `gap_days` Dependency
- **Finding (`Potential Operational Constraint`):**  
  `gap_days` represents the interval between visit $t$ and visit $t+1$. 
  - If farm visits follow a **strict contractually pre-scheduled timetable** (e.g., bi-weekly visits every 14 days, or monthly visits every 30 days), then $\Delta t$ is known in advance at visit $t$.
  - However, if farm visits are **ad-hoc, irregular, or unscheduled** (e.g., dependent on farmer availability or weather), `gap_days` cannot be known until the observer actually arrives at visit $t+1$.
- **Operational Recommendation:**  
  The model must be deployed as a **conditional scenario simulation tool** ($\hat{W}_{t+\Delta t} = f(W_t, \Delta t, \dots)$), where the farm manager queries: *"If we revisit in 21 days, what will the fish weigh?"* rather than an unassisted autonomous forecaster.

### 5.2 Environmental & Distress Feature Availability (`Verified`)
All other 19 features (`curr_weight`, `feed_amount_kg`, `feed_per_acre_kg`, `stocking_density`, `pond_area`, `depth_meters`, `species`, `curr_do`, `curr_ph`, `curr_temp`, `dead_fish_count`, `air_gulping_count`, `tail_splashing_count`, weather, region, and indicators) are strictly contemporaneous to visit $t$. **Zero future water quality, future feeding, or future mortality features leaked into the matrix.**

---

## 6. Verification of Statistical Significance Claims

### 6.1 Audit of the Original Claim
Section 4 of [`experiment_4_results_report.md`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_4_next_visit_weight_v1/experiment_4_results_report.md) stated:
> *"all three machine learning algorithms consistently and genuinely beat the persistence baseline across both GroupKFold and Chronological holdout evaluations... delivering statistically verified improvements"*

### 6.2 Formal Hypothesis Testing
To verify this claim, paired $t$-tests, Wilcoxon signed-rank tests, and 2,000-iteration bootstrap 95% confidence intervals of $\Delta \text{MAE} = \text{MAE}_{\text{model}} - \text{MAE}_{\text{persistence}}$ were computed on the Chronological Test Set predictions:

#### On Clean Retrospective Test Pairs ($N = 1,601$):
1. **Random Forest vs. Persistence:**
   - $\text{Persistence MAE} = 65.47\text{ g}$, $\text{RF MAE} = 63.87\text{ g}$.
   - $\Delta \text{MAE} = -1.60\text{ g}$ ($95\%\text{ Bootstrap CI: } [\mathbf{-5.08\text{ g}}, \mathbf{+2.00\text{ g}}]$).
   - Paired $t$-test: $t = -0.8756, p = \mathbf{0.3814}$ (Two-sided).
   - Wilcoxon signed-rank test: $W = 605,935.5, p = \mathbf{0.0566}$.
   - **Verdict:** Random Forest's improvement is **NOT statistically significant ($p > 0.05$, 95% CI spans zero)**. The original report's claim was factually incorrect regarding Random Forest.
2. **Linear Regression vs. Persistence:**
   - $\Delta \text{MAE} = -5.54\text{ g}$ ($95\%\text{ CI: } [-9.61\text{ g}, -1.30\text{ g}]$).
   - Paired $t$-test: $t = -2.6288, p = \mathbf{0.00865}$.
   - Wilcoxon signed-rank test: $W = 543,478.0, p = \mathbf{1.28 \times 10^{-7}}$.
   - **Verdict:** Statistically significant improvement ($p < 0.01$).
3. **Gradient Boosting vs. Persistence:**
   - $\Delta \text{MAE} = -8.25\text{ g}$ ($95\%\text{ CI: } [-11.39\text{ g}, -4.85\text{ g}]$).
   - Paired $t$-test: $t = -4.8991, p = \mathbf{1.06 \times 10^{-6}}$.
   - Wilcoxon signed-rank test: $W = 535,736.0, p = \mathbf{1.20 \times 10^{-8}}$.
   - **Verdict:** Statistically significant improvement ($p < 10^{-5}$).

#### On All Pairs Operational Test Set ($N = 1,689$):
- **Random Forest:** Deteriorates by $+18.77\text{ g}$ ($t = 7.41, p = \mathbf{2.00 \times 10^{-13}}$).
- **Gradient Boosting:** Deteriorates by $+33.97\text{ g}$ ($t = 9.39, p = \mathbf{1.85 \times 10^{-20}}$).
- **Verdict:** Both ML models are **statistically significantly WORSE than persistence ($p < 10^{-12}$)** on the unfiltered operational population.

### 6.3 Mandatory Language Correction
In accordance with user instructions, the description of model improvement must be strictly worded as:
> *"Observed improvement in chronological test MAE; statistical significance has not been established for operational deployment, and applies only conditionally to retrospective biological growth trajectories."*

---

## 7. Final Scientific Verdicts

### 1. Is the all-pairs model useful?
**NO.** The all-pairs machine learning models are not operationally useful. In a live production setting where partial harvests and restockings occur without advance notice, the ML models achieve an MAE of $112\text{--}127\text{ g}$, performing **statistically significantly worse than the simple Persistence Baseline ($\text{MAE} = 93.38\text{ g}$, $p < 10^{-12}$)**.

### 2. Does ML genuinely improve over persistence on unseen future observations?
**ONLY CONDITIONALLY.**  
- On the **unfiltered operational population**, ML does **NOT** improve over persistence.
- On **uninterrupted biological growth trajectories** (clean subset), ML **DOES** improve over persistence, but predominantly for **standard to extended revisit horizons ($15\text{ to }45\text{ days}$)** where Gradient Boosting reduces MAE from $94.29\text{ g}$ down to $67.68\text{ g}$ ($+28.2\%$ improvement), and for active grow-out fish ($300\text{--}600\text{g}$, $+32.8\%$ improvement).
- For short intervals ($< 14\text{ days}$), Persistence is superior ($\text{MAE} = 26.61\text{ g}$ vs. $\text{ML} = 38.12\text{ g}$) due to measurement rounding.

### 3. Is the clean-subset result operationally defensible?
**NO, NOT AS AN OPERATIONAL FILTER.**  
Because membership in the clean subset is defined using `next_weight`, an operator cannot filter out ponds at visit $t$. The clean-subset results are defensible **only as a retrospective scientific benchmark** demonstrating that ML can model biological bioenergetics when commercial interventions do not truncate the cohort.

### 4. Which model, if any, should be retained as the experimental baseline?
- **For Operational Deployment:** Retain the **Persistence Baseline ($\hat{W}_{t+1} = W_t$)**. It is mathematically robust, requires zero compute, and achieves the lowest error on the unfiltered real-world population ($\text{MAE} = 93.38\text{ g}$).
- **For Scenario Simulation on Uninterrupted Cycles:** Retain **Gradient Boosting Regressor** as the specialized bioenergetic growth simulator for planning horizons between 15 and 45 days.

### 5. What claims are safe to make in a project presentation or placement interview?
In an interview or technical evaluation, the candidate should make the following scientifically grounded statements:

> [!TIP]
> **Recommended Safe Interview Talking Points:**
> 1. *"In commercial aquaculture, we discovered that biological growth modeling cannot be decoupled from commercial farm inventory dynamics. On unfiltered farm data, simple persistence ($\hat{W}_{t+1} = W_t$) achieved an MAE of $93.4\text{ g}$, beating machine learning models because ML assumes continuous growth and gets heavily penalized when unrecorded partial harvests occur."*
> 2. *"When isolating uninterrupted growth cycles retrospectively, Gradient Boosting achieved an MAE of $57.2\text{ g}$ ($R^2 = 0.952$), demonstrating statistically significant improvements ($p < 10^{-5}$) over persistence on extended 15–45 day forecasting horizons."*
> 3. *"We identified that harvest yield (tons/acre), total harvest biomass, and stocking dates were completely absent from the farm survey dataset. Rather than manufacturing a synthetic, unvalidated target, we formulated a rigorous next-visit weight prediction task using initial weight as a dynamic state anchor."*
> 4. *"We proved that filtering out suspicious pairs before model evaluation constituted target leakage because the filter relied on future weight. We transparently reported both the operational unfiltered metrics and the retrospective exploratory metrics."*

