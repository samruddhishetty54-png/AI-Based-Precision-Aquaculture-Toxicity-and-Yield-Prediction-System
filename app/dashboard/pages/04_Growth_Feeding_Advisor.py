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
from app.dashboard.components.header import render_page_header
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_multi_week_observation_banner,
    render_simulation_warning_banner,
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
    colors = ["#0284c7", "#94a3b8", "#cbd5e1"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=models,
                y=maes,
                marker_color=colors,
                text=[f"{v:.2f} g" for v in maes],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title="Prospective Chronological Holdout MAE Comparison (Experiment 4)",
        yaxis_title="Mean Absolute Error (grams/fish)",
        xaxis_title="Modeling Approach",
        template="plotly_white",
        height=320,
        margin=dict(l=40, r=40, t=50, b=40),
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

    render_decision_support_banner()
    render_multi_week_observation_banner()

    # Section 1: Operating Mode & Context
    st.markdown("### 1. Operating Mode & Operational Context")
    mode = st.radio(
        "Select Operating Mode:",
        options=[
            "Manual Field Inspection Entry (Operational Field Telemetry)",
            "Simulated Benchmark Scenario (Quarantined Synthetic Demonstration)",
        ],
        index=0,
        horizontal=True,
    )
    is_simulated = "Simulated" in mode
    _, status_tag, operational_permitted = detect_simulation_source(is_simulated_flag=is_simulated)

    if is_simulated:
        render_simulation_warning_banner()
        st.warning(
            f"**Operational Gating Status:** `{status_tag}`. "
            f"Operational farm use permitted = `{operational_permitted}`."
        )

    # Section 2: Fish Weight & Feeding Input Panel
    st.markdown("### 2. Fish Cohort Weight & Feeding Telemetry Input")
    st.caption(
        "Enter observed fish cohort weight and feeding baseline. Software bounds are defensive integrity checks, "
        "NOT validated biological safety limits."
    )

    with st.form("fish_growth_feeding_form"):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Pond-Cohort Fish Weight Parameters")
            current_weight_val = st.number_input(
                "Current Observed Average Fish Weight (g/fish):",
                min_value=0.01,
                max_value=5000.0,
                value=150.0,
                step=5.0,
                format="%.1f",
                help="Observed average somatic body weight per fish from recent net sampling. Software boundary: 0.01 - 5000.0 g.",
            )
            revisit_days = st.slider(
                "Farm Revisit Interval (days):",
                min_value=3,
                max_value=45,
                value=21,
                step=1,
                help="Routine farm revisit interval. Audited range: 3 to 45 days (median ~22 days).",
            )

            st.markdown(
                """
                <div style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #0284c7; padding: 0.75rem 1rem; border-radius: 4px; font-size: 0.85rem; color: #0f172a; line-height: 1.45;">
                    <strong>TARGET DEFINITION & NEGATIVE SCOPE:</strong><br>
                    • <strong>Scope:</strong> Target is strictly <strong>next-visit pond-cohort average fish weight</strong> (<code>Ŵ_{t+1}</code>).<br>
                    • <strong>Strict Negative Scope:</strong> This is <strong>NOT individual fish growth</strong>, <strong>NOT pond biomass growth</strong>, and <strong>NOT total commercial yield in kg/ha</strong>.<br>
                    • <strong>Zero Harvest Yield Labels:</strong> The project dataset contains 0% total harvest yield labels. Commercial yield forecasting is strictly unsupported.
                </div>
                """,
                unsafe_allow_html=True,
            )

        with c2:
            st.markdown("#### Baseline Daily Feed & Water Quality")
            feed_mode = st.radio(
                "Feeding Baseline Method:",
                options=["Recorded Daily Feed (kg/day)", "Estimate from Biomass Parameters"],
                index=0,
                horizontal=True,
            )

            if "Recorded" in feed_mode:
                feed_amount_val = st.number_input(
                    "Current Baseline Daily Feed (kg/day):",
                    min_value=0.0,
                    max_value=2000.0,
                    value=25.0,
                    step=1.0,
                    format="%.1f",
                    help="Currently dispensed daily feed quantity. Software boundary: 0.0 - 2000.0 kg/day.",
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

            st.markdown("##### Environmental Stress Telemetry (Mandatory for Advisory)")
            env_c1, env_c2 = st.columns(2)
            with env_c1:
                do_val = st.number_input(
                    "Morning DO (mg/L):",
                    min_value=0.0,
                    max_value=25.0,
                    value=4.20,
                    step=0.1,
                    format="%.2f",
                    help="Mandatory morning DO reading for feeding throttle logic.",
                )
                temp_val = st.number_input(
                    "Water Temperature (°C):",
                    min_value=10.0,
                    max_value=45.0,
                    value=28.0,
                    step=0.5,
                    format="%.1f",
                    help="Water temperature. Heuristic stress triggers if < 20°C or > 34°C.",
                )
            with env_c2:
                tan_enabled = st.checkbox("Include Total Ammonia (TAN, mg/L)", value=True)
                tan_val = st.number_input(
                    "TAN (mg/L):",
                    min_value=0.0,
                    max_value=20.0,
                    value=0.50,
                    step=0.05,
                    disabled=not tan_enabled,
                    help="test-kit graduation note: 2.0 mg/L TAN is a test-kit graduation mark, NOT a validated biological toxicity threshold.",
                ) if tan_enabled else None

                nh3_enabled = st.checkbox("Include Calculated Un-ionized NH3 (mg/L)", value=False)
                nh3_val = st.number_input(
                    "Molecular NH3 (mg/L):",
                    min_value=0.0,
                    max_value=5.0,
                    value=0.03,
                    step=0.01,
                    disabled=not nh3_enabled,
                    help="Calculated toxic un-ionized ammonia.",
                ) if nh3_enabled else None

        submitted = st.form_submit_button("Calculate Next-Visit Weight Benchmark & Generate Advisory", use_container_width=True)

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

    # Section 3: Next-Visit Pond-Cohort Average Fish Weight Benchmark
    st.markdown("---")
    st.markdown("### 3. Next-Visit Pond-Cohort Average Fish Weight Benchmark")
    st.markdown(
        """
        <div style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; background-color: #f8fafc; border: 2px solid #0284c7; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1rem;">
            <div style="font-size: 0.8rem; text-transform: uppercase; color: #0284c7; font-weight: 700; letter-spacing: 0.05em;">
                Operational Primary Baseline (Experiment 4)
            </div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #0f172a; margin-top: 0.25rem;">
                Persistence Baseline: Ŵ<sub>t+1</sub> = {pred_wt:.1f} g/fish
            </div>
            <div style="font-size: 0.88rem; color: #1e293b; font-weight: 500; margin-top: 0.25rem;">
                Target: <strong>Next-visit pond-cohort average fish body weight</strong> (irregular 3–45 day revisit interval).
            </div>
            <div style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #0d5c75; padding: 0.5rem 0.75rem; border-radius: 4px; margin-top: 0.75rem; font-size: 0.82rem; color: #0f172a; line-height: 1.45;">
                <strong>MODEL PERFORMANCE DISCLOSURE:</strong> The reported <strong>MAE = 93.38 g</strong> belongs strictly to the all-pairs chronological persistence baseline (W<sub>t+1</sub> = W<sub>t</sub>).
                Complex ML regressors failed significantly on commercial ponds (RF MAE = 112.15 g, GBDT MAE = 127.34 g, p < 10⁻¹²) because they assume continuous growth and cannot foresee unrecorded commercial partial harvests, net thinning, or cycle terminations.
            </div>
        </div>
        """.format(pred_wt=res_weight.get("predicted_next_weight_g", current_weight_val)),
        unsafe_allow_html=True,
    )

    wc1, wc2, wc3, wc4 = st.columns(4)
    with wc1:
        render_metric_card(
            title="Current Observed Weight",
            value=f"{current_weight_val:.1f} g",
            subtitle="Observed Net Sampling",
            benchmark_ref="Input Metric",
        )
    with wc2:
        render_metric_card(
            title="Predicted Next-Visit Weight",
            value=f"{res_weight.get('predicted_next_weight_g', current_weight_val):.1f} g",
            subtitle=f"At ~{revisit_days} Days Revisit",
            benchmark_ref="Persistence Baseline",
        )
    with wc3:
        render_metric_card(
            title="Chronological Test MAE",
            value="93.38 g",
            subtitle="RMSE = 196.48 g (R² = 0.7135)",
            benchmark_ref="Experiment 4 Benchmark",
        )
    with wc4:
        render_metric_card(
            title="Negative Scope",
            value="NOT HARVEST YIELD",
            subtitle="0% total yield labels in data",
            benchmark_ref="Cohort Avg Weight Only",
        )

    # Plotly Chart
    st.plotly_chart(render_weight_mae_chart(), use_container_width=True)

    # Section 4: Provisional Rule-Based Feeding Advisory Engine
    st.markdown("---")
    st.markdown("### 4. Provisional Rule-Based Feeding Advisory Engine")
    st.caption("Provisional decision-support heuristics requiring human verification. No automatic actuation is executed.")

    advisory_action = res_feed.get("advisory_action", "UNKNOWN")
    rec_feed = res_feed.get("recommended_feed_kg")
    base_feed = res_feed.get("baseline_feed_kg")
    reduction_pct = res_feed.get("reduction_percentage", 0.0)
    throttles = res_feed.get("throttling_factors", {})
    explanations = res_feed.get("advisory_explanations", [])

    # Color badge based on action
    if "CEASE" in advisory_action:
        action_bg = "#fef2f2"
        action_border = "#dc2626"
        action_text = "#991b1b"
    elif "SUBSTANTIAL" in advisory_action:
        action_bg = "#fffbeb"
        action_border = "#d97706"
        action_text = "#92400e"
    elif "MODERATE" in advisory_action:
        action_bg = "#fefce8"
        action_border = "#ca8a04"
        action_text = "#854d0e"
    else:
        action_bg = "#f0fdf4"
        action_border = "#16a34a"
        action_text = "#166534"

    st.markdown(
        f"""
        <div style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; background-color: {action_bg}; border: 2px solid {action_border}; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1rem;">
            <div style="font-size: 0.8rem; text-transform: uppercase; color: {action_text}; font-weight: 700; letter-spacing: 0.05em;">
                Provisional Feeding Recommendation (Decision-Support Only)
            </div>
            <div style="font-size: 1.5rem; font-weight: 800; color: {action_text}; margin-top: 0.25rem;">
                Advisory Action: {advisory_action.replace('_', ' ')} ({reduction_pct:.0f}% Reduction)
            </div>
            <div style="font-size: 0.95rem; color: #0f172a; font-weight: 500; margin-top: 0.5rem;">
                • Baseline Calculated Feed: <strong>{base_feed:.1f} kg/day</strong><br>
                • Recommended Adjusted Feed: <strong>{rec_feed:.1f} kg/day</strong>
            </div>
            <div style="background-color: #fee2e2; border-left: 4px solid #ef4444; padding: 0.5rem 0.75rem; border-radius: 4px; margin-top: 0.75rem; font-size: 0.8rem; color: #991b1b;">
                <strong>CAUSALITY & VERIFICATION DISCLAIMER:</strong> Feed reductions mitigate post-prandial oxygen consumption and organic nitrogen loading,
                but <strong>do NOT cause immediate water quality recovery</strong> or cure hypoxia. All feeding adjustments are provisional decision-support heuristics requiring human verification.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        render_metric_card(
            title="DO Throttle Factor",
            value=f"{throttles.get('do_multiplier', 1.0) * 100:.0f}%",
            subtitle=throttles.get("do_status", "N/A").replace("_", " "),
            benchmark_ref="Hypoxia Protection",
        )
    with fc2:
        render_metric_card(
            title="Ammonia Throttle Factor",
            value=f"{throttles.get('ammonia_multiplier', 1.0) * 100:.0f}%",
            subtitle=throttles.get("ammonia_status", "N/A").replace("_", " "),
            benchmark_ref="Toxicity Mitigation",
        )
    with fc3:
        render_metric_card(
            title="Temperature Throttle",
            value=f"{throttles.get('temperature_multiplier', 1.0) * 100:.0f}%",
            subtitle=f"At {temp_val:.1f} °C",
            benchmark_ref="Thermal Stress Check",
        )

    st.markdown("#### Step-by-Step Heuristic Explanations")
    for exp in explanations:
        st.markdown(f"- {exp}")

    st.caption(
        "Note on Ammonia Throttling: If TAN is reported, 2.0 mg/L TAN represents a standard chemical test-kit graduation mark, NOT a validated biological toxicity threshold."
    )

    # Section 5: Observational Feeding Feedback Tracker (Field Compliance Form)
    st.markdown("---")
    st.markdown("### 5. Observational Feeding Feedback Tracker")
    st.caption("Record actual feed dispensed and compliance notes for retrospective observational audit.")

    with st.expander("Record Field Observation & Compliance Feedback", expanded=False):
        with st.form("feedback_form"):
            fb_c1, fb_c2 = st.columns(2)
            with fb_c1:
                pond_id = st.text_input("Pond Identifier:", value="POND-01")
                actual_feed = st.number_input(
                    "Actual Feed Dispensed by Farmer (kg):",
                    min_value=0.0,
                    max_value=2000.0,
                    value=float(rec_feed if rec_feed is not None else 25.0),
                    step=1.0,
                )
            with fb_c2:
                notes = st.text_area(
                    "Field Notes / Deviation Reasons:",
                    placeholder="e.g. Farmer reduced feed by 50% following visible surface air gulping.",
                )

            fb_submitted = st.form_submit_button("Log Observational Compliance Feedback")
            if fb_submitted:
                record_res = registry.record_feeding_feedback(
                    pond_id=pond_id,
                    advisory_record=res_feed,
                    actual_feed_kg=float(actual_feed),
                    notes=notes,
                )
                st.success(
                    f"Feedback successfully logged for pond `{pond_id}`. "
                    f"Compliance status: `{record_res.get('compliance_status')}`."
                )

        st.markdown(
            """
            <div style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 0.5rem 0.75rem; border-radius: 4px; font-size: 0.78rem; color: #1e293b; font-weight: 500; margin-top: 0.5rem;">
                <strong>Scientific Governance Notice:</strong> The feedback tracker is strictly an observational audit record for retrospective human review.
                It does <strong>NOT execute reinforcement learning, online retraining, or automatic parameter tuning</strong>.
            </div>
            """,
            unsafe_allow_html=True,
        )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
