"""Unit tests for Phase 5 Stage 2.4:
Page 1 – Pond Monitoring Overview & Model Status
Page 6 – Simulated Scenarios Sandbox (Non-Operational)
"""

import importlib
import py_compile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from app.core.data_manager import load_dataset
from app.models.registry import get_model_registry

# Dynamic import to avoid syntax errors from numeric page prefixes
page_01_mod = importlib.import_module("app.dashboard.pages.01_Overview")
render_page_1 = page_01_mod.render_page
classify_pond_priority = page_01_mod.classify_pond_priority

page_06_mod = importlib.import_module("app.dashboard.pages.06_Simulation_Sandbox")
render_page_6 = page_06_mod.render_page


class TestPage01Overview(unittest.TestCase):
    """Test Page 1: Pond Monitoring Overview & Model Status."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.page_path = self.repo_root / "app" / "dashboard" / "pages" / "01_Overview.py"
        self.registry = get_model_registry()

    def test_page_01_compiles(self):
        """Verify Page 1 compiles cleanly without syntax errors."""
        try:
            py_compile.compile(str(self.page_path), doraise=True)
        except py_compile.PyCompileError as exc:
            self.fail(f"Compilation error in Page 1: {exc}")

    def test_page_01_callable(self):
        """Verify render_page is callable."""
        self.assertTrue(callable(render_page_1))

    def test_page_01_data_loading_and_priority_queue(self):
        """Verify historical datasets load and priority queue logic functions correctly."""
        df_tox = load_dataset("toxicity_analysis")
        self.assertFalse(df_tox.empty)
        self.assertIn("pond_id", df_tox.columns)
        self.assertIn("dissolved_oxygen_mg_l", df_tox.columns)

        # Priority 1: Hypoxia
        row_hypoxia = pd.Series({"dissolved_oxygen_mg_l": 2.2, "primary_calculated_nh3_mg_l": 0.01})
        self.assertIn("Priority 1: Hypoxia", classify_pond_priority(row_hypoxia))

        # Priority 1: Ammonia Toxicity
        row_nh3 = pd.Series({"dissolved_oxygen_mg_l": 5.0, "primary_calculated_nh3_mg_l": 0.08})
        self.assertIn("Priority 1: Ammonia", classify_pond_priority(row_nh3))

        # Priority 2: Suboptimal DO
        row_subopt = pd.Series({"dissolved_oxygen_mg_l": 3.4, "primary_calculated_nh3_mg_l": 0.01})
        self.assertIn("Priority 2: Suboptimal", classify_pond_priority(row_subopt))

        # Priority 3: Routine
        row_routine = pd.Series({"dissolved_oxygen_mg_l": 5.2, "primary_calculated_nh3_mg_l": 0.01})
        self.assertIn("Priority 3: Routine", classify_pond_priority(row_routine))

    def test_page_01_scientific_disclaimers_and_real_time_prohibitions(self):
        """Verify Page 1 contains all required disclaimers and governance limits."""
        content = self.page_path.read_text(encoding="utf-8")

        # Historical nature & observation protocol
        self.assertIn("Historical observations aggregated from commercial pond inspection logs", content)
        self.assertIn("06:00–08:30 AM", content)
        self.assertIn("3 to 45 days", content)
        self.assertIn("NOT live or continuous streaming telemetry", content)
        self.assertIn("No Real-Time Monitoring", content)

        # Model Registry Status & Governance
        self.assertIn("Central Model Registry Health & Governance", content)
        self.assertIn("read-only", content)

        # Negative scope: Somatic weight, not harvest yield
        self.assertIn("NOT harvest yield", content)
        self.assertIn("0% total yield labels", content)

        # Zero automated actuation
        self.assertIn("is_automatic_control = False", content)


class TestPage06SimulationSandbox(unittest.TestCase):
    """Test Page 6: Simulated Scenarios Sandbox (Non-Operational)."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.page_path = self.repo_root / "app" / "dashboard" / "pages" / "06_Simulation_Sandbox.py"
        self.registry = get_model_registry()

    def test_page_06_compiles(self):
        """Verify Page 6 compiles cleanly without syntax errors."""
        try:
            py_compile.compile(str(self.page_path), doraise=True)
        except py_compile.PyCompileError as exc:
            self.fail(f"Compilation error in Page 6: {exc}")

    def test_page_06_callable(self):
        """Verify render_page is callable."""
        self.assertTrue(callable(render_page_6))

    def test_page_06_iot_dataset_metadata_and_loading(self):
        """Verify iot_water_model dataset is recognized as synthetic simulation."""
        df_iot = load_dataset("iot_water_model")
        self.assertFalse(df_iot.empty)
        self.assertTrue(df_iot.attrs.get("is_simulation", False))
        self.assertIn("MATHEMATICAL SIMULATION", df_iot.attrs["metadata"]["scientific_nature"])

    def test_page_06_backend_simulation_gating(self):
        """Verify that simulation inputs trigger strict operational prohibition."""
        # 1. Feeding Advisor in simulation mode
        feed_payload = {
            "dissolved_oxygen_mg_l": 1.5,
            "temp_c": 30.0,
            "current_feed_amount_kg": 50.0,
            "is_simulated": True,
            "data_source": "benchmark_simulation",
        }
        res_feed = self.registry.get_feeding_advisory(feed_payload)
        self.assertTrue(res_feed["is_valid"])
        self.assertEqual(res_feed["status"], "SIMULATED_SCENARIO_ONLY")
        self.assertFalse(res_feed["operational_use_permitted"])
        self.assertIn("SIMULATED_", res_feed["advisory_action"])

        # 2. DO Hypoxia in simulation mode
        do_payload = {
            "curr_do": 2.0,
            "gap_days": 21.0,
            "is_simulated": True,
            "data_source": "benchmark_simulation",
        }
        res_do = self.registry.predict_do_hypoxia(do_payload)
        self.assertTrue(res_do["is_valid"])
        self.assertEqual(res_do["status"], "SIMULATED_SCENARIO_ONLY")
        self.assertFalse(res_do["operational_use_permitted"])

    def test_page_06_mandatory_simulation_warnings_in_source(self):
        """Verify Page 6 source contains all required simulation warnings and gating tags."""
        content = self.page_path.read_text(encoding="utf-8")

        self.assertIn("SIMULATED_SCENARIO_ONLY", content)
        self.assertIn("operational_use_permitted = False", content)
        self.assertIn("PROHIBITED", content)
        self.assertIn("iot_water_model_v2.csv", content)
        self.assertIn("mathematical simulation benchmark model, NOT live physical IoT telemetry", content)
        self.assertIn("is_automatic_control = False", content)
        self.assertIn("Strict Isolation & Data Protection Boundary", content)


if __name__ == "__main__":
    unittest.main()
