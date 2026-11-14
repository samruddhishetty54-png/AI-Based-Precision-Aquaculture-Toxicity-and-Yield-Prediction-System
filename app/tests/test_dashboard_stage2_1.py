"""Unit tests for Phase 5 Stage 2.1 Dashboard Pages:
- Page 7: Model Registry Governance & Audit Benchmark Catalog
- Page 5: Historical Field Observations Explorer
"""

import importlib
import py_compile
import unittest
from pathlib import Path
import pandas as pd

# Dynamic import of pages starting with numbers
page_07_mod = importlib.import_module("app.dashboard.pages.07_Model_Registry_Governance")
page_05_mod = importlib.import_module("app.dashboard.pages.05_Historical_Data_Explorer")

render_page_7 = page_07_mod.render_page
AUDITED_DATASET_HASHES = page_07_mod.AUDITED_DATASET_HASHES
AUDITED_MODEL_HASHES = page_07_mod.AUDITED_MODEL_HASHES
_compute_sha256 = page_07_mod._compute_sha256

render_page_5 = page_05_mod.render_page
AVAILABLE_DATASETS = page_05_mod.AVAILABLE_DATASETS
_render_missingness_summary = page_05_mod._render_missingness_summary
_render_trajectory_chart = page_05_mod._render_trajectory_chart

from app.core.data_manager import load_dataset


class TestPage07Governance(unittest.TestCase):
    """Test Page 7 Governance & Benchmark Catalog."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.page_path = self.repo_root / "app" / "dashboard" / "pages" / "07_Model_Registry_Governance.py"

    def test_page_07_compiles(self):
        """Verify Page 7 compiles cleanly."""
        try:
            py_compile.compile(str(self.page_path), doraise=True)
        except py_compile.PyCompileError as exc:
            self.fail(f"Compilation error in Page 7: {exc}")

    def test_page_07_callable(self):
        """Verify render_page is callable."""
        self.assertTrue(callable(render_page_7))

    def test_audited_dataset_hashes_integrity(self):
        """Verify that all 10 datasets in AUDITED_DATASET_HASHES match disk exactly."""
        self.assertEqual(len(AUDITED_DATASET_HASHES), 10)
        for rel_path, expected_h in AUDITED_DATASET_HASHES.items():
            full_p = self.repo_root / rel_path
            self.assertTrue(full_p.exists(), f"Dataset file missing: {rel_path}")
            actual_h = _compute_sha256(full_p)
            self.assertEqual(actual_h, expected_h, f"Hash mismatch for {rel_path}")

    def test_audited_model_hashes_integrity(self):
        """Verify that all 9 models in AUDITED_MODEL_HASHES match disk exactly."""
        self.assertEqual(len(AUDITED_MODEL_HASHES), 9)
        for rel_path, expected_h in AUDITED_MODEL_HASHES.items():
            full_p = self.repo_root / rel_path
            self.assertTrue(full_p.exists(), f"Model file missing: {rel_path}")
            actual_h = _compute_sha256(full_p)
            self.assertEqual(actual_h, expected_h, f"Hash mismatch for {rel_path}")

    def test_page_07_scientific_terminology_and_benchmarks(self):
        """Verify that Page 7 text contains exact audited benchmarks and disclaimers."""
        content = self.page_path.read_text(encoding="utf-8")

        # Guardrails & limitations
        self.assertIn("is_automatic_control = False", content)
        self.assertIn("3 to 45 days interval", content)
        self.assertIn("morning DO observations (06:00–08:30 AM)", content)
        self.assertIn("NOT verified pre-dawn daily minimum DO", content)
        self.assertIn("next-visit pond-cohort average fish weight (grams/fish)", content)
        self.assertIn("NOT individual fish growth", content)
        self.assertIn("NOT harvest biomass", content)
        self.assertIn("NOT total commercial harvest yield in kg/ha", content)
        self.assertIn("TAN 2.0 mg/L", content)
        self.assertIn("test-kit graduation", content)

        # Experiment benchmarks
        self.assertIn("0.0528 mg/L", content)  # Exp 1 MAE
        self.assertIn("79.59%", content)       # Exp 1 underprediction
        self.assertIn("0.5917", content)       # Exp 2 ROC-AUC
        self.assertIn("3.81%", content)        # Exp 2 Precision
        self.assertIn("227 False Positives", content)
        self.assertIn("15 of 54 (27.8% Sensitivity)", content)  # Exp 3
        self.assertIn("93.38 g", content)      # Exp 4 MAE
        self.assertIn("3.4984 mg/L", content)  # Exp 5 Hist Mean DO
        self.assertIn("0.3963 mg/L", content)  # Exp 5 MAE
        self.assertIn("91.00%", content)       # Exp 5 GBDT FDR
        self.assertIn("REJECTED AS DEGENERATE", content)  # Exp 5 Severe RF

        # Chemistry formulas
        self.assertIn("0.09018", content)
        self.assertIn("2729.92", content)
        self.assertIn("17.031", content)
        self.assertIn("14.007", content)


class TestPage05HistoricalExplorer(unittest.TestCase):
    """Test Page 5 Historical Field Observations Explorer."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.page_path = self.repo_root / "app" / "dashboard" / "pages" / "05_Historical_Data_Explorer.py"

    def test_page_05_compiles(self):
        """Verify Page 5 compiles cleanly."""
        try:
            py_compile.compile(str(self.page_path), doraise=True)
        except py_compile.PyCompileError as exc:
            self.fail(f"Compilation error in Page 5: {exc}")

    def test_page_05_callable(self):
        """Verify render_page is callable."""
        self.assertTrue(callable(render_page_5))

    def test_available_datasets_keys(self):
        """Verify all 6 field datasets are registered in AVAILABLE_DATASETS."""
        expected_keys = {
            "water_quality",
            "toxicity_analysis",
            "fish_health_growth",
            "feeding_analysis",
            "enrolled_ponds",
            "dropouts",
        }
        self.assertEqual(set(AVAILABLE_DATASETS.keys()), expected_keys)

    def test_load_all_available_datasets(self):
        """Verify that each registered dataset can be loaded via data manager."""
        for key in AVAILABLE_DATASETS.keys():
            df = load_dataset(key, use_cache=True)
            self.assertIsInstance(df, pd.DataFrame)
            self.assertFalse(df.empty, f"Dataset '{key}' is unexpectedly empty.")
            self.assertFalse(df.attrs.get("is_simulation", False), f"Dataset '{key}' flagged as simulation.")

    def test_page_05_scientific_terminology(self):
        """Verify Page 5 enforces sampling context and disclaimers."""
        content = self.page_path.read_text(encoding="utf-8")

        self.assertIn("3 to 45 days", content)
        self.assertIn("06:00–08:30 AM", content)
        self.assertIn("NOT verified pre-dawn daily minimum DO", content)
        self.assertIn("NaNs) are strictly preserved", content)
        self.assertIn("Pond-cohort average", content)
        self.assertIn("does not represent total biomass or harvest yield (kg/ha)", content)
        self.assertIn("segregated from synthetic simulation models", content)


if __name__ == "__main__":
    unittest.main()
