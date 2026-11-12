"""
Data Access and Dataset Management Module - Phase 1 Foundation
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Provides safe, validated, cached access to the audited v2 processed datasets
located in processed_data_v2/.

Strict Operational & Scientific Rules:
1. All datasets are read-only; source CSVs are never modified or rewritten.
2. Missing values are preserved exactly as NaN; no silent zero-filling is performed.
3. Original column names and schemas are strictly preserved.
4. Historical field observation logs and hourly IoT simulation models are kept
   STRICTLY SEPARATED to prevent invalid cross-contamination.
5. The IoT dataset is explicitly flagged as a mathematical simulation model,
   NOT live sensor hardware telemetry.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
import pandas as pd

from app.config import DATASET_PATHS, PROCESSED_DATA_V2_DIR

# Internal in-memory dataset cache
_DATA_CACHE: Dict[str, pd.DataFrame] = {}

# Expected key schema columns for validation checks (verified against processed_data_v2/)
EXPECTED_SCHEMAS: Dict[str, List[str]] = {
    "water_quality": ["pond_id", "DO (mg/L)", "pH", "Temp (in °C)", "datetime"],
    "toxicity_analysis": ["pond_id", "dissolved_oxygen_mg_l", "ph", "temp_c", "primary_calculated_nh3_mg_l"],
    "fish_health_growth": ["pond_id", "datetime", "species", "average_fish_weight_g"],
    "feeding_analysis": ["pond_id", "datetime", "species", "feed_amount_kg"],
    "enrolled_ponds": ["pond_id", "region", "Pond area in acres"],
    "dropouts": ["pond_id", "Date of drop out", "Reason"],
    "iot_water_model": ["Datetime", "Dissolved Oxygen (mg/L)", "pH", "Temperature (°C)", "datetime_iso"],
}

# Scientific metadata catalog for datasets
DATASET_METADATA: Dict[str, Dict[str, Any]] = {
    "water_quality": {
        "title": "Cleaned Water Quality Field Logs",
        "description": "Standardized field water-quality observations collected across commercial ponds.",
        "is_simulation": False,
        "temporal_nature": "Irregular farmer monitoring visits (3 to 45 day revisits).",
        "scientific_nature": "Historical field inspection records; contains natural missingness."
    },
    "toxicity_analysis": {
        "title": "Audited Toxicity Analysis Dataset",
        "description": "Primary dataset for ammonia toxicity, dissolved oxygen depletion, and acute stress evaluation.",
        "is_simulation": False,
        "temporal_nature": "Field observation records with audited molecular NH3 calculations.",
        "scientific_nature": "Historical field inspection records with v2 Emerson ammonia equilibrium values."
    },
    "fish_health_growth": {
        "title": "Fish Health & Growth Analysis Dataset",
        "description": "Historical fish somatic weight and health observations.",
        "is_simulation": False,
        "temporal_nature": "Field sampling visits.",
        "scientific_nature": "Somatic individual fish weight (grams/fish), NOT commercial harvest yield or total biomass."
    },
    "feeding_analysis": {
        "title": "Pond Feeding Logs",
        "description": "Historical feed input logs per pond visit.",
        "is_simulation": False,
        "temporal_nature": "Field visit logs.",
        "scientific_nature": "Farmer-reported feed quantities (kg/day)."
    },
    "enrolled_ponds": {
        "title": "Enrolled Ponds Farm Metadata",
        "description": "Pond physical characteristics, farm metadata, stocking density, and acreage.",
        "is_simulation": False,
        "temporal_nature": "Static enrollment metadata.",
        "scientific_nature": "Farm registration profiles."
    },
    "dropouts": {
        "title": "Pond Dropout Records",
        "description": "Records of ponds that dropped out of the monitoring program and recorded reasons.",
        "is_simulation": False,
        "temporal_nature": "Static program dropout records.",
        "scientific_nature": "Operational dropout audit."
    },
    "iot_water_model": {
        "title": "Hourly IoT Reference Simulation Model",
        "description": "Hourly reference simulation model outputs from Data_Model_IoTMLCQ_2024.xlsx.",
        "is_simulation": True,
        "temporal_nature": "Continuous hourly synthetic/simulated time series.",
        "scientific_nature": (
            "MATHEMATICAL SIMULATION / BENCHMARK MODEL. "
            "This is NOT live physical IoT telemetry from commercial aquaculture ponds. "
            "It must NEVER be merged with field observation datasets."
        )
    }
}


def clear_cache() -> None:
    """Clears all cached datasets from memory."""
    _DATA_CACHE.clear()


def get_dataset_metadata(dataset_key: str) -> Dict[str, Any]:
    """
    Returns descriptive metadata, scientific disclaimers, and simulation flags
    for a given dataset key.
    """
    if dataset_key not in DATASET_METADATA:
        raise KeyError(
            f"Unknown dataset key: '{dataset_key}'. "
            f"Available datasets: {list(DATASET_METADATA.keys())}"
        )
    return DATASET_METADATA[dataset_key].copy()


def load_dataset(dataset_key: str, use_cache: bool = True) -> pd.DataFrame:
    """
    Safely loads an audited v2 dataset by key.

    Parameters:
        dataset_key: One of 'water_quality', 'toxicity_analysis', 'fish_health_growth',
                     'feeding_analysis', 'enrolled_ponds', 'dropouts', 'iot_water_model'.
        use_cache: If True, uses the in-memory cache to avoid repeated disk reads.
                   Returns a defensive deep copy so caller modifications do not pollute cache.

    Returns:
        pd.DataFrame containing the dataset with metadata attached in `df.attrs`.

    Raises:
        KeyError: If dataset_key is not recognized.
        FileNotFoundError: If the corresponding CSV file does not exist.
        ValueError: If file is empty or fails basic schema verification.
    """
    if dataset_key not in DATASET_PATHS:
        raise KeyError(
            f"Unrecognized dataset key: '{dataset_key}'. "
            f"Valid keys: {list(DATASET_PATHS.keys())}"
        )

    # Return cached defensive copy if available
    if use_cache and dataset_key in _DATA_CACHE:
        return _DATA_CACHE[dataset_key].copy(deep=True)

    file_path = DATASET_PATHS[dataset_key]
    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset file missing at expected path: '{file_path}'. "
            f"Verify that 'clean_datasets_v2.py' has executed and populated '{PROCESSED_DATA_V2_DIR}'."
        )

    # Load dataset with pandas (preserves NaNs, does NOT replace with zero)
    try:
        df = pd.read_csv(file_path, encoding="utf-8")
    except Exception as exc:
        raise ValueError(f"Failed to parse CSV file '{file_path}': {exc}") from exc

    if df.empty:
        raise ValueError(f"Dataset at '{file_path}' is empty (0 rows).")

    # Basic schema validation
    expected_cols = EXPECTED_SCHEMAS.get(dataset_key, [])
    missing_cols = [col for col in expected_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Schema validation failed for '{dataset_key}'. Missing required columns: {missing_cols}"
        )

    # Attach metadata to DataFrame attrs
    meta = get_dataset_metadata(dataset_key)
    df.attrs["metadata"] = meta
    df.attrs["is_simulation"] = meta["is_simulation"]
    df.attrs["dataset_key"] = dataset_key
    df.attrs["source_path"] = str(file_path)

    # Cache if enabled
    if use_cache:
        _DATA_CACHE[dataset_key] = df.copy(deep=True)

    return df.copy(deep=True)


# Specialized convenience loaders
def load_water_quality_data(use_cache: bool = True) -> pd.DataFrame:
    """Loads standardized field water quality observations."""
    return load_dataset("water_quality", use_cache=use_cache)


def load_toxicity_analysis_data(use_cache: bool = True) -> pd.DataFrame:
    """Loads primary toxicity analysis dataset with calculated NH3."""
    return load_dataset("toxicity_analysis", use_cache=use_cache)


def load_fish_health_growth_data(use_cache: bool = True) -> pd.DataFrame:
    """Loads fish health and somatic weight observations."""
    return load_dataset("fish_health_growth", use_cache=use_cache)


def load_feeding_analysis_data(use_cache: bool = True) -> pd.DataFrame:
    """Loads historical pond feeding records."""
    return load_dataset("feeding_analysis", use_cache=use_cache)


def load_enrolled_ponds_data(use_cache: bool = True) -> pd.DataFrame:
    """Loads enrolled pond farm and physical metadata."""
    return load_dataset("enrolled_ponds", use_cache=use_cache)


def load_dropouts_data(use_cache: bool = True) -> pd.DataFrame:
    """Loads dropout pond logs."""
    return load_dataset("dropouts", use_cache=use_cache)


def load_iot_water_model_data(use_cache: bool = True) -> pd.DataFrame:
    """
    Loads hourly IoT reference simulation model data.

    DISCLAIMER: This dataset contains simulated/mathematical water quality behavior
    from Data_Model_IoTMLCQ_2024.xlsx. It is NOT live sensor telemetry from ponds.
    """
    return load_dataset("iot_water_model", use_cache=use_cache)
