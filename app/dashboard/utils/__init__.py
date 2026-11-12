"""Dashboard utilities package."""

from app.dashboard.utils.helpers import (
    format_float,
    format_percentage,
    validate_defensive_bounds,
    detect_simulation_source,
    get_registry_health_summary,
    CATEGORIES,
)
from app.dashboard.utils.styles import inject_custom_css, PALETTE

__all__ = [
    "format_float",
    "format_percentage",
    "validate_defensive_bounds",
    "detect_simulation_source",
    "get_registry_health_summary",
    "CATEGORIES",
    "inject_custom_css",
    "PALETTE",
]

