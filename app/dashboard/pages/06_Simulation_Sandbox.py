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
from app.dashboard.utils.helpers import (
    format_percentage,
    get_active_farm_type,
    get_container_label,
    get_container_id_label,
    get_farm_type_disclaimer,
    log_prediction_event,
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
    st.subheader("What-If Scenario Stress Simulator & Early Warning Demonstration")
    st.caption(
        "Inject hypothetical conditions or choose a pre-configured stress scenario to inspect "
        "changing simulated sensor readings, early toxicity alerts, explainable risk factors, and feed waste reduction."
    )

    SCENARIO_PRESETS = {
        "Custom Scenario (Manual Sliders)": {
            "do": 1.50, "ph": 8.60, "temp": 32.0, "tan": 2.50, "feed": 50.0, "weight": 180.0,
            "desc": "Manual slider exploration across hypothetical water-quality conditions.",
        },
        "🚨 Overfeeding & Critical Ammonia Spike": {
            "do": 2.40, "ph": 8.85, "temp": 32.5, "tan": 3.80, "feed": 85.0, "weight": 200.0,
            "desc": "Demonstrates early ammonia toxicity warning, elevated un-ionized NH3, and 100% feed cessation to prevent feed waste.",
        },
        "⚠️ Severe Pre-Dawn Hypoxia Stress": {
            "do": 1.10, "ph": 7.60, "temp": 28.0, "tan": 0.80, "feed": 60.0, "weight": 150.0,
            "desc": "Demonstrates critical hypoxia warning, aerator intervention prompt, and emergency feed throttling.",
        },
        "☀️ Afternoon Thermal & pH Surge": {
            "do": 4.80, "ph": 9.10, "temp": 35.5, "tan": 1.60, "feed": 70.0, "weight": 220.0,
            "desc": "Demonstrates temperature throttle and elevated un-ionized fraction (f) driven by alkaline pH.",
        },
        "✅ Optimal Growth & Feeding Balance": {
            "do": 5.80, "ph": 7.70, "temp": 28.0, "tan": 0.35, "feed": 45.0, "weight": 160.0,
            "desc": "Demonstrates optimal conditions with 100% feed allowance and cohort growth support.",
        },
    }

    selected_preset_name = st.selectbox(
        "Select Simulation Scenario Preset:",
        options=list(SCENARIO_PRESETS.keys()),
        index=0,
        key="sim_preset_choice",
    )
    preset_data = SCENARIO_PRESETS[selected_preset_name]
    st.info(f"**Scenario Context:** {preset_data['desc']}")

    with st.form("what_if_scenario_form"):
        c1, c2 = st.columns(2)
        with c1:
            sim_do = st.slider(
                "Synthetic Morning DO (mg/L):",
                min_value=0.0,
                max_value=12.0,
                value=float(preset_data["do"]),
                step=0.1,
                help="Simulated DO reading. NOT physical live sensor data.",
            )
            sim_ph = st.slider(
                "Synthetic Water pH:",
                min_value=4.0,
                max_value=11.0,
                value=float(preset_data["ph"]),
                step=0.1,
                help="Simulated water pH.",
            )
            sim_temp = st.slider(
                "Synthetic Water Temperature (°C):",
                min_value=15.0,
                max_value=42.0,
                value=float(preset_data["temp"]),
                step=0.5,
                help="Simulated water temperature.",
            )
        with c2:
            sim_tan = st.slider(
                "Synthetic Total Ammonia (TAN, mg/L):",
                min_value=0.0,
                max_value=15.0,
                value=float(preset_data["tan"]),
                step=0.25,
                help="2.0 mg/L TAN is a test-kit graduation mark, NOT a validated toxicity threshold.",
            )
            sim_feed = st.slider(
                "Synthetic Baseline Feed (kg/day):",
                min_value=0.0,
                max_value=200.0,
                value=float(preset_data["feed"]),
                step=5.0,
                help="Baseline daily feeding before environmental throttling.",
            )
            sim_weight = st.slider(
                "Synthetic Fish Cohort Weight (g/fish):",
                min_value=10.0,
                max_value=1000.0,
                value=float(preset_data["weight"]),
                step=10.0,
                help="Average body weight of fish cohort.",
            )

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

    farm_type = get_active_farm_type()
    container_label = get_container_label(farm_type)

    # Log to session prediction history (explicitly tagged as simulation)
    sim_summary = (
        f"Sim NH3: {sim_nh3:.4f} mg/L | Sim Advisory: {res_feed.get('advisory_action', 'N/A').replace('SIMULATED_', '')} "
        f"({res_feed.get('reduction_percentage', 0.0):.0f}% cut) | DO Bench: {res_do.get('predicted_next_do_mg_l', 3.50):.2f} mg/L"
    )
    log_prediction_event(
        analysis_type=f"Simulation Sandbox ({farm_type})",
        container_id=f"Simulated {container_label}",
        data_source="benchmark_simulation (Quarantined)",
        is_simulated=True,
        results_summary=sim_summary,
        details={
            "sim_do": sim_do,
            "sim_ph": sim_ph,
            "sim_temp": sim_temp,
            "sim_tan": sim_tan,
            "sim_nh3": sim_nh3,
            "sim_feed_rec": res_feed.get("recommended_feed_kg"),
        },
        farm_type=farm_type,
    )

    # Simulated Results KPIs
    st.subheader(f"Quarantined Simulation Response (Simulated {container_label} — {farm_type})")
    st.info(
        f"**Simulation Quarantine Active:** Simulated readings are strictly mathematical scenario inputs "
        f"and are NEVER saved as actual historical {container_label.lower()} observations."
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
            benchmark_ref=f"Status: {res_feed.get('status')}",
        )
    with mr4:
        render_metric_card(
            title="DO / Weight Benchmarks",
            value=f"{res_do.get('predicted_next_do_mg_l', 3.50):.2f} mg/L",
            subtitle=f"Cohort Weight: {res_weight.get('predicted_next_weight_g', sim_weight):.0f} g",
            benchmark_ref="Constant / Persistence",
        )

    # ── Explainable Risk Factors & Early Toxicity Warning ─────────────
    st.markdown("#### 🚨 Early Toxicity Warning & Explainable Risk Factors")
    
    # Classify simulated NH3 toxicity tier
    if pd.notna(sim_nh3):
        if sim_nh3 >= 0.10:
            tox_badge = "CRITICAL AMMONIA TOXICITY (≥0.10 mg/L)"
            tox_color = "#D9534F"
            tox_bg = "#FDECEB"
        elif sim_nh3 >= 0.05:
            tox_badge = "ELEVATED AMMONIA RISK (0.05–0.10 mg/L)"
            tox_color = "#E7A23B"
            tox_bg = "#FFF8EB"
        elif sim_nh3 >= 0.02:
            tox_badge = "CAUTION: SUBOPTIMAL AMMONIA (0.02–0.05 mg/L)"
            tox_color = "#43BFC0"
            tox_bg = "#E3F5F3"
        else:
            tox_badge = "OPTIMAL UN-IONIZED AMMONIA (<0.02 mg/L)"
            tox_color = "#269B72"
            tox_bg = "#E3F6EE"
    else:
        tox_badge = "UNAVAILABLE"
        tox_color = "#94a3b8"
        tox_bg = "#f1f5f9"

    st.markdown(
        f"""
        <div style="background-color: #FFFFFF; border: 1px solid #DCE9E6; border-left: 4px solid {tox_color}; border-radius: 10px; padding: 0.85rem 1rem; margin-bottom: 0.9rem;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.4rem;">
                <span style="font-weight: 800; font-size: 0.88rem; color: #173747;">Screening Status: {tox_badge}</span>
                <span style="background-color: {tox_bg}; color: {tox_color}; font-size: 0.72rem; font-weight: 700; padding: 0.15rem 0.55rem; border-radius: 9999px;">
                    Simulated Reading
                </span>
            </div>
            <div style="font-size: 0.82rem; color: #526873; line-height: 1.5;">
                <strong>Explainable Chemistry Factors:</strong>
                Total Ammonia (TAN = {sim_tan:.2f} mg/L) dissociates into toxic un-ionized NH3 based on temperature ({sim_temp:.1f} °C) 
                and pH ({sim_ph:.2f}). At this equilibrium, <strong>{sim_f*100:.2f}%</strong> of total ammonia exists in the toxic un-ionized form (<strong>{sim_nh3:.4f} mg/L</strong>).
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Feed Waste Reduction & Adaptive Feeding Guidance ──────────────
    st.markdown("#### 🍽️ Adaptive Feeding Guidance & Feed Waste Reduction")
    throttles = res_feed.get("throttling_factors", {})
    rec_feed_kg = res_feed.get("recommended_feed_kg", 0.0)
    saved_feed_kg = max(0.0, sim_feed - rec_feed_kg)
    pct_cut = res_feed.get("reduction_percentage", 0.0)

    fw1, fw2, fw3 = st.columns([1, 1, 1.4])
    with fw1:
        render_metric_card(
            title="Baseline Daily Feed",
            value=f"{sim_feed:.1f} kg/day",
            subtitle="Standard ration",
            icon="🥣",
            accent="teal",
        )
    with fw2:
        render_metric_card(
            title="Adjusted Feed Recommendation",
            value=f"{rec_feed_kg:.1f} kg/day",
            subtitle=f"{pct_cut:.0f}% reduction applied",
            icon="⚖️",
            accent="warning" if pct_cut > 0 else "success",
        )
    with fw3:
        render_metric_card(
            title="Prevented Feed Waste",
            value=f"{saved_feed_kg:.1f} kg/day",
            subtitle="Intended reduction of unconsumed waste",
            benchmark_ref="Mitigates Organic Decay",
            icon="🛡️",
            accent="success" if saved_feed_kg > 0 else "aqua",
        )

    st.caption(
        "**Feed Waste Reduction Principle:** Lowering feed inputs during environmental stress (low DO, high ammonia, or thermal extremes) "
        "is intended to prevent unconsumed feed pellets from settling and decomposing into organic sludge. "
        "This is presented as an intended farm management benefit, not a guaranteed biological cure."
    )

    with st.expander("Detailed Causal Explanations & Throttle Multipliers", expanded=True):
        st.markdown(
            f"- **Dissolved Oxygen Throttle:** `{throttles.get('do_multiplier', 1.0) * 100:.0f}%` multiplier ({throttles.get('do_status')})\n"
            f"- **Ammonia Throttle:** `{throttles.get('ammonia_multiplier', 1.0) * 100:.0f}%` multiplier ({throttles.get('ammonia_status')})\n"
            f"- **Temperature Throttle:** `{throttles.get('temperature_multiplier', 1.0) * 100:.0f}%` multiplier\n"
            f"- **Negative Scope:** Somatic body weight persistence benchmark only; **NOT total harvest yield** or individual fish biomass."
        )
        for exp in res_feed.get("advisory_explanations", []):
            st.markdown(f"• {exp}")

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
