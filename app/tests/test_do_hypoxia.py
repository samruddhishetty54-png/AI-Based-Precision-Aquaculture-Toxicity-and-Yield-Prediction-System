"""
Test Suite: Dissolved Oxygen & Hypoxia Module - Phase 4
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Verifies:
- Model initialization, loading, and metadata
- Graceful handling of missing artifacts
- Valid inputs for point regression (Historical Training Mean Baseline)
- Input alias resolution and DataFrame input
- Rejection of invalid, negative, out-of-bounds, NaN, and infinite inputs
- Safe handling of optional missing values
- Strict operational prohibition for simulated inputs (SIMULATED_SCENARIO_ONLY)
- Exploratory classification warnings (FDR 91%, 50% alarm rate, no automated control)
- Rejection of the degenerate severe-hypoxia Random Forest classifier
- Central Model Registry integration and fault isolation
"""

import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from app.models.do_hypoxia import (
    DOHypoxiaModel,
    HISTORICAL_TRAIN_MEAN_DO,
    HISTORICAL_TRAIN_MEAN_DISPLAY,
    FROZEN_HIGH_RECALL_THRESHOLD,
)
from app.models.registry import ModelRegistry, get_model_registry


class TestDOHypoxiaModel(unittest.TestCase):
    """
    Unit test cases for the Experiment 5 DO & Hypoxia Risk module.
    """

    def setUp(self):
        self.model = DOHypoxiaModel()
        self.registry = get_model_registry()

    def test_model_loading_and_metadata(self):
        """
        Verifies default model initialization, operational status,
        and documented Experiment 5 benchmarks.
        """
        self.assertTrue(self.model.is_loaded)
        meta = self.model.get_metadata()
        self.assertEqual(meta["status"], "OPERATIONAL_HISTORICAL_MEAN_POINT_BENCHMARK")
        self.assertTrue(meta["is_operational_baseline"])
        self.assertIn("Historical Training Mean Baseline", meta["primary_point_predictor"])
        self.assertIn("3 to 45 days", meta["prediction_horizon"])
        self.assertIn("NOT an hourly", meta["prediction_horizon"])

        # Check documented regression benchmarks
        reg_benches = meta["experiment_5_benchmarks"]["regression_models"]
        self.assertEqual(reg_benches["historical_mean_baseline"]["mae_mg_l"], 0.3963)
        self.assertEqual(reg_benches["historical_mean_baseline"]["rmse_mg_l"], 0.6450)
        self.assertEqual(reg_benches["persistence_baseline"]["mae_mg_l"], 0.5334)
        self.assertEqual(reg_benches["persistence_baseline"]["r2"], -0.7071)
        self.assertEqual(reg_benches["random_forest_regressor"]["mae_mg_l"], 0.4172)
        self.assertEqual(reg_benches["gradient_boosting_regressor"]["mae_mg_l"], 0.4260)

        # Check documented moderate hypoxia benchmarks
        hyp_bench = meta["experiment_5_benchmarks"]["moderate_hypoxia_classification"]
        self.assertEqual(hyp_bench["test_pr_auc"], 0.0950)
        self.assertEqual(hyp_bench["no_skill_baseline"], 0.0846)
        self.assertEqual(hyp_bench["test_roc_auc"], 0.5328)
        self.assertEqual(hyp_bench["high_recall_threshold_p009"]["false_discovery_rate"], 0.9100)
        self.assertEqual(hyp_bench["high_recall_threshold_p009"]["alarm_rate_pct"], 50.25)

    def test_missing_artifacts_handled_gracefully(self):
        """
        Verifies that pointing to a missing artifact does not crash initialization,
        flags is_loaded = False, records the error, and raises RuntimeError
        only when classifier prediction is strictly requested.
        """
        fake_path = Path("non_existent_folder/fake_gb_classifier.joblib")
        broken_model = DOHypoxiaModel(model_path=fake_path)

        self.assertFalse(broken_model.is_loaded)
        self.assertFalse(broken_model.is_classifier_loaded)
        self.assertIsNotNone(broken_model._load_error)
        self.assertIn("not found", broken_model._load_error)

        # Strict classifier invocation raises RuntimeError
        sample = {"curr_do": 4.5, "curr_ph": 7.8, "curr_temp_c": 28.0}
        with self.assertRaises(RuntimeError) as ctx:
            broken_model.predict_hypoxia_risk(sample)
        self.assertIn("not loaded", str(ctx.exception))

        with self.assertRaises(RuntimeError) as ctx:
            broken_model.predict(sample, require_classifier=True)
        self.assertIn("not loaded", str(ctx.exception))

        # Operational point prediction continues operating cleanly
        point_res = broken_model.predict_point_do(sample)
        self.assertTrue(point_res["is_valid"])
        self.assertEqual(point_res["predicted_next_do_display_mg_l"], 3.50)

    def test_valid_inputs_point_prediction(self):
        """
        Verifies point regression forecast using the Historical Training Mean baseline.
        """
        sample = {
            "curr_do": 4.8,
            "curr_ph": 7.9,
            "curr_temp_c": 28.5,
            "gap_days": 14.0,
            "data_source": "field_inspection"
        }
        res = self.model.predict(sample)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["status"], "OPERATIONAL_HISTORICAL_MEAN_POINT_BENCHMARK")
        self.assertTrue(res["operational_use_permitted"])
        self.assertEqual(res["predicted_next_do_display_mg_l"], HISTORICAL_TRAIN_MEAN_DISPLAY)
        self.assertAlmostEqual(res["predicted_next_do_mg_l"], HISTORICAL_TRAIN_MEAN_DO, places=4)
        self.assertEqual(res["current_do_mg_l"], 4.8)
        self.assertEqual(res["revisit_interval_days"], 14.0)
        self.assertFalse(res["is_automatic_control"])
        self.assertIsNone(res["control_action"])

    def test_input_aliases_supported(self):
        """
        Verifies that common aliases for DO and environmental parameters are resolved.
        """
        aliases = [
            {"curr_do": 4.2},
            {"dissolved_oxygen_mg_l": 4.2},
            {"DO (mg/L)": 4.2},
            {"do_mg_l": 4.2},
            {"DO": 4.2},
            {"current_do": 4.2}
        ]
        for payload in aliases:
            res = self.model.predict(payload)
            self.assertTrue(res["is_valid"])
            self.assertEqual(res["current_do_mg_l"], 4.2)
            self.assertEqual(res["predicted_next_do_display_mg_l"], 3.50)

    def test_dataframe_input_supported(self):
        """
        Verifies that a single-row pandas DataFrame is supported for inference.
        """
        df = pd.DataFrame([{
            "dissolved_oxygen_mg_l": 5.1,
            "ph": 8.1,
            "temp_c": 29.0,
            "gap_days": 21.0,
            "region": "Bapatla"
        }])
        res = self.model.predict(df)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["current_do_mg_l"], 5.1)
        self.assertEqual(res["revisit_interval_days"], 21.0)

    def test_negative_do_raises_value_error(self):
        """
        CRITICAL RESTRICTION: Negative DO is physically impossible and must fail.
        """
        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"curr_do": -1.5})
        self.assertIn("cannot be negative", str(ctx.exception))

        # In safe_mode, returns invalid dictionary
        safe_res = self.model.predict({"curr_do": -1.5}, safe_mode=True)
        self.assertFalse(safe_res["is_valid"])
        self.assertEqual(safe_res["status"], "INVALID_PHYSICAL_MEASUREMENT")
        self.assertFalse(safe_res["operational_use_permitted"])

    def test_excessive_do_raises_value_error(self):
        """
        Verifies that impossibly high DO (> 25.0 mg/L) is rejected.
        """
        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"curr_do": 35.0})
        self.assertIn("saturation bounds", str(ctx.exception))

    def test_nan_and_infinite_do_raise_value_error(self):
        """
        Verifies that NaN or infinite DO values raise ValueError.
        """
        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"curr_do": np.nan})
        self.assertIn("cannot be NaN", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"curr_do": float("inf")})
        self.assertIn("cannot be infinite", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"curr_do": "not_a_number"})
        self.assertIn("Must be a valid numeric quantity", str(ctx.exception))

    def test_missing_do_raises_value_error(self):
        """
        Verifies that omitting DO entirely raises ValueError.
        """
        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"ph": 8.0, "temp_c": 28.0})
        self.assertIn("Missing required core input feature 'curr_do'", str(ctx.exception))

    def test_empty_dataframe_raises_value_error(self):
        """
        Verifies that passing an empty DataFrame raises ValueError.
        """
        with self.assertRaises(ValueError):
            self.model.predict(pd.DataFrame())

    def test_invalid_temperature_and_ph_bounds(self):
        """
        Verifies that physically impossible water temperatures and pH values are rejected.
        """
        # Absolute zero or boiling
        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"curr_do": 4.5, "temp_c": -280.0})
        self.assertIn("physically impossible", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"curr_do": 4.5, "temp_c": 75.0})
        self.assertIn("physically impossible", str(ctx.exception))

        # pH bounds
        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"curr_do": 4.5, "ph": -1.0})
        self.assertIn("Water pH must be within physical range", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"curr_do": 4.5, "ph": 15.5})
        self.assertIn("Water pH must be within physical range", str(ctx.exception))

        # Negative gap days
        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"curr_do": 4.5, "gap_days": -7.0})
        self.assertIn("gap_days must be strictly positive", str(ctx.exception))

    def test_missing_values_handled_safely(self):
        """
        Verifies that optional features (turbidity, TDS, feed, stocking density)
        with NaN values do not cause crashes.
        """
        sample = {
            "curr_do": 4.5,
            "curr_ph": 8.0,
            "curr_temp_c": 28.0,
            "curr_turbidity_cm": np.nan,
            "curr_tds_ppt": np.nan,
            "curr_feed_amount_kg": np.nan,
            "curr_weight": np.nan
        }
        res = self.model.predict(sample)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["predicted_next_do_display_mg_l"], 3.50)

    def test_simulated_inputs_prohibited_from_operational_use(self):
        """
        CRITICAL RESTRICTION: Simulated data must NEVER receive operational permission.
        Must set status='SIMULATED_SCENARIO_ONLY', operational_use_permitted=False,
        and attach demonstration_warning.
        """
        sim_cases = [
            {"curr_do": 4.5, "is_simulated": True},
            {"curr_do": 4.5, "is_simulated": "true"},
            {"curr_do": 4.5, "data_source": "simulated_iot_model"},
            {"curr_do": 4.5, "data_source": "synthetic_benchmark"}
        ]
        for case in sim_cases:
            res = self.model.predict(case)
            self.assertTrue(res["is_valid"])
            self.assertTrue(res["is_simulated"])
            self.assertEqual(res["status"], "SIMULATED_SCENARIO_ONLY")
            self.assertFalse(res["operational_use_permitted"])
            self.assertIsNotNone(res["demonstration_warning"])
            self.assertIn("SIMULATED SCENARIO ONLY (DEMONSTRATION)", res["demonstration_warning"])
            self.assertIn("MUST NOT be used to guide actual commercial pond management", res["demonstration_warning"])

    def test_exploratory_classification_warnings(self):
        """
        Verifies that the exploratory hypoxia screening section contains
        the audited 91% FDR and 50% alarm rate warnings, prohibiting automated alerting.
        """
        res = self.model.predict({"curr_do": 4.0})
        hyp = res["exploratory_hypoxia_screening"]
        self.assertEqual(hyp["status"], "EXPLORATORY_SCREENING_RANKING_ONLY")
        self.assertEqual(hyp["screening_threshold"], FROZEN_HIGH_RECALL_THRESHOLD)
        self.assertEqual(hyp["false_discovery_rate_pct"], 91.00)
        self.assertEqual(hyp["alarm_rate_pct"], 50.25)
        self.assertIn("91.00% False Discovery Rate", hyp["audit_warning"])
        self.assertIn("NEVER be used to trigger automated alarms", hyp["audit_warning"])

    def test_rejected_severe_hypoxia_classifier(self):
        """
        Verifies that the severe-hypoxia (< 2.0 mg/L) Random Forest classifier
        is documented as REJECTED ENTIRELY AS DEGENERATE due to class_weight='balanced'
        probability inflation (99.56% alarm rate).
        """
        res = self.model.predict({"curr_do": 4.0})
        sev = res["rejected_severe_hypoxia_model"]
        self.assertEqual(sev["verdict"], "REJECTED ENTIRELY AS DEGENERATE")
        self.assertEqual(sev["alarm_rate_pct"], 99.56)
        self.assertIn("flagged 99.56% of all test visits", sev["rationale"])
        self.assertIn("class_weight='balanced' probability inflation", sev["rationale"])
        self.assertIn("near-constant positive predictor", sev["rationale"])

    def test_prediction_horizon_disclaimers(self):
        """
        Verifies that prediction horizon is documented as discrete routine visits
        (3 to 45 days) and disclaims hourly or overnight forecasts.
        """
        res = self.model.predict({"curr_do": 4.5, "gap_days": 21.0})
        self.assertIn("3 to 45 days", res["prediction_horizon"])
        self.assertIn("NOT hourly, diurnal, or overnight nadir", res["prediction_horizon"])
        self.assertFalse(res["is_automatic_control"])
        self.assertIsNone(res["control_action"])

    def test_registry_integration_and_domain_method(self):
        """
        Verifies that DO & Hypoxia model is registered in central ModelRegistry
        and accessible through predict_do_hypoxia().
        """
        self.assertIn("do_hypoxia", self.registry.list_models())
        sample = {"curr_do": 4.5, "ph": 8.0, "temp_c": 28.0}
        res = self.registry.predict_do_hypoxia(sample)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["predicted_next_do_display_mg_l"], 3.50)

    def test_registry_fault_isolation_with_broken_do_hypoxia(self):
        """
        Verifies fault isolation: when do_hypoxia points to a missing artifact,
        the registry health check reports it, but other healthy models operate cleanly.
        """
        fake_path = Path("broken_folder/non_existent_exp5.joblib")
        partial_reg = ModelRegistry(do_hypoxia_path=fake_path)

        health = partial_reg.health_check()
        self.assertFalse(health["all_models_loaded"])
        self.assertEqual(health["total_loaded"], 5)
        self.assertEqual(health["total_registered"], 6)
        self.assertFalse(health["models"]["do_hypoxia"]["loaded"])
        self.assertTrue(health["models"]["exp1_soft_sensor"]["loaded"])
        self.assertTrue(health["models"]["exp2_mortality"]["loaded"])
        self.assertTrue(health["models"]["exp3_ammonia_risk"]["loaded"])
        self.assertTrue(health["models"]["fish_growth"]["loaded"])
        self.assertTrue(health["models"]["feeding_advisor"]["loaded"])

        # Other models execute predictions with complete stability
        res_exp1 = partial_reg.predict_ammonia_soft_sensor({"dissolved_oxygen_mg_l": 4.0, "ph": 8.0, "temp_c": 28.0})
        self.assertTrue(res_exp1["is_valid"])

        res_growth = partial_reg.predict_fish_growth({"current_weight_g": 350.0})
        self.assertTrue(res_growth["is_valid"])

        res_feeding = partial_reg.get_feeding_advisory({"current_feed_amount_kg": 100.0, "dissolved_oxygen_mg_l": 4.5})
        self.assertTrue(res_feeding["is_valid"])


if __name__ == "__main__":
    unittest.main()

