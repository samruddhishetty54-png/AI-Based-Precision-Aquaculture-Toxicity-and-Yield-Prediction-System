"""
Test Suite: Feeding Advisory and Adaptive Feedback Module - Phase 3
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Verifies transparent, rule-based feeding advisory throttles, input validation,
simulated vs historical labeling, provisional disclaimers, no-automatic-control
guardrails, and observational adaptive feedback tracking.
"""

import unittest
import numpy as np
import pandas as pd

from app.models.feeding_advisor import FeedingAdvisorModel, FeedingFeedbackTracker
from app.models.registry import get_model_registry


class TestFeedingAdvisorModel(unittest.TestCase):
    """
    Unit test cases for the Feeding Advisory Model.
    """

    def setUp(self):
        self.advisor = FeedingAdvisorModel()
        self.tracker = FeedingFeedbackTracker()
        self.registry = get_model_registry()

    def test_normal_feeding_with_recorded_baseline(self):
        """
        Verifies normal feeding advisory when DO >= 4.0 mg/L and feed amount is known.
        """
        payload = {
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 5.5,
            "temp_c": 28.0,
            "data_source": "field_inspection"
        }
        res = self.advisor.evaluate_advisory(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["status"], "ADVISORY_GENERATED")
        self.assertEqual(res["advisory_action"], "NORMAL_FEEDING")
        self.assertEqual(res["baseline_feed_kg"], 100.0)
        self.assertEqual(res["recommended_feed_kg"], 100.0)
        self.assertEqual(res["reduction_percentage"], 0.0)
        self.assertFalse(res["is_automatic_control"])
        self.assertIsNone(res["control_action"])
        self.assertFalse(res["is_simulated"])
        self.assertTrue(res["operational_use_permitted"])
        self.assertIsNone(res["demonstration_warning"])

    def test_biomass_based_feeding_estimation(self):
        """
        Verifies that baseline feed is estimated from biomass when feed amount is omitted.
        """
        payload = {
            "average_fish_weight_g": 300.0,  # 2% rate category
            "stocking_density_per_acre": 4000.0,
            "Pond area in acres": 2.5,
            "dissolved_oxygen_mg_l": 6.0
        }
        # Biomass = (4000 * 2.5 * 300) / 1000 = 3,000 kg. 2% rate = 60 kg baseline.
        res = self.advisor.evaluate_advisory(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["estimated_biomass_kg"], 3000.0)
        self.assertEqual(res["baseline_feed_kg"], 60.0)
        self.assertEqual(res["recommended_feed_kg"], 60.0)
        self.assertTrue(res["operational_use_permitted"])
        self.assertIn("biomass", res["baseline_method"])

    def test_dataframe_input_supported(self):
        """
        Verifies that a single-row pandas DataFrame is supported for feeding advisory.
        """
        df = pd.DataFrame([{
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 5.0,
            "temp_c": 28.0,
            "data_source": "field_inspection"
        }])
        res = self.advisor.evaluate_advisory(df)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["status"], "ADVISORY_GENERATED")
        self.assertEqual(res["recommended_feed_kg"], 100.0)
        self.assertTrue(res["operational_use_permitted"])

    def test_empty_dataframe_returns_validation_error(self):
        """
        Verifies that passing an empty DataFrame returns an input validation error.
        """
        res = self.advisor.evaluate_advisory(pd.DataFrame())
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["status"], "INPUT_VALIDATION_ERROR")
        self.assertFalse(res["operational_use_permitted"])
        self.assertIn("DataFrame is empty", res["explanation"])

    def test_nan_water_quality_values_handled_safely(self):
        """
        Verifies that NaN values in water quality inputs are treated as missing measurements.
        """
        payload = {
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": np.nan
        }
        res = self.advisor.evaluate_advisory(payload)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["status"], "MISSING_REQUIRED_WATER_QUALITY")
        self.assertFalse(res["operational_use_permitted"])

    def test_missing_do_returns_explanation(self):
        """
        Verifies that omitting DO does not crash or invent advice, but returns a clear explanation.
        """
        payload = {
            "current_feed_amount_kg": 80.0,
            # 'dissolved_oxygen_mg_l' is omitted
            "temp_c": 27.5
        }
        res = self.advisor.evaluate_advisory(payload)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["status"], "MISSING_REQUIRED_WATER_QUALITY")
        self.assertFalse(res["operational_use_permitted"])
        self.assertIn("Missing required dissolved oxygen measurement", res["explanation"])

    def test_negative_do_returns_invalid(self):
        """
        Verifies that negative DO is rejected as unphysical.
        """
        payload = {
            "current_feed_amount_kg": 80.0,
            "dissolved_oxygen_mg_l": -1.5
        }
        res = self.advisor.evaluate_advisory(payload)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["status"], "INVALID_PHYSICAL_MEASUREMENT")
        self.assertFalse(res["operational_use_permitted"])
        self.assertIn("cannot be negative", res["explanation"])

    def test_negative_feed_returns_invalid(self):
        """
        Verifies that negative feed amount is rejected as unphysical.
        """
        payload = {
            "current_feed_amount_kg": -25.0,
            "dissolved_oxygen_mg_l": 5.0
        }
        res = self.advisor.evaluate_advisory(payload)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["status"], "INVALID_PHYSICAL_MEASUREMENT")
        self.assertFalse(res["operational_use_permitted"])
        self.assertIn("cannot be negative", res["explanation"])

    def test_missing_feed_and_biomass_returns_explanation(self):
        """
        Verifies that omitting both baseline feed and biomass parameters returns a clear explanation.
        """
        payload = {
            "dissolved_oxygen_mg_l": 5.2,
            "temp_c": 28.0
        }
        res = self.advisor.evaluate_advisory(payload)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["status"], "MISSING_FEEDING_OR_BIOMASS_DATA")
        self.assertFalse(res["operational_use_permitted"])
        self.assertIn("Insufficient feeding or biomass data", res["explanation"])

    def test_do_severe_hypoxia_suppression(self):
        """
        Verifies that DO < 2.0 mg/L triggers 100% feed suppression (cessation).
        """
        payload = {
            "current_feed_amount_kg": 120.0,
            "dissolved_oxygen_mg_l": 1.6,
            "temp_c": 29.0
        }
        res = self.advisor.evaluate_advisory(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["advisory_action"], "CEASE_FEEDING")
        self.assertEqual(res["recommended_feed_kg"], 0.0)
        self.assertEqual(res["reduction_percentage"], 100.0)
        self.assertEqual(res["throttling_factors"]["do_multiplier"], 0.0)
        self.assertIn("Critical Hypoxia", res["advisory_explanations"][0])

    def test_do_moderate_hypoxia_suppression(self):
        """
        Verifies that DO between 2.0 and 3.0 mg/L triggers 50% feed reduction.
        """
        payload = {
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 2.5,
            "temp_c": 28.0
        }
        res = self.advisor.evaluate_advisory(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["advisory_action"], "SUBSTANTIAL_FEED_REDUCTION")
        self.assertEqual(res["recommended_feed_kg"], 50.0)
        self.assertEqual(res["reduction_percentage"], 50.0)
        self.assertEqual(res["throttling_factors"]["do_multiplier"], 0.5)

    def test_do_borderline_hypoxia_suppression(self):
        """
        Verifies that DO between 3.0 and 4.0 mg/L triggers 20% feed reduction.
        """
        payload = {
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 3.4,
            "temp_c": 28.0
        }
        res = self.advisor.evaluate_advisory(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["advisory_action"], "MODERATE_FEED_REDUCTION")
        self.assertEqual(res["recommended_feed_kg"], 80.0)
        self.assertEqual(res["reduction_percentage"], 20.0)
        self.assertEqual(res["throttling_factors"]["do_multiplier"], 0.8)

    def test_ammonia_suppression_when_available(self):
        """
        Verifies that elevated un-ionized NH3 triggers feed reduction even if DO is adequate.
        """
        # Test NH3 >= 0.10 mg/L -> 100% cut
        payload_severe = {
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 5.0,  # DO is good
            "primary_calculated_nh3_mg_l": 0.12  # Severe un-ionized NH3
        }
        res_severe = self.advisor.evaluate_advisory(payload_severe)
        self.assertEqual(res_severe["advisory_action"], "CEASE_FEEDING")
        self.assertEqual(res_severe["recommended_feed_kg"], 0.0)
        self.assertEqual(res_severe["throttling_factors"]["ammonia_multiplier"], 0.0)

        # Test NH3 >= 0.05 mg/L -> 50% cut
        payload_elevated = {
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 5.0,
            "primary_calculated_nh3_mg_l": 0.06
        }
        res_elevated = self.advisor.evaluate_advisory(payload_elevated)
        self.assertEqual(res_elevated["advisory_action"], "SUBSTANTIAL_FEED_REDUCTION")
        self.assertEqual(res_elevated["recommended_feed_kg"], 50.0)
        self.assertEqual(res_elevated["throttling_factors"]["ammonia_multiplier"], 0.5)

    def test_missing_ammonia_handled_gracefully(self):
        """
        Verifies that if ammonia is missing, the advisor notes it was not evaluated
        and still executes the DO throttle safely.
        """
        payload = {
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 4.5
            # No ammonia provided
        }
        res = self.advisor.evaluate_advisory(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["recommended_feed_kg"], 100.0)
        self.assertEqual(res["throttling_factors"]["ammonia_status"], "AMMONIA_DATA_UNAVAILABLE")

    def test_simulated_versus_historical_data_labeling(self):
        """
        CRITICAL RESTRICTION: Simulated data must NEVER be treated as real pond measurements.
        Must set status='SIMULATED_SCENARIO_ONLY', operational_use_permitted=False,
        prefix advisory_action with 'SIMULATED_', and attach demonstration_warning.
        """
        sim_payload = {
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 4.5,
            "data_source": "simulated_iot_model"
        }
        res = self.advisor.evaluate_advisory(sim_payload)
        self.assertTrue(res["is_simulated"])
        self.assertEqual(res["status"], "SIMULATED_SCENARIO_ONLY")
        self.assertFalse(res["operational_use_permitted"])
        self.assertEqual(res["advisory_action"], "SIMULATED_NORMAL_FEEDING")
        self.assertIsNotNone(res["simulation_warning"])
        self.assertIn("SYNTHETIC / SIMULATED DATA WARNING", res["simulation_warning"])
        self.assertIn("NEVER be treated as real-world farm guidance", res["simulation_warning"])
        self.assertIsNotNone(res["demonstration_warning"])
        self.assertIn("SIMULATED SCENARIO ONLY (DEMONSTRATION)", res["demonstration_warning"])
        self.assertIn("MUST NOT be used to guide actual commercial fish feeding", res["demonstration_warning"])

        # Historical / field inspection payload
        field_payload = {
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 4.5,
            "data_source": "field_inspection"
        }
        res_field = self.advisor.evaluate_advisory(field_payload)
        self.assertFalse(res_field["is_simulated"])
        self.assertEqual(res_field["status"], "ADVISORY_GENERATED")
        self.assertTrue(res_field["operational_use_permitted"])
        self.assertEqual(res_field["advisory_action"], "NORMAL_FEEDING")
        self.assertIsNone(res_field["simulation_warning"])
        self.assertIsNone(res_field["demonstration_warning"])

    def test_simulated_inputs_cannot_produce_operational_advisory(self):
        """
        CRITICAL SAFETY REQUIREMENT:
        Simulated data must NEVER produce an operationally permitted advisory.
        Under all simulation flags and water quality conditions, operational_use_permitted
        must remain False, status must be 'SIMULATED_SCENARIO_ONLY', and the action must be prefixed.
        """
        sim_cases = [
            {"current_feed_amount_kg": 100.0, "dissolved_oxygen_mg_l": 5.0, "is_simulated": True},
            {"current_feed_amount_kg": 100.0, "dissolved_oxygen_mg_l": 5.0, "is_simulated": "true"},
            {"current_feed_amount_kg": 100.0, "dissolved_oxygen_mg_l": 2.5, "data_source": "simulated_scenario"},
            {"current_feed_amount_kg": 100.0, "dissolved_oxygen_mg_l": 1.5, "data_source": "synthetic_benchmarking"}
        ]
        for idx, case in enumerate(sim_cases):
            with self.subTest(case_idx=idx):
                res = self.advisor.evaluate_advisory(case)
                self.assertTrue(res["is_valid"])
                self.assertTrue(res["is_simulated"])
                self.assertEqual(res["status"], "SIMULATED_SCENARIO_ONLY")
                self.assertFalse(res["operational_use_permitted"])
                self.assertTrue(res["advisory_action"].startswith("SIMULATED_"))
                self.assertIsNotNone(res["demonstration_warning"])
                self.assertIn("SIMULATED SCENARIO ONLY (DEMONSTRATION)", res["demonstration_warning"])

    def test_tan_test_kit_graduation_wording_and_throttle(self):
        """
        Verifies that TAN >= 2.0 mg/L triggers 50% feed reduction and is explicitly
        described as a test-kit graduation, NEVER as a validated toxicity threshold.
        """
        payload = {
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 5.0,
            "ammonia_tan_nh3_n_mg_l": 2.2
        }
        res = self.advisor.evaluate_advisory(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["advisory_action"], "SUBSTANTIAL_FEED_REDUCTION")
        self.assertEqual(res["recommended_feed_kg"], 50.0)
        self.assertEqual(res["throttling_factors"]["ammonia_multiplier"], 0.5)

        # Check explanation wording
        tan_reasons = [r for r in res["advisory_explanations"] if "Total Ammonia Nitrogen" in r]
        self.assertTrue(len(tan_reasons) > 0)
        self.assertIn("test-kit graduation", tan_reasons[0])
        self.assertNotIn("toxicity threshold", tan_reasons[0].lower())

    def test_provisional_advisory_wording_and_no_causal_recovery_claim(self):
        """
        Verifies that advisory wording states rules are provisional and avoids claiming
        that reducing feed causes water-quality recovery.
        """
        payload = {
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 2.5
        }
        res = self.advisor.evaluate_advisory(payload)
        # Check disclaimer text
        self.assertIn("does not cause water-quality recovery", res["disclaimer"])
        self.assertIn("PROVISIONAL ADVISORY GUIDANCE ONLY", res["warning"])
        self.assertIn("NOT scientifically validated", res["warning"])

    def test_no_automatic_control_actions(self):
        """
        CRITICAL RESTRICTION: Module must NOT execute automatic control actions or control equipment.
        """
        payload = {
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 1.5
        }
        res = self.advisor.evaluate_advisory(payload)
        self.assertFalse(res["is_automatic_control"])
        self.assertIsNone(res["control_action"])

    def test_adaptive_feedback_recording_and_condition_evaluation(self):
        """
        Verifies observational feedback recording, condition change evaluation,
        and governance notices disclaiming causal learning.
        """
        advisory = self.advisor.evaluate_advisory({
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 2.5
        })

        # Case 1: DO improves in next observation
        next_obs_improved = {"dissolved_oxygen_mg_l": 4.2}
        rec1 = self.tracker.record_feedback(
            pond_id="pond_101",
            advisory_record=advisory,
            actual_feed_kg=50.0,
            next_observation=next_obs_improved,
            notes="Followed advisory; reduced morning feed by 50%."
        )
        self.assertEqual(rec1["condition_change"], "improved")
        self.assertEqual(rec1["compliance_delta_kg"], 0.0)
        self.assertTrue(rec1["operational_use_permitted"])
        self.assertIn("OBSERVATIONAL AUDIT RECORD ONLY", rec1["governance_notice"])
        self.assertIn("does NOT perform causal learning", rec1["governance_notice"])

        # Record feedback for simulated advisory to verify operational flag is preserved as False
        sim_adv = self.advisor.evaluate_advisory({
            "current_feed_amount_kg": 100.0,
            "dissolved_oxygen_mg_l": 2.5,
            "is_simulated": True
        })
        self.assertFalse(sim_adv["operational_use_permitted"])
        rec_sim = self.tracker.record_feedback(
            pond_id="pond_sim",
            advisory_record=sim_adv,
            actual_feed_kg=50.0
        )
        self.assertFalse(rec_sim["operational_use_permitted"])

        # Case 2: DO worsens in next observation
        next_obs_worsened = {"dissolved_oxygen_mg_l": 1.8}
        rec2 = self.tracker.record_feedback(
            pond_id="pond_102",
            advisory_record=advisory,
            actual_feed_kg=100.0,  # Ignored advisory
            next_observation=next_obs_worsened,
            notes="Did not reduce feed."
        )
        self.assertEqual(rec2["condition_change"], "worsened")
        self.assertEqual(rec2["compliance_delta_kg"], 50.0)

        # Case 3: Condition unchanged
        next_obs_unchanged = {"dissolved_oxygen_mg_l": 2.6}
        rec3 = self.tracker.record_feedback(
            pond_id="pond_103",
            advisory_record=advisory,
            actual_feed_kg=50.0,
            next_observation=next_obs_unchanged
        )
        self.assertEqual(rec3["condition_change"], "unchanged")

        # Case 4: Pending next observation
        rec4 = self.tracker.record_feedback(
            pond_id="pond_104",
            advisory_record=advisory,
            actual_feed_kg=50.0,
            next_observation=None
        )
        self.assertEqual(rec4["condition_change"], "insufficient_data_pending_next_observation")

        # Verify retrieval and pond filtering
        all_recs = self.tracker.get_records()
        self.assertEqual(len(all_recs), 5)
        p101_recs = self.tracker.get_records("pond_101")
        self.assertEqual(len(p101_recs), 1)
        psim_recs = self.tracker.get_records("pond_sim")
        self.assertEqual(len(psim_recs), 1)

    def test_registry_integration_for_feeding_advisor(self):
        """
        Verifies that feeding advisor and feedback tracker are integrated in ModelRegistry.
        """
        payload = {
            "current_feed_amount_kg": 75.0,
            "dissolved_oxygen_mg_l": 4.8
        }
        res = self.registry.get_feeding_advisory(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["recommended_feed_kg"], 75.0)

        # Feedback through registry
        feedback_res = self.registry.record_feeding_feedback(
            pond_id="pond_alpha",
            advisory_record=res,
            actual_feed_kg=75.0,
            next_observation={"dissolved_oxygen_mg_l": 5.1}
        )
        self.assertEqual(feedback_res["condition_change"], "unchanged")
        records = self.registry.get_feeding_feedback_records("pond_alpha")
        self.assertEqual(len(records), 1)


if __name__ == "__main__":
    unittest.main()

