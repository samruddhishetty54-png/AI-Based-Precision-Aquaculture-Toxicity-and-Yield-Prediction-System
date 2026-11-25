"""Reusable warning, governance, and horizon disclaimers."""

import textwrap
import streamlit as st


def render_decision_support_banner() -> None:
    """Render persistent human-in-the-loop decision support banner."""
    html = textwrap.dedent("""
    <div class="banner-container banner-governance" style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; word-wrap: break-word;">
        <strong>🛡️ Decision-Support Interface Only:</strong>
        This system provides observational analytics and decision-support guidance for qualified farm managers.
        It executes <strong>zero automated control commands</strong> (aeration, feeding gates, or water exchange).
        All advisories require independent human verification.
    </div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def render_simulation_warning_banner() -> None:
    """Render high-visibility warning banner for simulated scenarios."""
    html = textwrap.dedent("""
    <div class="banner-container banner-simulation" style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; word-wrap: break-word;">
        <strong>⚠️ SIMULATED SCENARIO ONLY (DEMONSTRATION):</strong>
        Outputs in this section are derived from synthetic benchmark data.
        Operational application to live commercial fish ponds is strictly prohibited
        (<code>operational_use_permitted = False</code>).
    </div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def render_multi_week_observation_banner() -> None:
    """Render discrete sampling horizon banner."""
    html = textwrap.dedent("""
    <div class="banner-container banner-horizon" style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; word-wrap: break-word;">
        <strong>🗓️ Sampling Context:</strong>
        Observations represent routine multi-week commercial visits (revisit interval: 3–45 days; median ~21 days)
        and <strong>morning DO observations (06:00–08:30 AM)</strong>.
        These are <em>NOT verified pre-dawn daily minimum DO</em>.
        No continuous real-time streaming, diurnal cycling, or overnight predictions are provided.
    </div>
    """).strip()
    st.markdown(html, unsafe_allow_html=True)


def render_uploaded_context_notice(relevant_cols: list[str] | None = None) -> None:
    """Display an isolated summary of active uploaded CSV analysis results if present."""
    up_state = st.session_state.get("uploaded_analysis_state")
    res_state = st.session_state.get("uploaded_results_state")
    if not up_state or not up_state.get("is_valid"):
        return

    filename = up_state.get("filename", "uploaded.csv")
    selected_pond = up_state.get("selected_pond", "All Records")
    total_rows = up_state.get("total_rows", 0)

    with st.expander(
        f"Uploaded Dataset Active in Session: {filename} ({selected_pond}, {total_rows} rows)",
        expanded=False,
    ):
        st.caption(
            "Source: User-uploaded CSV (isolated in session state; NOT merged with historical field logs)."
        )
        if res_state and res_state.get("filename") == filename:
            res_df = res_state["results_df"]
            cols_to_show = [c for c in ["pond_id", "observation_date"] if c in res_df.columns]
            if relevant_cols:
                cols_to_show.extend([c for c in relevant_cols if c in res_df.columns and c not in cols_to_show])
            else:
                cols_to_show = list(res_df.columns)
            if cols_to_show:
                st.dataframe(res_df[cols_to_show].head(25), use_container_width=True, hide_index=True)
            else:
                st.info("No compatible outputs were generated for this module from the uploaded CSV.")
        else:
            st.info("Uploaded CSV is validated. Visit 'Import & Analyse' and click 'Run Analysis' to generate results.")
