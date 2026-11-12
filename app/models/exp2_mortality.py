"""
Experiment 2: Fish Mortality Diagnostic Wrapper - Phase 2 Foundation
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Wraps the pre-trained class-weighted Logistic Regression mortality diagnostic
pipeline from Experiment 2 (experiment_2_mortality_v1/models/logistic_regression_pipeline.joblib).

Scientific Constraints & Operational Benchmarks:
- Target: Binary occurrence of dead fish (`dead_fish_count > 0`).
- Chronological Holdout Benchmark (2025–2026, N = 2,600, 44 mortalities, No-skill baseline = 0.0169):
  * Logistic Regression (Primary Model):
    - ROC-AUC: 0.5917
    - PR-AUC: 0.0499 (vs no-skill 0.0169)
    - Recall: 20.45% (detected 9 of 44 mortalities)
    - Precision: 3.81% (9 true positives out of 236 alarms; 227 false alarms)
    - F1-Score: 0.0643
  * Random Forest (Alternative Model, train-tuned tau = 0.40):
    - ROC-AUC: 0.7322
    - PR-AUC: 0.0648
    - Recall: 13.64% (detected 6 of 44 mortalities)
    - Precision: 11.54% (6 true positives out of 52 alarms; 46 false alarms)
    - F1-Score: 0.1250
- Historical Spatial Reference (GroupKFold across all dates, N = 5,122, 75 mortalities):
  * Logistic Regression: ROC-AUC = 0.7712, PR-AUC = 0.0821
  * Random Forest: ROC-AUC = 0.8137, PR-AUC = 0.0934
  * IMPORTANT: GroupKFold metrics must NOT be presented as future-time performance.
- Operational Status: ADVISORY DIAGNOSTIC ONLY.
- Safety Guardrail: It must NEVER be used to trigger automated operational alarms,
  mortality alerts, or emergency interventions due to high false alarm rates.
"""

from pathlib import Path
from typing import Dict, Any, Union, Optional, List
import joblib
import numpy as np
import pandas as pd

from app.config import MODEL_PATHS
from app.core.chemistry import calculate_nh3_from_tan_n

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
    "region",
    "primary_calculated_nh3_mg_l"
]

CORE_REQUIRED_KEYS: List[str] = ["dissolved_oxygen_mg_l", "ph", "temp_c"]


class FishMortalityDiagnosticModel:
    """
    Inference wrapper for the Experiment 2 Fish Mortality Diagnostic model.
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_path = model_path or MODEL_PATHS.get("exp2_mortality_lr")
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
            self._load_error = f"Failed to load Experiment 2 model artifact: {exc}"

    @property
    def is_loaded(self) -> bool:
        """Returns True if the pipeline is loaded and ready for inference."""
        return self.pipeline is not None

    def get_metadata(self) -> Dict[str, Any]:
        """Returns model metadata, status, and verified benchmark metrics."""
        return {
            "model_identifier": "experiment_2_mortality_diagnostic",
            "model_title": "Experiment 2: Fish Mortality Diagnostic (Balanced Logistic Regression)",
            "status": "ADVISORY_DIAGNOSTIC_ONLY",
            "is_operational_baseline": False,
            "artifact_path": str(self.model_path),
            "is_loaded": self.is_loaded,
            "load_error": self._load_error,
            "target_variable": "dead_fish_flag (dead_fish_count > 0)",
            "input_features": EXPECTED_FEATURES,
            "warning": (
                "ADVISORY DIAGNOSTIC ONLY: Evaluates concurrent statistical association between "
                "environmental water parameters and mortality events. Due to extreme natural "
                "class imbalance (1.69% test prevalence) and low precision (chronological holdout "
                "PR-AUC = 0.0499, precision = 3.81%), this model generates frequent false alarms "
                "(227 false alarms vs. 9 true detections). It must NOT be used to trigger automated "
                "operational mortality alerts."
            ),
            "limitations": [
                "Extreme natural class imbalance: 67 negative visits for every 1 mortality observation.",
                "High false alarm rate: A positive prediction has low positive predictive value (PPV < 4% on holdout).",
                "Non-water mortality drivers (pathogens, viral outbreaks, biosecurity failures, aeration mechanical breakdown) are not captured.",
                "Must be treated strictly as an advisory severity indicator, not an automated warning system."
            ],
            "chronological_holdout_benchmark": {
                "cohort": "2025–2026 Holdout Test (N = 2,600, Positives = 44, Prevalence = 1.69%)",
                "no_skill_baseline_pr_auc": 0.0169,
                "logistic_regression": {
                    "roc_auc": 0.5917,
                    "pr_auc": 0.0499,
                    "recall": 0.2045,
                    "precision": 0.0381,
                    "f1_score": 0.0643,
                    "true_positives": 9,
                    "false_positives": 227
                },
                "random_forest_tuned": {
                    "roc_auc": 0.7322,
                    "pr_auc": 0.0648,
                    "recall": 0.1364,
                    "precision": 0.1154,
                    "f1_score": 0.1250,
                    "true_positives": 6,
                    "false_positives": 46
                }
            },
            "spatial_groupkfold_reference": {
                "cohort": "5-Fold GroupKFold OOF across all historical dates (N = 5,122, Positives = 75, Prev = 1.46%)",
                "logistic_regression": {"roc_auc": 0.7712, "pr_auc": 0.0821},
                "random_forest": {"roc_auc": 0.8137, "pr_auc": 0.0934},
                "caution": "GroupKFold metrics evaluate spatial cross-validation and MUST NOT be presented as future temporal forecasting ability."
            }
        }

    def validate_and_prepare_features(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> pd.DataFrame:
        """
        Validates input features and constructs a single-row DataFrame
        conforming to the pipeline's exact expected column names and order.
        """
        if isinstance(features, pd.DataFrame):
            df_in = features.copy()
        elif isinstance(features, dict):
            df_in = pd.DataFrame([features])
        else:
            raise TypeError(f"Features must be dict or pd.DataFrame, received: {type(features)}")

        # Check required core keys
        missing_keys = [k for k in CORE_REQUIRED_KEYS if k not in df_in.columns]
        if missing_keys:
            raise ValueError(
                f"Missing required core input features for Experiment 2 Diagnostic: {missing_keys}. "
                f"Core keys required: {CORE_REQUIRED_KEYS}"
            )

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

        # Ammonia feature: use primary_calculated_nh3_mg_l if provided, or derive from TAN
        if "primary_calculated_nh3_mg_l" in df_in.columns and pd.notna(df_in["primary_calculated_nh3_mg_l"].iloc[0]):
            clean_row["primary_calculated_nh3_mg_l"] = float(df_in["primary_calculated_nh3_mg_l"].iloc[0])
        elif "tan_n_mg_l" in df_in.columns and pd.notna(df_in["tan_n_mg_l"].iloc[0]):
            clean_row["primary_calculated_nh3_mg_l"] = calculate_nh3_from_tan_n(
                df_in["tan_n_mg_l"].iloc[0], clean_row["ph"], clean_row["temp_c"]
            )
        else:
            clean_row["primary_calculated_nh3_mg_l"] = np.nan

        df_prepared = pd.DataFrame([clean_row])[EXPECTED_FEATURES]
        return df_prepared

    def predict(self, features: Union[Dict[str, Any], pd.DataFrame]) -> Dict[str, Any]:
        """
        Executes mortality diagnostic classification and returns risk probability score.
        """
        if not self.is_loaded:
            raise RuntimeError(
                f"Experiment 2 Diagnostic model is not loaded: {self._load_error}. "
                "Ensure the model artifact exists in 'experiment_2_mortality_v1/models/'."
            )

        df_prepared = self.validate_and_prepare_features(features)

        try:
            # Predict probabilities: class 1 is mortality occurrence
            proba = self.pipeline.predict_proba(df_prepared)[0]
            risk_score = round(float(proba[1]), 4)
            is_valid = True
        except Exception:
            risk_score = np.nan
            is_valid = False

        meta = self.get_metadata()
        return {
            "mortality_risk_score": risk_score,
            "model_name": meta["model_title"],
            "status": meta["status"],
            "is_valid": is_valid,
            "features_used": df_prepared.to_dict(orient="records")[0],
            "warning": meta["warning"],
            "limitations": meta["limitations"],
            "disclaimer": (
                "Advisory diagnostic flag only. Never use as an autonomous warning or mortality alert."
            )
        }
