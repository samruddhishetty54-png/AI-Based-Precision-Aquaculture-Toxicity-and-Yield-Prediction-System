"""Unit tests for Phase 5 Dashboard Foundation and Helper Utilities.

Verifies:
1. Formatting and mathematical sanitization helpers.
2. Simulation gating logic and operational use flags.
3. Defensive software boundary checks (distinct from biological safety limits).
4. Model Registry health summary integration.
5. Verification that all 7 dashboard pages exist, compile, and declare approved scientific terminology.
6. Main launcher structure and navigation definitions.
"""

import math
import py_compile
import unittest
from pathlib import Path

from app.dashboard.utils.helpers import (
    format_float,
    format_percentage,
    detect_simulation_source,
    validate_defensive_bounds,
    get_registry_health_summary,
    CATEGORIES,
)
from app.dashboard.utils.styles import PALETTE
from app.models.registry import get_model_registry


class TestDashboardHelpers(unittest.TestCase):
    """Test dashboard helper and formatting routines."""

    def test_format_float(self):
        """Verify float formatting handles normal, edge, and invalid values."""
        self.assertEqual(format_float(3.4984, decimals=2), "3.50")
        self.assertEqual(format_float(3.4984, decimals=4), "3.4984")
        self.assertEqual(format_float(4.5, decimals=1, unit="mg/L"), "4.5 mg/L")
        self.assertEqual(format_float(float("nan")), "N/A")
        self.assertEqual(format_float(float("inf")), "N/A")
        self.assertEqual(format_float(None), "N/A")
        self.assertEqual(format_float("invalid"), "N/A")

    def test_format_percentage(self):
        """Verify percentage formatting handles ratios and invalid values."""
        self.assertEqual(format_percentage(0.5025, decimals=1), "50.2%")
        self.assertEqual(format_percentage(0.9100, decimals=2), "91.00%")
        self.assertEqual(format_percentage(float("nan")), "N/A")
        self.assertEqual(format_percentage(None), "N/A")
        self.assertEqual(format_percentage("invalid"), "N/A")

    def test_detect_simulation_source_field(self):
        """Verify field observations are permitted for operational use."""
        is_sim, tag, permitted = detect_simulation_source("water_quality_cleaned_v2.csv", False)
        self.assertFalse(is_sim)
        self.assertEqual(tag, "FIELD_OBSERVATION")
        self.assertTrue(permitted)

    def test_detect_simulation_source_synthetic(self):
        """Verify synthetic inputs are quarantined and barred from operational use."""
        # By boolean flag
        is_sim, tag, permitted = detect_simulation_source("unknown.csv", is_simulated_flag=True)
        self.assertTrue(is_sim)
        self.assertEqual(tag, "SIMULATED_SCENARIO_ONLY")
        self.assertFalse(permitted)

        # By filename keywords
        for test_source in [
            "iot_water_model_v2.csv",
            "synthetic_readings.csv",
            "simulated_pond_01",
            "benchmark_sim_data",
        ]:
            is_sim, tag, permitted = detect_simulation_source(test_source, False)
            self.assertTrue(is_sim, f"Failed to detect simulation in {test_source}")
            self.assertEqual(tag, "SIMULATED_SCENARIO_ONLY")
            self.assertFalse(permitted)

    def test_validate_defensive_bounds(self):
        """Verify defensive boundary checks catch unphysical entries without raising tracebacks."""
        # Normal inputs within range
        valid, msg = validate_defensive_bounds("do", 4.5)
        self.assertTrue(valid)
        self.assertIsNone(msg)

        valid, msg = validate_defensive_bounds("ph", 7.8)
        self.assertTrue(valid)
        self.assertIsNone(msg)

        # Out-of-bounds inputs
        valid, msg = validate_defensive_bounds("do", -1.0)
        self.assertFalse(valid)
        self.assertIn("below the defensive software bound", msg)

        valid, msg = validate_defensive_bounds("do", 30.0)
        self.assertFalse(valid)
        self.assertIn("exceeds the defensive software bound", msg)

        valid, msg = validate_defensive_bounds("fish_weight", 0.0)
        self.assertFalse(valid)
        self.assertIn("below the defensive software bound", msg)

        # Missing values (NaN) should be handled gracefully
        valid, msg = validate_defensive_bounds("turbidity", float("nan"))
        self.assertTrue(valid)
        self.assertIsNone(msg)

    def test_get_registry_health_summary(self):
        """Verify registry health integration returns valid operational status."""
        registry = get_model_registry()
        summary = get_registry_health_summary(registry)
        self.assertIn(summary["status"], ["HEALTHY", "DEGRADED"])
        self.assertEqual(summary["total_count"], 6)
        self.assertEqual(summary["ready_count"], 6)
        self.assertIn("do_hypoxia", summary["model_health"])
        self.assertIn("fish_growth", summary["model_health"])

    def test_categories_dict(self):
        """Verify the 5 formal scientific categories are defined."""
        expected_keys = {"HISTORICAL", "BENCHMARK", "EXPERIMENTAL", "SIMULATED", "ADVISORY"}
        self.assertEqual(set(CATEGORIES.keys()), expected_keys)
        for key, val in CATEGORIES.items():
            self.assertIn("label", val)
            self.assertIn("description", val)
            self.assertIn("badge_class", val)

    def test_palette_dict(self):
        """Verify the aesthetic palette defines navy and teal accents."""
        self.assertIn("navy_primary", PALETTE)
        self.assertIn("teal_primary", PALETTE)
        self.assertEqual(PALETTE["navy_primary"], "#0c2340")
        self.assertEqual(PALETTE["teal_primary"], "#0d5c75")


class TestDashboardStructureAndPages(unittest.TestCase):
    """Test dashboard directory layout, file compilation, and scientific content."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.pages_dir = self.repo_root / "app" / "dashboard" / "pages"
        self.expected_pages = [
            "01_Overview.py",
            "02_Water_Quality_Toxicity.py",
            "03_Next_Visit_DO_Hypoxia.py",
            "04_Growth_Feeding_Advisor.py",
            "05_Historical_Data_Explorer.py",
            "06_Simulation_Sandbox.py",
            "07_Model_Registry_Governance.py",
        ]

    def test_all_seven_pages_exist(self):
        """Verify all 7 dashboard page files exist."""
        for page_name in self.expected_pages:
            page_path = self.pages_dir / page_name
            self.assertTrue(page_path.exists(), f"Missing page file: {page_name}")

    def test_all_seven_pages_compile(self):
        """Verify all 7 dashboard pages compile with zero syntax errors."""
        for page_name in self.expected_pages:
            page_path = self.pages_dir / page_name
            try:
                py_compile.compile(str(page_path), doraise=True)
            except py_compile.PyCompileError as exc:
                self.fail(f"Syntax error compiling {page_name}: {exc}")

    def test_page_03_scientific_wording(self):
        """Verify Page 3 enforces DO benchmarks and disclaims real-time / overnight claims."""
        page_path = self.pages_dir / "03_Next_Visit_DO_Hypoxia.py"
        content = page_path.read_text(encoding="utf-8")

        self.assertIn("Next-Visit Morning DO and Hypoxia Screening", content)
        self.assertIn("3.4984 mg/L", content)
        self.assertIn("constant historical", content)
        self.assertIn("06:00–08:30 AM", content)
        self.assertIn("3–45 days", content)
        self.assertIn("NOT verified pre-dawn daily minimum DO", content)
        self.assertIn("91.00% False Discovery Rate", content)
        self.assertIn("REJECTED AS DEGENERATE", content)

    def test_page_04_target_definition_wording(self):
        """Verify Page 4 defines target as next-visit pond-cohort average fish weight."""
        page_path = self.pages_dir / "04_Growth_Feeding_Advisor.py"
        content = page_path.read_text(encoding="utf-8")

        self.assertIn("next-visit pond-cohort average fish weight", content)
        self.assertIn("NOT individual fish growth", content)
        self.assertIn("NOT harvest biomass", content)
        self.assertIn("NOT total commercial yield in kg/ha", content)
        self.assertIn("93.38 g", content)
        self.assertIn("provisional decision-support heuristics requiring human verification", content)
        self.assertIn("test-kit graduation", content)

    def test_page_06_simulation_gating(self):
        """Verify Page 6 enforces simulation isolation and prohibits operational use."""
        page_path = self.pages_dir / "06_Simulation_Sandbox.py"
        content = page_path.read_text(encoding="utf-8")

        self.assertIn("SIMULATED_SCENARIO_ONLY", content)
        self.assertIn("operational_use_permitted = False", content)
        self.assertIn("PROHIBITED", content)

    def test_dashboard_launcher_exists_and_compiles(self):
        """Verify main launcher dashboard.py exists, compiles, and routes all 7 pages."""
        launcher_path = self.repo_root / "dashboard.py"
        self.assertTrue(launcher_path.exists())
        py_compile.compile(str(launcher_path), doraise=True)

        content = launcher_path.read_text(encoding="utf-8")
        for page_name in self.expected_pages:
            self.assertIn(page_name, content, f"Launcher does not register {page_name}")
        self.assertIn("is_automatic_control = False", content)


if __name__ == "__main__":
    unittest.main()

