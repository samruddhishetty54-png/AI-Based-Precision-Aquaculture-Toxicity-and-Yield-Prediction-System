"""
Unit Tests for Aqueous Ammonia Chemistry Module - Phase 1 Foundation
AI-Based Precision Aquaculture Toxicity and Yield Prediction System
"""

import unittest
import numpy as np
import pandas as pd

from app.core.chemistry import (
    calculate_pka,
    calculate_unionized_fraction,
    calculate_nh3_from_tan_n,
    calculate_nh3_from_tan_nh3,
    calculate_ammonia_toxicity,
    calculate_nh3_series,
)
from app.config import MW_RATIO_NH3_N, ABSOLUTE_ZERO_CELSIUS


class TestAmmoniaChemistry(unittest.TestCase):
    """Verifies Emerson aqueous ammonia dissociation calculations and edge cases."""

    def test_pka_calculation(self):
        """Tests Emerson pKa calculation across known standard water temperatures."""
        # At 25°C: pKa = 0.09018 + 2729.92 / (25 + 273.15) = 9.2463765...
        pka_25 = calculate_pka(25.0)
        self.assertAlmostEqual(pka_25, 9.2464, places=3)

        # At 30°C: pKa = 0.09018 + 2729.92 / (30 + 273.15) = 9.0953589...
        pka_30 = calculate_pka(30.0)
        self.assertAlmostEqual(pka_30, 9.0954, places=3)

    def test_unionized_fraction(self):
        """Tests fraction of un-ionized ammonia increases with higher pH and temperature."""
        f_low_ph = calculate_unionized_fraction(ph=7.0, temp_c=25.0)
        f_high_ph = calculate_unionized_fraction(ph=8.5, temp_c=25.0)
        self.assertLess(f_low_ph, f_high_ph)

        # At pH == pKa, fraction should be exactly 0.5
        pka_25 = calculate_pka(25.0)
        f_at_pka = calculate_unionized_fraction(ph=pka_25, temp_c=25.0)
        self.assertAlmostEqual(f_at_pka, 0.5, places=5)

    def test_tan_n_applies_mw_conversion_once(self):
        """
        Verifies that calculate_nh3_from_tan_n applies the (17.031 / 14.007)
        molecular weight conversion factor exactly once.
        """
        temp = 28.5
        ph = 8.2
        tan = 2.0

        pka = calculate_pka(temp)
        f = 1.0 / (10.0 ** (pka - ph) + 1.0)
        expected_unrounded = f * tan * (17.031 / 14.007)
        expected = round(expected_unrounded, 5)

        actual = calculate_nh3_from_tan_n(tan, ph, temp)
        self.assertEqual(actual, expected)

    def test_tan_nh3_does_not_apply_mw_conversion(self):
        """
        Verifies that calculate_nh3_from_tan_nh3 does NOT apply the molecular weight conversion.
        """
        temp = 28.5
        ph = 8.2
        tan = 2.0

        pka = calculate_pka(temp)
        f = 1.0 / (10.0 ** (pka - ph) + 1.0)
        expected = round(f * tan, 5)

        actual = calculate_nh3_from_tan_nh3(tan, ph, temp)
        self.assertEqual(actual, expected)

    def test_ratio_between_tan_n_and_tan_nh3(self):
        """
        Verifies that the ratio of unrounded NH3 from TAN-N vs TAN-NH3 equals
        the molecular weight ratio (17.031 / 14.007 ≈ 1.2158919).
        """
        temp = 27.0
        ph = 8.0
        tan = 1.5

        res_n = calculate_nh3_from_tan_n(tan, ph, temp, round_digits=None)
        res_nh3 = calculate_nh3_from_tan_nh3(tan, ph, temp, round_digits=None)

        ratio = res_n / res_nh3
        self.assertAlmostEqual(ratio, MW_RATIO_NH3_N, places=7)

    def test_missing_values_handled_safely(self):
        """Verifies that missing values return np.nan and never throw unhandled errors."""
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(np.nan, 8.0, 25.0)))
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(1.0, np.nan, 25.0)))
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(1.0, 8.0, np.nan)))
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(None, 8.0, 25.0)))
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(1.0, None, 25.0)))
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(1.0, 8.0, None)))

        self.assertTrue(np.isnan(calculate_nh3_from_tan_nh3(np.nan, 8.0, 25.0)))
        self.assertTrue(np.isnan(calculate_nh3_from_tan_nh3(None, 8.0, 25.0)))

    def test_no_silent_zero_replacement(self):
        """
        CRITICAL RESTRICTION: Missing measurements must NEVER be silently
        replaced with zero.
        """
        result = calculate_nh3_from_tan_n(np.nan, 8.0, 25.0)
        self.assertFalse(result == 0.0)
        self.assertTrue(np.isnan(result))

    def test_invalid_inputs_handled_safely(self):
        """Verifies unphysical inputs (negative TAN, extreme pH, below absolute zero) return np.nan."""
        # Negative TAN is unphysical
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(-1.0, 8.0, 25.0)))
        self.assertTrue(np.isnan(calculate_nh3_from_tan_nh3(-0.5, 8.0, 25.0)))

        # pH outside 0 to 14
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(1.0, -1.0, 25.0)))
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(1.0, 15.0, 25.0)))

        # Temperature below absolute zero or boiling
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(1.0, 8.0, ABSOLUTE_ZERO_CELSIUS)))
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(1.0, 8.0, -300.0)))
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n(1.0, 8.0, 120.0)))

        # Non-numeric string input
        self.assertTrue(np.isnan(calculate_nh3_from_tan_n("invalid", 8.0, 25.0)))

    def test_numerical_consistency_with_audited_v2(self):
        """
        Verifies exact numerical agreement with the audited clean_datasets_v2.py benchmark.
        """
        # Benchmark aquaculture condition:
        # TAN = 1.5 mg/L, pH = 8.2, Temp = 28.5°C
        res_n = calculate_nh3_from_tan_n(1.5, 8.2, 28.5)
        self.assertEqual(res_n, 0.18778)

        res_nh3 = calculate_nh3_from_tan_nh3(1.5, 8.2, 28.5)
        self.assertEqual(res_nh3, 0.15444)

    def test_unified_toxicity_interface(self):
        """Verifies calculate_ammonia_toxicity returns correct transparency metadata."""
        out_n = calculate_ammonia_toxicity(1.5, 8.2, 28.5, basis="TAN_N")
        self.assertEqual(out_n["calculated_nh3_mg_l"], 0.18778)
        self.assertEqual(out_n["reporting_basis"], "TAN_N")
        self.assertTrue(out_n["mw_conversion_applied"])
        self.assertTrue(out_n["is_valid"])
        self.assertIn("theoretical un-ionized ammonia", out_n["scientific_disclaimer"])

        out_nh3 = calculate_ammonia_toxicity(1.5, 8.2, 28.5, basis="TAN_NH3")
        self.assertEqual(out_nh3["calculated_nh3_mg_l"], 0.15444)
        self.assertFalse(out_nh3["mw_conversion_applied"])

        # Invalid basis raises ValueError
        with self.assertRaises(ValueError):
            calculate_ammonia_toxicity(1.5, 8.2, 28.5, basis="unrecognized_basis")

    def test_vectorized_series_calculation(self):
        """Verifies calculate_nh3_series works correctly across pandas Series."""
        tans = pd.Series([1.5, np.nan, 2.0, -1.0])
        phs = pd.Series([8.2, 8.0, np.nan, 8.0])
        temps = pd.Series([28.5, 25.0, 25.0, 25.0])

        res = calculate_nh3_series(tans, phs, temps, basis="TAN_N")
        self.assertEqual(len(res), 4)
        self.assertEqual(res.iloc[0], 0.18778)
        self.assertTrue(pd.isna(res.iloc[1]))
        self.assertTrue(pd.isna(res.iloc[2]))
        self.assertTrue(pd.isna(res.iloc[3]))


if __name__ == "__main__":
    unittest.main()
