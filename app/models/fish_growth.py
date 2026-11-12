"""
Fish Growth Prediction Module - Phase 3 Foundation
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Wraps the audited operational fish growth baseline from Experiment 4.

Scientific Constraints & Governance:
- Target Variable: Next-visit average fish body weight (grams/fish).
- Operational Model: Persistence Baseline (predicted next weight = current observed weight, W_hat_{t+1} = W_t).
- Audit Ground Truth (Experiment 4):
  * On the unfiltered commercial operational population (N = 1,689 test pairs),
    Persistence is the superior operational model (MAE = 93.38 g, RMSE = 196.48 g, R² = 0.7135).
  * Machine learning models (Random Forest MAE = 112.15 g, Gradient Boosting MAE = 127.34 g)
    failed significantly (p < 10^-12) because they assume continuous growth and cannot foresee
    unrecorded commercial partial harvests, net thinning, or cycle terminations.
  * Suspicious-pair filtering in Experiment 4 relied on future target leakage (next_weight) and
    is strictly a retrospective exploratory analysis; it cannot be deployed at inference time.
- Prediction Scope: Next-visit average weight estimate only.
- Strict Prohibitions:
  * NEVER brand this module as "Harvest Yield Prediction" (dataset has 0% total yield labels).
  * NEVER claim reliable long-term harvest prediction or individual fish growth trajectories.
  * NEVER invent artificial yield labels or synthetic growth curves.
"""

from typing import Dict, Any, Union
import numpy as np
import pandas as pd


class FishGrowthModel:
    """
    Operational inference wrapper for Next-Visit Average Fish Weight Prediction.
    
    Implements the audited Persistence Baseline validated in Experiment 4.
    """

    def __init__(self):
        self.model_identifier = "experiment_4_fish_weight_persistence"
        self.model_title = "Experiment 4: Next-Visit Average Fish Weight (Persistence Baseline)"
        self.status = "OPERATIONAL_PERSISTENCE_BASELINE"

    @property
    def is_loaded(self) -> bool:
        """The persistence baseline is an analytical operational baseline and is always ready."""
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns scientific metadata, operational benchmarks, and empirical limitations.
        """
        return {
            "model_identifier": self.model_identifier,
            "model_title": self.model_title,
            "status": self.status,
            "is_operational_baseline": True,
            "target_variable": "next_visit_average_fish_weight_g (average weight in grams at next routine visit)",
            "prediction_horizon": "Next routine visit (irregular interval, 3 to 45 days, median 22 days)",
            "primary_predictor": "Persistence Baseline (W_hat_{t+1} = W_t)",
            "warning": (
                "OPERATIONAL PERSISTENCE BASELINE: Predicted next-visit average fish weight equals "
                "the current observed weight. In the Experiment 4 operational audit, machine learning "
                "regressors failed to outperform persistence on commercial ponds due to unrecorded "
                "partial harvests and management interventions (Persistence MAE = 93.38 g vs. Random "
                "Forest MAE = 112.15 g). This module estimates somatic average body weight per fish, "
                "NOT total commercial harvest yield (kg/ha) or individual fish growth trajectories."
            ),
            "limitations": [
                "Assumes weight remains static across the revisit interval; does not simulate biological growth increments.",
                "Cannot anticipate unrecorded commercial partial harvests, pond draining, or restocking events.",
                "Does NOT predict commercial harvest yield, total pond-level biomass production, or economic harvest date.",
                "Retrospective exploratory ML models (GBDT Clean MAE = 57.22 g) require unobservable future target filtering and cannot be deployed operationally."
            ],
            "experiment_4_benchmarks": {
                "evaluation_population": "All Pairs Operational Chronological Test Set (N = 1,689 pairs)",
                "persistence_baseline": {
                    "mae_g": 93.38,
                    "rmse_g": 196.48,
                    "r2": 0.7135,
                    "operational_verdict": "Designated Operational Primary Baseline"
                },
                "random_forest_exploratory": {
                    "mae_g": 112.15,
                    "rmse_g": 199.16,
                    "r2": 0.7056,
                    "operational_verdict": "Significantly Inferior to Persistence (p = 2.0e-13)"
                },
                "gradient_boosting_exploratory": {
                    "mae_g": 127.34,
                    "rmse_g": 215.17,
                    "r2": 0.6558,
                    "operational_verdict": "Significantly Inferior to Persistence (p = 1.9e-20)"
                }
            }
        }

    def validate_inputs(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> float:
        """
        Validates input features and extracts current average fish weight.

        Parameters:
            features: Dictionary or DataFrame containing current weight measurement.

        Returns:
            Validated current fish weight as float.

        Raises:
            ValueError: If weight is missing, non-numeric, or non-positive (<= 0).
        """
        if isinstance(features, pd.DataFrame):
            if features.empty:
                raise ValueError("Input DataFrame is empty.")
            row_dict = features.iloc[0].to_dict()
        elif isinstance(features, dict):
            row_dict = features
        else:
            raise ValueError(f"Features must be dict or DataFrame, got {type(features).__name__}.")

        # Supported aliases for current fish weight
        weight_aliases = [
            "current_weight_g",
            "curr_weight",
            "average_fish_weight_g",
            "weight_g",
            "Weight",
            "current_average_fish_weight_g"
        ]

        found_weight = None
        for alias in weight_aliases:
            if alias in row_dict and pd.notna(row_dict[alias]):
                found_weight = row_dict[alias]
                break

        if found_weight is None:
            raise ValueError(
                "Missing required fish weight measurement. Please provide 'current_weight_g' "
                f"or 'average_fish_weight_g'. Provided keys: {list(row_dict.keys())}"
            )

        try:
            numeric_weight = float(found_weight)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid fish weight value: {found_weight!r}. Must be a valid numeric quantity."
            ) from exc

        if np.isnan(numeric_weight):
            raise ValueError("Fish weight cannot be NaN.")

        if numeric_weight <= 0.0:
            raise ValueError(
                f"Fish weight must be strictly positive (> 0 grams). Received: {numeric_weight} g."
            )

        return numeric_weight

    def predict(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Predicts next-visit average fish weight using the audited Persistence Baseline.

        Parameters:
            features: Dictionary or DataFrame with current fish weight and optional context.

        Returns:
            Dictionary containing predicted next weight, metadata, and scientific disclaimers.

        Raises:
            ValueError: If input features fail validation.
        """
        curr_weight = self.validate_inputs(features)
        meta = self.get_metadata()

        # Optional context fields if provided
        context: Dict[str, Any] = {}
        if isinstance(features, dict):
            src_dict = features
        elif isinstance(features, pd.DataFrame) and not features.empty:
            src_dict = features.iloc[0].to_dict()
        else:
            src_dict = {}

        for k in ["pond_id", "species", "gap_days", "curr_do", "feed_amount_kg"]:
            if k in src_dict and pd.notna(src_dict[k]):
                context[k] = src_dict[k]

        return {
            "predicted_next_weight_g": float(curr_weight),
            "current_weight_g": float(curr_weight),
            "model_name": meta["model_title"],
            "status": meta["status"],
            "is_valid": True,
            "prediction_scope": "Next-visit average fish body weight (grams/fish). NOT commercial harvest yield or total biomass.",
            "context_features": context,
            "warning": meta["warning"],
            "limitations": meta["limitations"],
            "disclaimer": (
                "Operational baseline forecast. Predicts somatic individual body weight for the next inspection visit. "
                "Never interpret as commercial pond harvest yield or automated growth optimization."
            )
        }
