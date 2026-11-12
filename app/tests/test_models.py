"""
Unit Tests for Machine Learning Model Wrappers & Central Registry - Phase 2
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Verifies Phase 2 model loading, schema validation, output contracts,
scientific metadata, fault tolerance, and corrected chronological benchmarks.
"""

import unittest
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

from app.config import MODEL_PATHS
from app.models.exp1_soft_sensor import AmmoniaSoftSensorModel
from app.models.exp2_mortality import FishMortalityDiagnosticModel
from app.models.exp3_ammonia_risk import NextVisitAmmoniaRiskModel
from app.models.registry import ModelRegistry, get_model_registry


class TestModelWrappersAndRegistry(unittest.TestCase):
    """
    Verifies Phase 2 model loading, schema validation, output contracts,
    scientific metadata, and fault tolerance.
    """

    def setUp(self):
        self.registry = ModelRegistry()

    def test_all_models_load_successfully(self):
        """Verifies that all approved experiment artifacts load cleanly."""
        health = self.registry.health_check()
        self.assertTrue(health["all_models_loaded"])
        self.assertEqual(health["total_loaded"], 6)
        self.assertEqual(health["total_registered"], 6)

        self.assertTrue(self.registry.exp1_model.is_loaded)
        self.assertTrue(self.registry.exp2_model.is_loaded)
        self.assertTrue(self.registry.exp3_model.is_loaded)
        self.assertTrue(self.registry.do_hypoxia_model.is_loaded)

    def test_missing_model_artifact_handled_gracefully(self):
        """
        Verifies that pointing to a missing artifact does not crash initialization,
        flags is_loaded = False, and raises a clear RuntimeError upon prediction.
        """
        fake_path = Path("non_existent_folder/fake_model.joblib")
        broken_model = AmmoniaSoftSensorModel(model_path=fake_path)

        self.assertFalse(broken_model.is_loaded)
        self.assertIsNotNone(broken_model._load_error)
        self.assertIn("not found", broken_model._load_error)

        with self.assertRaises(RuntimeError) as ctx:
            broken_model.predict({"dissolved_oxygen_mg_l": 4.0, "ph": 8.0, "temp_c": 28.0})
        self.assertIn("is not loaded", str(ctx.exception))

    def test_exp1_soft_sensor_prediction_and_metadata(self):
        """
        Verifies Experiment 1 soft-sensor feature validation, output structure,
        and corrected chronological underprediction findings (0.05, 0.10, 0.20 mg/L).
        """
        features = {
            "dissolved_oxygen_mg_l": 4.5,
            "ph": 8.2,
            "temp_c": 28.5,
            "turbidity_cm": 35.0,
            "tds_ppt": 12.0,
            "Weather": "Clear",
            "water_color": "Greenish",
            "region": "Bapatla"
        }
        res = self.registry.predict_ammonia_soft_sensor(features)

        self.assertIn("estimated_nh3_mg_l", res)
        self.assertIsInstance(res["estimated_nh3_mg_l"], float)
        self.assertGreaterEqual(res["estimated_nh3_mg_l"], 0.0)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["status"], "EXPERIMENTAL_SOFT_SENSOR")

        # Verify corrected spike underprediction warnings
        self.assertIn("underpredicted dangerous acute ammonia spikes", res["warning"])
        self.assertIn("0.05 mg/L", res["warning"])
        self.assertIn("0.10 mg/L", res["warning"])
        self.assertIn("0.20 mg/L", res["warning"])
        # Verify incorrect 2.0 mg/L claim is removed from warning
        self.assertNotIn("> 2.0 mg/L", res["warning"])

        # Verify structured audit metadata
        meta = self.registry.exp1_model.get_metadata()
        audit = meta["chronological_underprediction_audit"]
        self.assertEqual(audit["nh3_ge_0_05_mg_l"]["underprediction_pct"], 79.59)
        self.assertEqual(audit["nh3_ge_0_10_mg_l"]["underprediction_pct"], 100.00)
        self.assertEqual(audit["nh3_ge_0_20_mg_l"]["underprediction_pct"], 100.00)
        self.assertIn("2.0 mg/L is the TAN test-kit graduation, not an NH3 toxicity threshold", audit["note"])
        self.assertIn("Emerson equation", audit["note"])
        self.assertNotIn("sublethal stress", str(meta).lower())
        self.assertNotIn("severe distress", str(meta).lower())
        self.assertNotIn("critical lethal", str(meta).lower())

    def test_exp1_soft_sensor_missing_core_key_raises_error(self):
        """Verifies that omitting a required core feature (e.g. pH) raises ValueError."""
        features = {
            "dissolved_oxygen_mg_l": 4.5,
            # 'ph' is omitted
            "temp_c": 28.5
        }
        with self.assertRaises(ValueError) as ctx:
            self.registry.predict_ammonia_soft_sensor(features)
        self.assertIn("Missing required core input features", str(ctx.exception))
        self.assertIn("ph", str(ctx.exception))

    def test_exp1_soft_sensor_handles_internal_nans(self):
        """Verifies that passing NaN for optional features (turbidity, TDS) does not crash."""
        features = {
            "dissolved_oxygen_mg_l": 4.5,
            "ph": 8.2,
            "temp_c": 28.5,
            "turbidity_cm": np.nan,
            "tds_ppt": np.nan
        }
        res = self.registry.predict_ammonia_soft_sensor(features)
        self.assertTrue(res["is_valid"])
        self.assertIsInstance(res["estimated_nh3_mg_l"], float)

    def test_exp2_mortality_diagnostic_prediction_and_metadata(self):
        """
        Verifies Experiment 2 mortality diagnostic probability score, status,
        and corrected chronological holdout benchmark metrics.
        """
        features = {
            "dissolved_oxygen_mg_l": 2.1,  # low DO
            "ph": 7.4,
            "temp_c": 29.0,
            "turbidity_cm": 25.0,
            "tds_ppt": 8.0,
            "primary_calculated_nh3_mg_l": 0.08,
            "Weather": "Cloudy",
            "water_color": "Brownish",
            "region": "Nellore"
        }
        res = self.registry.predict_mortality_diagnostic(features)

        self.assertIn("mortality_risk_score", res)
        self.assertIsInstance(res["mortality_risk_score"], float)
        self.assertGreaterEqual(res["mortality_risk_score"], 0.0)
        self.assertLessEqual(res["mortality_risk_score"], 1.0)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["status"], "ADVISORY_DIAGNOSTIC_ONLY")
        self.assertIn("extreme natural class imbalance", res["warning"])
        self.assertIn("NOT be used to trigger automated operational mortality alerts", res["warning"])

        # Check documented chronological benchmark metrics
        meta = self.registry.exp2_model.get_metadata()
        bench = meta["chronological_holdout_benchmark"]["logistic_regression"]
        self.assertEqual(bench["roc_auc"], 0.5917)
        self.assertEqual(bench["pr_auc"], 0.0499)
        self.assertEqual(bench["recall"], 0.2045)
        self.assertEqual(bench["precision"], 0.0381)
        self.assertEqual(bench["f1_score"], 0.0643)

        rf_bench = meta["chronological_holdout_benchmark"]["random_forest_tuned"]
        self.assertEqual(rf_bench["roc_auc"], 0.7322)
        self.assertEqual(rf_bench["pr_auc"], 0.0648)
        self.assertEqual(rf_bench["recall"], 0.1364)
        self.assertEqual(rf_bench["precision"], 0.1154)

    def test_exp3_next_visit_ammonia_risk_prediction_and_metadata(self):
        """
        Verifies Experiment 3 next-visit risk prognostic, revisit window,
        multi-week warnings, and chronological benchmark metrics.
        """
        features = {
            "curr_do": 3.8,
            "curr_ph": 8.4,
            "curr_temp": 28.0,
            "curr_nh3": 0.04,
            "gap_days": 14.0,
            "curr_weather": "Clear",
            "curr_color": "Greenish",
            "region": "Bapatla"
        }
        res = self.registry.predict_next_visit_ammonia_risk(features)

        self.assertIn("next_visit_risk_score", res)
        self.assertIsInstance(res["next_visit_risk_score"], float)
        self.assertGreaterEqual(res["next_visit_risk_score"], 0.0)
        self.assertLessEqual(res["next_visit_risk_score"], 1.0)
        self.assertEqual(res["revisit_interval_days"], 14.0)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["status"], "EXPLORATORY_PROGNOSTIC_RISK")
        self.assertIn("NOT an hourly or overnight forecast", res["warning"])
        self.assertIn("3 to 45 days", res["warning"])

        # Check documented chronological benchmark metrics
        meta = self.registry.exp3_model.get_metadata()
        bench = meta["chronological_holdout_benchmark"]["random_forest"]
        self.assertEqual(bench["pr_auc"], 0.0305)
        self.assertEqual(bench["roc_auc"], 0.5061)
        self.assertEqual(bench["recall"], 0.3158)
        self.assertEqual(bench["precision"], 0.0263)
        self.assertEqual(bench["f1_score"], 0.0486)
        self.assertEqual(bench["total_true_positives"], 18)
        self.assertEqual(bench["newly_developed_spikes_detected"], "15 / 54 (27.8%)")
        self.assertIn("18 total true positives", bench["detection_distinction"])
        self.assertIn("15 of 54 newly developed spikes", bench["detection_distinction"])
        self.assertEqual(meta["chronological_holdout_benchmark"]["no_skill_baseline_pr_auc"], 0.0280)

    def test_exp3_alias_resolution(self):
        """Verifies that Exp 3 resolves common aliases (e.g. 'dissolved_oxygen_mg_l' -> 'curr_do')."""
        features_aliased = {
            "dissolved_oxygen_mg_l": 3.8,
            "ph": 8.4,
            "temp_c": 28.0,
            "primary_calculated_nh3_mg_l": 0.04,
            "Weather": "Clear",
            "water_color": "Greenish",
            "region": "Bapatla"
        }
        res = self.registry.predict_next_visit_ammonia_risk(features_aliased)
        self.assertTrue(res["is_valid"])
        self.assertIsInstance(res["next_visit_risk_score"], float)

    def test_registry_partial_failure_tolerance(self):
        """
        Verifies that when one model fails to load, the registry still operates
        cleanly for the other healthy models.
        """
        fake_exp1 = Path("broken_folder/fake_exp1.joblib")
        partial_reg = ModelRegistry(exp1_path=fake_exp1)

        health = partial_reg.health_check()
        self.assertFalse(health["all_models_loaded"])
        self.assertEqual(health["total_loaded"], 5)
        self.assertEqual(health["total_registered"], 6)
        self.assertFalse(health["models"]["exp1_soft_sensor"]["loaded"])
        self.assertTrue(health["models"]["exp2_mortality"]["loaded"])
        self.assertTrue(health["models"]["exp3_ammonia_risk"]["loaded"])
        self.assertTrue(health["models"]["do_hypoxia"]["loaded"])

        # Exp 1 fails
        with self.assertRaises(RuntimeError):
            partial_reg.predict_ammonia_soft_sensor({"dissolved_oxygen_mg_l": 4.0, "ph": 8.0, "temp_c": 28.0})

        # Exp 2 and Exp 3 work perfectly
        res2 = partial_reg.predict_mortality_diagnostic({"dissolved_oxygen_mg_l": 4.0, "ph": 8.0, "temp_c": 28.0})
        self.assertTrue(res2["is_valid"])

        res3 = partial_reg.predict_next_visit_ammonia_risk({"curr_do": 4.0, "curr_ph": 8.0, "curr_temp": 28.0})
        self.assertTrue(res3["is_valid"])

    def test_no_model_retrained_or_modified(self):
        """
        Verifies that running predictions does not alter the serialized joblib
        files on disk.
        """
        model_paths = [
            MODEL_PATHS["exp1_soft_sensor"],
            MODEL_PATHS["exp2_mortality_lr"],
            MODEL_PATHS["exp3_ammonia_risk_rf"],
        ]

        hashes_before = {}
        for p in model_paths:
            with open(p, "rb") as f:
                hashes_before[str(p)] = hashlib.sha256(f.read()).hexdigest()

        # Run multiple predictions
        sample = {"dissolved_oxygen_mg_l": 4.0, "ph": 8.0, "temp_c": 28.0, "gap_days": 10.0}
        self.registry.predict_ammonia_soft_sensor(sample)
        self.registry.predict_mortality_diagnostic(sample)
        self.registry.predict_next_visit_ammonia_risk(sample)

        # Check hashes after
        for p in model_paths:
            with open(p, "rb") as f:
                hash_after = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(hashes_before[str(p)], hash_after, f"Artifact modified: {p}")


if __name__ == "__main__":
    unittest.main()
