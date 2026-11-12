# Final Scientific Target-Definition Audit: Experiment 3

**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System  
**Audit Scope:** Target Definition Audit for Experiment 3 (Next-Visit Ammonia Toxicity Risk Prediction)  
**Audit Date:** November 3, 2026  
**Status:** Audit Complete — Scientific Verification and Quantitative Impact Analysis  
**Deliverables Directory:** `experiment_3_target_definition_audit/`  
**Referenced Datasets:**  
- Processed Toxicity Dataset: [`toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv) ($N = 6,945$)
- Threshold Configuration: [`thresholds_config.json`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/thresholds_config.json)
- Experiment 3 Codebase: [`train_experiment_3.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/train_experiment_3.py)
- Data Cleaning Pipeline: [`clean_datasets_v2.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/clean_datasets_v2.py)

---

## Executive Summary

This independent audit conducts an exhaustive chemical, mathematical, and algorithmic evaluation of the target variable utilized in **Experiment 3: Next-Visit Ammonia Toxicity Risk Prediction**. 

Specifically, this audit:
1. Deconstructs the exact algebraic implementation of the `provisional_ammonia_risk_heuristic` in [`clean_datasets_v2.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/clean_datasets_v2.py#L502-L505).
2. Investigates the chemical dual-basis transition between $\text{TAN (NH}_3\text{-N)}$ (predominant in 2021–2025) and $\text{TAN (NH}_3\text{)}$ (predominant in 2025–2026), verifying the stoichiometric molecular-weight ratio ($\text{MW}(\text{NH}_3)/\text{MW}(\text{N}) = 1.21589$).
3. Identifies an algorithmic asymmetry where the secondary caution rule evaluated `raw_ammonia_tan_nh3_n_mg_l >= 1.0` but omitted `raw_ammonia_tan_nh3_mg_l`.
4. Quantifies the empirical impact of this asymmetry across all 6,945 dataset observations and all 4,900 temporal observation pairs in Experiment 3 under four distinct target formulations.
5. Classifies all findings under the required scientific taxonomy: **`Verified`**, **`Potential issue`**, or **`Cannot be verified from available data`**.

### Key Scientific Takeaway
- Under a **stoichiometrically consistent threshold** ($1.000\text{ mg/L TAN-N} \iff 1.216\text{ mg/L molecular TAN}$), the formula asymmetry has **exactly 0 practical impact** (0 flips across all 6,945 dataset rows and 0 flips across all 4,900 temporal pairs in Experiment 3).
- Even under an **unconverted direct $1.0\text{ mg/L}$ threshold** applied across both columns without molecular-weight adjustment, only **one single observation** in the entire dataset (Row 2373 in late 2025) changes label, altering exactly **1 test pair out of 2,034 test pairs (a 0.049% shift)**.
- Therefore, Experiment 3's reported findings, model training partitions, and chronological evaluations remain **empirically valid and methodologically sound**. No retraining or destructive dataset modifications are required.

---

## 1. Target Formula Audit

### 1.1 Script Implementation Inspection
In [`clean_datasets_v2.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/clean_datasets_v2.py#L501-L505), the binary target column `provisional_ammonia_risk_heuristic` is generated as:

```python
# Toxic ammonia risk evaluated on primary molecular NH3
df_tox['provisional_ammonia_risk_heuristic'] = (
    (df_tox['primary_calculated_nh3_mg_l'] >= THRESH['toxic_molecular_nh3_heuristic_mg_l']) |
    (df_tox['raw_ammonia_tan_nh3_n_mg_l'] >= THRESH['tan_caution_heuristic_mg_l'])
).astype(int)
```

Where the parameters defined in [`thresholds_config.json`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/thresholds_config.json#L13-L14) are:
- `toxic_molecular_nh3_heuristic_mg_l`: $0.05\text{ mg/L}$ (representing chronic toxic un-ionized molecular ammonia threshold).
- `tan_caution_heuristic_mg_l`: $1.0\text{ mg/L}$ (representing general total ammonia caution threshold).

### 1.2 Identified Formula Asymmetry
The heuristic is a disjunctive rule (logical OR) comprising two distinct physical criteria:
1. **Primary Toxic Condition:** `primary_calculated_nh3_mg_l >= 0.05`
2. **Secondary Caution Condition:** `raw_ammonia_tan_nh3_n_mg_l >= 1.0`

**Critical Finding (`Potential issue`):**
The secondary caution rule is hardcoded to query **`raw_ammonia_tan_nh3_n_mg_l`** specifically. It does **not** query **`raw_ammonia_tan_nh3_mg_l`**. 
- In years 2021–2024, 100% of observations have `raw_ammonia_tan_nh3_n_mg_l` populated.
- In year 2025, 942 observations have `raw_ammonia_tan_nh3_n_mg_l` populated, while 622 have `raw_ammonia_tan_nh3_mg_l`.
- In year 2026, `raw_ammonia_tan_nh3_n_mg_l` is completely null (1,037 observations have `raw_ammonia_tan_nh3_mg_l`).

Consequently, for observations in 2025 and 2026 that report ammonia under `raw_ammonia_tan_nh3_mg_l`, the secondary caution branch is structurally inert (evaluating to `NaN >= 1.0`, which evaluates to `False`). In those rows, risk status was governed solely by whether `primary_calculated_nh3_mg_l >= 0.05`.

---

## 2. Chemical Reporting Bases & Stoichiometric Verification

### 2.1 Chemical Distinctions Between Reporting Bases
Water testing kits and spectrophotometric photometers report Total Ammonia Nitrogen under two distinct molecular bases:

$$\begin{aligned}
\text{Basis A: } & \text{TAN expressed as Nitrogen } (\text{NH}_3\text{-N}) \\
\text{Basis B: } & \text{TAN expressed as Molecular Ammonia } (\text{NH}_3)
\end{aligned}$$

The relationship between the mass concentrations is governed by stoichiometry:
$$\text{MW}(\text{N}) = 14.007\text{ g/mol}, \quad \text{MW}(\text{NH}_3) = 14.007 + 3 \times 1.008 = 17.031\text{ g/mol}$$
$$\text{Stoichiometric Conversion Ratio: } \frac{\text{MW}(\text{NH}_3)}{\text{MW}(\text{N})} = \frac{17.031}{14.007} \approx 1.215892$$

$$\text{TAN}_{(\text{molecular NH}_3)} = \text{TAN}_{(\text{NH}_3\text{-N})} \times 1.215892$$
$$\text{TAN}_{(\text{NH}_3\text{-N})} = \frac{\text{TAN}_{(\text{molecular NH}_3)}}{1.215892} = \text{TAN}_{(\text{molecular NH}_3)} \times 0.822441$$

### 2.2 Emerson Equilibrium Dissociation Verification (`Verified`)
In [`clean_datasets_v2.py`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/clean_datasets_v2.py#L158-L197), the un-ionized toxic ammonia fraction $f$ is derived from the Emerson et al. (1975) dissociation formula:
$$\text{p}K_a = 0.09018 + \frac{2729.92}{T_K}, \quad T_K = T_{^\circ\text{C}} + 273.15$$
$$f = \frac{1}{10^{(\text{p}K_a - \text{pH})} + 1}$$

The pipeline handles the two raw columns with appropriate chemical rigor:
1. **For `raw_ammonia_tan_nh3_n_mg_l`:**
   $$\text{Molecular NH}_3 = f \times \text{TAN}_{(\text{NH}_3\text{-N})} \times \left(\frac{17.031}{14.007}\right)$$
   *(Stoichiometric scaling correctly converts nitrogen mass to ammonia molecular mass).*
2. **For `raw_ammonia_tan_nh3_mg_l`:**
   $$\text{Molecular NH}_3 = f \times \text{TAN}_{(\text{molecular NH}_3)}$$
   *(Direct calculation without scaling because input is already on an $\text{NH}_3$ mass basis).*

Both calculations are mathematically and chemically sound. The unified column `primary_calculated_nh3_mg_l` accurately represents molecular toxic un-ionized $\text{NH}_3$ across all 6,945 records.

### 2.3 Threshold Application: Nitrogen vs. Molecular Basis
If an operational standard stipulates a cautionary threshold of $1.0\text{ mg/L}$ Total Ammonia Nitrogen ($\text{TAN-N}$), the chemically equivalent molecular TAN threshold must be:
$$1.0\text{ mg/L TAN-N} \equiv 1.0 \times 1.215892 = 1.215892\text{ mg/L Molecular TAN}$$

Conversely, if an un-scaled threshold of $1.0\text{ mg/L}$ is applied directly to `raw_ammonia_tan_nh3_mg_l`, it corresponds to a lower nitrogen equivalent:
$$\frac{1.0\text{ mg/L}}{1.215892} = 0.822441\text{ mg/L TAN-N}$$
Applying $1.0\text{ mg/L}$ without conversion imposes a stricter caution standard on 2025–2026 data than on 2021–2024 data.

---

## 3. Quantitative Dataset-Wide Audit

The complete breakdown of chemical reporting columns across years in [`toxicity_analysis_v2.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/processed_data_v2/toxicity_analysis_v2.csv) is presented in Table 1 (exported as [`target_basis_summary.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_target_definition_audit/target_basis_summary.csv)).

### Table 1: Target Provenance and Chemical Reporting Basis Breakdown by Year

| Year | Total Obs | TAN-N Populated | TAN-$\text{NH}_3$ Populated | Unverified $\text{NH}_3$ Populated | Overlap Both TAN | Emerson via TAN-N | Emerson via TAN-$\text{NH}_3$ | TAN-N $\ge 1.0$ | TAN-$\text{NH}_3$ $\ge 1.0$ | TAN-$\text{NH}_3$ $\ge 1.216$ | Primary $\text{NH}_3 \ge 0.05$ | Existing Risk Positives |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **2021** | 309 | 309 | 0 | 0 | 0 | 309 | 0 | 2 | 0 | 0 | 7 | 7 |
| **2022** | 1,431 | 1,431 | 0 | 0 | 0 | 1,431 | 0 | 18 | 0 | 0 | 169 | 170 |
| **2023** | 1,082 | 1,082 | 0 | 0 | 0 | 1,082 | 0 | 3 | 0 | 0 | 95 | 95 |
| **2024** | 1,523 | 1,523 | 0 | 0 | 0 | 1,523 | 0 | 11 | 0 | 0 | 199 | 200 |
| **2025** | 1,563 | 942 | 622 | 623 | 1 | 942 | 621 | 9 | 14 | 0 | 43 | 44 |
| **2026** | 1,037 | 0 | 1,037 | 1,037 | 0 | 0 | 1,037 | 0 | 17 | 1 | 55 | 55 |
| **Total** | **6,945** | **5,287** | **1,659** | **1,660** | **1** | **5,287** | **1,658** | **43** | **31** | **1** | **568** | **571** |

*(Note: In row index 5205, date 2025-08-01, both TAN-N (0.25) and TAN-NH3 (0.30) are populated. Emerson calculation priority prioritized TAN-N, yielding 5,287 records from TAN-N and 1,658 records from TAN-NH3).*

### 3.1 Dissection of the 571 Positive Records in Existing Heuristic
Across all 6,945 observations:
- Observations with `primary_calculated_nh3_mg_l >= 0.05`: **568**
- Observations with `raw_ammonia_tan_nh3_n_mg_l >= 1.0`: **43**
- Co-occurring observations (both conditions true): **40**
- Observations with `primary >= 0.05` but `TAN-N < 1.0` or null: **528**
- Observations with `primary < 0.05` but `TAN-N >= 1.0`: **Exactly 3 records**

### Table 2: The 3 Divergent Records Where TAN-N $\ge 1.0$ but Molecular $\text{NH}_3 < 0.05\text{ mg/L}$

| Row Index | Pond ID | Datetime | Temp ($^\circ\text{C}$) | pH | Raw TAN-N (mg/L) | Primary Calc $\text{NH}_3$ (mg/L) | Existing Heuristic |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **980** | `ara2_2167f891` | 2024-12-19 07:05:00 | 25.6 | 7.69 | 1.12 | 0.03835 | **1** |
| **4061** | `ara2_957cbe38` | 2025-04-15 07:15:00 | 25.4 | 7.86 | 1.01 | 0.04979 | **1** |
| **6807** | `ara2_fe1074da` | 2022-03-20 07:05:00 | 28.2 | 7.49 | 1.50 | 0.03912 | **1** |

Because water pH in these three instances was relatively low (7.49–7.86), the un-ionized dissociation fraction was suppressed ($f \approx 2.5\% - 4.1\%$), keeping molecular $\text{NH}_3$ below the $0.05\text{ mg/L}$ toxicity threshold despite elevated total ammonia.

---

## 4. Evaluation of Alternative Target Formulations

To quantify the sensitivity of Experiment 3 to target definitions and chemical thresholding, we formulate and compare four distinct rules:

- **Definition 0 (Existing Operational Heuristic):**  
  `primary_calculated_nh3_mg_l >= 0.05 OR raw_ammonia_tan_nh3_n_mg_l >= 1.0`
- **Definition 1 (Pure Toxic Molecular $\text{NH}_3$):**  
  `primary_calculated_nh3_mg_l >= 0.05`  
  *(Eliminates the empirical TAN caution branch entirely; strictly toxicological).*
- **Definition 2 (Stoichiometrically Consistent Dual-Basis Caution):**  
  `primary_calculated_nh3_mg_l >= 0.05 OR raw_ammonia_tan_nh3_n_mg_l >= 1.0 OR raw_ammonia_tan_nh3_mg_l >= 1.21589`  
  *(Applies the $1.0\text{ mg/L TAN-N}$ threshold with chemical molecular-weight conversion to molecular TAN).*
- **Definition 3 (Direct Unconverted Dual-Basis Caution):**  
  `primary_calculated_nh3_mg_l >= 0.05 OR raw_ammonia_tan_nh3_n_mg_l >= 1.0 OR raw_ammonia_tan_nh3_mg_l >= 1.0`  
  *(Applies an unadjusted $1.0\text{ mg/L}$ threshold uniformly across both columns).*

### Table 3: Comparative Label Impact Matrix (Exported as [`potential_label_impact.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_target_definition_audit/potential_label_impact.csv))

| Scope | Total $N$ | Def 0: Existing Positives (%) | Def 1: Pure $\text{NH}_3$ Positives (%) | Def 1 Flips | Def 2: Consistent MW Positives (%) | Def 2 Flips | Def 3: Direct 1.0 Positives (%) | Def 3 Flips |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Full Dataset** | 6,945 | 571 (8.22%) | 568 (8.18%) | 3 | 571 (8.22%) | **0** | 572 (8.24%) | 1 |
| Year 2021 | 309 | 7 (2.27%) | 7 (2.27%) | 0 | 7 (2.27%) | **0** | 7 (2.27%) | 0 |
| Year 2022 | 1,431 | 170 (11.88%) | 169 (11.81%) | 1 | 170 (11.88%) | **0** | 170 (11.88%) | 0 |
| Year 2023 | 1,082 | 95 (8.78%) | 95 (8.78%) | 0 | 95 (8.78%) | **0** | 95 (8.78%) | 0 |
| Year 2024 | 1,523 | 200 (13.13%) | 199 (13.07%) | 1 | 200 (13.13%) | **0** | 200 (13.13%) | 0 |
| Year 2025 | 1,563 | 44 (2.82%) | 43 (2.75%) | 1 | 44 (2.82%) | **0** | 45 (2.88%) | 1 |
| Year 2026 | 1,037 | 55 (5.30%) | 55 (5.30%) | 0 | 55 (5.30%) | **0** | 55 (5.30%) | 0 |
| **Exp 3 Pairs: All** | **4,900** | **314 (6.41%)** | **312 (6.37%)** | **2** | **314 (6.41%)** | **0** | **315 (6.43%)** | **1** |
| **Exp 3: Train** | **2,788** | **257 (9.22%)** | **256 (9.18%)** | **1** | **257 (9.22%)** | **0** | **257 (9.22%)** | **0** |
| **Exp 3: Cross** | **78** | **0 (0.00%)** | **0 (0.00%)** | **0** | **0 (0.00%)** | **0** | **0 (0.00%)** | **0** |
| **Exp 3: Test** | **2,034** | **57 (2.80%)** | **56 (2.75%)** | **1** | **57 (2.80%)** | **0** | **58 (2.85%)** | **1** |

---

## 5. Detailed Analysis of Empirical Impact on Experiment 3

### 5.1 Impact Under Stoichiometrically Consistent Caution (Definition 2)
When the $1.0\text{ mg/L TAN-N}$ threshold is converted to its stoichiometric molecular ammonia equivalent ($1.21589\text{ mg/L}$):
- In years 2025 and 2026, there are 1,659 records reporting under `raw_ammonia_tan_nh3_mg_l`.
- Exactly **1 record** in this subset has $\text{TAN} \ge 1.21589\text{ mg/L}$: Row 2887 (Pond `ara2_6ca69422`, date 2026-04-20, $\text{TAN} = 2.0\text{ mg/L}$, $\text{pH} = 7.77$, $\text{Temp} = 26.5^\circ\text{C}$).
- In Row 2887, Emerson molecular ammonia is already $0.07684\text{ mg/L} \ge 0.05\text{ mg/L}$.
- Consequently, Row 2887 was **already classified as Risk (1)** under the primary condition!
- **Conclusion:** Definition 2 produces **IDENTICAL binary labels** to Definition 0 across every single row in the dataset ($N=6,945$) and every single pair in Experiment 3 ($N=4,900$). **Flip rate = 0.000%**.

### 5.2 Impact Under Direct Unconverted $1.0\text{ mg/L}$ Threshold (Definition 3)
If $1.0\text{ mg/L}$ is applied directly to `raw_ammonia_tan_nh3_mg_l` without molecular-weight adjustment:
- There are 31 records in 2025–2026 with `raw_ammonia_tan_nh3_mg_l >= 1.0`.
- 30 of these records already had `primary_calculated_nh3_mg_l >= 0.05` and were already positive.
- Exactly **one single observation** has `raw_ammonia_tan_nh3_mg_l >= 1.0` while `primary_calculated_nh3_mg_l < 0.05`:
  - **Row 2373:** Pond `ara2_51ffa437`, Date: `2025-11-14 07:12:00`.
  - Measurements: $\text{pH} = 7.82$, $\text{Temp} = 27.6^\circ\text{C}$, $\text{TAN} = 1.0\text{ mg/L}$.
  - Calculated Emerson molecular $\text{NH}_3 = 0.04302\text{ mg/L}$ (below $0.05$).
  - Current label in Def 0: **0**. Label under Def 3: **1**.
- **Role in Experiment 3:**
  - Row 2373 appears as the prediction target (`next_risk`) in exactly **one test pair**:  
    Current visit: `2025-10-17 07:43:00` $\rightarrow$ Next visit: `2025-11-14 07:12:00` ($\Delta t = 27.98$ days).
  - Training Partition Impact: **0 flips**.
  - Cross-Cutoff Partition Impact: **0 flips**.
  - Test Partition Impact: Target positive prevalence increases by 1 observation ($57/2034 = 2.80\% \rightarrow 58/2034 = 2.85\%$, a shift of $+0.049\%$).

### 5.3 Impact Under Pure Molecular Ammonia (Definition 1)
If the secondary TAN caution rule is discarded entirely:
- Across the entire dataset, only the 3 borderline records from Table 2 (Rows 980, 4061, 6807) flip from 1 to 0.
- In Experiment 3 temporal pairs:
  - Row 980 was a current visit whose subsequent visit was after the 2025 cutoff (or had gap $> 45$ days); it was **never evaluated as a next-visit target**.
  - Row 6807 is the target in 1 training pair (`2022-03-04` $\rightarrow$ `2022-03-20`). Train positive count shifts from 257 to 256 ($9.22\% \rightarrow 9.18\%$).
  - Row 4061 is the target in 1 test pair (`2025-04-03` $\rightarrow$ `2025-04-15`). Test positive count shifts from 57 to 56 ($2.80\% \rightarrow 2.75\%$).
- Overall flip rate on Experiment 3 target labels: $2 / 4900 = 0.041\%$.

---

## 6. Formal Scientific Finding Classifications

| Finding ID | Classification | Finding Statement & Detailed Evidence |
| :---: | :---: | :--- |
| **F-01** | **`Verified`** | **Stoichiometric Conversion Equivalence:** The molecular weight ratio $\text{MW}(\text{NH}_3)/\text{MW}(\text{N}) = 17.031 / 14.007 = 1.215892$ is chemically exact. Applying $1.216\text{ mg/L}$ to `raw_ammonia_tan_nh3_mg_l` results in **zero label changes (0 flips)** across all 6,945 dataset rows and 4,900 Experiment 3 temporal pairs. |
| **F-02** | **`Verified`** | **Primary Calculation Rigor:** The Emerson et al. (1975) dissociation formula is implemented correctly across both TAN reporting columns with proper temperature Kelvin conversion ($T + 273.15$) and pH dependency. |
| **F-03** | **`Verified`** | **Temporal Split Integrity:** In Experiment 3, all 2,788 training pairs have both visits strictly $< 2025\text{-}01\text{-}01$. All 78 straddling pairs are properly quarantined. All 2,034 test pairs have current visit $\ge 2025\text{-}01\text{-}01$. |
| **F-04** | **`Potential issue`** | **Formula Asymmetry in Heuristic:** The code in `clean_datasets_v2.py` checks `raw_ammonia_tan_nh3_n_mg_l >= 1.0` but omits `raw_ammonia_tan_nh3_mg_l >= 1.0`. In 2026, where TAN-N is null, this secondary branch never evaluates. |
| **F-05** | **`Potential issue`** | **Direct Threshold Ambiguity:** If an operational practitioner intends $1.0\text{ mg/L}$ to be applied as a flat threshold to whichever TAN number is recorded without molecular conversion, exactly 1 observation in 2025 flips from 0 to 1, causing a 1-pair shift (0.049%) in the test set. |
| **F-06** | **`Cannot be verified from available data`** | **Unverified Reported Ammonia Protocol:** The source column `reported_ammonia_nh3_unverified_mg_l` has no accompanying laboratory standard operating procedure, test kit model name, or detection limit documentation in the repository. (It matches `raw_ammonia_tan_nh3_mg_l` in only 44.79% of instances and was properly excluded from all modeling). |
| **F-07** | **`Cannot be verified from available data`** | **Field Heuristic Origin:** The written metadata does not state whether the historical farm threshold of $1.0\text{ mg/L}$ was originally established by farm agronomists on a TAN-N basis or a molecular TAN basis. |

---

## 7. Final Scientific Conclusion and Recommendations

### 7.1 Conclusion
1. **Target Robustness Confirmed:** The target variable in Experiment 3 is remarkably robust. The identified formula asymmetry in `clean_datasets_v2.py` has **zero empirical impact** when evaluated under a chemically consistent molecular-weight conversion, and at most a negligible **0.049% impact (1 test pair)** under an unconverted interpretation.
2. **Model Metrics Valid:** The performance metrics, cross-validation scores, chronological holdout results, and persistence baselines reported in [`experiment_3_results_report.md`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_next_visit_risk_v1/experiment_3_results_report.md) and [`experiment_3_final_audit_report.md`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_next_visit_risk_v1/experiment_3_final_audit_report.md) are not artifactual. They reflect true predictive performance on the established dataset.

### 7.2 Recommendations for Future Work
1. **Do NOT Retrain Experiment 3:** Retraining models to alter 0 pairs (or 1 pair) would invalidate previously approved audit milestones without providing any measurable scientific benefit.
2. **Preserve Provisional Heuristic Language:** Future reporting must continue to clearly designate this target as a *provisional rule-based risk heuristic* rather than biological ground truth or laboratory-certified toxicity.
3. **Formalize Dual-Basis Caution in v3 Specs:** If a future data processing iteration (`v3`) is created, update the threshold logic to explicitly accommodate both TAN reporting bases using the stoichiometric conversion:
   ```python
   # Recommended v3 formulation
   is_nh3_toxic = df['primary_calculated_nh3_mg_l'] >= 0.05
   is_tan_caution = (
       (df['raw_ammonia_tan_nh3_n_mg_l'] >= 1.0) |
       (df['raw_ammonia_tan_nh3_mg_l'] >= 1.0 * (17.031 / 14.007))
   )
   df['provisional_ammonia_risk_heuristic'] = (is_nh3_toxic | is_tan_caution).astype(int)
   ```

---

## Deliverables Summary

All four audit deliverables requested by the user are fully generated and permanently persisted in the dedicated directory [`experiment_3_target_definition_audit/`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_target_definition_audit):

1. **[`target_definition_audit_report.md`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_target_definition_audit/target_definition_audit_report.md)**: This comprehensive scientific audit report.
2. **[`target_basis_summary.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_target_definition_audit/target_basis_summary.csv)**: Detailed year-by-year inventory of TAN reporting bases, Emerson calculation sources, and threshold crossings.
3. **[`potential_label_impact.csv`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_target_definition_audit/potential_label_impact.csv)**: Quantitative impact matrix evaluating positive counts and flip rates across 4 target definitions on the full dataset and all Experiment 3 partitions.
4. **[`target_formula_verification.txt`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/experiment_3_target_definition_audit/target_formula_verification.txt)**: Plaintext audit log summarizing mathematical equations, stoichiometric ratios, finding classifications, and validation checks.

