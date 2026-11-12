"""
System Configuration and Data Paths - Phase 1 Foundation
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Defines paths, loads provisional thresholds, and establishes operational
metadata without introducing unverified scientific assumptions.
"""

from pathlib import Path
import json
from typing import Dict, Any, Optional

# Reliable project root path (two levels up from app/config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Core directories
APP_DIR = PROJECT_ROOT / "app"
DATASET_DIR = PROJECT_ROOT / "dataset"
PROCESSED_DATA_V2_DIR = PROJECT_ROOT / "processed_data_v2"
THRESHOLDS_CONFIG_PATH = PROCESSED_DATA_V2_DIR / "thresholds_config.json"

# Centrally defined dataset paths for audited v2 datasets
DATASET_PATHS: Dict[str, Path] = {
    "water_quality": PROCESSED_DATA_V2_DIR / "water_quality_cleaned_v2.csv",
    "toxicity_analysis": PROCESSED_DATA_V2_DIR / "toxicity_analysis_v2.csv",
    "fish_health_growth": PROCESSED_DATA_V2_DIR / "fish_health_growth_analysis_v2.csv",
    "feeding_analysis": PROCESSED_DATA_V2_DIR / "feeding_analysis_v2.csv",
    "enrolled_ponds": PROCESSED_DATA_V2_DIR / "enrolled_ponds_v2.csv",
    "dropouts": PROCESSED_DATA_V2_DIR / "dropouts_v2.csv",
    "iot_water_model": PROCESSED_DATA_V2_DIR / "iot_water_model_v2.csv",
}

# Centrally defined audited model artifact paths
MODEL_PATHS: Dict[str, Path] = {
    "exp1_soft_sensor": PROJECT_ROOT / "baseline_toxicity_v1" / "models" / "experiment_1_rf_pipeline.joblib",
    "exp2_mortality_lr": PROJECT_ROOT / "experiment_2_mortality_v1" / "models" / "logistic_regression_pipeline.joblib",
    "exp2_mortality_rf": PROJECT_ROOT / "experiment_2_mortality_v1" / "models" / "random_forest_pipeline.joblib",
    "exp3_ammonia_risk_rf": PROJECT_ROOT / "experiment_3_next_visit_risk_v1" / "models" / "random_forest_pipeline.joblib",
    "exp3_ammonia_risk_lr": PROJECT_ROOT / "experiment_3_next_visit_risk_v1" / "models" / "logistic_regression_pipeline.joblib",
}

# Scientific & Chemical Constants for Emerson et al. (1975) Aqueous Ammonia Dissociation
EMERSON_PKA_INTERCEPT: float = 0.09018
EMERSON_PKA_SLOPE: float = 2729.92
ABSOLUTE_ZERO_CELSIUS: float = -273.15
MW_NH3: float = 17.031  # Molecular weight of NH3 (g/mol)
MW_N: float = 14.007    # Molecular weight of Nitrogen (g/mol)
MW_RATIO_NH3_N: float = MW_NH3 / MW_N  # ~1.215891911


def load_thresholds_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Safely loads the threshold configuration from processed_data_v2/thresholds_config.json.

    Preserves the provisional status, scientific validation warnings, and
    descriptions exactly as approved in preprocessing audit v2.

    Raises:
        FileNotFoundError: If the thresholds configuration file is missing.
        ValueError: If the configuration file contains invalid JSON or lacks required keys.
    """
    target_path = config_path or THRESHOLDS_CONFIG_PATH
    if not target_path.exists():
        raise FileNotFoundError(
            f"Required threshold configuration file not found at: '{target_path}'. "
            "Please ensure that 'processed_data_v2/thresholds_config.json' is present "
            "and has not been renamed or deleted."
        )

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Corrupted or invalid JSON in '{target_path}': {exc}") from exc

    if "metadata" not in config or "heuristics" not in config:
        raise ValueError(
            f"Configuration at '{target_path}' is missing required sections ('metadata', 'heuristics')."
        )

    return config


# Module-level load of thresholds configuration
try:
    THRESHOLDS_CONFIG = load_thresholds_config()
    PROVISIONAL_THRESHOLDS = THRESHOLDS_CONFIG.get("heuristics", {})
    THRESHOLDS_METADATA = THRESHOLDS_CONFIG.get("metadata", {})
except FileNotFoundError as e:
    # Allow fallback in isolated test environments while logging explicit status
    THRESHOLDS_CONFIG = {}
    PROVISIONAL_THRESHOLDS = {}
    THRESHOLDS_METADATA = {
        "status": "missing_config",
        "warning": str(e)
    }

