"""Page 6: Simulated Scenarios Sandbox (Non-Operational).

Operational Category: SIMULATED (Synthetic Benchmark Modeling & Hypothetical Stress-Testing).
Provides:
1. Isolated Testing Environment: Completely segregated from commercial farm inspection workflows.
   Never mixed with or saved to historical field databases.
2. Synthetic Data Explorer: Dedicated viewer for iot_water_model_v2.csv (hourly mathematical
   simulation model from Data_Model_IoTMLCQ_2024.xlsx).
   Explicitly communicates that this is an hourly mathematical simulation, NOT physical sensor telemetry.
3. What-If Scenario Stress Simulator: Allows users to inject extreme synthetic water conditions
   (e.g. acute hypoxia, thermal extremes, ammonia spikes) and observe model responses.
4. Persistent Simulation Watermarking: Every output is tagged as SIMULATED_SCENARIO_ONLY with
   operational_use_permitted = False and PROHIBITED for live farm management.
"""

from typing import Dict, Any, Optional
import math
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from app.dashboard.utils.styles import inject_custom_css, PALETTE
from app.dashboard.utils.helpers import (
    format_float,
    format_percentage,
    validate_defensive_bounds,
    detect_simulation_source,
)
from app.dashboard.components.header import render_page_header
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_simulation_warning_banner,
)
from app.dashboard.components.metric_card import render_metric_card
from app.core.data_manager import load_dataset
from app.core.chemistry import (
    calculate_pka,
    calculate_unionized_fraction,
    calculate_nh3_from_tan_n,
)
from app.models.registry import get_model_registry


def render_synthetic_time_series_chart(df_iot: pd.DataFrame) -> go.Figure:
    """Render Plotly chart showing hourly synthetic simulation time series."""
    # Subsample every 12 hours for smooth interactive rendering
    df_sample = df_iot.iloc[::12].copy()
    df_sample["dt"] = pd.to_datetime(df_sample["datetime_iso"])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_sample["dt"],
            y=df_sample["Dissolved Oxygen (mg/L)"],
            mode="lines",
            name="Simulated DO (mg/L)",
            line=dict(color="#0284c7", width=1.5),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df_sample["dt"],
            y=df_sample["Temperature (°C)"],
            mode="lines",
            name="Simulated Temp (°C)",
            line=dict(color="#d97706", width=1.5),
            yaxis="y2",
        )
    )

    fig.update_layout(
        title="Hourly Synthetic Simulation Time Series (iot_water_model_v2.csv)",
        xaxis_title="Simulation Timeline (2024)",
        yaxis_title="Dissolved Oxygen (mg/L)",
        yaxis2=dict(
            title="Temperature (°C)",
            overlaying="y",
            side="right",
            showgrid=False,
        ),
        template="plotly_white",
        height=340,
        margin=dict(l=40, r=40, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


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

    # Mandatory Persistent Gating Notice
    st.markdown(
        """
        <div style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; background-color: #fffbeb; border: 2px solid #d97706; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1.25rem;">
            <div style="font-size: 0.8rem; text-transform: uppercase; color: #b45309; font-weight: 700; letter-spacing: 0.05em;">
                Quarantined Simulation Environment • Operational Use Strictly Prohibited
            </div>
            <div style="font-size: 1.3rem; font-weight: 800; color: #92400e; margin-top: 0.25rem;">
                Status: SIMULATED_SCENARIO_ONLY • operational_use_permitted = False
            </div>
            <div style="font-size: 0.85rem; color: #78350f; margin-top: 0.5rem;">
                This sandbox is completely segregated from commercial farm inspection workflows.
                All scenarios and calculations are purely synthetic mathematical demonstrations for model stress-testing.
                Commercial operational deployment is <strong>PROHIBITED</strong>.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Section 1: Synthetic Dataset Explorer (iot_water_model_v2.csv)
    st.markdown("### 1. Synthetic Reference Simulation Dataset (iot_water_model_v2.csv)")
    st.caption(
        "Hourly reference simulation time series generated from Data_Model_IoTMLCQ_2024.xlsx. "
        "Explicitly a mathematical simulation benchmark model, NOT live physical IoT telemetry from commercial aquaculture ponds."
    )

    try:
        df_iot = load_dataset("iot_water_model")
        total_rows = len(df_iot)
        mean_sim_do = df_iot["Dissolved Oxygen (mg/L)"].mean()
        mean_sim_temp = df_iot["Temperature (°C)"].mean()
        mean_sim_ph = df_iot["pH"].mean()
        mean_sim_weight = df_iot["Average Fish Weight (g)"].mean()
    except Exception as exc:
        st.error(f"Error loading synthetic dataset: {exc}")
        total_rows = 4383
        mean_sim_do = 6.34
        mean_sim_temp = 28.5
        mean_sim_ph = 7.98
        mean_sim_weight = 275.8
        df_iot = pd.DataFrame()

    sc1, sc2, sc3, sc4 = st.columns(4)
    with sc1:
        render_metric_card(
            title="Synthetic Records",
            value=f"{total_rows:,} Rows",
            subtitle="Hourly mathematical series",
            benchmark_ref="iot_water_model_v2.csv",
        )
    with sc2:
        render_metric_card(
            title="Simulated Mean DO",
            value=f"{mean_sim_do:.2f} mg/L",
            subtitle="Synthetic dissolved oxygen",
            benchmark_ref="Mathematical Model",
        )
    with sc3:
        render_metric_card(
            title="Simulated Mean Temp",
            value=f"{mean_sim_temp:.1f} °C",
            subtitle=f"Simulated pH: {mean_sim_ph:.2f}",
            benchmark_ref="Synthetic Climate",
        )
    with sc4:
        render_metric_card(
            title="Operational Gating",
            value="PROHIBITED",
            subtitle="Demonstration only",
            benchmark_ref="operational_use = False",
        )

    if not df_iot.empty:
        st.plotly_chart(render_synthetic_time_series_chart(df_iot), use_container_width=True)

    # Section 2: What-If Hypothetical Scenario Stress Simulator
    st.markdown("---")
    st.markdown("### 2. What-If Hypothetical Scenario Stress Simulator")
    st.caption(
        "Inject extreme or borderline synthetic water conditions to inspect how system models and advisory heuristics respond. "
        "Software validation bounds reject unphysical numbers. Results are strictly quarantined from operational records."
    )

    with st.form("what_if_scenario_form"):
        st.markdown("#### Hypothetical Synthetic Conditions")
        c1, c2, c3 = st.columns(3)
        with c1:
            sim_do = st.slider(
                "Synthetic Morning DO (mg/L):",
                min_value=0.0,
                max_value=12.0,
                value=1.50,
                step=0.1,
                help="Inject severe hypoxia (< 2.0 mg/L), moderate hypoxia (2.0–3.0 mg/L), or optimal DO (> 4.0 mg/L).",
            )
            sim_ph = st.slider(
                "Synthetic Water pH:",
                min_value=4.0,
                max_value=11.0,
                value=8.60,
                step=0.1,
                help="Inject acid stress (< 6.5) or alkaline ammonia-promoting stress (> 8.5).",
            )
        with c2:
            sim_temp = st.slider(
                "Synthetic Water Temperature (°C):",
                min_value=15.0,
                max_value=42.0,
                value=32.0,
                step=0.5,
                help="Inject thermal cold stress (< 20°C) or thermal heat stress (> 34°C).",
            )
            sim_tan = st.slider(
                "Synthetic Total Ammonia (TAN, mg/L):",
                min_value=0.0,
                max_value=15.0,
                value=2.50,
                step=0.25,
                help="Inject elevated TAN. Note: 2.0 mg/L TAN is a test-kit graduation mark, NOT a validated biological toxicity threshold.",
            )
        with c3:
            sim_feed = st.slider(
                "Synthetic Baseline Feed (kg/day):",
                min_value=0.0,
                max_value=200.0,
                value=50.0,
                step=5.0,
                help="Hypothetical baseline feeding schedule before stress throttling.",
            )
            sim_weight = st.slider(
                "Synthetic Fish Cohort Weight (g/fish):",
                min_value=10.0,
                max_value=1000.0,
                value=180.0,
                step=10.0,
                help="Somatic cohort average body weight per fish.",
            )

        sim_submitted = st.form_submit_button("Simulate Hypothetical Scenario & Inspect Model Responses", use_container_width=True)

    # Section 3: Quarantined Multi-Model Simulated Response
    st.markdown("---")
    st.markdown("### 3. Quarantined Multi-Model Simulation Response")
    st.caption("All model responses below are generated under is_simulated = True and data_source = 'benchmark_simulation'.")

    # 1. Chemical dissociation (Emerson et al., 1975)
    sim_pka = calculate_pka(sim_temp)
    sim_f = calculate_unionized_fraction(sim_ph, sim_temp)
    sim_nh3 = calculate_nh3_from_tan_n(sim_tan, sim_ph, sim_temp, round_digits=5)

    # 2. Model Registry Execution in Simulation Mode
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

    # Simulation Gating Status Verification
    st.markdown(
        f"""
        <div style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; background-color: #fffbeb; border: 1px solid #fcd34d; border-left: 4px solid #f59e0b; padding: 0.75rem 1rem; border-radius: 4px; font-size: 0.88rem; color: #78350f; font-weight: 500; margin-bottom: 1rem;">
            <strong>SIMULATED GATING CONFIRMATION:</strong><br>
            • Advisory Status: <code>{res_feed.get('status')}</code><br>
            • Operational Use Permitted: <code>{res_feed.get('operational_use_permitted')}</code> (Strictly False)<br>
            • Action Identifier: <code>{res_feed.get('advisory_action')}</code><br>
            • Demonstration Notice: <em>{res_feed.get('demonstration_warning', 'Simulated Scenario Only')}</em>
        </div>
        """,
        unsafe_allow_html=True,
    )

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
            benchmark_ref="Synthetic Response",
        )
    with mr4:
        render_metric_card(
            title="Point DO Benchmark",
            value="3.50 mg/L",
            subtitle="Historical Training Mean",
            benchmark_ref="Constant Reference",
        )

    # Explanation bullets
    st.markdown("#### Simulated Advisory Throttle Explanations")
    throttles = res_feed.get("throttling_factors", {})
    t_col1, t_col2, t_col3 = st.columns(3)
    with t_col1:
        st.markdown(f"**DO Throttle:** `{throttles.get('do_multiplier', 1.0) * 100:.0f}%` ({throttles.get('do_status')})")
    with t_col2:
        st.markdown(f"**Ammonia Throttle:** `{throttles.get('ammonia_multiplier', 1.0) * 100:.0f}%` ({throttles.get('ammonia_status')})")
    with t_col3:
        st.markdown(f"**Temp Throttle:** `{throttles.get('temperature_multiplier', 1.0) * 100:.0f}%`")

    for exp in res_feed.get("advisory_explanations", []):
        st.markdown(f"- {exp}")

    # Section 4: Strict Isolation & Non-Contamination Policy
    st.markdown("---")
    st.markdown("### 4. Strict Isolation & Data Protection Boundary")
    st.markdown(
        """
        - **Isolation Integrity:** Simulated scenarios are purely in-memory mathematical demonstrations. They are never written to `processed_data_v2/`, never logged as real pond records, and never used to calculate operational benchmarks.
        - **Operational Prohibition:** Real farm management, feeding adjustments, or aeration triggers must NEVER be based on simulated scenario outputs (`operational_use_permitted = False`).
        - **Zero Hardware Actuation:** The simulation environment operates in strict software isolation with zero actuator commands (`is_automatic_control = False`).
        """
    )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
