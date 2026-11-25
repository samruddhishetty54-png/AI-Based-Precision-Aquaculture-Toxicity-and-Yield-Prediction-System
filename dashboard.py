"""AI-Based Precision Aquaculture Decision-Support System.

Main Application Launcher (Phase 5 Dashboard).
Coordinates multi-page navigation, Deep Ocean + Emerald Aqua styling,
and system-level governance disclaimers across all 9 dashboard modules.
"""

import sys
from pathlib import Path
import streamlit as st

# Ensure repository root is on Python module search path
repo_root = Path(__file__).resolve().parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from app.dashboard.utils.styles import inject_custom_css

# Application Page Configuration
st.set_page_config(
    page_title="Precision Aquaculture DSS",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Global Aesthetic Styling
inject_custom_css()

# Top-of-sidebar Precision AquaDSS Logo
logo_path = repo_root / "app" / "dashboard" / "assets" / "logo.svg"
if logo_path.exists():
    st.logo(str(logo_path), size="large")

# Define Navigation Structure Using Organization-Facing Categories (9 Pages)
pages = {
    "Farm & Monitoring": [
        st.Page(
            "app/dashboard/pages/08_Farm_Overview.py",
            title="Organization Overview",
            icon=":material/home:",
            default=True,
        ),
        st.Page(
            "app/dashboard/pages/01_Overview.py",
            title="Pond Monitoring",
            icon=":material/dashboard:",
        ),
    ],
    "Data Management": [
        st.Page(
            "app/dashboard/pages/09_Import_Dataset.py",
            title="Upload New Dataset",
            icon=":material/upload_file:",
        ),
    ],
    "Water Quality & Risk": [
        st.Page(
            "app/dashboard/pages/02_Water_Quality_Toxicity.py",
            title="Water Quality & Toxicity Risk",
            icon=":material/science:",
        ),
        st.Page(
            "app/dashboard/pages/03_Next_Visit_DO_Hypoxia.py",
            title="DO & Hypoxia Screening",
            icon=":material/air:",
        ),
    ],
    "Growth & Feeding": [
        st.Page(
            "app/dashboard/pages/04_Growth_Feeding_Advisor.py",
            title="Fish Growth & Feeding Advisor",
            icon=":material/scale:",
        ),
    ],
    "Analytics": [
        st.Page(
            "app/dashboard/pages/05_Historical_Data_Explorer.py",
            title="Prediction History & Reports",
            icon=":material/analytics:",
        ),
        st.Page(
            "app/dashboard/pages/06_Simulation_Sandbox.py",
            title="Simulation Mode",
            icon=":material/biotech:",
        ),
    ],
    "System": [
        st.Page(
            "app/dashboard/pages/07_Model_Registry_Governance.py",
            title="Model Information",
            icon=":material/verified_user:",
        ),
    ],
}

# Execute Multi-Page Navigation
nav = st.navigation(pages)
nav.run()

# Sidebar Footer: Project Branding & System Safeguards on Deep Ocean Navy
with st.sidebar:
    st.markdown(
        """
        <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid rgba(220, 233, 230, 0.18);">
            <div style="background: linear-gradient(135deg, #087F72 0%, #0E5859 100%); border: 1px solid rgba(67, 191, 192, 0.35); border-radius: 10px; padding: 0.65rem 0.8rem; margin-bottom: 0.6rem;">
                <div style="font-size: 0.95rem; font-weight: 800; color: #FFFFFF !important; letter-spacing: -0.01em;">
                    🐟 Precision AquaDSS
                </div>
                <div style="font-size: 0.71rem; font-weight: 500; color: #D7F3F0 !important; margin-top: 0.1rem;">
                    Aquaculture AI Decision Support
                </div>
            </div>
            <div style="background-color: rgba(255, 255, 255, 0.06); border: 1px solid rgba(220, 233, 230, 0.15); border-radius: 8px; padding: 0.6rem 0.75rem; font-size: 0.71rem; color: #D5E4E3 !important; line-height: 1.45; font-weight: 500;">
                <span style="color: #43BFC0 !important; font-weight: 700; display: block; margin-bottom: 0.25rem; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em;">System Safeguards</span>
                • Decision-support only (is_automatic_control = False)<br>
                • Routine visits: 3–45 days (06:00–08:30 AM)<br>
                • No live IoT or overnight DO claims<br>
                • Read-only models • No runtime retraining
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
