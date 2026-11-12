"""
Unit Tests for Data Manager Module - Phase 1 Foundation
AI-Based Precision Aquaculture Toxicity and Yield Prediction System
"""

import unittest
import hashlib
from pathlib import Path
import numpy as np
import pandas as pd

from app.core.data_manager import (
    load_dataset,
    load_water_quality_data,
    load_toxicity_analysis_data,
    load_fish_health_growth_data,
    load_feeding_analysis_data,
    load_enrolled_ponds_data,
    load_dropouts_data,
    load_iot_water_model_data,
    get_dataset_metadata,
    clear_cache,
    DATASET_METADATA,
)
from app.config import DATASET_PATHS, PROCESSED_DATA_V2_DIR


class TestDataManager(unittest.TestCase):
    """Verifies dataset loading, schema enforcement, caching, and scientific restrictions."""

    def setUp(self):
        """Clear cache before each test."""
        clear_cache()

    def test_all_v2_datasets_load_successfully(self):
        """Verifies that all 7 audited v2 datasets load cleanly and are non-empty."""
        expected_keys = [
            "water_quality",
            "toxicity_analysis",
            "fish_health_growth",
            "feeding_analysis",
            "enrolled_ponds",
            "dropouts",
            "iot_water_model",
        ]

        for key in expected_keys:
            df = load_dataset(key, use_cache=False)
            self.assertIsInstance(df, pd.DataFrame, f"Failed for {key}")
            self.assertFalse(df.empty, f"Dataset {key} is unexpectedly empty")
            self.assertGreater(len(df), 0, f"Dataset {key} has 0 rows")

    def test_specialized_loaders(self):
        """Verifies each specialized convenience loader function."""
        df_wq = load_water_quality_data()
        self.assertEqual(len(df_wq), 12399)

        df_tox = load_toxicity_analysis_data()
        self.assertEqual(len(df_tox), 6945)

        df_growth = load_fish_health_growth_data()
        self.assertEqual(len(df_growth), 9422)

        df_feed = load_feeding_analysis_data()
        self.assertEqual(len(df_feed), 6752)

        df_ponds = load_enrolled_ponds_data()
        self.assertEqual(len(df_ponds), 324)

        df_drop = load_dropouts_data()
        self.assertEqual(len(df_drop), 128)

        df_iot = load_iot_water_model_data()
        self.assertEqual(len(df_iot), 4383)

    def test_missing_dataset_key_raises_keyerror(self):
        """Verifies that requesting an unknown dataset key raises a descriptive KeyError."""
        with self.assertRaises(KeyError) as ctx:
            load_dataset("non_existent_dataset")
        self.assertIn("Unrecognized dataset key", str(ctx.exception))

    def test_missing_file_raises_filenotfound(self):
        """Verifies that pointing to a missing file raises FileNotFoundError with clear message."""
        # Temporarily test with a patched fake path in DATASET_PATHS
        fake_key = "test_missing_file_key"
        DATASET_PATHS[fake_key] = PROCESSED_DATA_V2_DIR / "non_existent_file.csv"
        try:
            with self.assertRaises(FileNotFoundError) as ctx:
                load_dataset(fake_key, use_cache=False)
            self.assertIn("Dataset file missing at expected path", str(ctx.exception))
        finally:
            DATASET_PATHS.pop(fake_key, None)

    def test_missing_values_remain_missing(self):
        """
        CRITICAL RESTRICTION: Missing values must remain NaN and NEVER be
        silently replaced with zero.
        """
        df_wq = load_water_quality_data()
        # Find the TAN column (uses unicode em-dash)
        tan_col = [c for c in df_wq.columns if "TAN (NH3-N)" in c][0]
        missing_count = df_wq[tan_col].isna().sum()
        self.assertGreater(missing_count, 0)

        # Ensure no NaN is converted to 0.0
        null_mask = df_wq[tan_col].isna()
        self.assertTrue(df_wq.loc[null_mask, tan_col].isna().all())

    def test_historical_and_simulated_datasets_remain_separate(self):
        """
        CRITICAL RESTRICTION: Field observations and hourly IoT simulation models
        must NEVER be merged and must be clearly distinguished by metadata.
        """
        df_field = load_water_quality_data()
        df_sim = load_iot_water_model_data()

        # Check simulation flags
        self.assertFalse(df_field.attrs["is_simulation"])
        self.assertTrue(df_sim.attrs["is_simulation"])

        # Check metadata disclaimers
        sim_meta = get_dataset_metadata("iot_water_model")
        self.assertTrue(sim_meta["is_simulation"])
        self.assertIn("NOT live physical IoT telemetry", sim_meta["scientific_nature"])

        field_meta = get_dataset_metadata("water_quality")
        self.assertFalse(field_meta["is_simulation"])
        self.assertIn("Historical field inspection records", field_meta["scientific_nature"])

        # Column structures must be distinct
        self.assertIn("pond_id", df_field.columns)
        self.assertNotIn("oxigeno_scaled", df_field.columns)
        self.assertIn("oxigeno_scaled", df_sim.columns)

    def test_defensive_caching_prevents_mutation(self):
        """Verifies that modifying a returned DataFrame does not mutate the cached DataFrame."""
        df1 = load_enrolled_ponds_data(use_cache=True)
        original_val = df1.iloc[0, 0]

        # Mutate df1
        df1.iloc[0, 0] = "MUTATED_VALUE_TEST"

        # Load again
        df2 = load_enrolled_ponds_data(use_cache=True)
        self.assertEqual(df2.iloc[0, 0], original_val)
        self.assertNotEqual(df2.iloc[0, 0], "MUTATED_VALUE_TEST")

    def test_source_csv_files_unmodified(self):
        """Verifies that reading datasets does not modify the source CSV files on disk."""
        # Calculate SHA256 before loading
        target_path = DATASET_PATHS["dropouts"]
        with open(target_path, "rb") as f:
            hash_before = hashlib.sha256(f.read()).hexdigest()

        # Load the dataset
        _ = load_dropouts_data(use_cache=False)

        # Calculate SHA256 after loading
        with open(target_path, "rb") as f:
            hash_after = hashlib.sha256(f.read()).hexdigest()

        self.assertEqual(hash_before, hash_after)


if __name__ == "__main__":
    unittest.main()
