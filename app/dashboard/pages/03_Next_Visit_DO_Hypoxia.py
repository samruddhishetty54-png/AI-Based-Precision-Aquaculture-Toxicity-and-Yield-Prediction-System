"""Page 3: Next-Visit Morning DO and Hypoxia Screening."""

import streamlit as st
from app.dashboard.utils.styles import inject_custom_css
from app.dashboard.components.header import render_page_header
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_multi_week_observation_banner,
)
from app.dashboard.components.metric_card import render_metric_card


def render_page() -> None:
    """Render the Next-Visit Morning DO and Hypoxia Screening page."""
    inject_custom_css()

    render_page_header(
        title="Next-Visit Morning DO and Hypoxia Screening",
        subtitle="Historical mean DO benchmark and exploratory Gradient Boosting moderate-hypoxia screening.",
        category_key="BENCHMARK",
    )

    render_decision_support_banner()
    render_multi_week_observation_banner()

    # Mandatory Scientific Governance Disclaimers
    st.info(
        "📌 **Scientific & Modeling Context (Experiment 5):**\n"
        "- **Historical Mean DO Benchmark = 3.4984 mg/L:** This is an unconditional constant historical "
        "training mean benchmark (MAE 0.3963 mg/L, RMSE 0.6450 mg/L), **NOT a dynamic biological prediction**.\n"
        "- **Observation Window:** Represents **morning DO observations (06:00–08:30 AM)** across scheduled "
        "farm visits (3–45 days interval; median ~21 days). These observations **are NOT verified pre-dawn daily minimum DO**.\n"
        "- **Zero Real-Time Claims:** No continuous sensor streaming, diurnal cycling, hourly forecasts, or overnight predictions.\n"
        "- **Exploratory Moderate Hypoxia Screening (< 3.0 mg/L):** The Gradient Boosting classifier (p* = 0.090) has a "
        "**91.00% False Discovery Rate** (930 false alarms, 1,022 total alerts). It is strictly an exploratory screening "
        "score for inspection queues, **NEVER an automated emergency alert**.\n"
        "- **Severe Hypoxia Rejection (< 2.0 mg/L):** The Random Forest severe hypoxia classifier was **REJECTED AS DEGENERATE** "
        "(99.56% false alarm rate due to class_weight distortion) and is disabled."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card(
            title="Point Benchmark",
            value="3.50 mg/L",
            subtitle="Constant historical training mean (3.4984 mg/L)",
            benchmark_ref="MAE = 0.3963 mg/L",
        )
    with c2:
        render_metric_card(
            title="Moderate Hypoxia Screening",
            value="p* = 0.090",
            subtitle="GBDT exploratory score (91% FDR)",
            benchmark_ref="50.25% Alarm Rate",
        )
    with c3:
        render_metric_card(
            title="Severe Hypoxia (<2.0 mg/L)",
            value="REJECTED",
            subtitle="RF classifier degenerate (99.56% alarms)",
            benchmark_ref="Disabled by Governance",
        )

    st.info(
        "ℹ️ **Stage 1 Foundation Active:** Interactive DO projection card, visit horizon slider, "
        "and exploratory hypoxia risk screening outputs will be connected in subsequent stages."
    )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()

