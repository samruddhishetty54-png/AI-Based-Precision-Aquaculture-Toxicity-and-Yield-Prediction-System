"""Page 4: Live Simulation – Precision AquaDSS.

Operational Category: SIMULATED (Synthetic Sensor Simulation, Scenario Stress-Testing & Dynamic Adaptation).
Provides:
1. Real-Time Simulated Sensor Monitoring: Generates changing sample sensor readings
   for pH, Temperature, Ammonia, and Dissolved Oxygen.
2. Interactive Controls: Start / Step, Pause, Reset, and Scenario Selection:
   - Normal conditions
   - Increasing ammonia
   - Overfeeding scenario
   - Low dissolved oxygen (Hypoxia)
   - High temperature
   - Custom scenario
3. Updating Live Trend Charts: Plotly time-series visualising simulated sensor streams.
4. Dynamic Risk Alerts: Triggers immediate visual warnings when simulated values breach safe thresholds.
5. Adaptive Feeding Guidance: Demonstrates real-time feeding recommendation changes and prevented feed waste.
6. Quarantine Governance: Prominently labelled "SIMULATED SENSOR DATA – FOR DEMONSTRATION AND TESTING ONLY"
   with operational_use_permitted = False, is_automatic_control = False, and zero physical sensor claims.
"""

from typing import Dict, Any, List
import random
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from app.core.chemistry import calculate_nh3_from_tan_n, calculate_unionized_fraction
from app.core.data_manager import load_dataset
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_simulation_warning_banner,
)
from app.dashboard.components.header import render_page_header, render_section_bar
from app.dashboard.components.metric_card import render_metric_card
from app.dashboard.utils.helpers import (
    format_percentage,
    get_active_farm_type,
    get_container_label,
    get_container_id_label,
    get_farm_type_disclaimer,
    log_prediction_event,
    FREE_PLATFORM_NOTICE,
)
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


def initialize_simulation_state() -> None:
    """Initialize or reset live simulation time-series state in session."""
    st.session_state["live_sim_running"] = False
    st.session_state["live_sim_hour"] = 0
    st.session_state["live_sim_history"] = [
        {
            "hour": 0,
            "do": 5.80,
            "ph": 7.70,
            "temp": 28.0,
            "tan": 0.35,
            "nh3": 0.0125,
            "feed_baseline": 50.0,
            "feed_recommended": 50.0,
            "status": "Optimal",
        }
    ]


def advance_simulation_step(scenario: str, custom_vals: Dict[str, float]) -> None:
    """Advance simulation by 1 synthetic hour according to scenario rules."""
    history = st.session_state.get("live_sim_history", [])
    if not history:
        initialize_simulation_state()
        history = st.session_state["live_sim_history"]

    last = history[-1]
    new_h = last["hour"] + 1

    if scenario == "Normal conditions":
        # Natural oscillating diurnal conditions
        do = max(4.5, min(7.5, last["do"] + random.uniform(-0.15, 0.15)))
        ph = max(7.4, min(8.1, last["ph"] + random.uniform(-0.05, 0.05)))
        temp = max(26.0, min(30.0, last["temp"] + random.uniform(-0.2, 0.2)))
        tan = max(0.2, min(0.6, last["tan"] + random.uniform(-0.03, 0.03)))
        feed_b = 50.0
    elif scenario == "Increasing ammonia":
        # Steady consecutive rise in TAN and ammonia
        do = max(3.5, last["do"] - 0.2)
        ph = min(8.4, last["ph"] + 0.08)
        temp = min(31.5, last["temp"] + 0.3)
        tan = last["tan"] + 0.35
        feed_b = 60.0
    elif scenario == "Overfeeding scenario":
        # Rapid organic accumulation
        do = max(2.1, last["do"] - 0.45)
        ph = min(8.65, last["ph"] + 0.12)
        temp = min(32.0, last["temp"] + 0.2)
        tan = last["tan"] + 0.65
        feed_b = 85.0
    elif scenario == "Low dissolved oxygen":
        # Precipitous morning hypoxia drop
        do = max(0.9, last["do"] - 0.75)
        ph = max(7.2, last["ph"] - 0.05)
        temp = last["temp"]
        tan = last["tan"] + 0.05
        feed_b = 55.0
    elif scenario == "High temperature":
        # Thermal surge
        do = max(3.2, last["do"] - 0.3)
        ph = min(8.9, last["ph"] + 0.15)
        temp = min(36.5, last["temp"] + 1.2)
        tan = last["tan"] + 0.15
        feed_b = 65.0
    else:  # Custom scenario
        do = custom_vals["do"] + random.uniform(-0.05, 0.05)
        ph = custom_vals["ph"] + random.uniform(-0.02, 0.02)
        temp = custom_vals["temp"] + random.uniform(-0.1, 0.1)
        tan = custom_vals["tan"] + random.uniform(-0.02, 0.02)
        feed_b = custom_vals["feed"]

    nh3 = calculate_nh3_from_tan_n(tan, ph, temp, round_digits=5)

    # Evaluate provisional feeding advisory
    registry = get_model_registry()
    feed_payload = {
        "dissolved_oxygen_mg_l": float(do),
        "temp_c": float(temp),
        "ammonia_tan_nh3_n_mg_l": float(tan),
        "primary_calculated_nh3_mg_l": float(nh3) if pd.notna(nh3) else None,
        "current_feed_amount_kg": float(feed_b),
        "average_fish_weight_g": 180.0,
        "is_simulated": True,
        "data_source": "benchmark_simulation",
    }
    adv_res = registry.get_feeding_advisory(feed_payload)
    rec_feed = adv_res.get("recommended_feed_kg", feed_b)

    # Determine status
    if do < 2.0 or (pd.notna(nh3) and nh3 >= 0.10):
        status = "Emergency Critical"
    elif do < 3.0 or (pd.notna(nh3) and nh3 >= 0.05):
        status = "Hazard Warning"
    elif do < 4.0 or (pd.notna(nh3) and nh3 >= 0.02):
        status = "Suboptimal Caution"
    else:
        status = "Optimal"

    history.append({
        "hour": new_h,
        "do": round(do, 2),
        "ph": round(ph, 2),
        "temp": round(temp, 1),
        "tan": round(tan, 2),
        "nh3": round(nh3, 4) if pd.notna(nh3) else 0.0,
        "feed_baseline": feed_b,
        "feed_recommended": round(rec_feed, 1),
        "status": status,
    })
    st.session_state["live_sim_history"] = history
    st.session_state["live_sim_hour"] = new_h


def render_page() -> None:
    """Render the Live Simulation page."""
    inject_custom_css()

    farm_type = get_active_farm_type()
    container_label = get_container_label(farm_type)

    render_page_header(
        title="Live Simulation",
        subtitle=f"Interactive synthetic sensor monitoring, dynamic alerts, and real-time feeding adaptation ({farm_type}).",
        category_key="SIMULATED",
    )

    # ── Mandatory Simulation Labelling ────────────────────────────────
    st.markdown(
        """
        <div style="background-color: #FEF3C7; border: 1px solid #F59E0B; border-left: 5px solid #D97706; border-radius: 8px; padding: 0.85rem 1rem; margin-bottom: 0.9rem;">
            <div style="font-weight: 800; font-size: 0.88rem; color: #92400E; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.25rem;">
                ⚠️ SIMULATED SENSOR DATA – FOR DEMONSTRATION AND TESTING ONLY
            </div>
            <div style="font-size: 0.80rem; color: #78350F; line-height: 1.45;">
                This module generates changing synthetic readings to test predictive models and early warnings.
                <strong>Readings do NOT represent actual physical sensor telemetry</strong> and are quarantined from farm records
                (<code>operational_use_permitted = False</code>, <code>is_automatic_control = False</code>).
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if "live_sim_history" not in st.session_state:
        initialize_simulation_state()

    history = st.session_state.get("live_sim_history", [])
    current_step = history[-1] if history else {}

    # ── Simulation Scenarios & Control Panel ──────────────────────────
    render_section_bar("Simulation Controls & Scenario Selection")

    SCENARIOS = [
        "Normal conditions",
        "Increasing ammonia",
        "Overfeeding scenario",
        "Low dissolved oxygen",
        "High temperature",
        "Custom scenario",
    ]

    c_scen, c_act1, c_act2, c_act3 = st.columns([2.2, 1, 1, 1])

    with c_scen:
        selected_scenario = st.selectbox(
            "Select Environmental Scenario:",
            options=SCENARIOS,
            index=1,  # Default to increasing ammonia to demonstrate early warning
            key="live_sim_scenario_select",
        )

    with c_act1:
        st.write("")
        st.write("")
        if st.button("▶️ Step (+1h)", use_container_width=True, help="Advance simulation by 1 synthetic hour"):
            advance_simulation_step(selected_scenario, {
                "do": st.session_state.get("sim_custom_do", 4.5),
                "ph": st.session_state.get("sim_custom_ph", 7.8),
                "temp": st.session_state.get("sim_custom_temp", 28.0),
                "tan": st.session_state.get("sim_custom_tan", 0.5),
                "feed": st.session_state.get("sim_custom_feed", 50.0),
            })
            st.rerun()

    with c_act2:
        st.write("")
        st.write("")
        if st.button("⏩ Run 6-Hour Test", use_container_width=True, help="Simulate a 6-hour sequence"):
            for _ in range(6):
                advance_simulation_step(selected_scenario, {
                    "do": st.session_state.get("sim_custom_do", 4.5),
                    "ph": st.session_state.get("sim_custom_ph", 7.8),
                    "temp": st.session_state.get("sim_custom_temp", 28.0),
                    "tan": st.session_state.get("sim_custom_tan", 0.5),
                    "feed": st.session_state.get("sim_custom_feed", 50.0),
                })
            st.rerun()

    with c_act3:
        st.write("")
        st.write("")
        if st.button("🔄 Reset Simulation", use_container_width=True):
            initialize_simulation_state()
            st.rerun()

    # Custom Scenario Controls if selected
    custom_params = {}
    if selected_scenario == "Custom scenario":
        with st.expander("🛠️ Custom Sensor Parameter Sliders", expanded=True):
            c_c1, c_c2 = st.columns(2)
            with c_c1:
                custom_params["do"] = st.slider("Simulated DO (mg/L):", 0.0, 12.0, 4.5, 0.1, key="sim_custom_do")
                custom_params["ph"] = st.slider("Simulated pH:", 4.0, 11.0, 7.8, 0.05, key="sim_custom_ph")
                custom_params["temp"] = st.slider("Simulated Temperature (°C):", 15.0, 42.0, 28.0, 0.5, key="sim_custom_temp")
            with c_c2:
                custom_params["tan"] = st.slider("Simulated TAN (mg/L):", 0.0, 15.0, 0.5, 0.1, key="sim_custom_tan")
                custom_params["feed"] = st.slider("Baseline Feed (kg/day):", 0.0, 200.0, 50.0, 5.0, key="sim_custom_feed")

    # ── Live Sensor Gauges (Current Synthetic Hour) ────────────────────
    st.markdown(f"#### Current Simulated Sensor Telemetry (Hour {current_step.get('hour', 0)})")
    k1, k2, k3, k4 = st.columns(4)

    curr_do = current_step.get("do", 5.8)
    curr_ph = current_step.get("ph", 7.7)
    curr_temp = current_step.get("temp", 28.0)
    curr_nh3 = current_step.get("nh3", 0.0125)

    with k1:
        render_metric_card(
            title="Simulated DO",
            value=f"{curr_do:.2f} mg/L",
            subtitle="Hypoxia (< 3.0)" if curr_do < 3.0 else "Optimal",
            benchmark_ref="Synthetic Sensor",
            icon="🫁",
            accent="warning" if curr_do < 3.0 else "success",
        )
    with k2:
        render_metric_card(
            title="Simulated pH",
            value=f"{curr_ph:.2f}",
            subtitle=f"Temp: {curr_temp:.1f} °C",
            benchmark_ref="Synthetic Sensor",
            icon="🧪",
            accent="teal",
        )
    with k3:
        render_metric_card(
            title="Simulated Toxic NH₃",
            value=f"{curr_nh3:.4f} mg/L",
            subtitle="Toxic (≥ 0.05)" if curr_nh3 >= 0.05 else "Safe",
            benchmark_ref="Emerson Chemistry",
            icon="⚠️" if curr_nh3 >= 0.05 else "💧",
            accent="warning" if curr_nh3 >= 0.05 else "aqua",
        )
    with k4:
        render_metric_card(
            title="Simulated Risk Status",
            value=current_step.get("status", "Optimal"),
            subtitle=f"Hour {current_step.get('hour', 0)} of simulation",
            benchmark_ref="SIMULATED_SCENARIO_ONLY",
            icon="🛡️",
            accent="warning" if current_step.get("status") != "Optimal" else "success",
        )

    # ── Dynamic Risk Alerts ───────────────────────────────────────────
    if curr_do < 2.0:
        st.error(
            f"🚨 **EMERGENCY HYPOXIA ALERT (Simulated Hour {current_step.get('hour', 0)}):** "
            f"Dissolved oxygen has crashed to **{curr_do:.2f} mg/L**! Fish asphyxiation imminent. "
            "Automated recommendation: 100% feed suspension and emergency mechanical aeration."
        )
    elif curr_do < 3.0:
        st.warning(
            f"⚠️ **LOW DISSOLVED OXYGEN WARNING:** DO is **{curr_do:.2f} mg/L** (< 3.0 mg/L). "
            "Feed throttled by 50% to prevent organic decay in the water."
        )

    if curr_nh3 >= 0.05:
        st.error(
            f"⚠️ **EARLY TOXICITY WARNING (Consecutive Spike):** Toxic un-ionized ammonia has reached **{curr_nh3:.4f} mg/L**! "
            "Driven by rising TAN and alkaline pH. Dynamic feeding engine recommends immediate feed reduction to prevent further organic loading."
        )

    # ── Updating Trend Graphs (Multi-Parameter Time Series) ───────────
    render_section_bar("Simulated Water-Quality Timeline")
    df_hist = pd.DataFrame(history)

    fig_sim = make_subplots(
        rows=1,
        cols=2,
        subplot_titles=("Simulated DO & Temperature", "Simulated Toxic NH₃ & pH"),
        horizontal_spacing=0.1,
    )

    # DO & Temp
    fig_sim.add_trace(
        go.Scatter(x=df_hist["hour"], y=df_hist["do"], mode="lines+markers", name="Simulated DO (mg/L)", line=dict(color="#087F72", width=2.5)),
        row=1, col=1,
    )
    fig_sim.add_trace(
        go.Scatter(x=df_hist["hour"], y=df_hist["temp"], mode="lines", name="Simulated Temp (°C)", line=dict(color="#E7A23B", width=1.8, dash="dot")),
        row=1, col=1,
    )
    fig_sim.add_hline(y=3.0, line_dash="dash", line_color="#E53E3E", annotation_text="Hypoxia (3.0)", row=1, col=1)

    # NH3 & pH
    fig_sim.add_trace(
        go.Scatter(x=df_hist["hour"], y=df_hist["nh3"], mode="lines+markers", name="Toxic NH₃ (mg/L)", line=dict(color="#D9534F", width=2.5)),
        row=1, col=2,
    )
    fig_sim.add_hline(y=0.05, line_dash="dash", line_color="#D9534F", annotation_text="Toxicity (0.05)", row=1, col=2)

    fig_sim.update_layout(
        height=300,
        template="plotly_white",
        margin=dict(l=30, r=20, t=35, b=25),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig_sim.update_xaxes(title_text="Simulated Elapsed Hours")
    st.plotly_chart(fig_sim, use_container_width=True)

    # ── Real-Time Adaptive Feeding Adaptation ─────────────────────────
    render_section_bar("Adaptive Feeding Recommendation & Feed Waste Mitigation")

    baseline_feed = current_step.get("feed_baseline", 50.0)
    rec_feed = current_step.get("feed_recommended", 50.0)
    saved_feed = max(0.0, baseline_feed - rec_feed)
    pct_cut = ((baseline_feed - rec_feed) / baseline_feed * 100.0) if baseline_feed > 0 else 0.0

    af1, af2, af3 = st.columns([1, 1, 1.4])
    with af1:
        render_metric_card(
            title="Baseline Feed Requirement",
            value=f"{baseline_feed:.1f} kg/day",
            subtitle="Standard unconstrained ration",
            icon="🥣",
            accent="teal",
        )
    with af2:
        render_metric_card(
            title="Dynamically Adjusted Feed",
            value=f"{rec_feed:.1f} kg/day",
            subtitle=f"{pct_cut:.0f}% reduction applied",
            icon="⚖️",
            accent="warning" if pct_cut > 0 else "success",
        )
    with af3:
        render_metric_card(
            title="Prevented Feed Waste",
            value=f"{saved_feed:.1f} kg/day",
            subtitle="Intended reduction of unconsumed feed",
            benchmark_ref="Water Quality Preservation",
            icon="🛡️",
            accent="success" if saved_feed > 0 else "aqua",
        )

    st.caption(
        f"**Dynamic Adjustment Rationale:** At simulated DO = `{curr_do:.2f} mg/L` and NH₃ = `{curr_nh3:.4f} mg/L`, "
        f"the feeding recommendation engine cuts feed by **{pct_cut:.0f}%** ({saved_feed:.1f} kg prevented waste). "
        "Intended benefit: Prevents unconsumed feed from decomposing into toxic ammonia and worsening hypoxia."
    )

    # Log to session prediction history
    log_prediction_event(
        analysis_type=f"Live Simulation ({farm_type})",
        container_id=f"Simulated {container_label}",
        data_source="benchmark_simulation (Quarantined)",
        is_simulated=True,
        results_summary=f"Sim Hour {current_step.get('hour', 0)}: DO={curr_do:.2f}, NH3={curr_nh3:.4f}, Feed Cut={pct_cut:.0f}%",
        details=current_step,
        farm_type=farm_type,
    )

    # ── Synthetic Reference Dataset Explorer (iot_water_model_v2.csv) ──
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
            - **Quarantine Tag:** `SIMULATED_SCENARIO_ONLY` | `PROHIBITED`.
            """
        )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
