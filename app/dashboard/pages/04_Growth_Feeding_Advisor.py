"""Page 4: Next-Visit Pond-Cohort Fish Weight Benchmark & Provisional Feeding Advisory."""

import streamlit as st
from app.dashboard.utils.styles import inject_custom_css
from app.dashboard.components.header import render_page_header
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_multi_week_observation_banner,
)
from app.dashboard.components.metric_card import render_metric_card


def render_page() -> None:
    """Render the Fish Weight Benchmark & Feeding Advisory page."""
    inject_custom_css()

    render_page_header(
        title="Next-Visit Pond-Cohort Fish Weight Benchmark & Provisional Feeding Advisory",
        subtitle="Persistence baseline for cohort average fish weight and provisional feeding heuristics.",
        category_key="ADVISORY",
    )

    render_decision_support_banner()
    render_multi_week_observation_banner()

    # Mandatory Scientific Governance Disclaimers
    st.info(
        "📌 **Target Definition & Feeding Heuristics Governance:**\n"
        "- **Modeling Target (Experiment 4):** Strictly **next-visit pond-cohort average fish weight** (grams/fish).\n"
        "- **Negative Scope:** This is **NOT individual fish growth**, **NOT harvest biomass**, and **NOT total commercial yield in kg/ha**.\n"
        "- **Analytical Reference Benchmark:** The reported **MAE = 93.38 g** belongs to the all-pairs chronological "
        "persistence baseline (W_t+1 = W_t). It is an analytical reference standard, **not a reliable dynamic growth predictor**.\n"
        "- **Provisional Feeding Heuristics:** All feed adjustments are **provisional decision-support heuristics requiring human verification**, "
        "derived from extension literature and test-kit graduations (e.g. TAN 2.0 mg/L is a test-kit graduation, NOT a validated toxicity threshold).\n"
        "- **Causality Disclaimer:** Feed reductions mitigate biochemical oxygen demand (BOD) and waste accumulation, "
        "but **do not cause immediate water quality recovery** or cure hypoxia.\n"
        "- **Observational Feedback Logging:** Farmer feedback logs observational transitions for retrospective human review; "
        "it **does NOT execute causal learning, reinforcement learning, or automatic parameter updates**."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        render_metric_card(
            title="Weight Target",
            value="Cohort Avg (g/fish)",
            subtitle="Next-visit pond-cohort average",
            benchmark_ref="Not Harvest Yield (kg/ha)",
        )
    with c2:
        render_metric_card(
            title="Persistence Benchmark",
            value="W_t+1 = W_t",
            subtitle="Chronological baseline reference",
            benchmark_ref="MAE = 93.38 g",
        )
    with c3:
        render_metric_card(
            title="Feeding Guidance",
            value="Provisional Heuristic",
            subtitle="Human verification required",
            benchmark_ref="No Automated Actuation",
        )

    st.info(
        "ℹ️ **Stage 1 Foundation Active:** Interactive fish weight estimation, provisional rule-based feeding throttle engine, "
        "and observational feedback logging form will be connected in subsequent stages."
    )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()

