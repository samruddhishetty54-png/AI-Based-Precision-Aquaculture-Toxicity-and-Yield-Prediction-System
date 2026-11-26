"""Page 5: Feeding & Growth – Precision AquaDSS.

Operational Category: ADVISORY (Model Benchmark & Provisional Advisory Heuristics).
Combines:
1. Feeding Advisor: Dynamic rule-based feeding adjustments responding to morning DO,
   toxic ammonia trends, water temperature, and biomass.
   - Clear explanations for feed reductions (e.g. 25% cut due to suboptimal DO < 4.0 mg/L)
   - Highlights intended management benefit: Help reduce feed waste and maintain water quality.
2. Fish Growth Tracking:
   - Operational baseline: Persistence Baseline (W_hat_{t+1} = W_t).
   - Target Definition: Strictly next-visit pond-cohort average fish weight (grams/fish).
   - Negative Scope: NOT individual fish growth, NOT harvest biomass, and NOT total commercial yield in kg/ha (0% total yield labels).
   - Performance Disclosure: Persistence baseline achieved MAE = 93.38 g (RMSE = 196.48 g, R² = 0.7135)
     on unfiltered commercial test pairs, outperforming ML regressors (RF MAE = 112.15 g, GBDT MAE = 127.34 g).
3. Longitudinal Growth & Feeding Trajectories: Interactive Plotly trends for selected container.
4. Observational Feeding Feedback Tracker: Observational audit log for field compliance recording
   (feedback tracker is strictly an observational audit record; does NOT execute reinforcement learning).
"""

from typing import Dict, Any, Optional
import math
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from app.dashboard.utils.styles import inject_custom_css, PALETTE
from app.dashboard.utils.helpers import (
    format_float,
    format_percentage,
    validate_defensive_bounds,
    detect_simulation_source,
    get_active_farm_type,
    get_container_label,
    get_container_id_label,
    get_farm_type_disclaimer,
    log_prediction_event,
    FREE_PLATFORM_NOTICE,
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
    """Render the Feeding & Growth page."""
    inject_custom_css()

    farm_type = get_active_farm_type()
    container_label = get_container_label(farm_type)
    container_id_label = get_container_id_label(farm_type)

    render_page_header(
        title="Feeding & Growth",
        subtitle=f"Adaptive feeding guidance, feed waste mitigation, and cohort fish growth tracking ({farm_type}).",
        category_key="ADVISORY",
    )

    # 100% Free Platform & Operational Banner
    st.markdown(
        f"""
        <div style="background-color: #FFFFFF; border: 1px solid #DCE9E6; border-left: 4px solid #087F72; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.9rem; box-shadow: 0 1px 4px rgba(16,44,58,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.25rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-weight: 800; font-size: 0.85rem; color: #173747;">🍽️ {farm_type} Feeding & Growth Advisor</span>
                    <span style="background-color: #E3F6EE; color: #269B72; border: 1px solid #A6DEC8; font-size: 0.70rem; font-weight: 700; padding: 0.12rem 0.5rem; border-radius: 9999px;">
                        100% FREE ACCESS
                    </span>
                </div>
                <span style="font-size: 0.75rem; color: #087F72; font-weight: 600;">
                    Help reduce feed waste and maintain water quality
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #526873; line-height: 1.45;">
                <strong>Platform Notice:</strong> {FREE_PLATFORM_NOTICE}<br>
                <span style="color: #64748b;"><strong>Scientific Boundary:</strong> {get_farm_type_disclaimer(farm_type)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_uploaded_context_notice(["exp4_persistence_next_weight_g", "feeding_action", "recommended_feed_kg"])

    # Load Historical Datasets for Selected Container Context
    global_selected = st.session_state.get("selected_pond", "Manual Entry")
    selected_hist_pond = global_selected
    default_pond_id = "POND-001"
    default_weight = 150.0
    default_feed = 25.0
    df_pond_growth = pd.DataFrame()
    df_pond_feed = pd.DataFrame()

    try:
        from app.core.data_manager import load_dataset
        df_gw = load_dataset("fish_health_growth")
        df_feed_hist = load_dataset("feeding_analysis")
        pond_opts = ["Manual Entry"] + sorted(df_gw["pond_id"].dropna().astype(str).unique().tolist())
        if selected_hist_pond not in pond_opts:
            selected_hist_pond = "Manual Entry"

        if selected_hist_pond != "Manual Entry":
            default_pond_id = selected_hist_pond
            df_pond_growth = df_gw[df_gw["pond_id"].astype(str) == selected_hist_pond].copy()
            if not df_pond_growth.empty and "average_fish_weight_g" in df_pond_growth.columns:
                p_rows = df_pond_growth.dropna(subset=["average_fish_weight_g"])
                if not p_rows.empty:
                    default_weight = float(p_rows.iloc[-1]["average_fish_weight_g"])

            if not df_feed_hist.empty and "pond_id" in df_feed_hist.columns:
                df_pond_feed = df_feed_hist[df_feed_hist["pond_id"].astype(str) == selected_hist_pond].copy()
                if not df_pond_feed.empty and "feed_amount_kg" in df_pond_feed.columns:
                    f_rows = df_pond_feed.dropna(subset=["feed_amount_kg"])
                    if not f_rows.empty:
                        default_feed = float(f_rows.iloc[-1]["feed_amount_kg"])
    except Exception:
        pond_opts = ["Manual Entry"]
        selected_hist_pond = "Manual Entry"

    # Section 1: Container Selection & Inputs
    render_section_bar(f"{container_label} Selection & Environmental Inputs")
    ctrl1, ctrl2 = st.columns([1.2, 2.8])
    with ctrl1:
        chosen_pond_input = st.selectbox(
            f"Active {container_id_label}:",
            options=pond_opts,
            index=pond_opts.index(selected_hist_pond) if selected_hist_pond in pond_opts else 0,
            key="growth_pond_prefill",
        )
        if chosen_pond_input != selected_hist_pond:
            st.session_state["selected_pond"] = chosen_pond_input
            st.rerun()

    with ctrl2:
        st.caption(
            f"**Container Profile:** `{chosen_pond_input}` ({farm_type}). "
            f"Observed weight: `{default_weight:.1f} g/fish` | Recorded feed: `{default_feed:.1f} kg/day`."
        )

    # Input Form
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
                help="Observed average somatic body weight per fish.",
            )
            revisit_days = st.slider(
                "Revisit Horizon for Persistence (days):",
                min_value=3,
                max_value=45,
                value=21,
                step=1,
            )
            feed_amount_val = st.number_input(
                "Baseline Daily Feed Requirement (kg/day):",
                min_value=0.0,
                max_value=2000.0,
                value=default_feed,
                step=1.0,
                format="%.1f",
                help="Baseline daily feed ration before water-quality adjustments.",
            )

        with c2:
            do_val = st.number_input(
                "Morning DO (mg/L):",
                min_value=0.0,
                max_value=25.0,
                value=4.20,
                step=0.1,
                format="%.2f",
                help="Morning DO reading. Thresholds: < 2.0 (100% cut), 2.0–3.0 (50% cut), 3.0–4.0 (20% cut).",
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
                help="2.0 mg/L TAN represents a standard chemical test-kit graduation mark, NOT a validated biological toxicity threshold.",
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

        submitted = st.form_submit_button("⚡ Run Growth & Feeding Advisory Analysis", use_container_width=True)

    # Validations
    for p_name, p_val in [
        ("fish_weight", current_weight_val),
        ("do", do_val),
        ("water_temp", temp_val),
        ("revisit_interval", revisit_days),
    ]:
        ok, msg = validate_defensive_bounds(p_name, p_val)
        if not ok and msg:
            st.warning(msg)

    # Backend Inferences
    registry = get_model_registry()

    weight_payload = {
        "current_weight_g": float(current_weight_val),
        "gap_days": float(revisit_days),
        "curr_do": float(do_val),
        "is_simulated": False,
    }
    try:
        res_weight = registry.predict_fish_growth(weight_payload)
    except Exception as exc:
        st.error(f"Error evaluating fish weight benchmark: {exc}")
        return

    advisory_payload = {
        "dissolved_oxygen_mg_l": float(do_val),
        "temp_c": float(temp_val),
        "average_fish_weight_g": float(current_weight_val),
        "gap_days": float(revisit_days),
        "current_feed_amount_kg": float(feed_amount_val),
        "is_simulated": False,
        "data_source": "field_inspection",
    }
    if tan_val is not None:
        advisory_payload["ammonia_tan_nh3_n_mg_l"] = float(tan_val)
    if nh3_val is not None:
        advisory_payload["primary_calculated_nh3_mg_l"] = float(nh3_val)

    try:
        res_feed = registry.get_feeding_advisory(advisory_payload)
    except Exception as exc:
        st.error(f"Error evaluating feeding advisory: {exc}")
        return

    advisory_action = res_feed.get("advisory_action", "UNKNOWN")
    rec_feed = res_feed.get("recommended_feed_kg", feed_amount_val)
    base_feed = res_feed.get("baseline_feed_kg", feed_amount_val)
    reduction_pct = res_feed.get("reduction_percentage", 0.0)
    throttles = res_feed.get("throttling_factors", {})
    explanations = res_feed.get("advisory_explanations", [])
    saved_feed = max(0.0, base_feed - rec_feed)

    # Log to session
    summary_txt = f"Next Weight: {res_weight.get('predicted_next_weight_g', current_weight_val):.1f} g | Feed Rec: {rec_feed:.1f} kg/day ({reduction_pct:.0f}% cut)"
    log_prediction_event(
        analysis_type=f"Feeding & Growth ({farm_type})",
        container_id=str(chosen_pond_input),
        data_source="Field Inspection",
        is_simulated=False,
        results_summary=summary_txt,
        details={
            "current_weight_g": current_weight_val,
            "next_weight_g": res_weight.get("predicted_next_weight_g"),
            "baseline_feed_kg": base_feed,
            "recommended_feed_kg": rec_feed,
            "reduction_percentage": reduction_pct,
            "prevented_waste_kg": saved_feed,
        },
        farm_type=farm_type,
    )

    # ── Section 2: Advisory Results KPI Bar ────────────────────────────
    render_section_bar("Adaptive Feeding Recommendation & Growth Benchmark")
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        render_metric_card(
            title="Baseline Feed Requirement",
            value=f"{base_feed:.1f} kg/day",
            subtitle="Standard unconstrained ration",
            icon="🥣",
            accent="teal",
        )
    with k2:
        render_metric_card(
            title="Recommended Adjusted Feed",
            value=f"{rec_feed:.1f} kg/day",
            subtitle=f"{reduction_pct:.0f}% reduction applied",
            icon="⚖️",
            accent="warning" if reduction_pct > 0 else "success",
        )
    with k3:
        render_metric_card(
            title="Prevented Feed Waste",
            value=f"{saved_feed:.1f} kg/day",
            subtitle="Help reduce feed waste and maintain water quality",
            benchmark_ref="Mitigates Organic Decay",
            icon="🛡️",
            accent="success" if saved_feed > 0 else "aqua",
        )
    with k4:
        render_metric_card(
            title="Next-Visit Cohort Weight",
            value=f"{res_weight.get('predicted_next_weight_g', current_weight_val):.1f} g",
            subtitle=f"Persistence baseline (~{revisit_days}d)",
            benchmark_ref="Persistence Baseline (93.38 g MAE)",
            icon="🐟",
            accent="teal",
        )

    # ── Feed Reduction Explanation Callout ─────────────────────────────
    if reduction_pct > 0:
        reasons_list = []
        if do_val < 3.0:
            reasons_list.append(f"critical dissolved oxygen level ({do_val:.2f} mg/L < 3.0 mg/L)")
        elif do_val < 4.0:
            reasons_list.append(f"suboptimal dissolved oxygen levels ({do_val:.2f} mg/L < 4.0 mg/L)")

        if tan_val is not None and tan_val >= 2.0:
            reasons_list.append(f"elevated ammonia reading (TAN {tan_val:.2f} mg/L ≥ 2.0 mg/L)")

        if temp_val < 20.0 or temp_val > 34.0:
            reasons_list.append(f"suboptimal water temperature ({temp_val:.1f} °C)")

        reason_str = " and ".join(reasons_list) if reasons_list else "environmental stress factors"
        st.warning(
            f"⚠️ **Feed reduced by {reduction_pct:.0f}% due to {reason_str} to prevent feed waste and water degradation.**\n\n"
            f"• **Actionable Guidance:** Dispense `{rec_feed:.1f} kg/day` instead of `{base_feed:.1f} kg/day`.\n"
            f"• **Benefit:** Prevents `{saved_feed:.1f} kg/day` of uneaten feed from sinking and decomposing into toxic ammonia."
        )
    else:
        st.success(
            f"✅ **Normal Feeding Permitted:** Current water quality (DO: {do_val:.2f} mg/L, Temp: {temp_val:.1f} °C) "
            f"is within optimal operational ranges. Dispense full baseline ration ({rec_feed:.1f} kg/day)."
        )

    # ── Section 3: Growth Trajectory & Feeding History ────────────────
    if not df_pond_growth.empty or not df_pond_feed.empty:
        render_section_bar(f"Historical Trajectories — {container_label} {chosen_pond_input}")
        tr_c1, tr_c2 = st.columns(2)

        with tr_c1:
            if not df_pond_growth.empty and "average_fish_weight_g" in df_pond_growth.columns:
                df_g = df_pond_growth.dropna(subset=["average_fish_weight_g"]).copy()
                df_g["dt"] = pd.to_datetime(df_g["datetime"], errors="coerce")
                df_g = df_g.dropna(subset=["dt"]).sort_values("dt")
                fig_g = px.line(
                    df_g,
                    x="dt",
                    y="average_fish_weight_g",
                    markers=True,
                    title=f"Cohort Weight Trajectory (g/fish) — {chosen_pond_input}",
                    labels={"dt": "Inspection Date", "average_fish_weight_g": "Weight (g/fish)"},
                )
                fig_g.update_traces(line_color="#087F72", line_width=2.5)
                fig_g.update_layout(height=260, template="plotly_white", margin=dict(l=20, r=20, t=35, b=20))
                st.plotly_chart(fig_g, use_container_width=True)
            else:
                st.info("No dated fish weight records for this container.")

        with tr_c2:
            if not df_pond_feed.empty and "feed_amount_kg" in df_pond_feed.columns:
                df_f = df_pond_feed.dropna(subset=["feed_amount_kg"]).copy()
                df_f["dt"] = pd.to_datetime(df_f["datetime"], errors="coerce")
                df_f = df_f.dropna(subset=["dt"]).sort_values("dt")
                fig_f = px.bar(
                    df_f,
                    x="dt",
                    y="feed_amount_kg",
                    title=f"Historical Daily Feed (kg) — {chosen_pond_input}",
                    labels={"dt": "Date", "feed_amount_kg": "Feed (kg/day)"},
                    color_discrete_sequence=["#43BFC0"],
                )
                fig_f.update_layout(height=260, template="plotly_white", margin=dict(l=20, r=20, t=35, b=20))
                st.plotly_chart(fig_f, use_container_width=True)
            else:
                st.info("No recorded feeding history for this container.")

    # ── Section 4: Expandable Technical Details & Governance ─────────
    with st.expander("Technical Details, Negative Scope & Heuristic Explanations", expanded=False):
        st.markdown(
            """
            - **Target Definition:** Strictly **next-visit pond-cohort average fish weight** (`Ŵ_{t+1} = W_t` persistence baseline).
            - **Negative Scope:** **NOT individual fish growth**, **NOT harvest biomass**, and **NOT total commercial yield in kg/ha** (0% total yield labels, 0% total harvest yield labels).
            - **Benchmark Performance:** All-pairs persistence MAE = **93.38 g** (RMSE = 196.48 g, R² = 0.7135), outperforming RF (112.15 g) and GBDT (127.34 g).
            - **Provisional Feeding Recommendation:** These are provisional decision-support heuristics requiring human verification (`is_automatic_control = False`). Feed reductions mitigate organic waste loading but do NOT cause immediate water quality recovery or cure hypoxia.
            - **TAN Note:** 2.0 mg/L TAN represents a standard chemical test-kit graduation mark, NOT a validated biological toxicity threshold.
            """
        )
        for exp in explanations:
            st.markdown(f"- {exp}")
        st.plotly_chart(render_weight_mae_chart(), use_container_width=True)

    # ── Section 5: Observational Feeding Feedback Tracker ─────────────
    # This feedback tracker is strictly an observational audit record and does
    # NOT execute reinforcement learning, causal learning, or parameter updates.
    with st.expander("Observational Feeding Feedback Log", expanded=False):
        with st.form("feedback_form"):
            fb_c1, fb_c2 = st.columns(2)
            with fb_c1:
                pond_id = st.text_input("Container Identifier:", value=default_pond_id)
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
                    placeholder="e.g. Reduced feed following morning observation.",
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
