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
    /* =======================================================================
       1. GLOBAL THEME, RESPONSIVENESS, AND BASE TYPOGRAPHY
       ======================================================================= */
    *, *:before, *:after {
        box-sizing: border-box !important;
    }

    .stApp {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Headings outside hero banners */
    h2, h3, h4, h5, h6 {
        color: #0c2340 !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }
    .stApp h1:not(.hero-title) {
        color: #0c2340 !important;
        font-weight: 700 !important;
        letter-spacing: -0.01em;
    }

    /* General paragraphs & list items */
    p, li, span, div {
        color: #1e293b;
    }
    strong, b {
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* Captions & helper text */
    .stCaption, [data-testid="stCaptionContainer"] p, [data-testid="stCaptionContainer"] {
        color: #334155 !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        opacity: 1 !important;
    }

    /* Code blocks and inline code */
    code {
        color: #0c2340 !important;
        background-color: #f1f5f9 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 4px;
        padding: 0.15rem 0.35rem;
        font-weight: 600 !important;
        word-break: break-all;
    }

    /* Prevent horizontal overflow on markdown containers */
    div[data-testid="stMarkdownContainer"] {
        width: 100% !important;
        max-width: 100% !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
    }
    div[data-testid="stMarkdownContainer"] > div {
        box-sizing: border-box !important;
        width: 100% !important;
        max-width: 100% !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
    }

    /* =======================================================================
       2. TOP HERO HEADER & CATEGORY BADGES (HIGH CONTRAST WHITE ON NAVY)
       ======================================================================= */
    .aquaculture-header,
    div.aquaculture-header,
    [data-testid="stMarkdownContainer"] .aquaculture-header {
        background: linear-gradient(135deg, #0c2340 0%, #0d5c75 100%) !important;
        color: #ffffff !important;
        padding: 1.5rem 2rem !important;
        border-radius: 8px !important;
        margin-bottom: 1.5rem !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08) !important;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow: hidden !important;
    }
    .aquaculture-header h1,
    div.aquaculture-header h1,
    [data-testid="stMarkdownContainer"] .aquaculture-header h1,
    .hero-title {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        font-size: 1.85rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        letter-spacing: -0.02em !important;
        line-height: 1.25 !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.35) !important;
    }
    .aquaculture-header p,
    div.aquaculture-header p,
    [data-testid="stMarkdownContainer"] .aquaculture-header p,
    .hero-subtitle {
        color: #f8fafc !important;
        -webkit-text-fill-color: #f8fafc !important;
        font-size: 0.95rem !important;
        margin: 0.4rem 0 0 0 !important;
        font-weight: 400 !important;
        line-height: 1.4 !important;
    }

    /* Page classification pill badge */
    .category-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-top: 0.5rem;
    }
    .category-historical {
        background-color: #e0f2fe;
        color: #0369a1;
        border: 1px solid #7dd3fc;
    }
    .category-benchmark {
        background-color: #f1f5f9;
        color: #1e293b;
        border: 1px solid #94a3b8;
    }
    .category-experimental {
        background-color: #fef3c7;
        color: #78350f;
        border: 1px solid #fcd34d;
    }
    .category-simulated {
        background-color: #ffedd5;
        color: #7c2d12;
        border: 1px solid #fdba74;
    }
    .category-advisory {
        background-color: #ccfbf1;
        color: #134e4a;
        border: 1px solid #5eead4;
    }

    /* =======================================================================
       3. SIDEBAR NAVIGATION & SECTION HEADINGS (HIGH CONTRAST)
       ======================================================================= */
    section[data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
    }

    /* Sidebar Navigation Links */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"],
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a,
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {
        color: #1e293b !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        opacity: 1 !important;
        border-radius: 6px;
        margin: 2px 0;
        transition: background-color 0.15s ease-in-out, color 0.15s ease-in-out;
    }

    /* Sidebar Link Text Spans */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] span,
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] span {
        color: #1e293b !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    /* Active Navigation Link */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"],
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"],
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a.active,
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:has(span[data-testid="stSidebarNavLinkText"][aria-current="page"]) {
        background-color: #e0f2fe !important;
        color: #0c2340 !important;
        font-weight: 700 !important;
        border-left: 4px solid #0d5c75 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #0c2340 !important;
        font-weight: 700 !important;
    }

    /* Hover State for Sidebar Links */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
        background-color: #f1f5f9 !important;
        color: #0c2340 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover span {
        color: #0c2340 !important;
    }

    /* Sidebar Section Headings (Categorized Sections) */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] header,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] h1,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] h2,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] h3,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavSectionHeader"],
    section[data-testid="stSidebar"] span[data-testid="stSidebarNavSectionHeader"],
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] [data-testid="stSidebarNavSectionHeader"] span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] [data-testid="stMarkdownContainer"] > p,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] > div:first-child,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] ul > li > div {
        color: #0c2340 !important;
        font-weight: 800 !important;
        font-size: 0.82rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        opacity: 1 !important;
        margin-top: 0.75rem !important;
        margin-bottom: 0.25rem !important;
    }

    /* Sidebar Disclaimers & Info Text */
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] div {
        color: #1e293b !important;
    }

    /* =======================================================================
       4. WIDGET LABELS, RADIO BUTTONS, AND INPUT CONTROLS
       ======================================================================= */
    /* Primary Widget Labels (Select, Number, Slider, Text, Form) */
    label[data-testid="stWidgetLabel"],
    label[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] span,
    label[data-testid="stWidgetLabel"] div,
    div[data-testid="stWidgetLabel"] p,
    .stSelectbox label p,
    .stNumberInput label p,
    .stSlider label p,
    .stTextInput label p,
    .stTextArea label p,
    .stCheckbox label p,
    .stMultiSelect label p {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        opacity: 1 !important;
        line-height: 1.35;
    }

    /* Radio Button Group Labels & Radio Options Text */
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span,
    div[data-testid="stRadio"] [data-testid="stMarkdownContainer"] p,
    div[data-testid="stRadio"] div[role="radiogroup"] label,
    div[data-testid="stRadio"] div[role="radiogroup"] label div,
    div[data-testid="stRadio"] div[role="radiogroup"] label p {
        color: #0f172a !important;
        font-weight: 600 !important;
        font-size: 0.90rem !important;
        opacity: 1 !important;
    }

    /* Checkbox Options Text */
    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] label p,
    div[data-testid="stCheckbox"] label span,
    div[data-testid="stCheckbox"] [data-testid="stMarkdownContainer"] p {
        color: #0f172a !important;
        font-weight: 600 !important;
        font-size: 0.90rem !important;
        opacity: 1 !important;
    }

    /* Input Fields (Text, Number, Area) */
    div[data-baseweb="input"],
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"],
    div[data-baseweb="base-input"] input,
    div[data-baseweb="textarea"] textarea {
        color: #0f172a !important;
        font-weight: 600 !important;
        background-color: #ffffff !important;
        border-color: #94a3b8 !important;
    }
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="base-input"]:focus-within {
        border-color: #0d5c75 !important;
    }

    /* Selectbox Dropdowns */
    div[data-baseweb="select"],
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] span {
        color: #0f172a !important;
        font-weight: 600 !important;
        background-color: #ffffff !important;
    }

    /* Sliders */
    div[data-testid="stSlider"] div[data-testid="stTickBar"] + div,
    div[data-testid="stSlider"] div[data-testid="stThumbValue"] {
        color: #0c2340 !important;
        font-weight: 700 !important;
    }

    /* Expanders */
    div[data-testid="stExpander"] details summary,
    div[data-testid="stExpander"] summary span p,
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary {
        color: #0c2340 !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }

    /* Buttons */
    div[data-testid="stFormSubmitButton"] button,
    div.stButton button {
        background-color: #0d5c75 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.5rem 1.25rem !important;
    }
    div[data-testid="stFormSubmitButton"] button:hover,
    div.stButton button:hover {
        background-color: #0c2340 !important;
        color: #ffffff !important;
    }
    div[data-testid="stFormSubmitButton"] button p,
    div.stButton button p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }

    /* =======================================================================
       5. PROFESSIONAL METRIC CARDS & DATA CARDS
       ======================================================================= */
    .aqua-metric-card {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
        transition: border-color 0.15s ease-in-out;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
    }
    .aqua-metric-card:hover {
        border-color: #0d5c75;
    }
    .aqua-metric-title {
        font-size: 0.85rem;
        color: #334155;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }
    .aqua-metric-value {
        font-size: 1.85rem;
        color: #0c2340;
        font-weight: 800;
        line-height: 1.2;
    }
    .aqua-metric-subtitle {
        font-size: 0.82rem;
        color: #1e293b;
        font-weight: 500;
        margin-top: 0.35rem;
    }

    /* =======================================================================
       6. WARNING, GOVERNANCE & SAMPLING BANNERS (RESPONSIVE & NO OVERFLOW)
       ======================================================================= */
    .banner-container {
        box-sizing: border-box !important;
        width: 100% !important;
        max-width: 100% !important;
        border-radius: 6px;
        padding: 0.85rem 1.15rem !important;
        margin-bottom: 1.25rem !important;
        font-size: 0.875rem;
        line-height: 1.5;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
        word-break: normal !important;
    }
    .banner-simulation {
        background-color: #fffbeb !important;
        border: 1px solid #f59e0b !important;
        border-left: 5px solid #d97706 !important;
        color: #78350f !important;
    }
    .banner-governance {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1 !important;
        border-left: 5px solid #0d5c75 !important;
        color: #0f172a !important;
    }
    .banner-horizon {
        background-color: #f0f9ff !important;
        border: 1px solid #bae6fd !important;
        border-left: 5px solid #0284c7 !important;
        color: #075985 !important;
    }

    /* =======================================================================
       7. REGISTRY HEALTH PILLS & STATUS BADGES
       ======================================================================= */
    .health-pill-ready {
        background-color: #f0fdf4;
        color: #14532d;
        border: 1px solid #86efac;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
    }
    .health-pill-isolated {
        background-color: #fff7ed;
        color: #9a3412;
        border: 1px solid #fdba74;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 700;
    }
</style>
"""


def inject_custom_css() -> None:
    """Inject custom CSS rules into the running Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
