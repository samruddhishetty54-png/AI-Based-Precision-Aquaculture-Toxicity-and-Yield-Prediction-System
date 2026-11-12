"""
Experiment 5: Dissolved Oxygen & Hypoxia Module - Phase 4 Foundation
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Wraps the audited Experiment 5 models and analytical baselines:
1. Primary Operational Point Regression Benchmark:
   Historical Mean Baseline (unconditional training mean = 3.4984 mg/L ~ 3.50 mg/L).
2. Exploratory Moderate Hypoxia Classifier (< 3.0 mg/L):
   Gradient Boosting Classifier (exploratory risk-prioritization screening only).
3. Rejected Severe Hypoxia Classifier (< 2.0 mg/L):
   Random Forest Classifier (rejected as mathematically degenerate near-constant positive).

Scientific Constraints & Governance (Experiment 5 Final Audit):
- Prediction Horizon: Next-visit morning DO (routine inspection visits, 3 to 45 days,
  median ~21 days). Strictly NOT an hourly, diurnal, overnight, or real-time nadir prediction.
- Point Regression Reality: The Historical Mean Baseline achieved the lowest test error
  (MAE = 0.3963 mg/L, RMSE = 0.6450 mg/L) on commercial pond holdouts, significantly
  outperforming Persistence (MAE = 0.5334 mg/L, R² = -0.7071, p < 10^-12) and ML regressors
  (RF MAE = 0.4172 mg/L, GBDT MAE = 0.4260 mg/L). Point prediction is a constant training mean,
  NOT a dynamic biological or bioenergetic simulation.
- Hypoxia Screening Reality: At the frozen high-recall cutoff (p* = 0.090), the GBDT classifier
  detects 53.49% of crises (92/172), but triggers an unsustainable 50.25% alarm rate with a
  91.00% False Discovery Rate (930 false alarms out of 1,022 alerts). It is STRICTLY REJECTED
  as an automated binary alert trigger or equipment actuator, but retained as an exploratory
  ranking index for inspection queues.
- Severe Hypoxia Rejection: The Random Forest severe-hypoxia (< 2.0 mg/L) classifier flagged
  99.56% of test visits (2,025/2,034) as positive at p = 0.10 due to class_weight='balanced'
  probability inflation. It is REJECTED ENTIRELY as degenerate.
- Operational Guardrail: All recommendations are provisional decision-support heuristics.
  No automated aerator, pump, or equipment commands are executed (is_automatic_control = False).
- Simulation Guardrail: Simulated inputs yield status = 'SIMULATED_SCENARIO_ONLY' and
  operational_use_permitted = False.
"""

from pathlib import Path
from typing import Dict, Any, Union, Optional, List
import joblib
import numpy as np
import pandas as pd

from app.config import MODEL_PATHS

# Audited training mean DO from Experiment 5 (N = 3,066 training pairs, 2021–2024)
HISTORICAL_TRAIN_MEAN_DO: float = 3.4984  # Exact mean of next_do in train_pairs.csv (3.498369...)
HISTORICAL_TRAIN_MEAN_DISPLAY: float = 3.50

# Audited thresholds and cutoff benchmarks
MODERATE_HYPOXIA_THRESHOLD: float = 3.0  # mg/L
SEVERE_HYPOXIA_THRESHOLD: float = 2.0    # mg/L
FROZEN_HIGH_RECALL_THRESHOLD: float = 0.090  # p* (train recall >= 80%)
FROZEN_MAX_F1_THRESHOLD: float = 0.220       # p*
DEFAULT_PROB_THRESHOLD: float = 0.500

# Full feature inventory expected by Experiment 5 pipelines (31 features)
EXPECTED_NUMERIC_FEATURES: List[str] = [
    "curr_do", "curr_ph", "curr_temp_c", "curr_turbidity_cm", "curr_tds_ppt",
    "curr_feed_amount_kg", "curr_feed_per_acre_kg", "curr_stocking_density",
    "curr_weight", "curr_dead_fish", "curr_air_gulping", "curr_tail_splashing",
    "pond_area_acres", "depth_meters", "gap_days", "curr_time_hour",
    "day_of_year", "month"
]
EXPECTED_INDICATOR_FEATURES: List[str] = [
    "turbidity_is_missing", "tds_is_missing", "feed_is_missing",
    "density_is_missing", "species_is_missing", "weight_is_missing",
    "area_is_missing"
]
EXPECTED_CATEGORICAL_FEATURES: List[str] = [
    "curr_water_color", "curr_weather", "curr_species", "farm_equipment",
    "feed_type", "region"
]
ALL_EXPECTED_FEATURES: List[str] = (
    EXPECTED_NUMERIC_FEATURES + EXPECTED_INDICATOR_FEATURES + EXPECTED_CATEGORICAL_FEATURES
)

# Common key aliases for robust input resolution
DO_ALIASES: List[str] = [
    "curr_do", "dissolved_oxygen_mg_l", "DO (mg/L)", "do_mg_l", "DO", "current_do"
]
PH_ALIASES: List[str] = ["curr_ph", "ph", "pH"]
TEMP_ALIASES: List[str] = ["curr_temp_c", "curr_temp", "temp_c", "Temp (in °C)", "temperature_c"]
FEED_ALIASES: List[str] = ["curr_feed_amount_kg", "feed_amount_kg", "Feed amount (kg)", "feed_kg", "baseline_feed_kg"]
WEIGHT_ALIASES: List[str] = ["curr_weight", "average_fish_weight_g", "current_weight_g", "weight_g", "Weight"]
DENSITY_ALIASES: List[str] = ["curr_stocking_density", "stocking_density_per_acre", "density_per_acre"]
AREA_ALIASES: List[str] = ["pond_area_acres", "Pond area in acres", "pond_acres", "acres"]
GAP_ALIASES: List[str] = ["gap_days", "revisit_interval_days", "days"]


class DOHypoxiaModel:
    """
    Inference and advisory wrapper for Experiment 5 Dissolved Oxygen and Hypoxia Risk.

    Integrates:
    - Operational Primary Point Baseline: Historical Training Mean DO (3.50 mg/L).
    - Exploratory Moderate Hypoxia Screening (< 3.0 mg/L, Gradient Boosting).
    - Fully Documented Rejection of Severe Hypoxia (< 2.0 mg/L, Random Forest).
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model_identifier = "experiment_5_do_hypoxia"
        self.model_title = "Experiment 5: Next-Visit Morning DO & Hypoxia Risk"
        self.status = "OPERATIONAL_HISTORICAL_MEAN_POINT_BENCHMARK"
        self.model_path = model_path or MODEL_PATHS.get("exp5_hypoxia_gb")
        self.pipeline = None
        self._load_error: Optional[str] = None
        self._explicit_path_passed = model_path is not None
        self.load_model()

    def load_model(self) -> None:
        """
        Attempts to load an optional pre-trained Gradient Boosting classifier pipeline.
        If no path is provided or the artifact is absent, point regression continues
        operating via the audited historical mean baseline.
        """
        if self.model_path is None or not Path(self.model_path).exists():
            self.pipeline = None
            if self.model_path is not None:
                self._load_error = f"Model artifact not found at: '{self.model_path}'"
            else:
                self._load_error = None
            return

        try:
            self.pipeline = joblib.load(self.model_path)
            self._load_error = None
        except Exception as exc:
            self.pipeline = None
            self._load_error = f"Failed to load Experiment 5 classifier artifact: {exc}"

    @property
    def is_loaded(self) -> bool:
        """
        Returns True if the model is ready.
        If an explicit artifact path was provided and failed, returns False.
        Otherwise, returns True because the audited Historical Mean point baseline
        is an analytical operational baseline and is always ready.
        """
        if self._explicit_path_passed and self.pipeline is None and self._load_error is not None:
            return False
        return True

    @property
    def is_classifier_loaded(self) -> bool:
        """Returns True if the optional exploratory ML classifier pipeline is loaded."""
        return self.pipeline is not None

    def get_metadata(self) -> Dict[str, Any]:
        """
        Returns scientific metadata, operational benchmarks, and empirical limitations.
        """
        return {
            "model_identifier": self.model_identifier,
            "model_title": self.model_title,
            "status": self.status,
            "is_operational_baseline": True,
            "is_classifier_loaded": self.is_classifier_loaded,
            "artifact_path": str(self.model_path) if self.model_path else "internal_historical_mean_baseline",
            "load_error": self._load_error,
            "prediction_horizon": (
                "Next routine morning inspection visit (irregular interval, 3 to 45 days, "
                "mean 21.8 days, median 21.0 days; 06:00–08:30 AM). "
                "Strictly NOT an hourly, diurnal, overnight, or real-time nadir forecast."
            ),
            "target_variable_continuous": "next_do (morning dissolved oxygen in mg/L at next inspection)",
            "target_variable_hypoxia": "next_hypoxia_3 (binary indicator of moderate hypoxia next_do < 3.0 mg/L)",
            "primary_point_predictor": "Historical Training Mean Baseline (unconditional 3.50 mg/L)",
            "warning": (
                "OPERATIONAL HISTORICAL MEAN POINT BENCHMARK & EXPLORATORY SCREENING ONLY: "
                "Predicted next-visit DO is an unconditional historical training mean (3.50 mg/L), "
                "NOT a dynamic biological or bioenergetic prediction. In the Experiment 5 audit, "
                "the historical mean achieved the lowest test error (MAE = 0.3963 mg/L) on commercial ponds, "
                "significantly outperforming persistence (MAE = 0.5334 mg/L, p < 10^-12) and ML regressors "
                "(RF MAE = 0.4172 mg/L, GBDT MAE = 0.4260 mg/L). Hypoxia risk classification (GBDT < 3.0 mg/L) "
                "is strictly an exploratory screening tool for inspection ranking; at the high-recall cutoff "
                "(p* = 0.090), it exhibits a 50.25% alarm rate and a 91.00% False Discovery Rate. It must NEVER "
                "be used as an automated alert trigger, aeration actuator control, or emergency alarm. The severe "
                "hypoxia (< 2.0 mg/L) Random Forest classifier was REJECTED AS DEGENERATE (99.56% alarm rate due "
                "to class_weight='balanced' probability inflation)."
            ),
            "limitations": [
                "Historical mean baseline is constant (3.50 mg/L); it does not forecast pond-specific diurnal drops or oxygen crashes.",
                "Prediction horizon is discrete multi-week routine visits (3–45 days); it is NOT an hourly, overnight, or continuous sensor forecast.",
                "Exploratory GBDT hypoxia classifier triggers 91.00% false alarms at p*=0.090 and must not be used for automated equipment control.",
                "Severe hypoxia (< 2.0 mg/L) Random Forest classifier is rejected due to degenerate near-constant-positive behavior.",
                "Simulated inputs must never guide commercial aeration or farm operations."
            ],
            "experiment_5_benchmarks": {
                "evaluation_population": "Prospective Chronological Test Set (N = 2,034 pairs, 167 ponds, 2025–2026)",
                "regression_models": {
                    "historical_mean_baseline": {
                        "mae_mg_l": 0.3963,
                        "rmse_mg_l": 0.6450,
                        "delta_mae_vs_persistence": -0.1372,
                        "clustered_ci_95": "[-0.1557, -0.1187] (p < 10^-12)",
                        "operational_verdict": "Retained as Operational Point Regression Benchmark"
                    },
                    "persistence_baseline": {
                        "mae_mg_l": 0.5334,
                        "rmse_mg_l": 0.8237,
                        "r2": -0.7071,
                        "operational_verdict": "Rejected as Operational Model (Negative R2, misses 90.7% hypoxia)"
                    },
                    "random_forest_regressor": {
                        "mae_mg_l": 0.4172,
                        "rmse_mg_l": 0.6602,
                        "delta_mae_vs_hist_mean": +0.0209,
                        "operational_verdict": "Exploratory Bioenergetic Model Only (Inferior to Historical Mean)"
                    },
                    "gradient_boosting_regressor": {
                        "mae_mg_l": 0.4260,
                        "rmse_mg_l": 0.6668,
                        "delta_mae_vs_hist_mean": +0.0298,
                        "operational_verdict": "Exploratory Bioenergetic Model Only (Inferior to Historical Mean)"
                    }
                },
                "moderate_hypoxia_classification": {
                    "model": "Gradient Boosting Classifier (< 3.0 mg/L)",
                    "operational_status": "Exploratory Risk-Prioritization Screening Only",
                    "test_pr_auc": 0.0950,
                    "no_skill_baseline": 0.0846,
                    "test_roc_auc": 0.5328,
                    "clustered_ci_95": "[-0.0022, +0.0316] (Spans zero, p = 0.086)",
                    "high_recall_threshold_p009": {
                        "threshold_p": 0.090,
                        "recall": 0.5349,
                        "false_discovery_rate": 0.9100,
                        "alarm_rate_pct": 50.25,
                        "true_positives": 92,
                        "false_positives": 930
                    },
                    "max_f1_threshold_p022": {
                        "threshold_p": 0.220,
                        "recall": 0.0930,
                        "false_discovery_rate": 0.9080,
                        "alarm_rate_pct": 8.55,
                        "true_positives": 16,
                        "false_positives": 158
                    }
                },
                "severe_hypoxia_rejection": {
                    "model": "Random Forest Classifier (< 2.0 mg/L Severe Hypoxia)",
                    "operational_verdict": "REJECTED ENTIRELY AS DEGENERATE",
                    "cutoff_p010": {
                        "alarm_rate_pct": 99.56,
                        "flagged_visits": "2,025 / 2,034",
                        "true_positives": 91,
                        "false_positives": 1934,
                        "specificity": 0.0041,
                        "mathematical_cause": "class_weight='balanced' probability inflation shifted empirical distribution above cutoff"
                    }
                }
            }
        }

    def _extract_first_numeric(
        self, data: Dict[str, Any], aliases: List[str]
    ) -> Optional[float]:
        """Safely extracts a numeric float value from multiple key aliases."""
        for alias in aliases:
            if alias in data and pd.notna(data[alias]):
                try:
                    val = float(data[alias])
                    if not (np.isnan(val) or np.isinf(val)):
                        return val
                except (ValueError, TypeError):
                    continue
        return None

    def validate_inputs(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Validates input features for physical realism and completeness.

        Raises:
            ValueError: If inputs are invalid, non-physical, infinite, or missing mandatory DO.
        """
        if isinstance(features, pd.DataFrame):
            if features.empty:
                raise ValueError("Input DataFrame is empty.")
            row_dict = features.iloc[0].to_dict()
        elif isinstance(features, dict):
            row_dict = features
        else:
            raise ValueError(f"Features must be dict or DataFrame, got {type(features).__name__}.")

        # 1. Mandatory Initial Dissolved Oxygen (curr_do)
        raw_do = None
        for alias in DO_ALIASES:
            if alias in row_dict:
                raw_do = row_dict[alias]
                break

        if raw_do is None:
            raise ValueError(
                "Missing required core input feature 'curr_do' (or 'dissolved_oxygen_mg_l'). "
                "Cannot forecast next-visit DO without current morning baseline reading."
            )

        try:
            curr_do = float(raw_do)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"Invalid dissolved oxygen measurement: {raw_do!r}. Must be a valid numeric quantity."
            ) from exc

        if np.isnan(curr_do):
            raise ValueError("Dissolved oxygen cannot be NaN.")
        if np.isinf(curr_do):
            raise ValueError("Dissolved oxygen cannot be infinite.")
        if curr_do < 0.0:
            raise ValueError(f"Dissolved oxygen cannot be negative. Received: {curr_do} mg/L.")
        if curr_do > 25.0:
            raise ValueError(
                f"Dissolved oxygen exceeds physical aquaculture saturation bounds (> 25.0 mg/L). Received: {curr_do} mg/L."
            )

        # 2. Water Temperature (optional, physical bounds check)
        raw_temp = self._extract_first_numeric(row_dict, TEMP_ALIASES)
        if raw_temp is not None:
            if raw_temp <= -273.15 or raw_temp > 60.0:
                raise ValueError(
                    f"Water temperature is physically impossible. Received: {raw_temp} °C."
                )

        # 3. Water pH (optional, physical bounds check)
        raw_ph = self._extract_first_numeric(row_dict, PH_ALIASES)
        if raw_ph is not None:
            if raw_ph < 0.0 or raw_ph > 14.0:
                raise ValueError(
                    f"Water pH must be within physical range (0.0 to 14.0). Received: {raw_ph}."
                )

        # 4. Revisit Interval Gap Days (optional, physical bounds check)
        raw_gap = self._extract_first_numeric(row_dict, GAP_ALIASES)
        if raw_gap is not None:
            if raw_gap <= 0.0:
                raise ValueError(
                    f"Revisit interval gap_days must be strictly positive (> 0 days). Received: {raw_gap}."
                )

        return row_dict

    def predict(
        self,
        features: Union[Dict[str, Any], pd.DataFrame],
        require_classifier: bool = False,
        safe_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Executes next-visit DO forecasting and exploratory hypoxia screening.

        Parameters:
            features: Dictionary or DataFrame containing current water sensor observations.
            require_classifier: If True, raises RuntimeError when classifier artifact is not loaded.
            safe_mode: If True, returns an error dict on validation failure instead of raising ValueError.

        Returns:
            Dictionary containing point prediction, exploratory screening scores, and disclaimers.
        """
        if safe_mode:
            try:
                row_dict = self.validate_inputs(features)
            except ValueError as exc:
                return {
                    "is_valid": False,
                    "status": "INVALID_PHYSICAL_MEASUREMENT",
                    "explanation": str(exc),
                    "operational_use_permitted": False,
                    "is_automatic_control": False
                }
        else:
            row_dict = self.validate_inputs(features)

        curr_do = self._extract_first_numeric(row_dict, DO_ALIASES)
        gap_days = self._extract_first_numeric(row_dict, GAP_ALIASES)

        # Simulation Detection Guardrail
        data_source = str(row_dict.get("data_source", "field_inspection")).lower()
        raw_is_sim = row_dict.get("is_simulated", False)
        if isinstance(raw_is_sim, str):
            flag_sim = raw_is_sim.strip().lower() in ("true", "1", "yes")
        else:
            flag_sim = bool(raw_is_sim)
        is_simulated = bool(flag_sim or "simulat" in data_source or "synthetic" in data_source)

        meta = self.get_metadata()

        # Handle optional classifier inference
        gb_prob: Optional[float] = None
        if self.pipeline is not None:
            try:
                df_input = pd.DataFrame([row_dict])
                # Ensure all expected columns exist
                for col in ALL_EXPECTED_FEATURES:
                    if col not in df_input.columns:
                        df_input[col] = np.nan
                probs = self.pipeline.predict_proba(df_input[ALL_EXPECTED_FEATURES])[:, 1]
                gb_prob = float(probs[0])
            except Exception as exc:
                gb_prob = None
        elif require_classifier:
            raise RuntimeError(
                f"Classifier pipeline is not loaded: {self._load_error or 'No artifact loaded.'}"
            )

        # Status and Operational Gating
        if is_simulated:
            status_label = "SIMULATED_SCENARIO_ONLY"
            operational_permitted = False
            demonstration_notice = (
                "SIMULATED SCENARIO ONLY (DEMONSTRATION): This output was generated from synthetic or "
                "simulated benchmark data. It is intended strictly for model demonstration and testing, "
                "and MUST NOT be used to guide actual commercial pond management, aeration decisions, "
                "or live biological operations."
            )
        else:
            status_label = "OPERATIONAL_HISTORICAL_MEAN_POINT_BENCHMARK"
            operational_permitted = True
            demonstration_notice = None

        screening_flag: Optional[bool] = None
        if gb_prob is not None:
            screening_flag = bool(gb_prob >= FROZEN_HIGH_RECALL_THRESHOLD)

        return {
            "predicted_next_do_mg_l": round(float(HISTORICAL_TRAIN_MEAN_DO), 4),
            "predicted_next_do_display_mg_l": HISTORICAL_TRAIN_MEAN_DISPLAY,
            "point_prediction_method": "Historical Training Mean Baseline (unconditional 3.50 mg/L)",
            "current_do_mg_l": float(curr_do) if curr_do is not None else None,
            "revisit_interval_days": float(gap_days) if gap_days is not None else 21.0,
            "prediction_horizon": (
                "Next routine morning inspection visit (3 to 45 days, median 21 days). "
                "NOT hourly, diurnal, or overnight nadir."
            ),
            "status": status_label,
            "is_valid": True,
            "operational_use_permitted": operational_permitted,
            "data_source": data_source,
            "is_simulated": is_simulated,
            "exploratory_hypoxia_screening": {
                "status": "EXPLORATORY_SCREENING_RANKING_ONLY",
                "hypoxia_risk_score": round(gb_prob, 4) if gb_prob is not None else None,
                "screening_threshold": FROZEN_HIGH_RECALL_THRESHOLD,
                "screening_flag": screening_flag,
                "classifier_loaded": self.is_classifier_loaded,
                "audit_warning": (
                    "EXPLORATORY SCREENING / RANKING ONLY: The Gradient Boosting hypoxia classifier (< 3.0 mg/L) "
                    "exhibits a 50.25% alarm rate and a 91.00% False Discovery Rate at the high-recall cutoff (p* = 0.090). "
                    "It must NEVER be used to trigger automated alarms, equipment actuators, or emergency interventions. "
                    "It is intended solely for retrospective exploratory ranking of inspection queues."
                ),
                "false_discovery_rate_pct": 91.00,
                "alarm_rate_pct": 50.25
            },
            "rejected_severe_hypoxia_model": {
                "model_title": "Random Forest Classifier (< 2.0 mg/L Severe Hypoxia)",
                "verdict": "REJECTED ENTIRELY AS DEGENERATE",
                "rationale": (
                    "In the Experiment 5 audit, the severe hypoxia Random Forest model flagged 99.56% of all test visits "
                    "(2,025 out of 2,034) as severe hypoxia at cutoff p = 0.10 (TP = 91, FP = 1,934, Specificity = 0.41%). "
                    "The apparent 98.91% recall was an artifact of class_weight='balanced' probability inflation acting as "
                    "a near-constant positive predictor with zero clinical discrimination."
                ),
                "alarm_rate_pct": 99.56
            },
            "is_automatic_control": False,
            "control_action": None,
            "warning": meta["warning"],
            "limitations": meta["limitations"],
            "demonstration_warning": demonstration_notice,
            "disclaimer": (
                "Operational baseline forecast and exploratory screening tool for human operator review only. "
                "Point estimate is an unconditional training mean, not a dynamic bioenergetic simulation. "
                "Never use for automated actuator control or independent emergency alerting."
            )
        }

    def predict_point_do(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Any]:
        """Convenience method returning the operational point DO forecast."""
        res = self.predict(features)
        return {
            "predicted_next_do_mg_l": res["predicted_next_do_mg_l"],
            "predicted_next_do_display_mg_l": res["predicted_next_do_display_mg_l"],
            "point_prediction_method": res["point_prediction_method"],
            "current_do_mg_l": res["current_do_mg_l"],
            "revisit_interval_days": res["revisit_interval_days"],
            "status": res["status"],
            "is_valid": res["is_valid"],
            "operational_use_permitted": res["operational_use_permitted"],
            "warning": res["warning"],
            "disclaimer": res["disclaimer"]
        }

    def predict_hypoxia_risk(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Convenience method returning exploratory hypoxia screening results.
        Raises RuntimeError if classifier pipeline artifact is not loaded.
        """
        return self.predict(features, require_classifier=True)

