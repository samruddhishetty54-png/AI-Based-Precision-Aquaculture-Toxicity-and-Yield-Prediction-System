"""CSS styling and aesthetic palette for Precision AquaDSS.

Implements the Deep Ocean + Emerald Aqua SaaS design system:
- Sidebar: #102C3A (deep ocean navy) with #087F72 active item & white text/icons
- Main background: #F1F7F6
- Cards: #FFFFFF with #DCE9E6 borders
- Primary actions: #087F72 | Secondary accent: #43BFC0
- Headings: #173747 | Body text: #526873
- Status: Success #269B72 | Warning #E7A23B | Danger #D9534F
- Responsive flex/grid min-width: 0 rules to prevent horizontal overflow at 1366px/1440px/1920px.
"""

from typing import Dict
import streamlit as st

PALETTE: Dict[str, str] = {
    "navy_primary": "#0c2340",       # Legacy test-verified navy key
    "navy_secondary": "#102C3A",     # Sidebar deep ocean navy
    "teal_primary": "#0d5c75",       # Legacy test-verified teal key
    "teal_accent": "#43BFC0",        # Secondary aqua accent
    "ocean_sidebar": "#102C3A",      # Deep ocean sidebar
    "emerald_primary": "#087F72",    # Emerald teal primary & active nav
    "heading_ocean": "#173747",      # Main headings
    "body_slate": "#526873",         # Body text
    "aquatic_blue": "#43BFC0",       # Secondary aqua highlight
    "bg_light": "#F1F7F6",           # Main page background
    "bg_card": "#FFFFFF",            # Pure white cards
    "border_light": "#DCE9E6",       # Soft aqua-grey borders
    "text_dark": "#173747",          # Heading / primary dark text
    "text_muted": "#526873",         # Body / secondary text
    "success": "#269B72",            # Success indicator
    "amber_warn": "#E7A23B",         # Warning indicator
    "danger": "#D9534F",             # Danger indicator
    "amber_bg": "#FFF8EB",           # Soft warning background
    "blue_info_bg": "#EBF7F6",       # Soft aqua info background
    "border_teal": "#43BFC0",        # Aqua border accent
}

CUSTOM_CSS = """
<style>
    /* =======================================================================
       1. GLOBAL THEME, RESPONSIVE CONTAINERS & HORIZONTAL OVERFLOW FIX
       ======================================================================= */
    *, *:before, *:after {
        box-sizing: border-box;
    }

    html, body, .stApp {
        background-color: #F1F7F6 !important;
        color: #526873 !important;
        font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
    }

    /* Fix Streamlit flex layout so main content never overflows past viewport right edge */
    div[data-testid="stAppViewContainer"] {
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }
    section[data-testid="stMain"],
    section.main {
        flex: 1 1 0% !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 100% !important;
        overflow-x: hidden !important;
    }
    div[data-testid="stMainBlockContainer"],
    .main .block-container {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        padding: 1.2rem 1.5rem 2rem 1.5rem !important;
        margin: 0 !important;
        box-sizing: border-box !important;
    }

    /* Prevent flex/grid children (columns, forms, inputs, markdown, charts) from pushing width */
    div[data-testid="stHorizontalBlock"] {
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }
    div[data-testid="stColumn"] {
        min-width: 0 !important;
        flex: 1 1 0% !important;
    }
    div[data-testid="stVerticalBlock"],
    div[data-testid="stElementContainer"],
    div[data-testid="stForm"],
    div[data-testid="stMarkdownContainer"],
    div[data-testid="stPlotlyChart"],
    div[data-testid="stDataFrame"],
    div[data-testid="stNumberInput"],
    div[data-testid="stSelectbox"],
    div[data-testid="stSlider"] {
        min-width: 0 !important;
        max-width: 100% !important;
    }
    div[data-testid="stMarkdownContainer"] {
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6 {
        color: #173747 !important;
        font-weight: 700 !important;
        letter-spacing: -0.015em !important;
    }
    .stApp h1:not(.hero-title) {
        color: #173747 !important;
        font-weight: 800 !important;
    }
    p, li, span, div {
        color: #526873;
    }
    strong, b {
        color: #173747 !important;
        font-weight: 700 !important;
    }

    .stCaption, [data-testid="stCaptionContainer"] p, [data-testid="stCaptionContainer"] {
        color: #526873 !important;
        font-weight: 500 !important;
        font-size: 0.84rem !important;
        line-height: 1.45 !important;
        opacity: 1 !important;
    }

    code {
        color: #173747 !important;
        background-color: #E6F2F0 !important;
        border: 1px solid #DCE9E6 !important;
        border-radius: 4px;
        padding: 0.12rem 0.35rem;
        font-weight: 600 !important;
        font-size: 0.86em;
        word-break: break-word;
    }

    /* =======================================================================
       2. DEEP OCEAN + EMERALD AQUA PAGE HEADER & BADGES
       ======================================================================= */
    .aqua-breadcrumb {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        background-color: #FFFFFF;
        border: 1px solid #DCE9E6;
        border-radius: 9999px;
        padding: 0.22rem 0.75rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: #526873;
        margin-bottom: 0.55rem;
        box-shadow: 0 1px 3px rgba(16, 44, 58, 0.03);
    }
    .aqua-breadcrumb strong {
        color: #087F72 !important;
    }

    .aquaculture-header,
    div.aquaculture-header,
    [data-testid="stMarkdownContainer"] .aquaculture-header {
        background: linear-gradient(135deg, #FFFFFF 0%, #F1F7F6 60%, #E0F2F1 100%) !important;
        border: 1px solid #DCE9E6 !important;
        border-left: 5px solid #087F72 !important;
        border-radius: 12px !important;
        padding: 1.05rem 1.35rem !important;
        margin-bottom: 0.9rem !important;
        box-shadow: 0 2px 8px rgba(16, 44, 58, 0.05) !important;
        width: 100% !important;
        max-width: 100% !important;
    }

    .aqua-panel-bar {
        background: linear-gradient(90deg, #102C3A 0%, #087F72 100%);
        color: #FFFFFF !important;
        border-radius: 10px;
        padding: 0.55rem 1rem;
        margin: 0.5rem 0 0.65rem 0;
        font-size: 0.90rem;
        font-weight: 700;
        letter-spacing: -0.01em;
        box-shadow: 0 2px 5px rgba(16, 44, 58, 0.08);
    }
    .aquaculture-header h1,
    div.aquaculture-header h1,
    [data-testid="stMarkdownContainer"] .aquaculture-header h1,
    .hero-title {
        color: #173747 !important;
        -webkit-text-fill-color: #173747 !important;
        font-size: 1.5rem !important;
        font-weight: 800 !important;
        margin: 0 !important;
        letter-spacing: -0.02em !important;
        line-height: 1.25 !important;
    }
    .aquaculture-header p,
    div.aquaculture-header p,
    [data-testid="stMarkdownContainer"] .aquaculture-header p,
    .hero-subtitle {
        color: #526873 !important;
        -webkit-text-fill-color: #526873 !important;
        font-size: 0.89rem !important;
        margin: 0.25rem 0 0 0 !important;
        font-weight: 400 !important;
        line-height: 1.45 !important;
    }

    .category-badge {
        display: inline-block;
        padding: 0.22rem 0.7rem;
        border-radius: 9999px;
        font-size: 0.70rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        white-space: nowrap;
    }
    .category-historical {
        background-color: #E3F5F3;
        color: #087F72 !important;
        border: 1px solid #AEE2DC;
    }
    .category-benchmark {
        background-color: #EAF0F2;
        color: #173747 !important;
        border: 1px solid #C8D8DE;
    }
    .category-experimental {
        background-color: #FDF3E1;
        color: #9A6411 !important;
        border: 1px solid #F3D396;
    }
    .category-simulated {
        background-color: #FDECEB;
        color: #A83834 !important;
        border: 1px solid #F4B9B7;
    }
    .category-advisory {
        background-color: #E3F6EE;
        color: #1C7757 !important;
        border: 1px solid #A6DEC8;
    }

    /* =======================================================================
       3. DEEP OCEAN SIDEBAR (#073247) + EMERALD SELECTED (#087F72)
       ======================================================================= */
    section[data-testid="stSidebar"] {
        background-color: #073247 !important;
        border-right: 1px solid #052536 !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"][aria-expanded="true"] {
        min-width: 268px !important;
        width: 268px !important;
        max-width: 280px !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        padding: 0.75rem 0.85rem 1rem 0.85rem !important;
    }
    section[data-testid="stSidebar"] img[data-testid="stLogo"] {
        height: 46px !important;
        width: auto !important;
        max-width: 100% !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] {
        padding-top: 0.25rem !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] {
        padding: 0 !important;
    }

    /* Collapse button icon on dark sidebar */
    section[data-testid="stSidebar"] button[data-testid="stSidebarCollapseButton"] svg,
    section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] svg {
        color: #DCE9E6 !important;
        fill: #DCE9E6 !important;
    }

    /* Sidebar Navigation Links */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"],
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] a,
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] {
        display: flex !important;
        align-items: center !important;
        gap: 0.55rem !important;
        color: #E8F3F1 !important;
        font-weight: 500 !important;
        font-size: 0.84rem !important;
        line-height: 1.3 !important;
        opacity: 1 !important;
        border-radius: 8px !important;
        margin: 2px 0 !important;
        padding: 0.48rem 0.65rem !important;
        width: 100% !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: unset !important;
        transition: background-color 0.15s ease-in-out, color 0.15s ease-in-out;
    }

    /* Sidebar Icons */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span[data-testid="stIconMaterial"],
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] svg {
        flex-shrink: 0 !important;
        color: #43BFC0 !important;
        font-size: 1.05rem !important;
    }

    /* Sidebar Link Text */
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] span,
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"] span {
        color: #E8F3F1 !important;
        opacity: 1 !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: unset !important;
    }

    /* Selected / Active Sidebar Item (#087F72) */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"],
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"],
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a.active,
    section[data-testid="stSidebar"] a[data-testid="stSidebarNavLink"]:has(span[data-testid="stSidebarNavLinkText"][aria-current="page"]) {
        background-color: #087F72 !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.18) !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] span[data-testid="stIconMaterial"] {
        color: #FFFFFF !important;
    }

    /* Hover State on Dark Sidebar */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
        background-color: rgba(67, 191, 192, 0.15) !important;
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover span,
    section[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover span {
        color: #FFFFFF !important;
    }

    /* Sidebar Section Group Headings */
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
        color: #43BFC0 !important;
        font-weight: 700 !important;
        font-size: 0.70rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.09em !important;
        opacity: 1 !important;
        margin-top: 0.85rem !important;
        margin-bottom: 0.25rem !important;
        padding-left: 0.45rem !important;
    }

    /* =======================================================================
       4. FORM INPUTS, BUTTONS, CARDS & INTERACTIVE CONTROLS
       ======================================================================= */
    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 1px solid #DCE9E6 !important;
        border-radius: 12px !important;
        padding: 1.15rem 1.25rem !important;
        box-shadow: 0 2px 8px rgba(16, 44, 58, 0.04) !important;
    }

    label[data-testid="stWidgetLabel"],
    label[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] span,
    label[data-testid="stWidgetLabel"] div,
    div[data-testid="stWidgetLabel"] p {
        color: #173747 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        opacity: 1 !important;
        line-height: 1.35;
    }

    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label p,
    div[data-testid="stRadio"] label span,
    div[data-testid="stRadio"] div[role="radiogroup"] label,
    div[data-testid="stRadio"] div[role="radiogroup"] label p {
        color: #173747 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        opacity: 1 !important;
    }

    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] label p,
    div[data-testid="stCheckbox"] label span {
        color: #173747 !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        opacity: 1 !important;
    }

    div[data-baseweb="input"],
    div[data-baseweb="input"] input,
    div[data-baseweb="base-input"],
    div[data-baseweb="base-input"] input,
    div[data-baseweb="textarea"] textarea {
        color: #173747 !important;
        font-weight: 600 !important;
        background-color: #FFFFFF !important;
        border-color: #DCE9E6 !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"]:focus-within,
    div[data-baseweb="base-input"]:focus-within {
        border-color: #087F72 !important;
        box-shadow: 0 0 0 1px #087F72 !important;
    }

    div[data-baseweb="select"],
    div[data-baseweb="select"] div,
    div[data-baseweb="select"] span {
        color: #173747 !important;
        font-weight: 600 !important;
        background-color: #FFFFFF !important;
        border-color: #DCE9E6 !important;
        border-radius: 8px !important;
    }

    div[data-testid="stSlider"] div[data-testid="stTickBar"] + div,
    div[data-testid="stSlider"] div[data-testid="stThumbValue"] {
        color: #087F72 !important;
        font-weight: 700 !important;
    }

    /* Expanders */
    div[data-testid="stExpander"] details summary,
    div[data-testid="stExpander"] summary span p,
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary {
        color: #173747 !important;
        font-weight: 700 !important;
        font-size: 0.90rem !important;
    }
    div[data-testid="stExpander"] {
        border: 1px solid #DCE9E6 !important;
        border-radius: 10px !important;
        background-color: #FFFFFF !important;
        box-shadow: 0 1px 4px rgba(16, 44, 58, 0.03) !important;
        margin-bottom: 0.75rem !important;
    }

    /* Primary Buttons (#087F72) */
    div[data-testid="stFormSubmitButton"] button,
    div.stButton button,
    div[data-testid="stDownloadButton"] button {
        background-color: #087F72 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.55rem 1.2rem !important;
        box-shadow: 0 2px 5px rgba(8, 127, 114, 0.22) !important;
        transition: background-color 0.15s ease-in-out !important;
    }
    div[data-testid="stFormSubmitButton"] button:hover,
    div.stButton button:hover,
    div[data-testid="stDownloadButton"] button:hover {
        background-color: #102C3A !important;
        color: #FFFFFF !important;
    }
    div[data-testid="stFormSubmitButton"] button p,
    div.stButton button p,
    div[data-testid="stDownloadButton"] button p {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }

    /* Clickable Quick Action Page-Link Cards */
    div[data-testid="stPageLink"] a,
    a[data-testid="stPageLink-NavLink"] {
        background-color: #FFFFFF !important;
        border: 1px solid #DCE9E6 !important;
        border-top: 3px solid #087F72 !important;
        border-radius: 10px !important;
        padding: 0.8rem 0.95rem !important;
        box-shadow: 0 2px 6px rgba(16, 44, 58, 0.04) !important;
        display: flex !important;
        align-items: center !important;
        gap: 0.55rem !important;
        color: #173747 !important;
        font-weight: 700 !important;
        font-size: 0.86rem !important;
        text-decoration: none !important;
        transition: all 0.15s ease-in-out !important;
        min-height: 52px !important;
        width: 100% !important;
    }
    div[data-testid="stPageLink"] a:hover,
    a[data-testid="stPageLink-NavLink"]:hover {
        border-color: #087F72 !important;
        background-color: #EBF7F6 !important;
        box-shadow: 0 4px 10px rgba(8, 127, 114, 0.12) !important;
    }
    div[data-testid="stPageLink"] a p,
    a[data-testid="stPageLink-NavLink"] p {
        color: #173747 !important;
        font-weight: 700 !important;
        margin: 0 !important;
    }

    /* Tabs */
    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        color: #526873 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #173747 !important;
        font-weight: 700 !important;
        border-bottom-color: #087F72 !important;
    }

    /* File Uploader */
    section[data-testid="stFileUploaderDropzone"] {
        background-color: #FFFFFF !important;
        border: 2px dashed #43BFC0 !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }

    /* Bordered Streamlit containers styled as white SaaS cards */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF !important;
        border: 1px solid #DCE9E6 !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px rgba(16, 44, 58, 0.04) !important;
        padding: 0.75rem 1rem !important;
        min-width: 0 !important;
        max-width: 100% !important;
    }

    /* =======================================================================
       5. STANDARDIZED SAAS KPI METRIC CARDS
       ======================================================================= */
    .aqua-metric-card {
        background-color: #FFFFFF;
        border: 1px solid #DCE9E6;
        border-radius: 12px;
        padding: 1rem 1.15rem;
        margin-bottom: 0.75rem;
        box-shadow: 0 2px 6px rgba(16, 44, 58, 0.04);
        transition: border-color 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
        width: 100% !important;
        max-width: 100% !important;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
        min-height: 118px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .aqua-metric-card:hover {
        border-color: #43BFC0;
        box-shadow: 0 4px 12px rgba(8, 127, 114, 0.10);
    }
    .aqua-metric-title {
        font-size: 0.73rem;
        color: #526873;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 0.25rem;
    }
    .aqua-metric-value {
        font-size: 1.55rem;
        color: #173747;
        font-weight: 800;
        line-height: 1.15;
    }
    .aqua-metric-subtitle {
        font-size: 0.79rem;
        color: #526873;
        font-weight: 500;
        margin-top: 0.25rem;
    }

    /* =======================================================================
       6. SLEEK SAAS ALERT & GOVERNANCE BANNERS
       ======================================================================= */
    .banner-container {
        width: 100% !important;
        max-width: 100% !important;
        border-radius: 8px;
        padding: 0.65rem 0.95rem !important;
        margin-bottom: 0.75rem !important;
        font-size: 0.84rem;
        line-height: 1.45;
        overflow-wrap: break-word !important;
        word-wrap: break-word !important;
    }
    .banner-simulation {
        background-color: #FFF8EB !important;
        border: 1px solid #F3D396 !important;
        border-left: 4px solid #E7A23B !important;
        color: #7A4E0B !important;
    }
    .banner-governance {
        background-color: #FFFFFF !important;
        border: 1px solid #DCE9E6 !important;
        border-left: 4px solid #087F72 !important;
        color: #173747 !important;
    }
    .banner-horizon {
        background-color: #EBF7F6 !important;
        border: 1px solid #BEE5E1 !important;
        border-left: 4px solid #43BFC0 !important;
        color: #173747 !important;
    }

    /* =======================================================================
       7. REGISTRY HEALTH PILLS & STATUS BADGES
       ======================================================================= */
    .health-pill-ready {
        background-color: #E3F6EE;
        color: #269B72;
        border: 1px solid #A6DEC8;
        padding: 0.2rem 0.55rem;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 700;
        display: inline-block;
    }
    .health-pill-isolated {
        background-color: #FDECEB;
        color: #D9534F;
        border: 1px solid #F4B9B7;
        padding: 0.2rem 0.55rem;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 700;
        display: inline-block;
    }

    /* =======================================================================
       8. GENERAL SAAS CARD CONTAINERS & DIVIDERS
       ======================================================================= */
    .saas-card {
        background-color: #FFFFFF;
        border: 1px solid #DCE9E6;
        border-radius: 12px;
        padding: 1.1rem 1.25rem;
        margin-bottom: 0.9rem;
        box-shadow: 0 2px 6px rgba(16, 44, 58, 0.04);
        width: 100%;
        max-width: 100%;
    }
    hr {
        margin: 1rem 0 !important;
        border: 0 !important;
        border-top: 1px solid #DCE9E6 !important;
    }
</style>
"""


def inject_custom_css() -> None:
    """Inject custom CSS rules into the running Streamlit page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def apply_aqua_chart_theme(fig, height: int = 300):
    """Apply consistent Deep Ocean + Emerald Aqua styling to any Plotly figure."""
    fig.update_layout(
        template="plotly_white",
        height=height,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#526873", size=12),
        title=dict(font=dict(size=14, color="#173747")),
        yaxis=dict(gridcolor="#DCE9E6", zerolinecolor="#DCE9E6"),
        xaxis=dict(gridcolor="#F1F7F6"),
    )
    return fig
