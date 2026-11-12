"""
Central Model Registry Module - Phase 2 & Phase 3 Integration
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Provides a unified, validated interface for accessing all completed models:
- Experiment 1: Ammonia Soft-Sensor (Random Forest)
- Experiment 2: Fish Mortality Diagnostic (Balanced Logistic Regression)
- Experiment 3: Next-Visit Ammonia Toxicity Risk (Random Forest)
- Experiment 4: Next-Visit Average Fish Weight (Persistence Baseline)
- Provisional Rule-Based Feeding Advisor & Observational Feedback Tracker

Strict Governance & Operational Rules:
1. Machine learning models are loaded read-only from pre-existing, audited .joblib artifacts.
2. Zero model training, fine-tuning, or parameter updates occur at startup or runtime.
3. Missing or corrupted model artifacts are reported explicitly; models are NEVER
   silently substituted with unvalidated fallbacks.
4. Model status, scientific disclaimers, and empirical limitations are permanently
   attached to all prediction outputs and registry health checks.
5. Feeding recommendations are strictly provisional decision-support advisory heuristics;
   no automated equipment control is executed.
"""

from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import pandas as pd

from app.models.exp1_soft_sensor import AmmoniaSoftSensorModel
from app.models.exp2_mortality import FishMortalityDiagnosticModel
from app.models.exp3_ammonia_risk import NextVisitAmmoniaRiskModel
from app.models.fish_growth import FishGrowthModel
from app.models.feeding_advisor import FeedingAdvisorModel, FeedingFeedbackTracker
from app.models.do_hypoxia import DOHypoxiaModel


class ModelRegistry:
    """
    Central model coordinator and registry for the aquaculture decision-support system.
    """

    def __init__(
        self,
        exp1_path: Optional[Path] = None,
        exp2_path: Optional[Path] = None,
        exp3_path: Optional[Path] = None,
        do_hypoxia_path: Optional[Path] = None,
    ):
        # Initialize model wrappers (lazy or immediate load)
        self.exp1_model = AmmoniaSoftSensorModel(model_path=exp1_path)
        self.exp2_model = FishMortalityDiagnosticModel(model_path=exp2_path)
        self.exp3_model = NextVisitAmmoniaRiskModel(model_path=exp3_path)
        self.fish_growth_model = FishGrowthModel()
        self.feeding_advisor_model = FeedingAdvisorModel()
        self.feedback_tracker = FeedingFeedbackTracker()
        self.do_hypoxia_model = DOHypoxiaModel(model_path=do_hypoxia_path)

        self._models = {
            "exp1_soft_sensor": self.exp1_model,
            "exp2_mortality": self.exp2_model,
            "exp3_ammonia_risk": self.exp3_model,
            "fish_growth": self.fish_growth_model,
            "feeding_advisor": self.feeding_advisor_model,
            "do_hypoxia": self.do_hypoxia_model,
        }

    def list_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Lists all registered models, their loading status, target variables, and limitations.
        """
        summary = {}
        for key, model in self._models.items():
            summary[key] = model.get_metadata()
        return summary

    def get_model(self, model_key: str) -> Any:
        """
        Retrieves a registered model wrapper by key.

        Raises:
            KeyError: If model_key is unrecognized.
        """
        if model_key not in self._models:
            raise KeyError(
                f"Unrecognized model key: '{model_key}'. "
                f"Available models: {list(self._models.keys())}"
            )
        return self._models[model_key]

    def get_model_status(self, model_key: str) -> Dict[str, Any]:
        """
        Returns the health, loading status, and metadata for a specific model.
        """
        model = self.get_model(model_key)
        return model.get_metadata()

    def health_check(self) -> Dict[str, Any]:
        """
        Performs a health check across all registered models.
        """
        status_report = {}
        all_ready = True

        for key, model in self._models.items():
            is_ready = model.is_loaded
            if not is_ready:
                all_ready = False
            
            artifact_path = str(getattr(model, "model_path", "internal_baseline_or_rules"))
            load_error = getattr(model, "_load_error", None)

            status_report[key] = {
                "loaded": is_ready,
                "status": model.get_metadata()["status"],
                "artifact_path": artifact_path,
                "error": load_error,
            }

        return {
            "all_models_loaded": all_ready,
            "total_registered": len(self._models),
            "total_loaded": sum(1 for m in self._models.values() if m.is_loaded),
            "models": status_report,
        }

    # High-level domain inference methods
    def predict_ammonia_soft_sensor(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Executes Experiment 1 Ammonia Soft-Sensor regression.
        """
        return self.exp1_model.predict(features)

    def predict_mortality_diagnostic(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Executes Experiment 2 Fish Mortality concurrent diagnostic.
        """
        return self.exp2_model.predict(features)

    def predict_next_visit_ammonia_risk(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Executes Experiment 3 Next-Visit Ammonia Toxicity Risk prognostic.
        """
        return self.exp3_model.predict(features)

    def predict_fish_growth(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Executes Experiment 4 Next-Visit Average Fish Weight persistence prediction.
        """
        return self.fish_growth_model.predict(features)

    def predict_do_hypoxia(
        self, features: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Executes Experiment 5 Next-Visit Morning DO & Hypoxia Risk evaluation.
        """
        return self.do_hypoxia_model.predict(features)

    def get_feeding_advisory(
        self, inputs: Union[Dict[str, Any], pd.DataFrame]
    ) -> Dict[str, Any]:
        """
        Executes rule-based provisional feeding advisory evaluation.
        """
        return self.feeding_advisor_model.evaluate_advisory(inputs)

    def record_feeding_feedback(
        self,
        pond_id: str,
        advisory_record: Dict[str, Any],
        actual_feed_kg: float,
        next_observation: Optional[Dict[str, Any]] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Records farmer feeding compliance and subsequent water quality observation.
        """
        return self.feedback_tracker.record_feedback(
            pond_id=pond_id,
            advisory_record=advisory_record,
            actual_feed_kg=actual_feed_kg,
            next_observation=next_observation,
            notes=notes
        )

    def get_feeding_feedback_records(
        self, pond_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieves observational feedback records.
        """
        return self.feedback_tracker.get_records(pond_id=pond_id)


# Global singleton instance
_GLOBAL_REGISTRY: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    """
    Returns the global singleton ModelRegistry instance.
    """
    global _GLOBAL_REGISTRY
    if _GLOBAL_REGISTRY is None:
        _GLOBAL_REGISTRY = ModelRegistry()
    return _GLOBAL_REGISTRY
