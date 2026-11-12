"""Page 6: Simulated Scenarios Sandbox (Non-Operational)."""

import streamlit as st
from app.dashboard.utils.styles import inject_custom_css
from app.dashboard.components.header import render_page_header
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_simulation_warning_banner,
)
from app.dashboard.components.metric_card import render_metric_card


def render_page() -> None:
    """Render the Simulated Scenarios Sandbox page."""
    inject_custom_css()

    render_page_header(
        title="Simulated Scenarios Sandbox (Non-Operational)",
        subtitle="Synthetic benchmark modeling and hypothetical stress-testing environment.",
        category_key="SIMULATED",
    )

    render_decision_support_banner()
    render_simulation_warning_banner()

    st.markdown(
        "This isolated sandbox allows researchers and farm planners to explore hypothetical water quality scenarios "
        "and inspect model advisory responses under simulated stress conditions. "
        "All outputs here are strictly tagged as **`SIMULATED_SCENARIO_ONLY`** and **`operational_use_permitted = False`**."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card(
            title="Operational Gating",
            value="PROHIBITED",
            subtitle="Demonstration & stress-testing only",
            benchmark_ref="operational_use = False",
        )
    with c2:
        render_metric_card(
            title="Synthetic Dataset",
            value="IoT Model v2",
            subtitle="Hourly mathematical simulation",
            benchmark_ref="iot_water_model_v2.csv",
        )
    with c3:
        render_metric_card(
            title="Isolation Boundary",
            value="100% Segregated",
            subtitle="Separated from commercial field data",
            benchmark_ref="Sandbox Environment",
        )

    st.info(
        "ℹ️ **Stage 1 Foundation Active:** Synthetic scenario injection controls, extreme parameter simulators, "
        "and simulated advisory responses will be connected in subsequent stages."
    )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()

