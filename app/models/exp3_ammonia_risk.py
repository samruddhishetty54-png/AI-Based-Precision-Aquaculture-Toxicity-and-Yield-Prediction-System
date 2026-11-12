"""
Experiment 3: Next-Visit Ammonia Toxicity Risk Wrapper - Phase 2 Foundation
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Wraps the pre-trained Random Forest classifier pipeline from Experiment 3
(experiment_3_next_visit_risk_v1/models/random_forest_pipeline.joblib).

Scientific Constraints & Operational Benchmarks:
- Target: High ammonia risk at subsequent farm inspection visit ($t+1$), defined as
  primary_calculated_nh3 >= 0.05 mg/L or TAN >= 1.0 mg/L.
- Revisit Interval: Strictly discrete multi-week intervals between 3 and 45 days
  (median sampling gap: 22.0 days).
- Temporal Horizon: This is strictly a multi-week prognostic model. It is NOT
  an hourly, diurnal, or overnight forecast.
- Chronological Holdout Benchmark (2025–2026, N = 2,034 pairs, 57 events, No-skill PR = 0.0280):
  * Random Forest (Primary Model):
    - PR-AUC: 0.0305 (close to no-skill baseline of 0.0280)
    - ROC-AUC: 0.5061 (near random coin toss of 0.5000)
    - Recall: 31.58% (detected 18 of 57 events)
    - Precision: 2.63% (18 total true positives out of 684 alarms; 666 false alarms)
    - F1-Score: 0.0486
    - Detection Breakdown: 18 total true positives (consisting of 15 of 54 newly developed spikes detected [27.8% sensitivity] plus 3 persistent spikes detected)
  * Logistic Regression (Alternative Model):
    - PR-AUC: 0.0309
    - ROC-AUC: 0.5010
    - Recall: 36.84% (detected 21 of 57 events)
    - Precision: 2.36% (21 total true positives out of 889 alarms; 868 false alarms)
    - F1-Score: 0.0444
    - Detection Breakdown: 21 total true positives (consisting of 18 of 54 newly developed spikes detected [33.3% sensitivity] plus 3 persistent spikes detected)
  * Persistence Baseline:
    - Recall: 5.26% (3 total true positives out of 57 events; completely blind to 54 newly developed spikes, 0.0% sensitivity)
- Spatial GroupKFold Reference (Across all dates, N = 4,900 pairs, 314 events, Baseline = 0.0641):
  * Random Forest: PR-AUC = 0.3461, ROC-AUC = 0.8137, Recall = 61.15%, Precision = 24.71%
  * Logistic Regression: PR-AUC = 0.2893, ROC-AUC = 0.7876, Recall = 71.34%, Precision = 18.33%
  * IMPORTANT: GroupKFold metrics evaluate spatial cross-validation and MUST NOT be presented as future temporal forecasting ability.
- Operational Status: EXPLORATORY PROGNOSTIC RISK ONLY.
- Safety Guardrail: It must NEVER be used to trigger automatic operational alarms or actuators.
"""

from pathlib import Path
from typing import Dict, Any, Union, Optional, List
import joblib
import numpy as np
import pandas as pd

from app.config import MODEL_PATHS
from app.core.chemistry import calculate_nh3_from_tan_n

EXPECTED_FEATURES: List[str] = [
    "gap_days",
    "curr_do",
    "curr_ph",
    "curr_temp",
    "curr_turbidity",
    "curr_tds",
    "tds_is_missing",
    "turbidity_is_missing",
    "curr_weather",
    "curr_color",
    "region",
    "curr_nh3"
]

CORE_REQUIRED_KEYS: List[str] = ["curr_do", "curr_ph", "curr_temp"]


class NextVisitAmmoniaRiskModel:
    """
    Inference wrapper for Experiment 3 Next-Visit Ammonia Toxicity Risk Prediction.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_PATHS.get("exp3_ammonia_risk_rf")
        self.pipeline = None
        self._load_error: Optional[str] = None
        self.load_model()

    def load_model(self) -> None:
        """Loads the serialized model artifact from disk."""
        if self.model_path is None or not Path(self.model_path).exists():
            self.pipeline = None
            self._load_error = f"Model artifact not found at: '{self.model_path}'"
            return

        try:
            self.pipeline = joblib.load(self.model_path)
            self._load_error = None
        except Exception as exc:
            self.pipeline = None
            self._load_error = f"Failed to load Experiment 3 model artifact: {exc}"

    @property
    def is_loaded(self) -> bool:
        """Returns True if the pipeline is loaded and ready for inference."""
        return self.pipeline is not None

    def get_metadata(self) -> Dict[str, Any]:
        """Returns model metadata, status, and verified benchmark metrics."""
        return {
            "model_identifier": "experiment_3_next_visit_ammonia_risk",
            "model_title": "Experiment 3: Next-Visit Ammonia Toxicity Risk (Random Forest)",
            "status": "EXPLORATORY_PROGNOSTIC_RISK",
            "is_operational_baseline": False,
            "artifact_path": str(self.model_path),
            "is_loaded": self.is_loaded,
            "load_error": self._load_error,
            "target_variable": "next_visit_ammonia_risk (y_{t+1} >= 0.05 mg/L NH3 at 3-45 day revisit)",
            "input_features": EXPECTED_FEATURES,
            "warning": (
                "EXPLORATORY MULTI-WEEK ESTIMATE ONLY: Evaluates transition risk over discrete revisit "
                "intervals of 3 to 45 days (median 22 days). This is NOT an hourly or overnight forecast. "
                "Chronological holdout validation (2025–2026) showed performance close to the no-skill baseline "
                "(PR-AUC = 0.0305 vs. no-skill 0.0280; ROC-AUC = 0.5061 vs. random 0.5000) due to field kit "
                "protocol shifts. Do NOT use for automatic operational alerts."
            ),
            "limitations": [
                "Designed strictly for multi-week revisit intervals (3 to 45 days); cannot forecast diurnal or hourly spikes.",
                "Chronological performance degraded significantly on holdout data (PR-AUC 0.0305 vs no-skill 0.0280).",
                "Unobserved intervening farm management (water exchanges, emergency aeration, feeding shifts) cannot be accounted for.",
                "Exploratory advisory tool only; never wire to automated warning alarms or actuators."
            ],
            "chronological_holdout_benchmark": {
                "cohort": "2025–2026 Holdout Test (N = 2,034 pairs, Positives = 57, Prevalence = 2.80%)",
                "no_skill_baseline_pr_auc": 0.0280,
                "random_forest": {
                    "pr_auc": 0.0305,
                    "roc_auc": 0.5061,
                    "recall": 0.3158,
                    "precision": 0.0263,
                    "f1_score": 0.0486,
                    "total_true_positives": 18,
                    "true_positives": 18,
                    "false_positives": 666,
                    "newly_developed_spikes_detected": "15 / 54 (27.8%)",
                    "new_spikes_detected": "15 / 54 (27.8%)",
                    "detection_distinction": "18 total true positives (15 of 54 newly developed spikes + 3 persistent spikes)"
                },
                "logistic_regression": {
                    "pr_auc": 0.0309,
                    "roc_auc": 0.5010,
                    "recall": 0.3684,
                    "precision": 0.0236,
                    "f1_score": 0.0444,
                    "total_true_positives": 21,
                    "true_positives": 21,
                    "false_positives": 868,
                    "newly_developed_spikes_detected": "18 / 54 (33.3%)",
                    "new_spikes_detected": "18 / 54 (33.3%)",
                    "detection_distinction": "21 total true positives (18 of 54 newly developed spikes + 3 persistent spikes)"
                },
                "persistence_baseline": {
                    "recall": 0.0526,
                    "precision": 0.0577,
                    "f1_score": 0.0550,
                    "total_true_positives": 3,
                    "newly_developed_spikes_detected": "0 / 54 (0.0% [BLIND])",
                    "new_spikes_detected": "0 / 54 (0.0% [BLIND])",
                    "detection_distinction": "3 total true positives (0 of 54 newly developed spikes + 3 persistent spikes)"
                }
            },
            "spatial_groupkfold_reference": {
                "cohort": "5-Fold GroupKFold OOF across all historical dates (N = 4,900 pairs, Positives = 314, Prev = 6.41%)",
                "random_forest": {"pr_auc": 0.3461, "roc_auc": 0.8137, "recall": 0.6115, "precision": 0.2471},
                "logistic_regression": {"pr_auc": 0.2893, "roc_auc": 0.7876, "recall": 0.7134, "precision": 0.1833},
                "caution": "GroupKFold metrics evaluate spatial cross-validation and MUST NOT be presented as future temporal forecasting ability."
            }
        }

    def validate_and_prepare_features(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Validates input features, resolving column name aliases (e.g., 'dissolved_oxygen_mg_l' -> 'curr_do'),
        and constructs a single-row DataFrame adhering to pipeline expectations.
        """
        if isinstance(features, pd.DataFrame):
            df_in = features.copy()
        elif isinstance(features, dict):
            df_in = pd.DataFrame([features])
        else:
            raise TypeError(f"Features must be dict or pd.DataFrame, received: {type(features)}")

        # Column alias resolution
        aliases = {
            "curr_do": ["curr_do", "dissolved_oxygen_mg_l", "DO (mg/L)", "do"],
            "curr_ph": ["curr_ph", "ph", "pH"],
            "curr_temp": ["curr_temp", "temp_c", "Temp (in °C)", "temperature"],
            "curr_turbidity": ["curr_turbidity", "turbidity_cm", "Turbidity (in cm)"],
            "curr_tds": ["curr_tds", "tds_ppt", "TDS (ppt)"],
            "curr_weather": ["curr_weather", "Weather", "weather"],
            "curr_color": ["curr_color", "water_color", "Water color"],
            "region": ["region", "Region"],
            "curr_nh3": ["curr_nh3", "primary_calculated_nh3_mg_l", "calculated_toxic_nh3_mg_l"],
            "gap_days": ["gap_days", "interval_days", "gap"]
        }

        resolved = {}
        for canonical, possible_keys in aliases.items():
            found = False
            for k in possible_keys:
                if k in df_in.columns and pd.notna(df_in[k].iloc[0]):
                    resolved[canonical] = df_in[k].iloc[0]
                    found = True
                    break
            if not found:
                resolved[canonical] = np.nan

        # Check required core keys
        for req in CORE_REQUIRED_KEYS:
            if np.isnan(resolved.get(req, np.nan)):
                provided_keys = list(df_in.columns)
                raise ValueError(
                    f"Missing required core input feature '{req}' (or alias) for Experiment 3. "
                    f"Provided keys: {provided_keys}"
                )

        clean_row = {}

        # Gap days handling (validated between 3 and 45 days)
        gap = resolved.get("gap_days", np.nan)
        if pd.isna(gap) or gap is None:
            clean_row["gap_days"] = 14.0  # Standard default within 3-45 day window
        else:
            try:
                g_val = float(gap)
                clean_row["gap_days"] = max(3.0, min(45.0, g_val))
            except (ValueError, TypeError):
                clean_row["gap_days"] = 14.0

        # Numeric core features
        for col in ["curr_do", "curr_ph", "curr_temp"]:
            try:
                clean_row[col] = float(resolved[col])
            except (ValueError, TypeError):
                clean_row[col] = np.nan

        # Optional continuous features with missing indicators
        for col, ind_col in [("curr_turbidity", "turbidity_is_missing"), ("curr_tds", "tds_is_missing")]:
            val = resolved.get(col, np.nan)
            try:
                num_val = float(val) if pd.notna(val) else np.nan
            except (ValueError, TypeError):
                num_val = np.nan
            clean_row[col] = num_val
            clean_row[ind_col] = 1.0 if np.isnan(num_val) else 0.0

        # Categoricals with fallbacks
        clean_row["curr_weather"] = str(resolved["curr_weather"]) if pd.notna(resolved.get("curr_weather")) else "Missing"
        clean_row["curr_color"] = str(resolved["curr_color"]) if pd.notna(resolved.get("curr_color")) else "Missing"
        clean_row["region"] = str(resolved["region"]) if pd.notna(resolved.get("region")) else "Unknown"

        # Current ammonia
        nh3_val = resolved.get("curr_nh3", np.nan)
        if pd.notna(nh3_val):
            try:
                clean_row["curr_nh3"] = float(nh3_val)
            except (ValueError, TypeError):
                clean_row["curr_nh3"] = np.nan
        else:
            # Attempt to derive from TAN if tan_n_mg_l is present in original input
            if "tan_n_mg_l" in df_in.columns and pd.notna(df_in["tan_n_mg_l"].iloc[0]):
                clean_row["curr_nh3"] = calculate_nh3_from_tan_n(
                    df_in["tan_n_mg_l"].iloc[0], clean_row["curr_ph"], clean_row["curr_temp"]
                )
            else:
                clean_row["curr_nh3"] = np.nan

        df_prepared = pd.DataFrame([clean_row])[EXPECTED_FEATURES]
        return df_prepared

    def predict(self, features: Union[Dict[str, Any], pd.DataFrame]) -> Dict[str, Any]:
        """
        Executes next-visit ammonia toxicity risk classification.
        """
        if not self.is_loaded:
            raise RuntimeError(
                f"Experiment 3 Ammonia Risk model is not loaded: {self._load_error}. "
                "Ensure the model artifact exists in 'experiment_3_next_visit_risk_v1/models/'."
            )

        df_prepared = self.validate_and_prepare_features(features)

        try:
            proba = self.pipeline.predict_proba(df_prepared)[0]
            risk_score = round(float(proba[1]), 4)
            is_valid = True
        except Exception:
            risk_score = np.nan
            is_valid = False

        meta = self.get_metadata()
        gap_used = float(df_prepared["gap_days"].iloc[0])

        return {
            "next_visit_risk_score": risk_score,
            "revisit_interval_days": gap_used,
            "model_name": meta["model_title"],
            "status": meta["status"],
            "is_valid": is_valid,
            "features_used": df_prepared.to_dict(orient="records")[0],
            "warning": meta["warning"],
            "limitations": meta["limitations"],
            "disclaimer": (
                f"Multi-week next-visit risk score over a {gap_used}-day revisit interval. "
                "Do NOT use as an automatic alert or real-time forecast."
            )
        }
