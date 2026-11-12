"""AI-Based Precision Aquaculture Decision-Support System.

Main Application Launcher (Phase 5 Dashboard).
Coordinates multi-page navigation, operational categorization, and system-level
governance disclaimers across all 7 dashboard modules.
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

# Define Navigation Structure Using Categorized Sections
pages = {
    "Operational Monitoring": [
        st.Page(
            "app/dashboard/pages/01_Overview.py",
            title="Pond Monitoring Overview",
            icon="🏠",
            default=True,
        ),
        st.Page(
            "app/dashboard/pages/02_Water_Quality_Toxicity.py",
            title="Water Quality & Toxicity Screening",
            icon="🧪",
        ),
        st.Page(
            "app/dashboard/pages/03_Next_Visit_DO_Hypoxia.py",
            title="Next-Visit Morning DO & Hypoxia",
            icon="🫁",
        ),
        st.Page(
            "app/dashboard/pages/04_Growth_Feeding_Advisor.py",
            title="Fish Weight & Feeding Advisory",
            icon="🐟",
        ),
        st.Page(
            "app/dashboard/pages/05_Historical_Data_Explorer.py",
            title="Historical Observations Explorer",
            icon="📈",
        ),
    ],
    "Simulation & Sandbox": [
        st.Page(
            "app/dashboard/pages/06_Simulation_Sandbox.py",
            title="Simulated Scenarios Sandbox",
            icon="🔬",
        ),
    ],
    "System Governance": [
        st.Page(
            "app/dashboard/pages/07_Model_Registry_Governance.py",
            title="Governance & Benchmark Catalog",
            icon="🛡️",
        ),
    ],
}

# Render Sidebar Branding & Disclaimers
with st.sidebar:
    st.markdown(
        """
        <div style="padding: 0.5rem 0 1rem 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 1rem;">
            <div style="font-size: 1.1rem; font-weight: 700; color: #0c2340;">
                🐟 Precision AquaDSS
            </div>
            <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.15rem;">
                Toxicity & Yield Decision Support (BAI507P)
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Execute Multi-Page Navigation
nav = st.navigation(pages)
nav.run()

# Sidebar Footer Disclaimers
with st.sidebar:
    st.markdown("---")
    st.markdown(
        """
        <div style="font-size: 0.72rem; color: #64748b; line-height: 1.35;">
            <strong>System Safeguards:</strong><br>
            • Decision-support only (<code>is_automatic_control = False</code>)<br>
            • Sampling interval: 3–45 days (routine visits)<br>
            • Morning observations: 06:00–08:30 AM<br>
            • No continuous real-time or overnight minimum DO claims<br>
            • Read-only models • No runtime retraining
        </div>
        """,
        unsafe_allow_html=True,
    )
