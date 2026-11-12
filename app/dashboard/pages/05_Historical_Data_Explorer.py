"""Page 5: Historical Field Observations Explorer."""

import streamlit as st
from app.dashboard.utils.styles import inject_custom_css
from app.dashboard.components.header import render_page_header
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_multi_week_observation_banner,
)
from app.dashboard.components.metric_card import render_metric_card


def render_page() -> None:
    """Render the Historical Field Observations Explorer page."""
    inject_custom_css()

    render_page_header(
        title="Historical Field Observations Explorer",
        subtitle="Longitudinal multi-week field inspection records across monitored commercial ponds.",
        category_key="HISTORICAL",
    )

    render_decision_support_banner()
    render_multi_week_observation_banner()

    st.markdown(
        "Explore real-world commercial aquaculture records from Andhra Pradesh field inspections. "
        "All data represents scheduled routine visits ($3 \\le \\Delta t \\le 45$ days) and morning DO observations (06:00–08:30 AM). "
        "Missing values (NaNs) are strictly preserved to reflect true sampling records without synthetic imputation."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card(
            title="Monitored Ponds",
            value="10 Ponds",
            subtitle="Longitudinal commercial records",
            benchmark_ref="Cleaned Field Data v2",
        )
    with c2:
        render_metric_card(
            title="Inspection Schedule",
            value="3 to 45 Days",
            subtitle="Routine field visit frequency",
            benchmark_ref="Median = 21 Days",
        )
    with c3:
        render_metric_card(
            title="Missingness Policy",
            value="NaN Preserved",
            subtitle="Defensive data handling",
            benchmark_ref="Zero Silent Imputation",
        )

    st.info(
        "ℹ️ **Stage 1 Foundation Active:** Longitudinal time-series visualizations, pond-level parameter trajectories, "
        "and empirical missingness tables will be connected in subsequent stages."
    )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()

