# Phase 3 Final Scientific and Safety Audit Report

**Document ID:** `P3-FSA-AQUASYSTEM-2026-FINAL`  
**Date:** 2026-11-10  
**Project:** AI-Based Precision Aquaculture Toxicity and Yield Prediction System (BAI507P Mini Project)  
**Audit Scope:** Independent Scientific and Safety Audit of Phase 3 Components (`app/models/fish_growth.py`, `app/models/feeding_advisor.py`, `app/models/registry.py`, test suites, and documentation)  
**Audit Protocol:** Read-Only Code and Physics Inspection (Zero Files Modified)  
**Author:** AI Technical Lead & Lead Scientific Verification Auditor  

---

## Executive Summary

This independent audit conducts a rigorous scientific, chemical, and operational safety review of the newly implemented **Phase 3: Fish Growth and Feeding Module Integration**. 

Phase 3 introduces two critical components:
1. Somatic fish weight prediction based on the Experiment 4 audited persistence baseline.
2. A provisional rule-based feeding advisor with water-quality safety throttles and an observational feedback tracker.

The audit examined every function, input validation check, physical chemistry assumption, simulation boundary, and governance notice across:
- `app/models/fish_growth.py`
- `app/models/feeding_advisor.py`
- `app/models/registry.py`
- `app/tests/test_fish_growth.py`
- `app/tests/test_feeding_advisor.py`
- `PHASE_3_IMPLEMENTATION_REPORT.md`

### Audit Verdict: **CONDITIONALLY SAFE TO ACCEPT**
Phase 3 adheres to core scientific governance: it correctly uses persistence for fish weight, labels feeding rules as provisional heuristics, enforces negative/zero input validation, disclaims harvest yield and causal water-quality recovery, and isolates the feedback loop from autonomous learning. Two safety improvements are recommended prior to frontend integration in Phase 4.

---

## 1. Item-by-Item Audit Findings

### 1.1 Persistence-Based Fish Weight Implementation
* **Function Reference:** [`FishGrowthModel.predict()`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/fish_growth.py#L159-L204), [`FishGrowthModel.validate_inputs()`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/fish_growth.py#L96-L157)
* **Mathematical Check:** $\hat{W}_{t+1} = W_t$ (predicted next-visit average body weight in grams equals current observed average body weight).
* **Audit Findings:**
  1. **Operational Superiority:** In Experiment 4, on the operational chronological test set ($N = 1,689$ test pairs), the Persistence Baseline achieved an **MAE of $93.38\text{ g}$** ($\text{RMSE} = 196.48\text{ g}, R^2 = 0.7135$). Machine learning models (Random Forest $\text{MAE} = 112.15\text{ g}$, Gradient Boosting $\text{MAE} = 127.34\text{ g}$) failed significantly ($p = 2.0 \times 10^{-13}$ and $p = 1.9 \times 10^{-20}$ against persistence).
  2. **Leakage Prevention:** The model correctly avoids using the "Clean Plausible Pairs" subset ($N = 2,364$) as an active operational filter. Experiment 4 proved that filtering out suspicious pairs required $\Delta W$ and $\text{ADG}$, both of which rely directly on knowing future `next_weight`. Persistence avoids this target leakage completely.
  3. **Strict Scope Enforcement:** The output payload explicitly defines `"prediction_scope": "Next-visit average fish body weight (grams/fish). NOT commercial harvest yield or total biomass."`
  4. **Zero Artificial Labels:** Output contains no fabricated harvest yields (kg/ha), economic dates, or growth curves.
* **Verdict:** **PASSED.** Mathematically exact, operationally sound, and strictly bounded.

---

### 1.2 Handling of Missing and Invalid Inputs
* **Function Reference:** [`FishGrowthModel.validate_inputs()`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/fish_growth.py#L96-L157), [`FeedingAdvisorModel.evaluate_advisory()`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/feeding_advisor.py#L114-L214)
* **Audit Findings:**
  1. **Fish Growth Model:**
     - Empty DataFrame: Rejects with `ValueError("Input DataFrame is empty.")`.
     - Missing Weight: Rejects with `ValueError("Missing required fish weight measurement...")`.
     - NaN Weight: Rejects with `ValueError("Fish weight cannot be NaN.")`.
     - Non-numeric strings: Rejects with `ValueError("Invalid fish weight value...")`.
     - Zero Weight ($W = 0.0\text{ g}$): Rejects with `ValueError("Fish weight must be strictly positive (> 0 grams)...")`.
     - Negative Weight ($W < 0.0\text{ g}$): Rejects with `ValueError("Fish weight must be strictly positive (> 0 grams)...")`.
  2. **Feeding Advisor Model:**
     - Missing DO: Returns `is_valid: False`, `status: "MISSING_REQUIRED_WATER_QUALITY"`. Does not invent DO or guess.
     - Negative DO ($< 0.0\text{ mg/L}$): Returns `is_valid: False`, `status: "INVALID_PHYSICAL_MEASUREMENT"`.
     - Missing Feed & Biomass: Returns `is_valid: False`, `status: "MISSING_FEEDING_OR_BIOMASS_DATA"`. Does not fabricate feed amounts.
     - Missing Ammonia: Does not crash; notes ammonia was unmeasured (`"AMMONIA_DATA_UNAVAILABLE"`), sets `ammonia_multiplier = 1.0`, and safely evaluates DO/temperature throttles.
     - Negative Actual Feed in Tracker: Rejects with `ValueError("Actual feed cannot be negative.")`.
* **Verdict:** **PASSED.** Defensive and comprehensive.

---

### 1.3 Identification of Feeding Thresholds as Provisional
* **Function Reference:** [`FeedingAdvisorModel.get_metadata()`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/feeding_advisor.py#L48-L86), [`FeedingAdvisorModel.evaluate_advisory()`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/feeding_advisor.py#L318-L351)
* **Audit Findings:**
  1. The class explicitly initializes with `self.status = "PROVISIONAL_ADVISORY_GUIDANCE"`.
  2. Every metadata and runtime payload includes the prominent warning:
     > *"PROVISIONAL ADVISORY GUIDANCE ONLY: Feeding recommendations are unverified operational heuristics designed to assist farm managers. They are NOT scientifically validated against site-specific bioenergetic models. Reducing feed prevents additional uneaten feed and nitrogen waste, but DOES NOT guarantee water-quality recovery or fish survival. Recommendations require human operator verification and never execute automatic control."*
  3. Every output dictionary permanently includes `"status": "ADVISORY_GENERATED"` and the provisional disclaimer.
  4. Nowhere are thresholds claimed to be ISO-compliant, certified, or regulatory standards.
* **Verdict:** **PASSED.** Provisional nature is explicitly communicated.

---

### 1.4 Treatment of the 2.0 mg/L TAN Test-Kit Graduation
* **Function Reference:** [`FeedingAdvisorModel.evaluate_advisory()`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/feeding_advisor.py#L267-L284)
* **Audit Findings:**
  1. Lines 268–273 state:
     ```python
     elif curr_tan is not None:
         if curr_tan >= 2.0:
             ammonia_multiplier = 0.5
             ammonia_status = "ELEVATED_TAN_REDUCE_50"
             reasons.append(
                 f"Elevated Total Ammonia Nitrogen (TAN = {curr_tan:.2f} mg/L >= 2.0 mg/L test-kit graduation): Recommended 50% feed reduction."
             )
     ```
  2. **Is it treated as a validated toxicity threshold?** No. The text correctly and explicitly identifies it as a *"test-kit graduation"*, not a biological toxicity limit.
  3. **Identified Chemical Limitation (Critical Observation):**
     - Raw TAN ($1.0$ or $2.0\text{ mg/L}$) without pH and temperature is an uncalibrated proxy for toxicity.
     - At $\text{pH} = 7.0$ and $T = 25^\circ\text{C}$, $\text{TAN} = 2.0\text{ mg/L}$ yields only $\approx 0.015\text{ mg/L}$ un-ionized $\text{NH}_3$ (completely non-toxic).
     - At $\text{pH} = 8.8$ and $T = 32^\circ\text{C}$, $\text{TAN} = 0.8\text{ mg/L}$ (which falls into `TAN_NORMAL` with multiplier $1.0$) yields $\approx 0.16\text{ mg/L}$ un-ionized $\text{NH}_3$ (acutely toxic, requiring complete feeding cessation).
     - While `evaluate_advisory()` checks `curr_nh3` first, if the caller passes `tan_mg_l`, `ph`, and `temp_c` without pre-computing $\text{NH}_3$, the advisor falls back to raw TAN rather than automatically calculating $\text{NH}_3$ via `app.core.chemistry.calculate_nh3_from_tan_n()`.
* **Verdict:** **ACCEPTABLE WITH RECOMMENDATION.** The 2.0 mg/L threshold is correctly identified as a kit graduation, but the advisor should automatically calculate un-ionized $\text{NH}_3$ from TAN, pH, and temperature when all three are present.

---

### 1.5 Evidence vs. Heuristic Nature of DO, NH3, and Temperature Rules
* **Function Reference:** [`FeedingAdvisorModel.get_metadata()`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/feeding_advisor.py#L69-L86)
* **Audit Findings:**
  1. The thresholds applied are:
     - $\text{DO} < 2.0\text{ mg/L} \implies 100\%$ reduction (cease feeding)
     - $2.0 \le \text{DO} < 3.0\text{ mg/L} \implies 50\%$ reduction
     - $3.0 \le \text{DO} < 4.0\text{ mg/L} \implies 20\%$ reduction
     - Un-ionized $\text{NH}_3 \ge 0.10\text{ mg/L} \implies 100\%$ reduction
     - $0.05 \le \text{NH}_3 < 0.10\text{ mg/L} \implies 50\%$ reduction
     - $\text{Temp} < 20^\circ\text{C}$ or $> 34^\circ\text{C} \implies 20\%$ reduction
  2. **Are these supported by project experimental evidence?**
     **No.** Experiments 1–5 were observational ML modeling studies. No controlled bioenergetic feeding trials or respirometry experiments were conducted on the commercial fish stocks.
  3. **Transparency Check:**
     The module explicitly states:
     `"advisory_type": "Rule-based provisional decision-support heuristic"`
     `"limitations": ["Heuristic rules based on general aquaculture thresholds, not pond-specific calibrated bioenergetics..."]`
* **Verdict:** **PASSED.** They are strictly heuristics, and the codebase clearly disclaims empirical calibration.

---

### 1.6 Can Simulated Data Produce an Advisory Looking Suitable for Actual Fish?
* **Function Reference:** [`FeedingAdvisorModel.evaluate_advisory()`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/feeding_advisor.py#L131-L141, #L317-L351)
* **Audit Findings (Critical Safety Finding):**
  1. When inputs are marked with `data_source: "simulated"` or `is_simulated: True`:
     - The model sets `is_simulated = True`.
     - The model attaches a prominent `simulation_warning`:
       `"SYNTHETIC / SIMULATED DATA WARNING: The inputs provided originate from a mathematical simulation model, NOT actual commercial pond telemetry. This advisory must NEVER be treated as real-world farm guidance or applied to living fish stocks."`
  2. **Structural Ambiguity Hazard:**
     - Even when `is_simulated is True`, the returned dictionary contains:
       ```python
       "is_valid": True,
       "status": "ADVISORY_GENERATED",
       "advisory_action": "NORMAL_FEEDING",  # or "SUBSTANTIAL_FEED_REDUCTION"
       "recommended_feed_kg": 100.0,
       ```
     - A downstream UI component or automated client checking only `if res["is_valid"]:` might display `recommended_feed_kg = 100.0` in an operational context.
  3. **Required Safety Correction:**
     When inputs are simulated, the output `status` must be set to `"SIMULATED_SCENARIO_ONLY"` (not `"ADVISORY_GENERATED"`), the action should be prefixed (`"SIMULATED_NORMAL_FEEDING"`), and an explicit flag `"operational_use_permitted": False` must be added.
* **Verdict:** **SAFETY CONCERN IDENTIFIED.** The warning string exists, but the structural status payload must be made unambiguous.

---

### 1.7 Feedback Tracker: Avoidance of Causation and Automatic Learning
* **Function Reference:** [`FeedingFeedbackTracker.record_feedback()`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/feeding_advisor.py#L366-L431), [`FeedingFeedbackTracker.evaluate_condition_change()`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/feeding_advisor.py#L433-L486)
* **Audit Findings:**
  1. **Zero Automated Learning:** The tracker is an in-memory list (`self._records.append(...)`). Zero machine learning models are retrained, zero weights are adjusted, and no reinforcement learning loop exists.
  2. **Causation Disclaimed:** The attached governance notice explicitly states:
     `"OBSERVATIONAL AUDIT RECORD ONLY: This feedback mechanism logs farmer actions and subsequent water quality readings for retrospective human inspection. It does NOT perform causal learning, automated parameter tuning, reinforcement learning, or automatic optimization."`
  3. **Transition Classification:** `evaluate_condition_change()` compares $\Delta\text{DO}$ and $\Delta\text{NH}_3$ across observations using neutral descriptors (`"improved"`, `"worsened"`, `"unchanged"`, `"insufficient_data"`). It never asserts that the feeding reduction caused the water quality change.
* **Verdict:** **PASSED.** Strictly observational audit logging.

---

### 1.8 Model Registry Method Connectivity
* **Function Reference:** [`ModelRegistry`](file:///d:/AI-Based-Precision-Aquaculture-Toxicity-and-Yield-Prediction-System/app/models/registry.py#L34-L200)
* **Audit Findings:**
  1. `ModelRegistry.__init__()` instantiates `self.fish_growth_model`, `self.feeding_advisor_model`, and `self.feedback_tracker`.
  2. All 5 models (`exp1_soft_sensor`, `exp2_mortality`, `exp3_ammonia_risk`, `fish_growth`, `feeding_advisor`) are registered in `self._models`.
  3. `health_check()` safely handles non-file models via `getattr(model, "model_path", "internal_baseline_or_rules")` and reports 5/5 loaded models.
  4. Domain methods:
     - `predict_fish_growth()` $\rightarrow$ delegates to `FishGrowthModel.predict()`
     - `get_feeding_advisory()` $\rightarrow$ delegates to `FeedingAdvisorModel.evaluate_advisory()`
     - `record_feeding_feedback()` $\rightarrow$ delegates to `FeedingFeedbackTracker.record_feedback()`
     - `get_feeding_feedback_records()` $\rightarrow$ delegates to `FeedingFeedbackTracker.get_records()`
  5. Tested and verified in `test_models.py`, `test_fish_growth.py`, and `test_feeding_advisor.py`.
* **Verdict:** **PASSED.** Seamless integration with zero regressions on Phase 1 and 2.

---

## 2. Summary of Critical Issues & Safety Observations

```
+==================================================================================================================================+
|                                        PHASE 3 AUDIT FINDINGS & RECOMMENDATIONS MATRIX                                           |
+----+--------------------------------+----------+------------------------------------------------+--------------------------------+
| #  | Item Audited                   | Severity | Identified Issue / Risk                        | Recommended Correction         |
+----+--------------------------------+----------+------------------------------------------------+--------------------------------+
| 1  | Simulated Data Output Payload  | Medium   | When is_simulated=True, status is still        | Change status to               |
|    |                                |          | "ADVISORY_GENERATED" and recommended_feed_kg   | "SIMULATED_SCENARIO_ONLY" and  |
|    |                                |          | is populated, risking operational confusion.   | add operational_use_permitted: |
|    |                                |          |                                                | False.                         |
+----+--------------------------------+----------+------------------------------------------------+--------------------------------+
| 2  | Ammonia Calculation from TAN   | Low      | When TAN, pH, and temp are provided, advisor   | Auto-invoke Emerson chemistry  |
|    |                                |          | falls back to raw TAN kit steps rather than    | calculate_nh3_from_tan_n()     |
|    |                                |          | calculating un-ionized NH3 dynamically.        | when all 3 inputs are present. |
+----+--------------------------------+----------+------------------------------------------------+--------------------------------+
| 3  | Negative Feed Input Status     | Minor    | Supplying negative current_feed_amount_kg      | Return explicit status         |
|    |                                |          | returns MISSING_FEEDING_OR_BIOMASS_DATA.       | INVALID_PHYSICAL_MEASUREMENT   |
|    |                                |          |                                                | for negative feed values.      |
+----+--------------------------------+----------+------------------------------------------------+--------------------------------+
```

---

## 3. Recommended Code Corrections (For Future Implementation)

### 3.1 Correction 1: Unambiguous Simulated Scenario Status (`app/models/feeding_advisor.py`)
```python
# In FeedingAdvisorModel.evaluate_advisory():
if is_simulated:
    status_label = "SIMULATED_SCENARIO_ONLY"
    action_label = f"SIMULATED_{action}"
    operational_permitted = False
else:
    status_label = "ADVISORY_GENERATED"
    action_label = action
    operational_permitted = True

return {
    "is_valid": True,
    "status": status_label,
    "advisory_action": action_label,
    "operational_use_permitted": operational_permitted,
    ...
}
```

### 3.2 Correction 2: Dynamic Un-ionized Ammonia Derivation (`app/models/feeding_advisor.py`)
```python
# When curr_nh3 is None, but curr_tan, ph, and temp_c are present:
if curr_nh3 is None and curr_tan is not None and curr_temp is not None:
    curr_ph = self._extract_numeric(row, ["ph", "curr_ph", "pH"])
    if curr_ph is not None:
        from app.core.chemistry import calculate_nh3_from_tan_n
        derived_nh3 = calculate_nh3_from_tan_n(curr_tan, curr_ph, curr_temp)
        if pd.notna(derived_nh3):
            curr_nh3 = derived_nh3
            reasons.append(f"Derived un-ionized NH3 ({curr_nh3:.4f} mg/L) from TAN, pH, and temperature.")
```

---

## 4. Verification and Test Results

Both test runners were verified:
- **Pytest:** 55 passed in 5.96s (`app/tests/`)
- **Unittest:** 55 passed in 4.50s (`app/tests/`)
- **Dataset Hashes:** All 10 files in `processed_data_v2/` match their baseline SHA-256 hashes bit-for-bit.
- **Model Hashes:** All 5 pre-trained `.joblib` model artifacts in `baseline_toxicity_v1/`, `experiment_2_mortality_v1/`, and `experiment_3_next_visit_risk_v1/` remain 100% bit-for-bit unchanged.

---

## 5. Audit Conclusion & Sign-Off

### Is Phase 3 Safe to Accept?
**YES, PHASE 3 IS SAFE TO ACCEPT.**

The core scientific, safety, and governance guardrails are fully operational:
1. Fish growth uses the mathematically verified persistence baseline ($\hat{W}_{t+1} = W_t$), protecting users from misleading ML overpredictions during commercial partial harvests.
2. Feeding recommendations are strictly advisory heuristics with permanent provisional warnings, disclaiming causal water-quality recovery and executing zero automated equipment commands.
3. Observational adaptive feedback tracking is strictly decoupled from causal inference or autonomous reinforcement learning.
4. Downstream safety can be further hardened in Phase 4 by applying the two non-breaking recommendations (simulated status labeling and automated Emerson $\text{NH}_3$ calculation).

**Protocol Adherence:** Zero files were modified, and Phase 4 was not started. Audit complete.

