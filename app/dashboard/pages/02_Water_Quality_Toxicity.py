"""Page 2: Water Quality Chemistry & Experimental Toxicity Screening."""

import streamlit as st
from app.dashboard.utils.styles import inject_custom_css
from app.dashboard.components.header import render_page_header
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_multi_week_observation_banner,
)
from app.dashboard.components.metric_card import render_metric_card


def render_page() -> None:
    """Render the Water Quality Chemistry & Toxicity Screening page."""
    inject_custom_css()

    render_page_header(
        title="Water Quality Chemistry & Experimental Toxicity Screening",
        subtitle="Emerson dissociation equilibrium chemistry and experimental ML screening proxies.",
        category_key="EXPERIMENTAL",
    )

    render_decision_support_banner()
    render_multi_week_observation_banner()

    # Empirical Warnings Card
    st.warning(
        "⚠️ **Experimental Screening Notice (Do Not Use as Independent Emergency Alarms):**\n"
        "- **Experiment 1 Soft-Sensor:** Demonstrates severe underprediction at elevated ammonia levels "
        "(79.6% underprediction at ≥ 0.05 mg/L; 100% underprediction at ≥ 0.10 mg/L).\n"
        "- **Experiment 2 Mortality Diagnostic:** High false alarm rate (precision 3.81%; 227 false alarms / 236 alerts).\n"
        "- **TAN 2.0 mg/L Value:** Represents a standard chemical test-kit graduation, NOT a validated biological toxicity threshold."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card(
            title="Aqueous Chemistry",
            value="Emerson (1975)",
            subtitle="Equilibrium NH3 / NH4+ dissociation",
            benchmark_ref="Analytical Chemistry",
        )
    with c2:
        render_metric_card(
            title="Exp 1 Soft-Sensor Tier",
            value="Screening Only",
            subtitle="Tiered underprediction warning",
            benchmark_ref="Holdout N=98",
        )
    with c3:
        render_metric_card(
            title="Exp 2 Mortality Precision",
            value="3.81%",
            subtitle="Low-precision diagnostic",
            benchmark_ref="ROC-AUC 0.5917",
        )

    st.info(
        "ℹ️ **Stage 1 Foundation Active:** Interactive chemical evaluation form, Emerson calculator, "
        "and experimental diagnostic inference cards will be connected in subsequent stages."
    )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()

