"""Unit tests for Phase 5 Stage 2.3:
Page 3 – Next-Visit Morning DO and Hypoxia Screening
Page 4 – Next-Visit Pond-Cohort Fish Weight Benchmark and Provisional Feeding Advisory
"""

import importlib
import py_compile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from app.models.registry import get_model_registry
from app.models.do_hypoxia import (
    HISTORICAL_TRAIN_MEAN_DO,
    HISTORICAL_TRAIN_MEAN_DISPLAY,
    FROZEN_HIGH_RECALL_THRESHOLD,
    FROZEN_MAX_F1_THRESHOLD,
)

# Dynamic import to avoid syntax errors from numeric page prefixes
page_03_mod = importlib.import_module("app.dashboard.pages.03_Next_Visit_DO_Hypoxia")
render_page_3 = page_03_mod.render_page

page_04_mod = importlib.import_module("app.dashboard.pages.04_Growth_Feeding_Advisor")
render_page_4 = page_04_mod.render_page


class TestPage03NextVisitDOHypoxia(unittest.TestCase):
    """Test Page 3: Next-Visit Morning DO & Hypoxia Screening."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.page_path = self.repo_root / "app" / "dashboard" / "pages" / "03_Next_Visit_DO_Hypoxia.py"
        self.registry = get_model_registry()

    def test_page_03_compiles(self):
        """Verify Page 3 compiles cleanly without syntax errors."""
        try:
            py_compile.compile(str(self.page_path), doraise=True)
        except py_compile.PyCompileError as exc:
            self.fail(f"Compilation error in Page 3: {exc}")

    def test_page_03_callable(self):
        """Verify render_page is callable."""
        self.assertTrue(callable(render_page_3))

    def test_page_03_backend_do_hypoxia_integration(self):
        """Verify backend inference returns audited point benchmark and metadata."""
        payload = {
            "curr_do": 4.50,
            "gap_days": 21.0,
            "curr_temp_c": 28.0,
            "curr_ph": 7.80,
            "curr_feed_amount_kg": 25.0,
            "curr_weight": 150.0,
            "is_simulated": False,
        }
        res = self.registry.predict_do_hypoxia(payload)
        self.assertTrue(res["is_valid"])
        self.assertAlmostEqual(res["predicted_next_do_mg_l"], 3.4984, places=3)
        self.assertEqual(res["predicted_next_do_display_mg_l"], 3.50)
        self.assertIn("Historical Training Mean Baseline", res["point_prediction_method"])
        self.assertIn("exploratory_hypoxia_screening", res)
        self.assertIn("rejected_severe_hypoxia_model", res)
        self.assertFalse(res["is_automatic_control"])

    def test_page_03_scientific_disclaimers_and_terminology(self):
        """Verify Page 3 contains all mandatory scientific disclaimers and audited holdout numbers."""
        content = self.page_path.read_text(encoding="utf-8")

        # Historical mean DO benchmark
        self.assertIn("Historical Training Mean Baseline: 3.50 mg/L", content)
        self.assertIn("3.4984 mg/L", content)
        self.assertIn("constant historical benchmark, NOT a dynamic biological prediction", content)
        self.assertIn("0.3963 mg/L", content)  # Historical mean holdout MAE
        self.assertIn("0.5334 mg/L", content)  # Persistence MAE

        # Observation horizon & morning protocol
        self.assertIn("06:00–08:30 AM", content)
        self.assertIn("NOT verified pre-dawn daily minimum DO", content)
        self.assertIn("Zero Real-Time Streaming", content)
        self.assertIn("3 to 45 days", content)

        # Exploratory moderate hypoxia screening & false alarm rate
        self.assertIn("0.090", content)
        self.assertIn("91.00% False Discovery Rate", content)
        self.assertIn("50.25% alarm rate", content)
        self.assertIn("930 false alarms", content)
        self.assertIn("EXPLORATORY ONLY", content)

        # Severe hypoxia classifier rejection
        self.assertIn("REJECTED AS DEGENERATE", content)
        self.assertIn("99.56% of test visits", content)
        self.assertIn("class_weight='balanced'", content)
        self.assertIn("1,934 false alarms", content)

        # Defensive bounds vs biological limits
        self.assertIn("defensive integrity checks", content)
        self.assertIn("NOT validated biological safety thresholds", content)


class TestPage04GrowthFeedingAdvisor(unittest.TestCase):
    """Test Page 4: Fish Weight Benchmark & Feeding Advisory."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.page_path = self.repo_root / "app" / "dashboard" / "pages" / "04_Growth_Feeding_Advisor.py"
        self.registry = get_model_registry()

    def test_page_04_compiles(self):
        """Verify Page 4 compiles cleanly without syntax errors."""
        try:
            py_compile.compile(str(self.page_path), doraise=True)
        except py_compile.PyCompileError as exc:
            self.fail(f"Compilation error in Page 4: {exc}")

    def test_page_04_callable(self):
        """Verify render_page is callable."""
        self.assertTrue(callable(render_page_4))

    def test_page_04_backend_fish_growth_integration(self):
        """Verify backend persistence fish growth baseline."""
        payload = {
            "current_weight_g": 175.5,
            "gap_days": 21.0,
            "curr_do": 4.5,
        }
        res = self.registry.predict_fish_growth(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["predicted_next_weight_g"], 175.5)
        self.assertEqual(res["current_weight_g"], 175.5)
        self.assertIn("Persistence Baseline", res["model_name"])
        self.assertIn("NOT commercial harvest yield", res["prediction_scope"])

    def test_page_04_backend_feeding_advisory_integration(self):
        """Verify provisional rule-based feeding advisory throttles correctly."""
        # 1. Normal conditions: DO >= 4.0 -> 100% feed
        res_normal = self.registry.get_feeding_advisory({
            "dissolved_oxygen_mg_l": 5.0,
            "current_feed_amount_kg": 50.0,
            "temp_c": 28.0,
        })
        self.assertTrue(res_normal["is_valid"])
        self.assertEqual(res_normal["advisory_action"], "NORMAL_FEEDING")
        self.assertEqual(res_normal["recommended_feed_kg"], 50.0)
        self.assertEqual(res_normal["reduction_percentage"], 0.0)

        # 2. Critical Hypoxia: DO < 2.0 -> 100% cut (CEASE_FEEDING)
        res_critical = self.registry.get_feeding_advisory({
            "dissolved_oxygen_mg_l": 1.5,
            "current_feed_amount_kg": 50.0,
            "temp_c": 28.0,
        })
        self.assertTrue(res_critical["is_valid"])
        self.assertEqual(res_critical["advisory_action"], "CEASE_FEEDING")
        self.assertEqual(res_critical["recommended_feed_kg"], 0.0)
        self.assertEqual(res_critical["reduction_percentage"], 100.0)

        # 3. Moderate Hypoxia: 2.0 <= DO < 3.0 -> 50% cut (SUBSTANTIAL_FEED_REDUCTION)
        res_mod = self.registry.get_feeding_advisory({
            "dissolved_oxygen_mg_l": 2.5,
            "current_feed_amount_kg": 50.0,
            "temp_c": 28.0,
        })
        self.assertTrue(res_mod["is_valid"])
        self.assertEqual(res_mod["advisory_action"], "SUBSTANTIAL_FEED_REDUCTION")
        self.assertEqual(res_mod["recommended_feed_kg"], 25.0)
        self.assertEqual(res_mod["reduction_percentage"], 50.0)

    def test_page_04_scientific_disclaimers_and_negative_scope(self):
        """Verify Page 4 source contains all required scientific statements and negative scope."""
        content = self.page_path.read_text(encoding="utf-8")

        # Persistence baseline and MAE
        self.assertIn("Persistence Baseline", content)
        self.assertIn("93.38 g", content)
        self.assertIn("112.15 g", content)  # Random forest inferior MAE
        self.assertIn("127.34 g", content)  # GBDT inferior MAE

        # Target definition & strict negative scope
        self.assertIn("next-visit pond-cohort average fish weight", content)
        self.assertIn("NOT individual fish growth", content)
        self.assertIn("NOT harvest biomass", content)
        self.assertIn("NOT total commercial yield in kg/ha", content)
        self.assertIn("0% total harvest yield labels", content)

        # Provisional feeding heuristics and causality disclaimer
        self.assertIn("Provisional Feeding Recommendation", content)
        self.assertIn("provisional decision-support heuristics requiring human verification", content)
        self.assertIn("do NOT cause immediate water quality recovery", content)
        self.assertIn("2.0 mg/L TAN represents a standard chemical test-kit graduation mark, NOT a validated biological toxicity threshold", content)

        # Observational feedback tracker
        self.assertIn("feedback tracker is strictly an observational audit record", content)
        self.assertIn("NOT execute reinforcement learning", content)


if __name__ == "__main__":
    unittest.main()
