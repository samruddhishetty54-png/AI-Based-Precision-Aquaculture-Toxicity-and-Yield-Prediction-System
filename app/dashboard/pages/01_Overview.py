"""Page 1: Pond Monitoring Overview & Model Status."""

import streamlit as st
from app.dashboard.utils.styles import inject_custom_css
from app.dashboard.components.header import render_page_header
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_multi_week_observation_banner,
)
from app.dashboard.components.registry_status import render_registry_status_bar
from app.dashboard.components.metric_card import render_metric_card
from app.models.registry import get_model_registry


def render_page() -> None:
    """Render the Pond Monitoring Overview page."""
    inject_custom_css()

    render_page_header(
        title="Pond Monitoring Overview & Model Status",
        subtitle="Executive multi-pond commercial farm overview and central model registry health.",
        category_key="HISTORICAL",
    )

    render_decision_support_banner()
    render_multi_week_observation_banner()

    # Registry Health Section
    st.subheader("Model Registry Health")
    registry = get_model_registry()
    render_registry_status_bar(registry)

    # Executive Overview Cards
    st.subheader("Farm Summary Indicators")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            title="Enrolled Monitored Ponds",
            value="10 Ponds",
            subtitle="Active commercial ponds",
            benchmark_ref="AP Shrimp & Fish Cohort",
        )
    with c2:
        render_metric_card(
            title="Typical DO Observation",
            value="3.50 mg/L",
            subtitle="Morning visit benchmark (06:00–08:30 AM)",
            benchmark_ref="Exp 5 Hist Mean",
        )
    with c3:
        render_metric_card(
            title="Cohort Body Weight",
            value="350.0 g",
            subtitle="Pond-cohort average per fish",
            benchmark_ref="Exp 4 Persistence",
        )
    with c4:
        render_metric_card(
            title="Toxicity Risk Status",
            value="Nominal",
            subtitle="Routine inspection schedule",
            benchmark_ref="Multi-week horizon",
        )

    st.info(
        "ℹ️ **Stage 1 Foundation Active:** Interactive multi-pond attention queue and live dataset tables "
        "will be populated in subsequent implementation stages."
    )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()

