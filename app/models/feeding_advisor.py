"""
Feeding Advisory and Adaptive Feedback Module - Phase 3 Foundation
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Provides transparent, rule-based feeding advisory guidance and observational
adaptive feedback tracking.

Scientific Constraints & Governance:
- Operational Nature: Provisional rule-based operational heuristic.
- Scientific Validation: UNVERIFIED. These rules are NOT scientifically validated
  against site-specific bioenergetic trials, laboratory respirometry, or published
  regulatory standards.
- Causal Reality: Reducing feed minimizes additional unconsumed organic waste, biological
  oxygen demand (BOD), and excreted nitrogen, but feed reduction DOES NOT cause immediate
  water-quality recovery or eliminate existing hypoxia/ammonia spikes.
- Data Source Integrity: Simulated inputs (e.g. from IoT simulation models) are NEVER
  treated as actual commercial pond measurements.
- Operational Guardrail: Strictly advisory decision-support for farm managers.
  Does NOT automatically change feeding amounts, control electronic feeders, or trigger
  aeration equipment (no automated actuators).
- Adaptive Feedback Structure: Observational tracking and retrospective record-keeping only.
  Does NOT claim causal learning, reinforcement learning, or automatic optimization.
"""

from typing import Dict, Any, Union, Optional, List
import uuid
from datetime import datetime
import numpy as np
import pandas as pd


class FeedingAdvisorModel:
    """
    Transparent, rule-based Feeding Advisory Model for commercial aquaculture ponds.
    """

    def __init__(self):
        self.model_identifier = "feeding_advisor_rule_based"
        self.model_title = "Provisional Rule-Based Feeding Advisory"
        self.status = "PROVISIONAL_ADVISORY_GUIDANCE"

    @property
    def is_loaded(self) -> bool:
        """Rule-based advisory engine is always loaded and ready."""
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """Returns metadata, status, rules, and governance disclaimers."""
        return {
            "model_identifier": self.model_identifier,
            "model_title": self.model_title,
            "status": self.status,
            "is_operational_baseline": False,
            "advisory_type": "Rule-based provisional decision-support heuristic",
            "is_automatic_control": False,
            "warning": (
                "PROVISIONAL ADVISORY GUIDANCE ONLY: Feeding recommendations are unverified "
                "operational heuristics designed to assist farm managers. They are NOT scientifically "
                "validated against site-specific bioenergetic models. Reducing feed prevents additional "
                "uneaten feed and nitrogen waste, but DOES NOT guarantee water-quality recovery or fish "
                "survival. Recommendations require human operator verification and never execute automatic control."
            ),
            "limitations": [
                "Heuristic rules based on general aquaculture thresholds, not pond-specific calibrated bioenergetics.",
                "Feed reduction mitigates organic waste loading but does not reverse existing severe hypoxia.",
                "Simulated inputs must never be treated as physical pond measurements.",
                "Requires operator inspection; does not execute automated actuator or equipment commands."
            ],
            "rules_summary": {
                "dissolved_oxygen_throttles": {
                    "do_below_2_0_mg_l": "100% feed suppression (complete cessation recommended)",
                    "do_between_2_0_and_3_0_mg_l": "50% feed reduction recommended",
                    "do_between_3_0_and_4_0_mg_l": "20% feed reduction recommended",
                    "do_at_or_above_4_0_mg_l": "Normal feeding rate (100% baseline)"
                },
                "ammonia_throttles_when_available": {
                    "nh3_at_or_above_0_10_mg_l": "100% feed suppression (complete cessation recommended)",
                    "nh3_at_or_above_0_05_mg_l": "50% feed reduction recommended",
                    "tan_at_or_above_2_0_mg_l": "50% feed reduction recommended (provisional heuristic based on 2.0 mg/L TAN test-kit graduation, not an NH3 toxicity threshold)",
                    "tan_at_or_above_1_0_mg_l": "20% feed reduction recommended"
                },
                "temperature_modifiers": {
                    "temp_extreme_below_20_or_above_34_c": "20% feed reduction due to thermal metabolic stress"
                }
            }
        }

    def _extract_numeric(
        self, data: Dict[str, Any], aliases: List[str]
    ) -> Optional[float]:
        """Safely extracts a numeric value from multiple possible key aliases."""
        for alias in aliases:
            if alias in data and pd.notna(data[alias]):
                try:
                    val = float(data[alias])
                    if not np.isnan(val):
                        return val
                except (ValueError, TypeError):
                    continue
        return None

    def evaluate_advisory(
        self, inputs: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Evaluates water quality, biomass, and feed inputs to generate provisional feeding advice.

        Parameters:
            inputs: Dictionary or DataFrame containing DO, optional ammonia, feed, and pond info.

        Returns:
            Dictionary containing recommended feed, throttling factors, status, and explanations.
        """
        if isinstance(inputs, pd.DataFrame):
            if inputs.empty:
                return {
                    "is_valid": False,
                    "explanation": "Input DataFrame is empty.",
                    "status": "INPUT_VALIDATION_ERROR",
                    "operational_use_permitted": False
                }
            row = inputs.iloc[0].to_dict()
        elif isinstance(inputs, dict):
            row = inputs
        else:
            return {
                "is_valid": False,
                "explanation": f"Inputs must be a dict or DataFrame, got {type(inputs).__name__}.",
                "status": "INPUT_VALIDATION_ERROR",
                "operational_use_permitted": False
            }

        # 1. Data Source and Simulation Guardrail
        data_source = str(row.get("data_source", "field_inspection")).lower()
        raw_is_sim = row.get("is_simulated", False)
        if isinstance(raw_is_sim, str):
            flag_sim = raw_is_sim.strip().lower() in ("true", "1", "yes")
        else:
            flag_sim = bool(raw_is_sim)
        is_simulated = bool(flag_sim or "simulat" in data_source or "synthetic" in data_source)

        simulation_warning: Optional[str] = None
        if is_simulated:
            simulation_warning = (
                "SYNTHETIC / SIMULATED DATA WARNING: The inputs provided originate from a mathematical "
                "simulation model, NOT actual commercial pond telemetry. This advisory must NEVER be "
                "treated as real-world farm guidance or applied to living fish stocks."
            )

        # 2. Extract Water Quality Inputs
        curr_do = self._extract_numeric(row, ["dissolved_oxygen_mg_l", "curr_do", "DO (mg/L)", "do_mg_l", "DO"])
        curr_nh3 = self._extract_numeric(row, ["primary_calculated_nh3_mg_l", "curr_nh3", "nh3_mg_l", "un-ionized_ammonia_mg_l"])
        curr_tan = self._extract_numeric(row, ["ammonia_tan_nh3_n_mg_l", "tan_mg_l", "Ammonia—TAN (NH3-N) (mg/L)", "tan"])
        curr_temp = self._extract_numeric(row, ["temp_c", "curr_temp", "Temp (in °C)", "temperature_c"])

        # Validate mandatory DO input
        if curr_do is None:
            return {
                "is_valid": False,
                "status": "MISSING_REQUIRED_WATER_QUALITY",
                "explanation": (
                    "Missing required dissolved oxygen measurement ('dissolved_oxygen_mg_l'). "
                    "Cannot formulate a safe feeding advisory without current DO observation."
                ),
                "is_simulated": is_simulated,
                "simulation_warning": simulation_warning,
                "operational_use_permitted": False,
                "is_automatic_control": False
            }

        if curr_do < 0.0:
            return {
                "is_valid": False,
                "status": "INVALID_PHYSICAL_MEASUREMENT",
                "explanation": f"Dissolved oxygen cannot be negative. Received: {curr_do} mg/L.",
                "is_simulated": is_simulated,
                "simulation_warning": simulation_warning,
                "operational_use_permitted": False,
                "is_automatic_control": False
            }

        # 3. Determine Baseline Feeding Quantity
        curr_feed = self._extract_numeric(row, ["current_feed_amount_kg", "feed_amount_kg", "Feed amount (kg)", "baseline_feed_kg"])

        # Validate non-negative feed if provided
        if curr_feed is not None and curr_feed < 0.0:
            return {
                "is_valid": False,
                "status": "INVALID_PHYSICAL_MEASUREMENT",
                "explanation": f"Current feed amount cannot be negative. Received: {curr_feed} kg.",
                "is_simulated": is_simulated,
                "simulation_warning": simulation_warning,
                "operational_use_permitted": False,
                "is_automatic_control": False
            }

        fish_weight_g = self._extract_numeric(row, ["average_fish_weight_g", "current_weight_g", "curr_weight", "weight_g", "Weight"])
        stocking_density = self._extract_numeric(row, ["stocking_density_per_acre", "density_per_acre"])
        pond_acres = self._extract_numeric(row, ["Pond area in acres", "pond_area_acres", "acres", "pond_acres"])

        baseline_feed_kg: Optional[float] = None
        baseline_method: str = "unknown"
        estimated_biomass_kg: Optional[float] = None

        if curr_feed is not None and curr_feed > 0.0:
            baseline_feed_kg = float(curr_feed)
            baseline_method = "recorded_current_feed"
        elif fish_weight_g is not None and stocking_density is not None and pond_acres is not None:
            if fish_weight_g > 0.0 and stocking_density > 0.0 and pond_acres > 0.0:
                total_fish = stocking_density * pond_acres
                estimated_biomass_kg = round((total_fish * fish_weight_g) / 1000.0, 2)
                # Standard provisional body-weight feeding rate heuristic
                if fish_weight_g < 50.0:
                    rate_pct = 4.0
                elif fish_weight_g < 200.0:
                    rate_pct = 3.0
                elif fish_weight_g < 500.0:
                    rate_pct = 2.0
                else:
                    rate_pct = 1.5
                baseline_feed_kg = round(estimated_biomass_kg * (rate_pct / 100.0), 2)
                baseline_method = f"estimated_from_biomass_{rate_pct}pct_body_weight"

        if baseline_feed_kg is None or baseline_feed_kg <= 0.0:
            return {
                "is_valid": False,
                "status": "MISSING_FEEDING_OR_BIOMASS_DATA",
                "explanation": (
                    "Insufficient feeding or biomass data to establish a baseline feed quantity. "
                    "Please provide either 'current_feed_amount_kg' (> 0) or complete biomass parameters "
                    "('average_fish_weight_g', 'stocking_density_per_acre', and 'pond_area_acres')."
                ),
                "is_simulated": is_simulated,
                "simulation_warning": simulation_warning,
                "operational_use_permitted": False,
                "is_automatic_control": False
            }

        # 4. Evaluate Throttling Factors
        reasons: List[str] = []

        # A. Dissolved Oxygen Throttle
        if curr_do < 2.0:
            do_multiplier = 0.0
            do_status = "CRITICAL_HYPOXIA_CEASE_FEEDING"
            reasons.append(
                f"Critical Hypoxia (DO = {curr_do:.2f} mg/L < 2.0 mg/L): Recommended complete feeding cessation (100% cut). "
                "Digestion requires substantial oxygen; feeding during severe hypoxia causes acute mortality."
            )
        elif curr_do < 3.0:
            do_multiplier = 0.5
            do_status = "MODERATE_HYPOXIA_REDUCE_50"
            reasons.append(
                f"Moderate Hypoxia (DO = {curr_do:.2f} mg/L between 2.0 and 3.0 mg/L): Recommended 50% feed reduction "
                "to minimize post-prandial oxygen consumption."
            )
        elif curr_do < 4.0:
            do_multiplier = 0.8
            do_status = "BORDERLINE_DO_REDUCE_20"
            reasons.append(
                f"Borderline Dissolved Oxygen (DO = {curr_do:.2f} mg/L between 3.0 and 4.0 mg/L): Recommended 20% feed reduction "
                "as a precautionary measure until morning DO stabilizes."
            )
        else:
            do_multiplier = 1.0
            do_status = "DO_ADEQUATE"
            reasons.append(f"Dissolved Oxygen Adequate (DO = {curr_do:.2f} mg/L >= 4.0 mg/L): No DO-based suppression applied.")

        # B. Ammonia Throttle (when genuinely available)
        ammonia_multiplier = 1.0
        ammonia_status = "NOT_EVALUATED"

        if curr_nh3 is not None:
            if curr_nh3 >= 0.10:
                ammonia_multiplier = 0.0
                ammonia_status = "CRITICAL_NH3_CEASE_FEEDING"
                reasons.append(
                    f"Critical Un-ionized Ammonia (NH3 = {curr_nh3:.4f} mg/L >= 0.10 mg/L): Recommended complete feeding cessation (100% cut) "
                    "to prevent further metabolic and microbial nitrogen loading."
                )
            elif curr_nh3 >= 0.05:
                ammonia_multiplier = 0.5
                ammonia_status = "ELEVATED_NH3_REDUCE_50"
                reasons.append(
                    f"Elevated Un-ionized Ammonia (NH3 = {curr_nh3:.4f} mg/L >= 0.05 mg/L): Recommended 50% feed reduction."
                )
            else:
                ammonia_multiplier = 1.0
                ammonia_status = "NH3_NORMAL"
                reasons.append(f"Un-ionized Ammonia Acceptable (NH3 = {curr_nh3:.4f} mg/L < 0.05 mg/L).")
        elif curr_tan is not None:
            if curr_tan >= 2.0:
                ammonia_multiplier = 0.5
                ammonia_status = "ELEVATED_TAN_REDUCE_50"
                reasons.append(
                    f"Elevated Total Ammonia Nitrogen (TAN = {curr_tan:.2f} mg/L >= 2.0 mg/L test-kit graduation): Recommended 50% feed reduction."
                )
            elif curr_tan >= 1.0:
                ammonia_multiplier = 0.8
                ammonia_status = "BORDERLINE_TAN_REDUCE_20"
                reasons.append(
                    f"Borderline Total Ammonia Nitrogen (TAN = {curr_tan:.2f} mg/L >= 1.0 mg/L): Recommended 20% feed reduction."
                )
            else:
                ammonia_multiplier = 1.0
                ammonia_status = "TAN_NORMAL"
                reasons.append(f"Total Ammonia Nitrogen Normal (TAN = {curr_tan:.2f} mg/L < 1.0 mg/L).")
        else:
            ammonia_multiplier = 1.0
            ammonia_status = "AMMONIA_DATA_UNAVAILABLE"
            reasons.append("Ammonia measurement not provided; ammonia safety throttle was not evaluated.")

        # C. Water Temperature Modifier (optional)
        temp_multiplier = 1.0
        if curr_temp is not None:
            if curr_temp < 20.0 or curr_temp > 34.0:
                temp_multiplier = 0.8
                reasons.append(
                    f"Thermal Stress (Temp = {curr_temp:.1f}°C outside 20–34°C): Recommended 20% feed reduction "
                    "due to thermal inhibition of fish metabolic feeding response."
                )

        # 5. Calculate Recommended Quantity
        combined_water_quality_factor = min(do_multiplier, ammonia_multiplier)
        effective_multiplier = round(combined_water_quality_factor * temp_multiplier, 3)
        recommended_feed_kg = round(baseline_feed_kg * effective_multiplier, 2)
        reduction_pct = round((1.0 - (recommended_feed_kg / baseline_feed_kg)) * 100.0, 1)

        # Categorical advisory action
        if effective_multiplier == 0.0:
            action = "CEASE_FEEDING"
        elif effective_multiplier <= 0.5:
            action = "SUBSTANTIAL_FEED_REDUCTION"
        elif effective_multiplier < 1.0:
            action = "MODERATE_FEED_REDUCTION"
        else:
            action = "NORMAL_FEEDING"

        meta = self.get_metadata()

        if is_simulated:
            status_label = "SIMULATED_SCENARIO_ONLY"
            action_label = f"SIMULATED_{action}"
            operational_permitted = False
            demonstration_notice = (
                "SIMULATED SCENARIO ONLY (DEMONSTRATION): This output was generated from synthetic or "
                "simulated benchmark data. It is intended strictly for model demonstration and testing, "
                "and MUST NOT be used to guide actual commercial fish feeding, pond management, or live biological operations."
            )
        else:
            status_label = "ADVISORY_GENERATED"
            action_label = action
            operational_permitted = True
            demonstration_notice = None

        return {
            "is_valid": True,
            "status": status_label,
            "advisory_action": action_label,
            "operational_use_permitted": operational_permitted,
            "baseline_feed_kg": baseline_feed_kg,
            "baseline_method": baseline_method,
            "recommended_feed_kg": recommended_feed_kg,
            "reduction_percentage": reduction_pct,
            "effective_multiplier": effective_multiplier,
            "estimated_biomass_kg": estimated_biomass_kg,
            "throttling_factors": {
                "do_multiplier": do_multiplier,
                "do_status": do_status,
                "ammonia_multiplier": ammonia_multiplier,
                "ammonia_status": ammonia_status,
                "temperature_multiplier": temp_multiplier
            },
            "observed_water_quality": {
                "dissolved_oxygen_mg_l": curr_do,
                "un_ionized_nh3_mg_l": curr_nh3,
                "tan_mg_l": curr_tan,
                "temperature_c": curr_temp
            },
            "advisory_explanations": reasons,
            "data_source": data_source,
            "is_simulated": is_simulated,
            "simulation_warning": simulation_warning,
            "demonstration_warning": demonstration_notice,
            "is_automatic_control": False,
            "control_action": None,
            "warning": meta["warning"],
            "disclaimer": (
                "Provisional advisory guidance for human operator review only. Feed reduction mitigates organic waste loading "
                "but does not cause water-quality recovery or cure hypoxia. No automated control actions are executed."
            )
        }


class FeedingFeedbackTracker:
    """
    Observational tracking structure for recording feeding recommendations,
    farmer actions, and subsequent water quality changes.
    
    Strictly an observational audit log; does NOT perform causal inference,
    reinforcement learning, or automatic parameter optimization.
    """

    def __init__(self):
        self._records: List[Dict[str, Any]] = []

    def record_feedback(
        self,
        pond_id: str,
        advisory_record: Dict[str, Any],
        actual_feed_kg: float,
        next_observation: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records a farmer feeding action following an advisory recommendation.

        Parameters:
            pond_id: Identifier of the pond.
            advisory_record: The output dictionary from FeedingAdvisorModel.evaluate_advisory().
            actual_feed_kg: The actual kilograms of feed dispensed by the farmer.
            next_observation: Optional subsequent water quality observation dictionary.
            notes: Optional text notes from the farmer or farm technician.

        Returns:
            Dictionary containing the stored feedback record.
        """
        record_id = str(uuid.uuid4())[:8]
        created_at = datetime.now().isoformat()

        try:
            actual_feed = float(actual_feed_kg)
            if actual_feed < 0.0:
                raise ValueError("Actual feed cannot be negative.")
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid actual feed quantity: {actual_feed_kg!r}") from exc

        recommended_feed = advisory_record.get("recommended_feed_kg", np.nan)
        baseline_feed = advisory_record.get("baseline_feed_kg", np.nan)

        compliance_delta_kg: Optional[float] = None
        if pd.notna(recommended_feed):
            compliance_delta_kg = round(actual_feed - float(recommended_feed), 2)

        # Condition transition analysis
        initial_obs = advisory_record.get("observed_water_quality", {})
        condition_change = self.evaluate_condition_change(initial_obs, next_observation)

        stored_record = {
            "record_id": record_id,
            "timestamp": created_at,
            "pond_id": str(pond_id),
            "advisory_action": advisory_record.get("advisory_action", "UNKNOWN"),
            "operational_use_permitted": bool(advisory_record.get("operational_use_permitted", False)),
            "baseline_feed_kg": baseline_feed,
            "recommended_feed_kg": recommended_feed,
            "actual_feed_kg": actual_feed,
            "compliance_delta_kg": compliance_delta_kg,
            "initial_observation": initial_obs,
            "next_observation": next_observation or {},
            "condition_change": condition_change,
            "notes": notes,
            "governance_notice": (
                "OBSERVATIONAL AUDIT RECORD ONLY: This feedback mechanism logs farmer actions "
                "and subsequent water quality readings for retrospective human inspection. "
                "It does NOT perform causal learning, automated parameter tuning, reinforcement learning, "
                "or automatic optimization."
            )
        }

        self._records.append(stored_record)
        return stored_record

    def evaluate_condition_change(
        self,
        initial_obs: Dict[str, Any],
        next_obs: Optional[Dict[str, Any]]
    ) -> str:
        """
        Evaluates whether water quality improved, worsened, or remained unchanged.

        Parameters:
            initial_obs: Initial water quality dict containing DO and optional ammonia.
            next_obs: Next water quality dict containing subsequent DO and ammonia.

        Returns:
            One of: 'improved', 'worsened', 'unchanged', 'insufficient_data'.
        """
        if not next_obs or not isinstance(next_obs, dict):
            return "insufficient_data_pending_next_observation"

        init_do = initial_obs.get("dissolved_oxygen_mg_l")
        next_do = next_obs.get("dissolved_oxygen_mg_l")

        if init_do is None or next_do is None or pd.isna(init_do) or pd.isna(next_do):
            return "insufficient_data_missing_do"

        try:
            do_delta = float(next_do) - float(init_do)
        except (ValueError, TypeError):
            return "insufficient_data_invalid_numeric"

        # Check un-ionized ammonia if available
        init_nh3 = initial_obs.get("un_ionized_nh3_mg_l")
        next_nh3 = next_obs.get("un_ionized_nh3_mg_l")
        nh3_delta: Optional[float] = None
        if init_nh3 is not None and next_nh3 is not None and pd.notna(init_nh3) and pd.notna(next_nh3):
            try:
                nh3_delta = float(next_nh3) - float(init_nh3)
            except (ValueError, TypeError):
                nh3_delta = None

        # Evaluative heuristic for water quality transition
        # DO improvement >= +0.5 mg/L without severe ammonia spike
        is_do_improved = do_delta >= 0.5
        is_do_worsened = do_delta <= -0.5
        is_nh3_worsened = (nh3_delta is not None) and (nh3_delta >= 0.02)
        is_nh3_improved = (nh3_delta is not None) and (nh3_delta <= -0.02)

        if is_do_worsened or is_nh3_worsened:
            return "worsened"
        elif is_do_improved and not is_nh3_worsened:
            return "improved"
        elif is_nh3_improved and not is_do_worsened:
            return "improved"
        else:
            return "unchanged"

    def get_records(self, pond_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns stored feedback records, optionally filtered by pond_id."""
        if pond_id is None:
            return list(self._records)
        return [r for r in self._records if r.get("pond_id") == pond_id]

    def clear_records(self) -> None:
        """Clears in-memory feedback history."""
        self._records.clear()

