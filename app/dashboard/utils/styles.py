"""CSS styling and aesthetic palette for the Precision Aquaculture Dashboard.

Implements a clean, modern scientific theme featuring dark navy and deep teal
accents on a light neutral background, emphasizing legibility, consistent
spacing, and professional decision-support interfaces.
"""

from typing import Dict
import streamlit as st

# Color palette definition
PALETTE: Dict[str, str] = {
    "navy_primary": "#0c2340",       # Deep classic navy
    "navy_secondary": "#1e3a5f",     # Mid navy
    "teal_primary": "#0d5c75",       # Deep professional teal
    "teal_accent": "#0e7490",        # Muted cyan/teal accent
    "bg_light": "#f8fafc",           # Crisp light slate background
    "bg_card": "#ffffff",            # Pure white card background
    "border_light": "#e2e8f0",       # Light gray border
    "text_dark": "#0f172a",          # Dark charcoal primary text
    "text_muted": "#475569",         # Muted slate secondary text
    "amber_warn": "#d97706",         # Warm amber for simulation/advisory alerts
    "amber_bg": "#fffbeb",           # Light amber background for simulation banners
    "blue_info_bg": "#f0f9ff",       # Soft blue info background
    "border_teal": "#14b8a6",        # Teal border accent
}

CUSTOM_CSS = """
<style>
    /* Main application background and font smoothing */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Top header styling */
    .aquaculture-header {
        background: linear-gradient(135deg, #0c2340 0%, #0d5c75 100%);
        color: #ffffff;
        padding: 1.5rem 2rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.06);
    }
    .aquaculture-header h1 {
        color: #ffffff !important;
        font-size: 1.85rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .aquaculture-header p {
        color: #cbd5e1 !important;
        font-size: 0.95rem;
        margin: 0.35rem 0 0 0;
        font-weight: 400;
    }

    /* Page classification pill badge */
    .category-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-top: 0.5rem;
    }
    .category-historical {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #bae6fd;
    }
    .category-benchmark {
        background-color: #f1f5f9;
        color: #334155;
        border: 1px solid #cbd5e1;
    }
    .category-experimental {
        background-color: #fef3c7;
        color: #92400e;
        border: 1px solid #fde68a;
    }
    .category-simulated {
        background-color: #ffedd5;
        color: #9a3412;
        border: 1px solid #fed7aa;
    }
    .category-advisory {
        background-color: #ccfbf1;
        color: #115e59;
        border: 1px solid #99f6e4;
    }

    /* Professional Metric Cards */
    .aqua-metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        transition: border-color 0.15s ease-in-out;
    }
    .aqua-metric-card:hover {
        border-color: #0d5c75;
    }
    .aqua-metric-title {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }
    .aqua-metric-value {
        font-size: 1.85rem;
        color: #0c2340;
        font-weight: 700;
        line-height: 1.2;
    }
    .aqua-metric-subtitle {
        font-size: 0.8rem;
        color: #475569;
        margin-top: 0.35rem;
    }

    /* Warning & Governance Banners */
    .banner-container {
        border-radius: 6px;
        padding: 0.85rem 1.25rem;
        margin-bottom: 1.25rem;
        font-size: 0.875rem;
        line-height: 1.45;
    }
    .banner-simulation {
        background-color: #fffbeb;
        border: 1px solid #f59e0b;
        border-left: 5px solid #d97706;
        color: #92400e;
    }
    .banner-governance {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-left: 5px solid #0d5c75;
        color: #334155;
    }
    .banner-horizon {
        background-color: #f0f9ff;
        border: 1px solid #bae6fd;
        border-left: 5px solid #0284c7;
        color: #0369a1;
    }

    /* Registry Health Pill */
    .health-pill-ready {
        background-color: #f0fdf4;
        color: #166534;
        border: 1px solid #bbf7d0;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .health-pill-isolated {
        background-color: #fff7ed;
        color: #c2410c;
        border: 1px solid #ffedd5;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Sidebar visual adjustments */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
</style>
"""


def inject_custom_css() -> None:
    """Inject custom CSS rules into the running Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

