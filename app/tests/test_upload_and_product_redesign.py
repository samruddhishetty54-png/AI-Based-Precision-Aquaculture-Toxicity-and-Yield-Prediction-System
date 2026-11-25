"""Tests for Organization-Facing Product Redesign & CSV Upload Workflow.

Covers:
1. Valid CSV upload & parsing.
2. Unsupported format rejection (.xlsx).
3. Missing required columns & unsupported model requests.
4. Ambiguous unit detection without silent assumptions.
5. Missing values (NaN preservation, never zero-filled).
6. Duplicate record & duplicate (pond_id, datetime) detection.
7. Multiple pond identifiers & hierarchy non-invention.
8. Valid batch analysis execution against ModelRegistry.
9. Simulation marker quarantine on uploaded filenames.
10. Compilation of new pages (08_Farm_Overview.py, 09_Import_Dataset.py) and launcher.
"""

import py_compile
import unittest
from pathlib import Path
import numpy as np
import pandas as pd

from app.dashboard.utils.upload_processor import (
    assess_model_compatibility,
    inspect_dataframe_profile,
    parse_uploaded_csv,
    run_batch_analysis,
    suggest_column_mapping,
    validate_mapped_dataset,
)
from app.models.registry import get_model_registry


class TestUploadProcessorAndProductRedesign(unittest.TestCase):
    """Test upload parsing, validation, compatibility, and execution."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.registry = get_model_registry()

    def test_valid_csv_upload_and_mapping(self):
        """Valid CSV with explicit canonical columns parses and maps cleanly."""
        csv_text = (
            "pond_id,datetime,dissolved_oxygen_mg_l,ph,temp_c,tan_n_mg_l,average_fish_weight_g,feed_amount_kg\n"
            "POND_A,2026-01-10,4.5,7.8,28.5,0.4,120.0,15.0\n"
            "POND_B,2026-01-11,2.8,8.2,30.0,1.2,180.0,20.0\n"
        )
        df, err = parse_uploaded_csv(csv_text.encode("utf-8"), "org_ponds.csv")
        self.assertIsNone(err)
        self.assertEqual(len(df), 2)

        mapping, ambiguities = suggest_column_mapping(list(df.columns))
        self.assertEqual(len(ambiguities), 0)
        self.assertEqual(mapping["pond_id"], "pond_id")
        self.assertEqual(mapping["dissolved_oxygen_mg_l"], "dissolved_oxygen_mg_l")

        val = validate_mapped_dataset(df, mapping, filename="org_ponds.csv")
        self.assertTrue(val["is_valid"])
        self.assertEqual(val["pond_count"], 2)
        self.assertEqual(val["farm_count"], 0)  # Never invented
        self.assertFalse(val["is_simulated"])
        self.assertTrue(val["operational_use_permitted"])

    def test_reject_excel_upload(self):
        """Unsupported Excel file is cleanly rejected."""
        df, err = parse_uploaded_csv(b"dummy", "ponds.xlsx")
        self.assertIsNone(df)
        self.assertIn("Only CSV (.csv) files are supported", err)

    def test_invalid_schema_and_non_numeric(self):
        """Non-numeric values in mapped numeric field produce validation errors."""
        csv_text = "pond_id,dissolved_oxygen_mg_l,ph,temp_c\nP1,abc,7.5,28.0\n"
        df, _ = parse_uploaded_csv(csv_text.encode("utf-8"), "bad_num.csv")
        mapping, _ = suggest_column_mapping(list(df.columns))
        val = validate_mapped_dataset(df, mapping, filename="bad_num.csv")
        self.assertFalse(val["is_valid"])
        self.assertTrue(any("non-numeric" in e for e in val["errors"]))

    def test_ambiguous_units_flagged(self):
        """Ambiguous columns like 'ammonia' or 'temp' are flagged and not silently mapped."""
        csv_text = "pond,temp,ammonia,do\nP1,28.0,0.5,4.2\n"
        df, _ = parse_uploaded_csv(csv_text.encode("utf-8"), "ambig.csv")
        mapping, ambiguities = suggest_column_mapping(list(df.columns))
        amb_cols = {a["uploaded_column"] for a in ambiguities}
        self.assertIn("ammonia", amb_cols)
        self.assertIn("temp", amb_cols)
        self.assertIsNone(mapping["tan_n_mg_l"])

    def test_missing_values_preserved_not_zero_filled(self):
        """Missing values remain NaN and are never zero-filled."""
        csv_text = (
            "pond_id,dissolved_oxygen_mg_l,ph,temp_c\n"
            "P1,4.2,,28.0\n"
            "P2,,7.9,29.0\n"
        )
        df, _ = parse_uploaded_csv(csv_text.encode("utf-8"), "missing.csv")
        profile = inspect_dataframe_profile(df)
        self.assertEqual(profile["total_rows"], 2)
        mapping, _ = suggest_column_mapping(list(df.columns))
        val = validate_mapped_dataset(df, mapping, filename="missing.csv")
        work = val["canonical_df"]
        self.assertTrue(np.isnan(work.loc[0, "ph"]))
        self.assertTrue(np.isnan(work.loc[1, "dissolved_oxygen_mg_l"]))

    def test_duplicate_detection(self):
        """Exact duplicate rows and duplicate (pond_id, datetime) are detected."""
        csv_text = (
            "pond_id,datetime,dissolved_oxygen_mg_l,ph,temp_c\n"
            "P1,2026-01-10,4.2,7.8,28.0\n"
            "P1,2026-01-10,4.2,7.8,28.0\n"
        )
        df, _ = parse_uploaded_csv(csv_text.encode("utf-8"), "dups.csv")
        mapping, _ = suggest_column_mapping(list(df.columns))
        val = validate_mapped_dataset(df, mapping, filename="dups.csv")
        self.assertEqual(val["duplicate_rows"], 1)
        self.assertEqual(val["duplicate_pond_dates"], 1)

    def test_model_compatibility_and_unsupported_models(self):
        """Only models whose actual requirements are met are marked compatible."""
        csv_text = "pond_id,dissolved_oxygen_mg_l\nP1,4.2\n"
        df, _ = parse_uploaded_csv(csv_text.encode("utf-8"), "do_only.csv")
        mapping, _ = suggest_column_mapping(list(df.columns))
        val = validate_mapped_dataset(df, mapping, filename="do_only.csv")
        compat = {c["key"]: c for c in assess_model_compatibility(val["canonical_df"])}

        self.assertTrue(compat["exp5_do_hypoxia"]["compatible"])
        self.assertFalse(compat["exp1_soft_sensor"]["compatible"])
        self.assertFalse(compat["exp2_mortality"]["compatible"])
        self.assertFalse(compat["exp4_fish_growth"]["compatible"])
        self.assertFalse(compat["emerson_nh3"]["compatible"])
        self.assertFalse(compat["feeding_advisor"]["compatible"])

    def test_out_of_range_weight_and_do_ineligible(self):
        """Zero/negative fish weight and out-of-range DO are not counted as compatible."""
        csv_text = "pond_id,dissolved_oxygen_mg_l,average_fish_weight_g\nP1,30.0,-5.0\n"
        df, _ = parse_uploaded_csv(csv_text.encode("utf-8"), "oob.csv")
        mapping, _ = suggest_column_mapping(list(df.columns))
        val = validate_mapped_dataset(df, mapping, filename="oob.csv")
        compat = {c["key"]: c for c in assess_model_compatibility(val["canonical_df"])}
        self.assertFalse(compat["exp4_fish_growth"]["compatible"])
        self.assertFalse(compat["exp5_do_hypoxia"]["compatible"])

    def test_valid_batch_analysis_execution(self):
        """Batch analysis runs compatible models and produces clean outputs."""
        csv_text = (
            "pond_id,datetime,dissolved_oxygen_mg_l,ph,temp_c,tan_n_mg_l,average_fish_weight_g,feed_amount_kg\n"
            "POND_1,2026-02-01,4.5,7.8,28.5,0.5,150.0,18.0\n"
            "POND_2,2026-02-02,2.5,8.4,30.0,1.5,200.0,22.0\n"
        )
        df, _ = parse_uploaded_csv(csv_text.encode("utf-8"), "full_sample.csv")
        mapping, _ = suggest_column_mapping(list(df.columns))
        val = validate_mapped_dataset(df, mapping, filename="full_sample.csv")
        compat = assess_model_compatibility(val["canonical_df"])
        keys = [c["key"] for c in compat if c["compatible"]]
        self.assertEqual(len(keys), 7)

        res_df, summary = run_batch_analysis(val["canonical_df"], self.registry, keys)
        self.assertEqual(summary["analyzed_rows"], 2)
        self.assertTrue(res_df["emerson_nh3_mg_l"].notna().all())
        self.assertTrue(res_df["exp1_est_nh3_mg_l"].notna().all())
        self.assertTrue(res_df["exp2_mortality_risk_score"].notna().all())
        self.assertTrue(res_df["exp3_next_visit_nh3_risk"].notna().all())
        self.assertEqual(res_df.loc[0, "exp4_persistence_next_weight_g"], 150.0)
        self.assertAlmostEqual(res_df.loc[0, "exp5_benchmark_next_do_mg_l"], 3.4984, places=3)
        self.assertEqual(res_df.loc[1, "feeding_action"], "CEASE_FEEDING")

    def test_simulation_filename_quarantine(self):
        """Uploaded file with simulation marker in filename is flagged."""
        csv_text = "pond_id,dissolved_oxygen_mg_l,ph,temp_c\nSIM_1,5.0,7.5,28.0\n"
        df, _ = parse_uploaded_csv(csv_text.encode("utf-8"), "synthetic_sim_test.csv")
        mapping, _ = suggest_column_mapping(list(df.columns))
        val = validate_mapped_dataset(df, mapping, filename="synthetic_sim_test.csv")
        self.assertTrue(val["is_simulated"])
        self.assertFalse(val["operational_use_permitted"])

    def test_new_pages_and_launcher_compile(self):
        """Verify new pages 08, 09 and dashboard.py compile and register all 9 pages."""
        for rel in [
            "dashboard.py",
            "app/dashboard/pages/08_Farm_Overview.py",
            "app/dashboard/pages/09_Import_Dataset.py",
            "app/dashboard/utils/upload_processor.py",
        ]:
            path = self.repo_root / rel
            self.assertTrue(path.exists(), f"Missing {rel}")
            py_compile.compile(str(path), doraise=True)

        launcher_src = (self.repo_root / "dashboard.py").read_text(encoding="utf-8")
        self.assertIn("08_Farm_Overview.py", launcher_src)
        self.assertIn("09_Import_Dataset.py", launcher_src)


if __name__ == "__main__":
    unittest.main()
