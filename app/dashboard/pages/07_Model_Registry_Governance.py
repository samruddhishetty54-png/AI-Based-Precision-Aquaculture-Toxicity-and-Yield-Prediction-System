"""Page 7: Model Registry Governance & Audit Benchmark Catalog."""

import streamlit as st
from app.dashboard.utils.styles import inject_custom_css
from app.dashboard.components.header import render_page_header
from app.dashboard.components.banners import render_decision_support_banner
from app.dashboard.components.metric_card import render_metric_card
from app.dashboard.components.registry_status import render_registry_status_bar
from app.models.registry import get_model_registry


def render_page() -> None:
    """Render the Model Registry Governance & Audit Benchmark Catalog page."""
    inject_custom_css()

    render_page_header(
        title="Model Registry Governance & Audit Benchmark Catalog",
        subtitle="Audited empirical benchmarks, chemical equilibrium equations, and scientific disclosures.",
        category_key="BENCHMARK",
    )

    render_decision_support_banner()

    st.subheader("Model Registry Operational State")
    registry = get_model_registry()
    render_registry_status_bar(registry)

    st.subheader("Audited Scientific Benchmarks Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        render_metric_card(
            title="Exp 1 Soft-Sensor",
            value="79.6% - 100%",
            subtitle="Underprediction at high NH3",
            benchmark_ref="Screening Only",
        )
    with c2:
        render_metric_card(
            title="Exp 2 Mortality LR",
            value="3.81% Prec.",
            subtitle="Low precision diagnostic",
            benchmark_ref="AUC = 0.5917",
        )
    with c3:
        render_metric_card(
            title="Exp 4 Fish Weight",
            value="93.38 g MAE",
            subtitle="Cohort average persistence",
            benchmark_ref="W_t+1 = W_t",
        )
    with c4:
        render_metric_card(
            title="Exp 5 Mean DO",
            value="3.50 mg/L",
            subtitle="Constant historical baseline",
            benchmark_ref="MAE = 0.3963 mg/L",
        )

    st.info(
        "ℹ️ **Stage 1 Foundation Active:** Complete cryptographic SHA-256 verification table, chemical equilibrium "
        "formulations, and audited confusion matrices will be connected in subsequent stages."
    )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()

