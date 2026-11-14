"""Integration and Final Verification tests for Phase 5 Stage 2.5:
Comprehensive multi-page audit, cross-page consistency, scientific terminology,
cryptographic hash immutability, and simulation isolation verification.
"""

import hashlib
import importlib
from pathlib import Path
from typing import Dict
import unittest
import pandas as pd

from app.core.data_manager import load_dataset, DATASET_METADATA
from app.models.registry import get_model_registry
from app.dashboard.utils.helpers import (
    CATEGORIES,
    detect_simulation_source,
    validate_defensive_bounds,
    get_registry_health_summary,
)

# Audited baseline SHA-256 hashes for datasets (processed_data_v2/)
AUDITED_DATASET_HASHES: Dict[str, str] = {
    "processed_data_v2/dropouts_v2.csv": "12b7e730aac7ae9e4eed0b89d3a98489ac6cd3c72d55cd4f9b4e3d6dd424d250",
    "processed_data_v2/enrolled_ponds_v2.csv": "94dae8de04c53891af6550afa39a8df8920b67f4b347d01cf9aa5f73aaa16e57",
    "processed_data_v2/feeding_analysis_v2.csv": "c6cf43d6449d81ed7d591f4bbcf5a74a880a6c0f89bcda126f065921a5b3a582",
    "processed_data_v2/fish_health_growth_analysis_v2.csv": "2ed226697d2b7999e3b15b1604ac574b005144598f6cf35fbacf8b7ba2f0023f",
    "processed_data_v2/iot_water_model_v2.csv": "4a577164b2836ffb77ab2f102eea2c8ab5a9898d88590c3cf969808b370ea5af",
    "processed_data_v2/preprocessing_v2_report.json": "b163443291beccefea488270e7dde780d20aad806ab95cd1b1f59ec5d6205333",
    "processed_data_v2/preprocessing_v2_report.md": "66775bbf0ee2a5c423f5d9e372cd0692cff432908d03f476a0e49c6c2323058c",
    "processed_data_v2/thresholds_config.json": "7aad8fc6df5cebfb311b0ca97d6764f25eb313c35814740ad0d8e6953cad3e94",
    "processed_data_v2/toxicity_analysis_v2.csv": "073f5ab11da085160dcb0821e4a16533d96555f8587261c0bd348f385c60c462",
    "processed_data_v2/water_quality_cleaned_v2.csv": "500b2d6fd032eeabb6d1b947dbc6d93b4464c146d41d9e91f4a0367f54f50e1b",
}

# Audited baseline SHA-256 hashes for pre-trained model pipelines (.joblib)
AUDITED_MODEL_HASHES: Dict[str, str] = {
    "baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib": "e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a",
    "experiment_1_sensor_ablation_v1/models/model_a_rf_pipeline.joblib": "e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a",
    "experiment_1_sensor_ablation_v1/models/model_b_rf_pipeline.joblib": "08907e58a01036eaadb44b6c10370e0219b920ddaa07279504b6e101a0f4a281",
    "experiment_2_mortality_v1/models/dummy_prior_pipeline.joblib": "c6259edd0a0908614ba93b3faa78256359098c4461576ec08d40ae46714985fa",
    "experiment_2_mortality_v1/models/logistic_regression_pipeline.joblib": "02c8a34ae4ff8b8d907beeed18be4ecd00bb463cd204e8298163f6864afcdadf",
    "experiment_2_mortality_v1/models/random_forest_pipeline.joblib": "464344d33ffc3cff26726bfa15ec73d6b8a59b773ae61083db3d3082f44b4216",
    "experiment_3_next_visit_risk_v1/models/dummy_prior_pipeline.joblib": "2a51e871bbf2fa4d0d5f7a3c1f0dcbfc49499418383cc887514112bf8fa0de8b",
    "experiment_3_next_visit_risk_v1/models/logistic_regression_pipeline.joblib": "957aea9b8cd0066e364c776c76b12128b7b8e63cafe9800cbda39a03d8486ad7",
    "experiment_3_next_visit_risk_v1/models/random_forest_pipeline.joblib": "2f7980756c02a5fa00e325919944c8dd416456d785af9f110135e10edd38853c",
}


def _compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not filepath.exists():
        return "FILE_NOT_FOUND"
    return hashlib.sha256(filepath.read_bytes()).hexdigest()


class TestDashboardStage25Integration(unittest.TestCase):
    """Stage 2.5 final integration and governance verification test suite."""

    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.pages_dir = self.repo_root / "app" / "dashboard" / "pages"
        self.registry = get_model_registry()
        self.page_names = [
            "01_Overview.py",
            "02_Water_Quality_Toxicity.py",
            "03_Next_Visit_DO_Hypoxia.py",
            "04_Growth_Feeding_Advisor.py",
            "05_Historical_Data_Explorer.py",
            "06_Simulation_Sandbox.py",
            "07_Model_Registry_Governance.py",
        ]

    def test_all_seven_pages_import_and_render_callable(self):
        """Verify all seven pages can be imported dynamically and render_page is callable."""
        for p_name in self.page_names:
            mod_name = f"app.dashboard.pages.{p_name.replace('.py', '')}"
            mod = importlib.import_module(mod_name)
            self.assertTrue(hasattr(mod, "render_page"), f"{p_name} missing render_page")
            self.assertTrue(callable(getattr(mod, "render_page")), f"{p_name} render_page not callable")

    def test_cryptographic_dataset_hashes_immutability(self):
        """Verify 100% cryptographic immutability of all 10 processed dataset files."""
        for rel_path, expected_hash in AUDITED_DATASET_HASHES.items():
            full_path = self.repo_root / rel_path
            self.assertTrue(full_path.exists(), f"Dataset file missing: {rel_path}")
            actual_hash = _compute_sha256(full_path)
            self.assertEqual(
                actual_hash,
                expected_hash,
                f"SHA-256 hash mismatch for dataset {rel_path}! Expected {expected_hash}, got {actual_hash}",
            )

    def test_cryptographic_model_hashes_immutability(self):
        """Verify 100% cryptographic immutability of all 9 pre-trained model .joblib files."""
        for rel_path, expected_hash in AUDITED_MODEL_HASHES.items():
            full_path = self.repo_root / rel_path
            self.assertTrue(full_path.exists(), f"Model file missing: {rel_path}")
            actual_hash = _compute_sha256(full_path)
            self.assertEqual(
                actual_hash,
                expected_hash,
                f"SHA-256 hash mismatch for model {rel_path}! Expected {expected_hash}, got {actual_hash}",
            )

    def test_disclaimer_against_real_time_and_overnight_claims(self):
        """Verify that across all 7 pages, real-time and overnight claims are explicitly disclaimed."""
        for p_name in self.page_names:
            p_path = self.pages_dir / p_name
            content = p_path.read_text(encoding="utf-8")

            # Check that terms implying real-time streaming are qualified or disclaimed
            if "real-time" in content.lower() or "live" in content.lower():
                # Must contain disclaimers like 'NOT live', 'No Real-Time', 'zero real-time', etc.
                has_disclaimer = any(
                    discl in content
                    for discl in [
                        "NOT live",
                        "No Real-Time",
                        "zero real-time",
                        "Zero Real-Time",
                        "strictly NOT live",
                        "not live",
                        "NOT continuous",
                    ]
                )
                self.assertTrue(
                    has_disclaimer,
                    f"{p_name} mentions live/real-time without explicit negation/disclaimer!",
                )

            # Check morning DO observation window disclaimers
            if "minimum do" in content.lower() or "overnight" in content.lower():
                has_do_disclaimer = any(
                    discl in content
                    for discl in [
                        "NOT verified pre-dawn",
                        "not verified pre-dawn",
                        "NOT daily minimum",
                        "NOT an overnight forecast",
                        "not an hourly or overnight",
                        "No Hourly/Overnight Claims",
                    ]
                )
                self.assertTrue(
                    has_do_disclaimer,
                    f"{p_name} mentions overnight/minimum DO without explicit disclaimer!",
                )

    def test_harvest_yield_negative_scope_enforcement(self):
        """Verify that fish growth pages explicitly enforce negative scope (NOT commercial harvest yield)."""
        growth_page = self.pages_dir / "04_Growth_Feeding_Advisor.py"
        growth_content = growth_page.read_text(encoding="utf-8")
        self.assertIn("NOT total commercial yield in kg/ha", growth_content)
        self.assertIn("0% total yield labels", growth_content)

        overview_page = self.pages_dir / "01_Overview.py"
        overview_content = overview_page.read_text(encoding="utf-8")
        self.assertIn("NOT harvest yield", overview_content)

        governance_page = self.pages_dir / "07_Model_Registry_Governance.py"
        gov_content = governance_page.read_text(encoding="utf-8")
        self.assertIn("DISCLAIMED (Not Total Yield kg/ha)", gov_content)

    def test_zero_automated_actuation_enforcement(self):
        """Verify zero automated actuator commands is enforced across dashboard pages and launcher."""
        launcher_content = (self.repo_root / "dashboard.py").read_text(encoding="utf-8")
        self.assertIn("is_automatic_control = False", launcher_content)

        overview_content = (self.pages_dir / "01_Overview.py").read_text(encoding="utf-8")
        self.assertIn("is_automatic_control = False", overview_content)

        governance_content = (self.pages_dir / "07_Model_Registry_Governance.py").read_text(encoding="utf-8")
        self.assertIn("is_automatic_control = False", governance_content)

    def test_simulation_data_isolation_and_quarantine(self):
        """Verify simulation inputs always produce operational_use_permitted = False."""
        is_sim, tag, permitted = detect_simulation_source(is_simulated_flag=True)
        self.assertTrue(is_sim)
        self.assertEqual(tag, "SIMULATED_SCENARIO_ONLY")
        self.assertFalse(permitted)

        # Feeding advisory in simulation mode
        sim_res = self.registry.get_feeding_advisory({
            "dissolved_oxygen_mg_l": 1.5,
            "temp_c": 32.0,
            "current_feed_amount_kg": 25.0,
            "is_simulated": True,
            "data_source": "benchmark_simulation",
        })
        self.assertEqual(sim_res.get("status"), "SIMULATED_SCENARIO_ONLY")
        self.assertFalse(sim_res.get("operational_use_permitted"))
        self.assertTrue(sim_res.get("is_simulated"))

        # DO Hypoxia in simulation mode
        do_res = self.registry.predict_do_hypoxia({
            "curr_do": 1.5,
            "is_simulated": True,
            "data_source": "benchmark_simulation",
        })
        self.assertEqual(do_res.get("data_source"), "benchmark_simulation")
        self.assertTrue(do_res.get("is_simulated"))

    def test_defensive_bounds_validation_across_parameters(self):
        """Verify software validation boundaries reject out-of-range values defensively."""
        params_to_test = [
            ("do", -0.5, False),
            ("do", 4.0, True),
            ("do", 26.0, False),
            ("ph", -1.0, False),
            ("ph", 7.5, True),
            ("ph", 15.0, False),
            ("water_temp", 5.0, False),
            ("water_temp", 28.0, True),
            ("water_temp", 50.0, False),
            ("tan", -0.1, False),
            ("tan", 1.0, True),
            ("tan", 25.0, False),
            ("fish_weight", 0.0, False),
            ("fish_weight", 150.0, True),
            ("fish_weight", 6000.0, False),
            ("revisit_interval", 1.0, False),
            ("revisit_interval", 21.0, True),
            ("revisit_interval", 50.0, False),
        ]
        for param, val, expected_valid in params_to_test:
            valid, msg = validate_defensive_bounds(param, val)
            self.assertEqual(
                valid,
                expected_valid,
                f"Failed defensive bound check for {param}={val}: expected {expected_valid}, got {valid} ({msg})",
            )

    def test_chemical_dissociation_molecular_weight_ratio(self):
        """Verify chemical dissociation applies 17.031 / 14.007 ratio accurately."""
        from app.core.chemistry import calculate_nh3_from_tan_n, calculate_nh3_from_tan_nh3
        tan_n_res = calculate_nh3_from_tan_n(1.0, 8.0, 28.0, round_digits=None)
        tan_nh3_res = calculate_nh3_from_tan_nh3(1.0, 8.0, 28.0, round_digits=None)
        ratio = tan_n_res / tan_nh3_res
        expected_ratio = 17.031 / 14.007
        self.assertAlmostEqual(ratio, expected_ratio, places=5)

    def test_registry_health_operational_state(self):
        """Verify model registry returns HEALTHY with all 6 registered models ready."""
        health = get_registry_health_summary(self.registry)
        self.assertEqual(health["status"], "HEALTHY")
        self.assertEqual(health["total_count"], 6)
        self.assertEqual(health["ready_count"], 6)


if __name__ == "__main__":
    unittest.main()
