"""Unit tests for Phase 5 Stage 2.2:
Page 2 – Water Quality Chemistry & Experimental Toxicity Screening.
"""

import importlib
import py_compile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from app.core.chemistry import (
    calculate_pka,
    calculate_unionized_fraction,
    calculate_nh3_from_tan_n,
    calculate_nh3_from_tan_nh3,
)
from app.models.registry import get_model_registry

page_02_mod = importlib.import_module("app.dashboard.pages.02_Water_Quality_Toxicity")
render_page_2 = page_02_mod.render_page
classify_ammonia_toxicity = page_02_mod.classify_ammonia_toxicity


class TestPage02WaterQualityToxicity(unittest.TestCase):
    """Test Page 2 Chemistry & Toxicity Screening."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.page_path = self.repo_root / "app" / "dashboard" / "pages" / "02_Water_Quality_Toxicity.py"
        self.registry = get_model_registry()

    def test_page_02_compiles(self):
        """Verify Page 2 compiles cleanly without syntax errors."""
        try:
            py_compile.compile(str(self.page_path), doraise=True)
        except py_compile.PyCompileError as exc:
            self.fail(f"Compilation error in Page 2: {exc}")

    def test_page_02_callable(self):
        """Verify render_page is callable."""
        self.assertTrue(callable(render_page_2))

    def test_emerson_chemistry_accuracy_and_basis_distinction(self):
        """Verify Emerson calculation accuracy and difference between TAN-N and TAN-NH3."""
        temp = 28.0
        ph = 7.8
        tan = 0.50

        pka = calculate_pka(temp)
        # Emerson (1975) at 28 C: 0.09018 + 2729.92 / (28 + 273.15) ≈ 9.155
        self.assertAlmostEqual(pka, 9.155, places=2)

        f = calculate_unionized_fraction(ph, temp)
        self.assertGreater(f, 0.0)
        self.assertLess(f, 1.0)

        nh3_from_tan_n = calculate_nh3_from_tan_n(tan, ph, temp, round_digits=None)
        nh3_from_tan_nh3 = calculate_nh3_from_tan_nh3(tan, ph, temp, round_digits=None)

        self.assertFalse(np.isnan(nh3_from_tan_n))
        self.assertFalse(np.isnan(nh3_from_tan_nh3))

        # TAN-N must be greater than TAN-NH3 by exactly the molecular weight ratio 17.031/14.007
        expected_ratio = 17.031 / 14.007
        actual_ratio = nh3_from_tan_n / nh3_from_tan_nh3
        self.assertAlmostEqual(actual_ratio, expected_ratio, places=5)

        # Missing values must return NaN, never 0.0
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(None, ph, temp)))
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(tan, None, temp)))
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(tan, ph, None)))

    def test_ammonia_toxicity_heuristic_classification(self):
        """Verify provisional ammonia tier classifications handle ranges and missing values."""
        self.assertEqual(classify_ammonia_toxicity(None)["tier"], "UNKNOWN")
        self.assertEqual(classify_ammonia_toxicity(np.nan)["tier"], "UNKNOWN")
        self.assertEqual(classify_ammonia_toxicity(0.01)["tier"], "OPTIMAL")
        self.assertEqual(classify_ammonia_toxicity(0.03)["tier"], "CAUTION")
        self.assertEqual(classify_ammonia_toxicity(0.06)["tier"], "ELEVATED")
        self.assertEqual(classify_ammonia_toxicity(0.12)["tier"], "CRITICAL")
        self.assertEqual(classify_ammonia_toxicity(0.25)["tier"], "EXTREME")

    def test_exp1_soft_sensor_integration(self):
        """Verify Experiment 1 soft-sensor returns valid proxy estimate and disclaimers."""
        payload = {
            "dissolved_oxygen_mg_l": 4.5,
            "ph": 7.8,
            "temp_c": 28.0,
            "turbidity_cm": 25.0,
            "tds_ppt": 1.2,
        }
        res = self.registry.predict_ammonia_soft_sensor(payload)
        self.assertTrue(res["is_valid"])
        self.assertIn("estimated_nh3_mg_l", res)
        self.assertIsInstance(res["estimated_nh3_mg_l"], (int, float))
        self.assertIn("warning", res)
        self.assertIn("underpredicted", res["warning"].lower())

    def test_exp2_mortality_diagnostic_integration(self):
        """Verify Experiment 2 mortality diagnostic returns probability score."""
        payload = {
            "dissolved_oxygen_mg_l": 4.5,
            "ph": 7.8,
            "temp_c": 28.0,
            "turbidity_cm": 25.0,
            "tds_ppt": 1.2,
        }
        res = self.registry.predict_mortality_diagnostic(payload)
        self.assertTrue(res["is_valid"])
        self.assertIn("mortality_risk_score", res)
        score = res["mortality_risk_score"]
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertIn("warning", res)

    def test_exp3_ammonia_risk_integration(self):
        """Verify Experiment 3 returns next-visit risk over 3-45 days."""
        payload = {
            "curr_do": 4.5,
            "curr_ph": 7.8,
            "curr_temp": 28.0,
            "curr_turbidity": 25.0,
            "curr_tds": 1.2,
            "gap_days": 21,
        }
        res = self.registry.predict_next_visit_ammonia_risk(payload)
        self.assertTrue(res["is_valid"])
        self.assertIn("next_visit_risk_score", res)
        self.assertEqual(res["revisit_interval_days"], 21)

    def test_page_02_scientific_disclaimers_and_terminology(self):
        """Verify Page 2 text contains mandatory scientific disclaimers and audited holdout numbers."""
        content = self.page_path.read_text(encoding="utf-8")

        # Chemistry & test kit graduation
        self.assertIn("TAN-N (Ammonia-Nitrogen, NH3-N)", content)
        self.assertIn("TAN-NH3 (Molecular Ammonia)", content)
        self.assertIn("17.031 / 14.007", content)
        self.assertIn("2.0 mg/L TAN", content)
        self.assertIn("chemical test-kit graduation mark, NOT a validated biological toxicity threshold", content)

        # Experiment 1 underprediction warnings
        self.assertIn("79.59% underpredicted", content)
        self.assertIn("100.00% underpredicted", content)
        self.assertIn("NEVER be used as an independent safety alarm", content)

        # Experiment 2 low precision warnings
        self.assertIn("1.69%", content)
        self.assertIn("3.81%", content)
        self.assertIn("227 false alarms", content)

        # Experiment 3 multi-week horizon & sensitivity
        self.assertIn("15 of 54 (27.8% sensitivity)", content)
        self.assertIn("3 TO 45 DAYS", content)
        self.assertIn("does NOT provide continuous hourly or overnight forecasts", content)

        # Defensive bounds vs biological limits
        self.assertIn("defensive integrity checks", content)
        self.assertIn("NOT validated biological safety thresholds", content)


if __name__ == "__main__":
    unittest.main()

