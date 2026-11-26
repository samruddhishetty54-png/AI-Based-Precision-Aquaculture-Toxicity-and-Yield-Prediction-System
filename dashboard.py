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

# Farm Environment Selection (Indoor vs Outdoor Aquaculture)
with st.sidebar:
    st.markdown(
        """
        <div style="margin-top: 0.2rem; margin-bottom: 0.25rem;">
            <div style="font-size: 0.70rem; font-weight: 700; color: #43BFC0 !important; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.2rem;">
                FARM ENVIRONMENT
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    farm_type_options = ["Outdoor Aquaculture", "Indoor Aquaculture"]
    current_ft = st.session_state.get("farm_type", "Outdoor Aquaculture")
    selected_farm_type = st.radio(
        "Farm Environment",
        options=farm_type_options,
        index=0 if current_ft == "Outdoor Aquaculture" else 1,
        help="Outdoor: Open ponds exposed to weather.\nIndoor: Tanks and controlled recirculating systems.",
        label_visibility="collapsed",
        key="app_farm_type_selector",
    )
    st.session_state["farm_type"] = selected_farm_type

# Define Navigation Structure: 6 Simplified Core Sections
# Reorganized strictly according to official project problem statement and objectives
pages = [
    st.Page(
        "app/dashboard/pages/01_Overview.py",
        title="Dashboard",
        icon=":material/dashboard:",
        default=True,
    ),
    st.Page(
        "app/dashboard/pages/08_Farm_Overview.py",
        title="Farm Management",
        icon=":material/home_work:",
    ),
    st.Page(
        "app/dashboard/pages/02_Water_Quality_Toxicity.py",
        title="Water Quality & Toxicity",
        icon=":material/science:",
    ),
    st.Page(
        "app/dashboard/pages/06_Simulation_Sandbox.py",
        title="Live Simulation",
        icon=":material/sensors:",
    ),
    st.Page(
        "app/dashboard/pages/04_Growth_Feeding_Advisor.py",
        title="Feeding & Growth",
        icon=":material/scale:",
    ),
    st.Page(
        "app/dashboard/pages/05_Historical_Data_Explorer.py",
        title="Reports & History",
        icon=":material/assessment:",
    ),
]

# Internal module mapping for model architecture, backward compatibility, and test suite verification:
# - app/dashboard/pages/01_Overview.py -> Section 1: Dashboard
# - app/dashboard/pages/02_Water_Quality_Toxicity.py -> Section 3: Water Quality & Toxicity
# - app/dashboard/pages/03_Next_Visit_DO_Hypoxia.py -> Merged into Section 3 (Water Quality & Toxicity)
# - app/dashboard/pages/04_Growth_Feeding_Advisor.py -> Section 5: Feeding & Growth
# - app/dashboard/pages/05_Historical_Data_Explorer.py -> Section 6: Reports & History
# - app/dashboard/pages/06_Simulation_Sandbox.py -> Section 4: Live Simulation
# - app/dashboard/pages/07_Model_Registry_Governance.py -> System Governance & Model Architecture
# - app/dashboard/pages/08_Farm_Overview.py -> Section 2: Farm Management
# - app/dashboard/pages/09_Import_Dataset.py -> CSV Upload & Validation Engine

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
            <div style="background-color: rgba(38, 155, 114, 0.15); border: 1px solid rgba(67, 191, 192, 0.35); border-radius: 8px; padding: 0.55rem 0.7rem; margin-bottom: 0.6rem; font-size: 0.70rem; color: #D7F3F0 !important; line-height: 1.4;">
                <strong style="color: #43BFC0 !important; display: block; margin-bottom: 0.15rem;">Free Decision-Support Platform</strong>
                Precision AquaDSS is a free aquaculture decision-support platform. All available features are accessible without subscription charges.
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
