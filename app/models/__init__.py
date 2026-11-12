"""
Machine Learning Model Services & Registry - Phase 2 Foundation
AI-Based Precision Aquaculture Toxicity and Yield Prediction System

Wraps audited models from Experiments 1–3 with explicit scientific disclaimers,
feature validation, and baseline fallbacks.
"""

from app.models.registry import ModelRegistry, get_model_registry

__all__ = ["ModelRegistry", "get_model_registry"]

