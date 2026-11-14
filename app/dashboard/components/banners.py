"""Reusable warning, governance, and horizon disclaimers."""

import streamlit as st


def render_decision_support_banner() -> None:
    """Render persistent human-in-the-loop decision support banner."""
    html = """
    <div class="banner-container banner-governance" style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; word-wrap: break-word;">
        <strong>🛡️ Decision-Support Interface Only:</strong>
        This system provides observational analytics and decision-support guidance for qualified farm managers.
        It executes <strong>zero automated control commands</strong> (aeration, feeding gates, or water exchange).
        All advisories require independent human verification.
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_simulation_warning_banner() -> None:
    """Render high-visibility warning banner for simulated scenarios."""
    html = """
    <div class="banner-container banner-simulation" style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; word-wrap: break-word;">
        <strong>⚠️ SIMULATED SCENARIO ONLY (DEMONSTRATION):</strong>
        Outputs in this section are derived from synthetic benchmark data.
        Operational application to live commercial fish ponds is strictly prohibited
        (<code>operational_use_permitted = False</code>).
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_multi_week_observation_banner() -> None:
    """Render discrete sampling horizon banner."""
    html = """
    <div class="banner-container banner-horizon" style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; word-wrap: break-word;">
        <strong>🗓️ Sampling Context:</strong>
        Observations represent routine multi-week commercial visits (revisit interval: 3–45 days; median ~21 days)
        and <strong>morning DO observations (06:00–08:30 AM)</strong>.
        These are <em>NOT verified pre-dawn daily minimum DO</em>.
        No continuous real-time streaming, diurnal cycling, or overnight predictions are provided.
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

