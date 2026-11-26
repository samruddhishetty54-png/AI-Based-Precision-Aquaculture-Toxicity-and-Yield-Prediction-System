"""Helper functions, formatting utilities, and defensive validation logic for the dashboard.

All functions uphold the project's strict scientific principles:
- Discrete multi-week inspection horizon (3-45 days, 06:00-08:30 AM morning observations).
- Clear segregation of simulated vs historical field observations.
- Defensive software bounds are never portrayed as validated biological safety limits.
"""

from typing import Any, Dict, Optional, Tuple, Union
import math

# Formal Operational Categories
CATEGORIES: Dict[str, Dict[str, str]] = {
    "HISTORICAL": {
        "label": "Historical Field Observations",
        "description": "Empirical multi-week commercial pond inspection records.",
        "badge_class": "category-historical",
    },
    "BENCHMARK": {
        "label": "Model Benchmarks",
        "description": "Prospective analytical baselines (e.g. historical mean DO, weight persistence).",
        "badge_class": "category-benchmark",
    },
    "EXPERIMENTAL": {
        "label": "Experimental Screening Results",
        "description": "Exploratory machine learning models with documented empirical error profiles.",
        "badge_class": "category-experimental",
    },
    "SIMULATED": {
        "label": "Simulated Scenarios (Non-Operational)",
        "description": "Synthetic benchmark models for demonstration and stress-testing only.",
        "badge_class": "category-simulated",
    },
    "ADVISORY": {
        "label": "Provisional Advisories",
        "description": "Rule-based decision-support heuristics requiring qualified human verification.",
        "badge_class": "category-advisory",
    },
}

# Software Defensive Validation Bounds
# NOTE: These represent software boundary checks to catch numeric corruption,
# parsing faults, or physical impossibilities. They are NOT biological safety limits.
DEFENSIVE_BOUNDS: Dict[str, Tuple[float, float, str]] = {
    "do": (0.0, 25.0, "mg/L"),
    "ph": (0.0, 14.0, "pH"),
    "water_temp": (10.0, 45.0, "°C"),
    "tan": (0.0, 20.0, "mg/L"),
    "turbidity": (0.0, 150.0, "cm"),
    "tds": (0.0, 50.0, "ppt"),
    "fish_weight": (0.01, 5000.0, "g/fish"),
    "daily_feed": (0.0, 2000.0, "kg/day"),
    "revisit_interval": (3.0, 45.0, "days"),
}


def format_float(val: Any, decimals: int = 2, unit: str = "") -> str:
    """Format numeric values safely with units; returns 'N/A' on NaN or None."""
    if val is None:
        return "N/A"
    try:
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return "N/A"
        formatted = f"{f_val:.{decimals}f}"
        return f"{formatted} {unit}".strip() if unit else formatted
    except (ValueError, TypeError):
        return "N/A"


def format_percentage(val: Any, decimals: int = 1) -> str:
    """Format decimal probability/ratio (0.0 - 1.0) as percentage."""
    if val is None:
        return "N/A"
    try:
        f_val = float(val)
        if math.isnan(f_val) or math.isinf(f_val):
            return "N/A"
        return f"{f_val * 100.0:.{decimals}f}%"
    except (ValueError, TypeError):
        return "N/A"


def detect_simulation_source(
    source_identifier: Optional[str] = None,
    is_simulated_flag: bool = False,
) -> Tuple[bool, str, bool]:
    """Detect whether an input or dataset is synthetic / simulated.

    Returns:
        (is_simulated, status_tag, operational_use_permitted)
    """
    if is_simulated_flag:
        return True, "SIMULATED_SCENARIO_ONLY", False

    if source_identifier:
        lower_id = str(source_identifier).lower()
        if any(marker in lower_id for marker in ["simulat", "synthetic", "iot_water_model", "benchmark_sim"]):
            return True, "SIMULATED_SCENARIO_ONLY", False

    return False, "FIELD_OBSERVATION", True


def validate_defensive_bounds(
    param_name: str,
    value: Union[int, float],
) -> Tuple[bool, Optional[str]]:
    """Validate numeric input against software defensive bounds.

    CRITICAL GOVERNANCE NOTE:
    These boundaries are software defensive constraints to reject unphysical
    measurements or entry errors. They are NOT validated biological safety
    thresholds or physiological tolerance limits.
    """
    key = param_name.lower().strip()
    if key not in DEFENSIVE_BOUNDS:
        return True, None

    min_val, max_val, unit = DEFENSIVE_BOUNDS[key]
    try:
        val = float(value)
    except (ValueError, TypeError):
        return False, f"Invalid numeric input for {param_name}: '{value}'."

    if math.isnan(val):
        return True, None  # Graceful missingness

    if val < min_val:
        return False, (
            f"Value {val} {unit} is below the defensive software bound ({min_val} {unit}) "
            f"for {param_name}. Please inspect data entry."
        )
    if val > max_val:
        return False, (
            f"Value {val} {unit} exceeds the defensive software bound ({max_val} {unit}) "
            f"for {param_name}. Please inspect data entry."
        )

    return True, None


def get_registry_health_summary(registry: Any) -> Dict[str, Any]:
    """Extract health status and model availability safely from ModelRegistry."""
    try:
        health = registry.health_check()
        models_dict = health.get("models", {})
        total_registered = health.get("total_registered", len(models_dict))
        total_loaded = health.get("total_loaded", sum(1 for m in models_dict.values() if m.get("loaded")))
        all_loaded = health.get("all_models_loaded", total_loaded == total_registered and total_registered > 0)

        return {
            "status": "HEALTHY" if all_loaded else "DEGRADED",
            "ready_count": total_loaded,
            "total_count": total_registered,
            "model_health": models_dict,
            "registered_models": list(models_dict.keys()),
        }
    except Exception as exc:
        return {
            "status": "UNAVAILABLE",
            "ready_count": 0,
            "total_count": 0,
            "error": str(exc),
            "model_health": {},
            "registered_models": [],
        }


# =======================================================================
# Farm Type (Indoor / Outdoor) & Prediction History Logging Utilities
# =======================================================================

FARM_TYPES = ["Outdoor Aquaculture", "Indoor Aquaculture"]
DEFAULT_FARM_TYPE = "Outdoor Aquaculture"
FREE_PLATFORM_NOTICE = (
    "Precision AquaDSS is a free aquaculture decision-support platform. "
    "All available features are accessible without subscription charges."
)


def get_active_farm_type() -> str:
    """Return the currently selected farm type from session state."""
    try:
        import streamlit as st
        val = st.session_state.get("active_farm_type") or st.session_state.get("farm_type")
        return val if val else DEFAULT_FARM_TYPE
    except Exception:
        return DEFAULT_FARM_TYPE


def get_container_label(farm_type: Optional[str] = None) -> str:
    """Return 'Tank' for indoor aquaculture or 'Pond' for outdoor."""
    f_type = farm_type or get_active_farm_type()
    return "Tank" if "indoor" in f_type.lower() else "Pond"


def get_container_id_label(farm_type: Optional[str] = None) -> str:
    """Return 'Tank Identifier' for indoor or 'Pond Identifier' for outdoor."""
    f_type = farm_type or get_active_farm_type()
    return "Tank Identifier" if "indoor" in f_type.lower() else "Pond Identifier"


def get_farm_type_disclaimer(farm_type: Optional[str] = None) -> str:
    """Return scientific applicability disclaimer based on farm type."""
    f_type = farm_type or get_active_farm_type()
    if "indoor" in f_type.lower():
        return (
            "Indoor Aquaculture Mode Active: Models were trained on outdoor commercial pond observation logs. "
            "Predictions for indoor recirculating / tank systems serve as exploratory decision-support proxies "
            "and require independent manual or sensor verification."
        )
    return (
        "Outdoor Aquaculture Mode Active: Observations reflect open commercial pond conditions subject to "
        "weather exposure, diurnal cycling, and multi-week routine visits (06:00–08:30 AM)."
    )


def log_prediction_event(
    analysis_type: str,
    container_id: str,
    data_source: str,
    is_simulated: bool,
    results_summary: str,
    details: Optional[Dict[str, Any]] = None,
    farm_type: Optional[str] = None,
) -> None:
    """Log an analysis run or prediction event to session history.

    Maintains session-level traceability across all 9 dashboard pages.
    """
    try:
        import streamlit as st
        import datetime

        history = st.session_state.setdefault("prediction_history", [])
        active_farm = farm_type or get_active_farm_type()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "timestamp": now_str,
            "farm_type": active_farm,
            "analysis_type": analysis_type,
            "container_id": container_id,
            "data_source": data_source,
            "is_simulated": "YES (Simulation)" if is_simulated else "NO (Field/Real)",
            "results_summary": results_summary,
        }
        if details:
            for k, v in details.items():
                if k not in entry:
                    entry[k] = v

        # Deduplicate identical recent entry in the same session
        if history:
            last = history[-1]
            if (
                last.get("analysis_type") == entry["analysis_type"]
                and last.get("container_id") == entry["container_id"]
                and last.get("results_summary") == entry["results_summary"]
                and last.get("is_simulated") == entry["is_simulated"]
            ):
                return

        history.append(entry)
    except Exception:
        pass

