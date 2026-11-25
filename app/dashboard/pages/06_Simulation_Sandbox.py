"""Page 6: Simulated Scenarios Sandbox (Non-Operational).

Operational Category: SIMULATED (Synthetic Benchmark Modeling & Hypothetical Stress-Testing).
Provides:
1. Isolated What-If Scenario Stress Simulator (strictly quarantined, operational_use_permitted = False).
2. Synthetic Reference Simulation Explorer for iot_water_model_v2.csv.
3. Expandable isolation and non-contamination governance policy.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.core.chemistry import calculate_nh3_from_tan_n, calculate_unionized_fraction
from app.core.data_manager import load_dataset
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_simulation_warning_banner,
)
from app.dashboard.components.header import render_page_header
from app.dashboard.components.metric_card import render_metric_card
from app.dashboard.utils.helpers import format_percentage
from app.dashboard.utils.styles import inject_custom_css
from app.models.registry import get_model_registry


def render_synthetic_time_series_chart(df_iot: pd.DataFrame) -> go.Figure:
    """Render Plotly chart showing hourly synthetic simulation time series."""
    df_sample = df_iot.iloc[::12].copy()
    df_sample["dt"] = pd.to_datetime(df_sample["datetime_iso"])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_sample["dt"],
            y=df_sample["Dissolved Oxygen (mg/L)"],
            mode="lines",
            name="Simulated DO (mg/L)",
            line=dict(color="#087F72", width=1.8),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_sample["dt"],
            y=df_sample["Temperature (°C)"],
            mode="lines",
            name="Simulated Temp (°C)",
            line=dict(color="#E7A23B", width=1.8),
            yaxis="y2",
        )
    )

    fig.update_layout(
        title=dict(
            text="Hourly Synthetic Simulation Time Series (iot_water_model_v2.csv)",
            font=dict(size=14, color="#173747"),
        ),
        xaxis_title="Simulation Timeline (2024)",
        yaxis_title="Dissolved Oxygen (mg/L)",
        yaxis2=dict(
            title="Temperature (°C)",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        template="plotly_white",
        height=300,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#f1f5f9"),
    )
    return fig


def render_page() -> None:
    """Render the Simulated Scenarios Sandbox page."""
    inject_custom_css()

    render_page_header(
        title="Simulated Scenarios Sandbox (Non-Operational)",
        subtitle="Quarantined synthetic benchmark modeling and hypothetical stress-testing.",
        category_key="SIMULATED",
    )

    render_decision_support_banner()
    render_simulation_warning_banner()

    st.warning(
        "**Quarantine Status:** `SIMULATED_SCENARIO_ONLY` | `operational_use_permitted = False` | "
        "Operational farm deployment is **PROHIBITED**."
    )

    # ── What-If Scenario Stress Simulator ─────────────────────────────
    st.subheader("What-If Scenario Stress Simulator")
    st.caption("Inject hypothetical conditions to inspect quarantined model and feeding-heuristic responses.")

    with st.form("what_if_scenario_form"):
        c1, c2 = st.columns(2)
        with c1:
            sim_do = st.slider("Synthetic Morning DO (mg/L):", min_value=0.0, max_value=12.0, value=1.50, step=0.1)
            sim_ph = st.slider("Synthetic Water pH:", min_value=4.0, max_value=11.0, value=8.60, step=0.1)
            sim_temp = st.slider("Synthetic Water Temperature (°C):", min_value=15.0, max_value=42.0, value=32.0, step=0.5)
        with c2:
            sim_tan = st.slider(
                "Synthetic Total Ammonia (TAN, mg/L):",
                min_value=0.0,
                max_value=15.0,
                value=2.50,
                step=0.25,
                help="2.0 mg/L TAN is a test-kit graduation mark, NOT a validated toxicity threshold.",
            )
            sim_feed = st.slider("Synthetic Baseline Feed (kg/day):", min_value=0.0, max_value=200.0, value=50.0, step=5.0)
            sim_weight = st.slider("Synthetic Fish Cohort Weight (g/fish):", min_value=10.0, max_value=1000.0, value=180.0, step=10.0)

        st.form_submit_button("Simulate Hypothetical Scenario", use_container_width=True)

    # Execute quarantined models
    sim_f = calculate_unionized_fraction(sim_ph, sim_temp)
    sim_nh3 = calculate_nh3_from_tan_n(sim_tan, sim_ph, sim_temp, round_digits=5)

    registry = get_model_registry()
    feed_payload = {
        "dissolved_oxygen_mg_l": float(sim_do),
        "temp_c": float(sim_temp),
        "ammonia_tan_nh3_n_mg_l": float(sim_tan),
        "primary_calculated_nh3_mg_l": float(sim_nh3) if pd.notna(sim_nh3) else None,
        "current_feed_amount_kg": float(sim_feed),
        "average_fish_weight_g": float(sim_weight),
        "is_simulated": True,
        "data_source": "benchmark_simulation",
    }
    do_payload = {
        "curr_do": float(sim_do),
        "gap_days": 21.0,
        "is_simulated": True,
        "data_source": "benchmark_simulation",
    }
    weight_payload = {
        "current_weight_g": float(sim_weight),
        "gap_days": 21.0,
        "curr_do": float(sim_do),
        "is_simulated": True,
    }

    try:
        res_feed = registry.get_feeding_advisory(feed_payload)
        res_do = registry.predict_do_hypoxia(do_payload)
        res_weight = registry.predict_fish_growth(weight_payload)
    except Exception as exc:
        st.error(f"Error executing simulated model responses: {exc}")
        return

    # Simulated Results KPIs
    st.subheader("Quarantined Simulation Response")
    mr1, mr2, mr3, mr4 = st.columns(4)
    with mr1:
        render_metric_card(
            title="Simulated Molecular NH3",
            value=f"{sim_nh3:.4f} mg/L" if pd.notna(sim_nh3) else "N/A",
            subtitle=f"f = {format_percentage(sim_f, decimals=2)}",
            benchmark_ref="Emerson (1975) Sim",
        )
    with mr2:
        render_metric_card(
            title="Simulated Advisory Action",
            value=res_feed.get("advisory_action", "N/A").replace("SIMULATED_", ""),
            subtitle=f"{res_feed.get('reduction_percentage', 0.0):.0f}% Reduction Applied",
            benchmark_ref="Provisional Heuristic",
        )
    with mr3:
        render_metric_card(
            title="Simulated Adjusted Feed",
            value=f"{res_feed.get('recommended_feed_kg', 0.0):.1f} kg/day",
            subtitle=f"From baseline {sim_feed:.1f} kg/day",
            benchmark_ref=f"Status: {res_feed.get('status')}",
        )
    with mr4:
        render_metric_card(
            title="DO / Weight Benchmarks",
            value=f"{res_do.get('predicted_next_do_mg_l', 3.50):.2f} mg/L",
            subtitle=f"Cohort Weight: {res_weight.get('predicted_next_weight_g', sim_weight):.0f} g",
            benchmark_ref="Constant / Persistence",
        )

    with st.expander("Simulated Throttle Breakdown & Gating Confirmation", expanded=False):
        throttles = res_feed.get("throttling_factors", {})
        st.markdown(
            f"- **Gating:** `status = {res_feed.get('status')}`, `operational_use_permitted = {res_feed.get('operational_use_permitted')}`\n"
            f"- **DO Throttle:** `{throttles.get('do_multiplier', 1.0) * 100:.0f}%` ({throttles.get('do_status')})\n"
            f"- **Ammonia Throttle:** `{throttles.get('ammonia_multiplier', 1.0) * 100:.0f}%` ({throttles.get('ammonia_status')})\n"
            f"- **Temp Throttle:** `{throttles.get('temperature_multiplier', 1.0) * 100:.0f}%`"
        )
        for exp in res_feed.get("advisory_explanations", []):
            st.markdown(f"- {exp}")

    # ── Synthetic Reference Dataset Explorer ──────────────────────────
    st.markdown("---")
    st.subheader("Synthetic Reference Series (iot_water_model_v2.csv)")
    st.caption(
        "Explicitly a mathematical simulation benchmark model, NOT live physical IoT telemetry "
        "from commercial aquaculture ponds."
    )

    try:
        df_iot = load_dataset("iot_water_model")
        total_rows = len(df_iot)
        mean_sim_do = df_iot["Dissolved Oxygen (mg/L)"].mean()
        mean_sim_temp = df_iot["Temperature (°C)"].mean()
        mean_sim_ph = df_iot["pH"].mean()
    except Exception as exc:
        st.error(f"Error loading synthetic dataset: {exc}")
        total_rows, mean_sim_do, mean_sim_temp, mean_sim_ph = 4383, 6.34, 28.5, 7.98
        df_iot = pd.DataFrame()

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        render_metric_card(title="Synthetic Records", value=f"{total_rows:,} Rows", subtitle="Hourly mathematical series", benchmark_ref="iot_water_model_v2.csv")
    with sc2:
        render_metric_card(title="Simulated Mean DO", value=f"{mean_sim_do:.2f} mg/L", subtitle="Synthetic dissolved oxygen", benchmark_ref="Mathematical Model")
    with sc3:
        render_metric_card(title="Simulated Mean Temp", value=f"{mean_sim_temp:.1f} °C", subtitle=f"Simulated pH: {mean_sim_ph:.2f}", benchmark_ref="Synthetic Climate")
    with sc4:
        render_metric_card(title="Operational Gating", value="PROHIBITED", subtitle="Demonstration only", benchmark_ref="operational_use = False")

    if not df_iot.empty:
        st.plotly_chart(render_synthetic_time_series_chart(df_iot), use_container_width=True)

    with st.expander("Strict Isolation & Data Protection Boundary", expanded=False):
        st.markdown(
            """
            - **Isolation Integrity:** Simulated scenarios are purely in-memory mathematical demonstrations. They are never written to `processed_data_v2/`, never logged as real pond records, and never used to calculate operational benchmarks.
            - **Operational Prohibition:** Real farm management, feeding adjustments, or aeration triggers must NEVER be based on simulated scenario outputs (`operational_use_permitted = False`).
            - **Zero Hardware Actuation:** The simulation environment operates in strict software isolation with zero actuator commands (`is_automatic_control = False`).
            """
        )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
