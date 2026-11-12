"""
Test Suite: Fish Growth Prediction Module - Phase 3
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Verifies Experiment 4 Next-Visit Average Fish Weight persistence baseline,
input validation, zero/negative weight handling, and scientific disclaimers.
"""

import unittest
import numpy as np
import pandas as pd

from app.models.fish_growth import FishGrowthModel
from app.models.registry import get_model_registry


class TestFishGrowthModel(unittest.TestCase):
    """
    Unit test cases for the Fish Growth Persistence Baseline model.
    """

    def setUp(self):
        self.model = FishGrowthModel()
        self.registry = get_model_registry()

    def test_persistence_prediction_accuracy(self):
        """
        Verifies that predicted next-visit average fish weight equals current observed weight.
        """
        test_weights = [15.0, 120.5, 450.0, 980.0, 1500.0]
        for w in test_weights:
            res = self.model.predict({"current_weight_g": w})
            self.assertTrue(res["is_valid"])
            self.assertEqual(res["predicted_next_weight_g"], w)
            self.assertEqual(res["current_weight_g"], w)
            self.assertEqual(res["status"], "OPERATIONAL_PERSISTENCE_BASELINE")

    def test_weight_aliases_supported(self):
        """
        Verifies that common aliases (e.g. 'average_fish_weight_g', 'curr_weight') are resolved.
        """
        aliases = [
            {"average_fish_weight_g": 320.0},
            {"curr_weight": 320.0},
            {"weight_g": 320.0},
            {"current_average_fish_weight_g": 320.0}
        ]
        for payload in aliases:
            res = self.model.predict(payload)
            self.assertTrue(res["is_valid"])
            self.assertEqual(res["predicted_next_weight_g"], 320.0)

    def test_dataframe_input_supported(self):
        """
        Verifies that a single-row pandas DataFrame is supported for inference.
        """
        df = pd.DataFrame([{"current_weight_g": 275.5, "gap_days": 14.0, "species": "Rohu"}])
        res = self.model.predict(df)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["predicted_next_weight_g"], 275.5)
        self.assertEqual(res["context_features"].get("species"), "Rohu")
        self.assertEqual(res["context_features"].get("gap_days"), 14.0)

    def test_zero_weight_raises_value_error(self):
        """
        CRITICAL RESTRICTION: Fish weight must be strictly positive (> 0 g). Zero weight must fail.
        """
        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"current_weight_g": 0.0})
        self.assertIn("strictly positive (> 0 grams)", str(ctx.exception))

    def test_negative_weight_raises_value_error(self):
        """
        CRITICAL RESTRICTION: Negative weight is unphysical and must raise ValueError.
        """
        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"current_weight_g": -50.0})
        self.assertIn("strictly positive (> 0 grams)", str(ctx.exception))

    def test_missing_weight_raises_value_error(self):
        """
        Verifies that omitting weight entirely raises ValueError with informative message.
        """
        with self.assertRaises(ValueError) as ctx:
            self.model.predict({"pond_id": "p_01", "curr_do": 4.5})
        self.assertIn("Missing required fish weight measurement", str(ctx.exception))

    def test_nan_or_invalid_weight_raises_value_error(self):
        """
        Verifies that NaN or non-numeric strings for weight raise ValueError.
        """
        with self.assertRaises(ValueError):
            self.model.predict({"current_weight_g": np.nan})

        with self.assertRaises(ValueError):
            self.model.predict({"current_weight_g": "not_a_number"})

    def test_empty_dataframe_raises_value_error(self):
        """
        Verifies that passing an empty DataFrame raises ValueError.
        """
        with self.assertRaises(ValueError):
            self.model.predict(pd.DataFrame())

    def test_metadata_and_scientific_disclaimers(self):
        """
        Verifies that model metadata explicitly clarifies that this is a next-visit estimate
        and disclaims commercial harvest yield or total biomass prediction.
        """
        meta = self.model.get_metadata()
        self.assertEqual(meta["status"], "OPERATIONAL_PERSISTENCE_BASELINE")
        self.assertTrue(meta["is_operational_baseline"])
        self.assertIn("next_visit_average_fish_weight_g", meta["target_variable"])

        # Verify no claim of total yield prediction
        self.assertIn("NOT total commercial harvest yield", meta["warning"])
        self.assertIn("commercial harvest yield", str(meta["limitations"]).lower())

        # Verify documented Experiment 4 audit metrics
        benches = meta["experiment_4_benchmarks"]
        self.assertEqual(benches["persistence_baseline"]["mae_g"], 93.38)
        self.assertEqual(benches["persistence_baseline"]["rmse_g"], 196.48)
        self.assertEqual(benches["persistence_baseline"]["r2"], 0.7135)
        self.assertEqual(benches["random_forest_exploratory"]["mae_g"], 112.15)
        self.assertEqual(benches["gradient_boosting_exploratory"]["mae_g"], 127.34)

    def test_no_artificial_yield_labels_generated(self):
        """
        Verifies that output dictionary does NOT invent or output commercial harvest yield keys.
        """
        res = self.model.predict({"current_weight_g": 350.0})
        self.assertNotIn("harvest_yield_kg_ha", res)
        self.assertNotIn("total_pond_yield_kg", res)
        self.assertNotIn("commercial_yield_grade", res)

    def test_registry_integration_for_fish_growth(self):
        """
        Verifies that fish growth model is accessible through central ModelRegistry.
        """
        res = self.registry.predict_fish_growth({"current_weight_g": 500.0})
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["predicted_next_weight_g"], 500.0)
        self.assertIn("fish_growth", self.registry.list_models())


if __name__ == "__main__":
    unittest.main()

