"""Compatibility forwarder for app.dashboard.utils.helpers."""

from app.dashboard.utils.helpers import (
    CATEGORIES,
    DEFENSIVE_BOUNDS,
    format_float,
    format_percentage,
    detect_simulation_source,
    validate_defensive_bounds,
    get_registry_health_summary,
)

__all__ = [
    "CATEGORIES",
    "DEFENSIVE_BOUNDS",
    "format_float",
    "format_percentage",
    "detect_simulation_source",
    "validate_defensive_bounds",
    "get_registry_health_summary",
]

