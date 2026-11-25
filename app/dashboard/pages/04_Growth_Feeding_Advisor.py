"""Page 4: Next-Visit Pond-Cohort Fish Weight Benchmark & Provisional Feeding Advisory.

Operational Category: ADVISORY (Model Benchmark & Provisional Advisory Heuristics).
Provides:
1. Operational Fish Weight Baseline: Persistence Baseline (W_hat_{t+1} = W_t).
   - Target Definition: Strictly next-visit pond-cohort average fish body weight (grams/fish).
   - Negative Scope: NOT individual fish growth, NOT harvest biomass, and NOT total commercial yield in kg/ha.
   - Performance Disclosure: Persistence baseline achieved MAE = 93.38 g (RMSE = 196.48 g, R² = 0.7135)
     on unfiltered commercial test pairs (N = 1,689), outperforming ML regressors (RF MAE = 112.15 g,
     GBDT MAE = 127.34 g, p < 10⁻¹²) due to unrecorded commercial partial harvests and management interventions.
2. Provisional Rule-Based Feeding Advisory Engine:
   - Decision-support heuristics evaluating morning DO, optional un-ionized NH3 / TAN, temperature, and biomass.
   - Adjustment tiers: DO < 2.0 mg/L (100% cut), 2.0–3.0 mg/L (50% cut), 3.0–4.0 mg/L (20% cut);
     NH3 >= 0.10 mg/L (100% cut), NH3 >= 0.05 mg/L (50% cut); TAN >= 2.0 mg/L (50% cut, test-kit mark);
     Temp < 20°C or > 34°C (20% cut).
   - Explicit disclaimer: Provisional heuristics requiring human verification. Feed reductions mitigate organic
     waste loading but DO NOT cause immediate water quality recovery or cure hypoxia.
   - Zero automated feeder actuation (is_automatic_control = False).
3. Observational Feeding Feedback Tracker:
   - Observational audit log for field compliance recording.
   - Strictly observational; does NOT execute causal learning, reinforcement learning, or parameter updates.
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
from app.dashboard.components.header import render_page_header, render_section_bar
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_multi_week_observation_banner,
    render_simulation_warning_banner,
    render_uploaded_context_notice,
)
from app.dashboard.components.metric_card import render_metric_card
from app.models.registry import get_model_registry


def render_weight_mae_chart() -> go.Figure:
    """Render Plotly bar chart comparing prospective test MAE across fish weight models."""
    models = [
        "Persistence Baseline",
        "Random Forest Regressor",
        "Gradient Boosting Regressor",
    ]
    maes = [93.38, 112.15, 127.34]
    colors = ["#087F72", "#43BFC0", "#526873"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=models,
                y=maes,
                marker_color=colors,
                text=[f"{v:.2f} g" for v in maes],
                textposition="auto",
                marker_line_width=0,
            )
        ]
    )
    fig.update_layout(
        title=dict(
            text="Prospective Chronological Holdout MAE Comparison (Experiment 4)",
            font=dict(size=14, color="#0c2340"),
        ),
        yaxis_title="Mean Absolute Error (grams/fish)",
        xaxis_title="Modeling Approach",
        template="plotly_white",
        height=300,
        margin=dict(l=40, r=40, t=50, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#f1f5f9"),
    )
    return fig


def render_page() -> None:
    """Render the Fish Weight Benchmark & Feeding Advisory page."""
    inject_custom_css()

    render_page_header(
        title="Next-Visit Pond-Cohort Fish Weight Benchmark & Provisional Feeding Advisory",
        subtitle="Persistence baseline for cohort average fish weight and provisional rule-based feeding advisory.",
        category_key="ADVISORY",
    )

    render_uploaded_context_notice(["exp4_persistence_next_weight_g", "feeding_action", "recommended_feed_kg"])

    with st.expander("Decision-Support & Sampling Context Notices", expanded=False):
        render_decision_support_banner()
        render_multi_week_observation_banner()

    # Section 1: Pond Selection & Operating Mode
    st.markdown("#### Pond Selection & Observation Inputs")
    ctrl1, ctrl2 = st.columns([1, 1])
    with ctrl1:
        mode = st.radio(
            "Operating Mode:",
            options=[
                "Manual / Pond Record Entry (Operational)",
                "Simulated Benchmark Scenario (Quarantined)",
            ],
            index=0,
            horizontal=True,
        )
    is_simulated = "Simulated" in mode
    _, status_tag, operational_permitted = detect_simulation_source(is_simulated_flag=is_simulated)

    if is_simulated:
        render_simulation_warning_banner()

    # Optional historical pond pre-fill (strictly read-only reference)
    default_pond_id = "POND-01"
    default_weight = 150.0
    default_feed = 25.0
    with ctrl2:
        try:
            from app.core.data_manager import load_dataset
            df_gw = load_dataset("fish_health_growth")
            pond_opts = ["Manual Entry"] + sorted(df_gw["pond_id"].dropna().astype(str).unique().tolist())
            selected_hist_pond = st.selectbox(
                "Pre-fill from Historical Pond Record (Optional):",
                options=pond_opts,
                index=0,
                key="growth_pond_prefill",
            )
            if selected_hist_pond != "Manual Entry":
                default_pond_id = selected_hist_pond
                p_rows = df_gw[df_gw["pond_id"].astype(str) == selected_hist_pond].dropna(subset=["average_fish_weight_g"])
                if not p_rows.empty:
                    default_weight = float(p_rows.iloc[-1]["average_fish_weight_g"])
        except Exception:
            selected_hist_pond = "Manual Entry"

    with st.form("fish_growth_feeding_form"):
        c1, c2 = st.columns(2)
        with c1:
            current_weight_val = st.number_input(
                "Current Average Fish Weight (g/fish):",
                min_value=0.01,
                max_value=5000.0,
                value=max(0.01, min(5000.0, default_weight)),
                step=5.0,
                format="%.1f",
                help="Observed average somatic body weight per fish. Software boundary: 0.01 - 5000.0 g.",
            )
            revisit_days = st.slider(
                "Revisit Interval (days):",
                min_value=3,
                max_value=45,
                value=21,
                step=1,
            )
            feed_mode = st.radio(
                "Feeding Baseline Method:",
                options=["Recorded Daily Feed (kg/day)", "Estimate from Biomass Parameters"],
                index=0,
                horizontal=True,
            )
            if "Recorded" in feed_mode:
                feed_amount_val = st.number_input(
                    "Baseline Daily Feed (kg/day):",
                    min_value=0.0,
                    max_value=2000.0,
                    value=default_feed,
                    step=1.0,
                    format="%.1f",
                )
                pond_area_val = 1.0
                stocking_density_val = 5000.0
            else:
                feed_amount_val = None
                bio_c1, bio_c2 = st.columns(2)
                with bio_c1:
                    pond_area_val = st.number_input("Pond Area (acres):", min_value=0.1, max_value=50.0, value=1.0, step=0.1)
                with bio_c2:
                    stocking_density_val = st.number_input("Stocking Density (fish/acre):", min_value=100.0, max_value=50000.0, value=5000.0, step=500.0)

        with c2:
            do_val = st.number_input(
                "Morning DO (mg/L):",
                min_value=0.0,
                max_value=25.0,
                value=4.20,
                step=0.1,
                format="%.2f",
            )
            temp_val = st.number_input(
                "Water Temperature (°C):",
                min_value=10.0,
                max_value=45.0,
                value=28.0,
                step=0.5,
                format="%.1f",
            )
            tan_enabled = st.checkbox("Include Total Ammonia (TAN, mg/L)", value=True)
            tan_val = st.number_input(
                "TAN (mg/L):",
                min_value=0.0,
                max_value=20.0,
                value=0.50,
                step=0.05,
                disabled=not tan_enabled,
                help="2.0 mg/L TAN is a test-kit graduation mark, NOT a biological toxicity threshold.",
            ) if tan_enabled else None

            nh3_enabled = st.checkbox("Include Calculated Un-ionized NH3 (mg/L)", value=False)
            nh3_val = st.number_input(
                "Molecular NH3 (mg/L):",
                min_value=0.0,
                max_value=5.0,
                value=0.03,
                step=0.01,
                disabled=not nh3_enabled,
            ) if nh3_enabled else None

        submitted = st.form_submit_button("Run Growth & Feeding Analysis", use_container_width=True)

    # Defensive software bound validations
    val_errs = []
    for p_name, p_val in [
        ("fish_weight", current_weight_val),
        ("do", do_val),
        ("water_temp", temp_val),
        ("revisit_interval", revisit_days),
    ]:
        ok, msg = validate_defensive_bounds(p_name, p_val)
        if not ok and msg:
            val_errs.append(msg)

    if val_errs:
        for err in val_errs:
            st.warning(err)

    # Backend Inferences
    registry = get_model_registry()

    # 1. Weight Model Inference
    weight_payload = {
        "current_weight_g": float(current_weight_val),
        "gap_days": float(revisit_days),
        "curr_do": float(do_val),
        "is_simulated": is_simulated,
    }
    try:
        res_weight = registry.predict_fish_growth(weight_payload)
    except Exception as exc:
        st.error(f"Error evaluating fish weight benchmark: {exc}")
        return

    # 2. Feeding Advisory Inference
    advisory_payload = {
        "dissolved_oxygen_mg_l": float(do_val),
        "temp_c": float(temp_val),
        "average_fish_weight_g": float(current_weight_val),
        "gap_days": float(revisit_days),
        "is_simulated": is_simulated,
        "data_source": "benchmark_simulation" if is_simulated else "field_inspection",
    }
    if feed_amount_val is not None:
        advisory_payload["current_feed_amount_kg"] = float(feed_amount_val)
    if pond_area_val is not None:
        advisory_payload["pond_area_acres"] = float(pond_area_val)
    if stocking_density_val is not None:
        advisory_payload["stocking_density_per_acre"] = float(stocking_density_val)
    if tan_val is not None:
        advisory_payload["ammonia_tan_nh3_n_mg_l"] = float(tan_val)
    if nh3_val is not None:
        advisory_payload["primary_calculated_nh3_mg_l"] = float(nh3_val)

    try:
        res_feed = registry.get_feeding_advisory(advisory_payload)
    except Exception as exc:
        st.error(f"Error evaluating feeding advisory: {exc}")
        return

    # Section 2: Analysis Results (Compact SaaS Layout)
    render_section_bar("Weight Benchmark & Provisional Feeding Advisory Results")

    advisory_action = res_feed.get("advisory_action", "UNKNOWN")
    rec_feed = res_feed.get("recommended_feed_kg")
    base_feed = res_feed.get("baseline_feed_kg")
    reduction_pct = res_feed.get("reduction_percentage", 0.0)
    throttles = res_feed.get("throttling_factors", {})
    explanations = res_feed.get("advisory_explanations", [])

    wc1, wc2, wc3, wc4 = st.columns(4)
    with wc1:
        render_metric_card(
            title="Next-Visit Cohort Weight",
            value=f"{res_weight.get('predicted_next_weight_g', current_weight_val):.1f} g",
            subtitle=f"Persistence Benchmark (~{revisit_days}d)",
            benchmark_ref="Persistence Baseline (93.38 g MAE)",
            icon="⚖️",
            accent="aqua",
        )
    with wc2:
        render_metric_card(
            title="Recommended Feed",
            value=f"{rec_feed:.1f} kg/day" if rec_feed is not None else "N/A",
            subtitle=f"{advisory_action.replace('_', ' ')} ({reduction_pct:.0f}% cut)",
            benchmark_ref=f"Baseline: {base_feed:.1f} kg/day" if base_feed is not None else "",
            icon="🍽️",
            accent="warning" if reduction_pct > 0 else "success",
        )
    with wc3:
        render_metric_card(
            title="DO / Ammonia Throttles",
            value=f"{throttles.get('do_multiplier', 1.0)*100:.0f}% / {throttles.get('ammonia_multiplier', 1.0)*100:.0f}%",
            subtitle=f"Temp: {throttles.get('temperature_multiplier', 1.0)*100:.0f}% ({temp_val:.1f} °C)",
            benchmark_ref="Provisional Heuristic",
            icon="🎚️",
            accent="teal",
        )
    with wc4:
        render_metric_card(
            title="Scope Boundary",
            value="Cohort Avg Only",
            subtitle="NOT harvest biomass / kg/ha",
            benchmark_ref="0% total yield labels",
        )

    # Expandable Technical Details & Governance
    with st.expander("Technical Details, Negative Scope & Heuristic Explanations", expanded=False):
        st.markdown(
            """
            - **Target Definition:** Strictly **next-visit pond-cohort average fish weight** (`Ŵ_{t+1} = W_t` persistence baseline).
            - **Negative Scope:** **NOT individual fish growth**, **NOT harvest biomass**, and **NOT total commercial yield in kg/ha** (0% total harvest yield labels).
            - **Benchmark Performance:** All-pairs persistence MAE = **93.38 g** (RMSE = 196.48 g, R² = 0.7135), outperforming RF (112.15 g) and GBDT (127.34 g).
            - **Provisional Feeding Recommendation:** These are provisional decision-support heuristics requiring human verification (`is_automatic_control = False`). Feed reductions mitigate organic waste loading but do NOT cause immediate water quality recovery or cure hypoxia.
            - **TAN Note:** 2.0 mg/L TAN represents a standard chemical test-kit graduation mark, NOT a validated biological toxicity threshold.
            """
        )
        for exp in explanations:
            st.markdown(f"- {exp}")
        st.plotly_chart(render_weight_mae_chart(), use_container_width=True)

    # Section 3: Observational Feeding Feedback Tracker
    # This feedback tracker is strictly an observational audit record and does
    # NOT execute reinforcement learning, causal learning, or parameter updates.
    with st.expander("Observational Feeding Feedback Log", expanded=False):
        with st.form("feedback_form"):
            fb_c1, fb_c2 = st.columns(2)
            with fb_c1:
                pond_id = st.text_input("Pond Identifier:", value=default_pond_id)
                actual_feed = st.number_input(
                    "Actual Feed Dispensed (kg):",
                    min_value=0.0,
                    max_value=2000.0,
                    value=float(rec_feed if rec_feed is not None else 25.0),
                    step=1.0,
                )
            with fb_c2:
                notes = st.text_area(
                    "Field Notes / Deviation Reasons:",
                    placeholder="e.g. Reduced feed 50% following morning observation.",
                )
            fb_submitted = st.form_submit_button("Log Observational Compliance Feedback")
            if fb_submitted:
                record_res = registry.record_feeding_feedback(
                    pond_id=pond_id,
                    advisory_record=res_feed,
                    actual_feed_kg=float(actual_feed),
                    notes=notes,
                )
                st.success(f"Feedback logged for `{pond_id}`. Status: `{record_res.get('compliance_status')}`.")
        st.caption("Observational audit log only; executes zero reinforcement learning or online retraining.")


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
