"""
Experiment 1: Ammonia Soft-Sensor Wrapper - Phase 2 Foundation
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Wraps the pre-trained Random Forest soft-sensor pipeline from Experiment 1
(baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib).

Scientific Constraints & Governance:
- Target Variable: Calculated un-ionized ammonia proxy (primary_calculated_nh3_mg_l)
  derived from field TAN, pH, and water temperature using Emerson's equilibrium formula.
- Physical Chemistry Boundary: Molecular un-ionized ammonia (NH3) is distinct from Total
  Ammonia Nitrogen (TAN). The un-ionized NH3 fraction depends on pH and temperature and is
  calculated using the Emerson equation. 2.0 mg/L is the TAN test-kit graduation, not an
  NH3 toxicity threshold.
- Chronological Holdout Findings Across Audited NH3 Concentration Tiers (2025–2026, N = 2,600):
  * Actual NH3 >= 0.05 mg/L: 79.59% underpredicted (N = 98, bias = -0.0537 mg/L).
  * Actual NH3 >= 0.10 mg/L: 100.00% underpredicted (N = 33, bias = -0.1336 mg/L).
  * Actual NH3 >= 0.20 mg/L: 100.00% underpredicted (N = 10, bias = -0.2234 mg/L).
- Operational Status: EXPERIMENTAL SOFT-SENSOR ONLY.
- Safety Guardrail: It must NEVER be presented as an analytical laboratory measurement,
  regulatory compliance standard, or an independent automated safety shutoff alarm.
"""

from pathlib import Path
from typing import Dict, Any, Union, Optional, List
import joblib
import numpy as np
import pandas as pd

from app.config import MODEL_PATHS

# Exact feature order expected by the trained ColumnTransformer
EXPECTED_FEATURES: List[str] = [
    "dissolved_oxygen_mg_l",
    "ph",
    "temp_c",
    "turbidity_cm",
    "tds_ppt",
    "tds_ppt_is_missing",
    "turbidity_cm_is_missing",
    "Weather",
    "water_color",
    "region"
]

CORE_REQUIRED_KEYS: List[str] = ["dissolved_oxygen_mg_l", "ph", "temp_c"]


class AmmoniaSoftSensorModel:
    """
    Inference wrapper for the Experiment 1 Random Forest Ammonia Soft-Sensor.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_PATHS.get("exp1_soft_sensor")
        self.pipeline = None
        self._load_error: Optional[str] = None
        self.load_model()

    def load_model(self) -> None:
        """
        Loads the serialized pipeline artifact from disk.
        Does not retrain or alter any model parameters.
        """
        if self.model_path is None or not Path(self.model_path).exists():
            self.pipeline = None
            self._load_error = f"Model artifact not found at: '{self.model_path}'"
            return

        try:
            self.pipeline = joblib.load(self.model_path)
            self._load_error = None
        except Exception as exc:
            self.pipeline = None
            self._load_error = f"Failed to load Experiment 1 model artifact: {exc}"

    @property
    def is_loaded(self) -> bool:
        """Returns True if the pipeline is loaded and ready for inference."""
        return self.pipeline is not None

    def get_metadata(self) -> Dict[str, Any]:
        """Returns scientific metadata, status, and verified audit findings."""
        return {
            "model_identifier": "experiment_1_ammonia_soft_sensor",
            "model_title": "Experiment 1: Ammonia Soft-Sensor (Random Forest)",
            "status": "EXPERIMENTAL_SOFT_SENSOR",
            "is_operational_baseline": False,
            "artifact_path": str(self.model_path),
            "is_loaded": self.is_loaded,
            "load_error": self._load_error,
            "target_variable": "primary_calculated_nh3_mg_l (proxy equilibrium un-ionized ammonia)",
            "input_features": EXPECTED_FEATURES,
            "warning": (
                "EXPERIMENTAL SOFT-SENSOR ESTIMATE ONLY: Estimates un-ionized ammonia proxy "
                "from physical water quality parameters. Under chronological holdout validation (2025–2026), "
                "it systematically underpredicted dangerous acute ammonia spikes: 79.59% underpredicted at "
                "actual NH3 >= 0.05 mg/L (N=98), 100.0% underpredicted at actual NH3 >= 0.10 mg/L (N=33), "
                "and 100.0% underpredicted at actual NH3 >= 0.20 mg/L (N=10). It must NEVER be used as an "
                "independent safety alarm, regulatory compliance metric, or certified laboratory measurement."
            ),
            "limitations": [
                "Target is a calculated equilibrium proxy, not an analytical chemistry laboratory standard.",
                "100% underprediction failure across elevated NH3 concentration tiers (NH3 >= 0.10 and >= 0.20 mg/L).",
                "Chronological validation showed significant performance degradation across unseen production seasons (R² = 0.329).",
                "Must be treated as an exploratory auxiliary soft-sensor, never an autonomous shutoff control."
            ],
            "chronological_underprediction_audit": {
                "nh3_ge_0_05_mg_l": {"count": 98, "underprediction_pct": 79.59, "mean_bias_mg_l": -0.05371, "mae_mg_l": 0.06664},
                "nh3_ge_0_10_mg_l": {"count": 33, "underprediction_pct": 100.00, "mean_bias_mg_l": -0.13358, "mae_mg_l": 0.13358},
                "nh3_ge_0_20_mg_l": {"count": 10, "underprediction_pct": 100.00, "mean_bias_mg_l": -0.22343, "mae_mg_l": 0.22343},
                "max_holdout_underestimation_error_mg_l": 0.50540,
                "note": (
                    "2.0 mg/L is the TAN test-kit graduation, not an NH3 toxicity threshold. "
                    "The un-ionized NH3 fraction depends on pH and temperature and is calculated using the Emerson equation."
                )
            }
        }

    def validate_and_prepare_features(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Validates input features and formats them into a single-row DataFrame
        with the exact column names and types expected by the pipeline.

        Auto-derives missingness indicator columns if they are not provided.
        """
        if isinstance(features, pd.DataFrame):
            df_in = features.copy()
        elif isinstance(features, dict):
            df_in = pd.DataFrame([features])
        else:
            raise TypeError(f"Features must be a dict or pd.DataFrame, received: {type(features)}")

        # Check required core keys
        missing_keys = [k for k in CORE_REQUIRED_KEYS if k not in df_in.columns]
        if missing_keys:
            raise ValueError(
                f"Missing required core input features for Experiment 1 Soft-Sensor: {missing_keys}. "
                f"Core keys required: {CORE_REQUIRED_KEYS}"
            )

        # Build clean output dataframe with exact feature ordering
        clean_row = {}
        for col in ["dissolved_oxygen_mg_l", "ph", "temp_c"]:
            val = df_in[col].iloc[0] if col in df_in.columns else np.nan
            try:
                clean_row[col] = float(val) if pd.notna(val) else np.nan
            except (ValueError, TypeError):
                clean_row[col] = np.nan

        # Optional continuous features with missing indicators
        for col, ind_col in [("turbidity_cm", "turbidity_cm_is_missing"), ("tds_ppt", "tds_ppt_is_missing")]:
            val = df_in[col].iloc[0] if col in df_in.columns else np.nan
            try:
                num_val = float(val) if pd.notna(val) else np.nan
            except (ValueError, TypeError):
                num_val = np.nan
            clean_row[col] = num_val

            # Auto-calculate indicator if omitted
            if ind_col in df_in.columns and pd.notna(df_in[ind_col].iloc[0]):
                clean_row[ind_col] = float(df_in[ind_col].iloc[0])
            else:
                clean_row[ind_col] = 1.0 if np.isnan(num_val) else 0.0

        # Optional categorical features with missing fallbacks
        for cat_col, default_val in [("Weather", "Missing"), ("water_color", "Missing"), ("region", "Unknown")]:
            if cat_col in df_in.columns and pd.notna(df_in[cat_col].iloc[0]):
                clean_row[cat_col] = str(df_in[cat_col].iloc[0])
            else:
                clean_row[cat_col] = default_val

        df_prepared = pd.DataFrame([clean_row])[EXPECTED_FEATURES]
        return df_prepared

    def predict(self, features: Union[Dict[str, Any], pd.DataFrame]) -> Dict[str, Any]:
        """
        Executes soft-sensor regression to estimate un-ionized ammonia.

        Parameters:
            features: Dictionary or DataFrame with water quality parameters.

        Returns:
            Dictionary containing estimated NH3, model status, warnings, and limitations.

        Raises:
            RuntimeError: If model artifact is not loaded.
            ValueError: If required core features are missing.
        """
        if not self.is_loaded:
            raise RuntimeError(
                f"Experiment 1 Soft-Sensor model is not loaded: {self._load_error}. "
                "Ensure the model artifact exists in 'baseline_toxicity_v1/models/'."
            )

        df_prepared = self.validate_and_prepare_features(features)

        try:
            pred_arr = self.pipeline.predict(df_prepared)
            pred_val = float(pred_arr[0])
            # Clamping: un-ionized ammonia cannot be negative in physical aqueous solutions
            est_nh3 = max(0.0, round(pred_val, 5))
            is_valid = True
        except Exception:
            est_nh3 = np.nan
            is_valid = False

        meta = self.get_metadata()
        return {
            "estimated_nh3_mg_l": est_nh3,
            "model_name": meta["model_title"],
            "status": meta["status"],
            "is_valid": is_valid,
            "features_used": df_prepared.to_dict(orient="records")[0],
            "warning": meta["warning"],
            "limitations": meta["limitations"],
            "disclaimer": (
                "Calculated soft-sensor estimate. Never treat as a laboratory chemical assay "
                "or an independent safety alarm."
            )
        }
