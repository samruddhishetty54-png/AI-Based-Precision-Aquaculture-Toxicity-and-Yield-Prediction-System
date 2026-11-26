"""Page 3: Water Quality & Toxicity – Precision AquaDSS.

Operational Category: EXPERIMENTAL (Emerson Equilibrium Chemistry, DO Hypoxia & Toxicity Forecasting).
Combines:
1. Water-Quality Analysis: Temperature, pH, Dissolved Oxygen, Total Ammonia Nitrogen (TAN).
2. Dissolved Oxygen Monitoring: Morning DO hypoxia risk detection (< 3.0 mg/L).
3. Consecutive Increasing Ammonia Trend Detection: Identifies rising NH3 trends across
   successive observations (e.g. Day 1: 0.02, Day 2: 0.04, Day 3: 0.06) and issues explicit warnings:
   "Ammonia is increasing compared with previous observations. Review recent feeding activity and check water quality."
4. Explainable Risk Factors: Details chemical equilibrium drivers, temperature/pH interaction,
   and biological hypoxia compounding effects.
5. Toxicity Risk Forecasting:
   - Historical observations (actual recorded field logs)
   - Rule-based alerts (Emerson equilibrium, consecutive rising trend, DO thresholds)
   - Machine learning screening models (Exp 1 soft-sensor, Exp 2 concurrent mortality, Exp 3 multi-week horizon).
"""

from typing import Dict, Any, Optional, List
import math
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from app.core.data_manager import load_dataset
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
from app.dashboard.components.header import (
    get_asset_base64,
    render_page_header,
    render_section_bar,
)
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_multi_week_observation_banner,
    render_simulation_warning_banner,
    render_uploaded_context_notice,
)
from app.dashboard.components.metric_card import render_metric_card
from app.core.chemistry import (
    calculate_pka,
    calculate_unionized_fraction,
    calculate_nh3_from_tan_n,
    calculate_nh3_from_tan_nh3,
)
from app.models.registry import get_model_registry


def classify_ammonia_toxicity(nh3_mg_l: Optional[float]) -> Dict[str, str]:
    """Provisional heuristic tier classification for un-ionized ammonia (NH3).

    NOTE: Unverified operational heuristic, NOT a certified biological standard.
    """
    if nh3_mg_l is None or (isinstance(nh3_mg_l, float) and (math.isnan(nh3_mg_l) or math.isinf(nh3_mg_l))):
        return {"tier": "UNKNOWN", "provisional_action": "Missing / Invalid Input"}
    if nh3_mg_l >= 0.20:
        return {"tier": "EXTREME", "provisional_action": "Emergency Inspection / Aeration"}
    if nh3_mg_l >= 0.10:
        return {"tier": "CRITICAL", "provisional_action": "Cease Feeding / Aerate"}
    if nh3_mg_l >= 0.05:
        return {"tier": "ELEVATED", "provisional_action": "Reduce Feed 50% / Monitor"}
    if nh3_mg_l >= 0.02:
        return {"tier": "CAUTION", "provisional_action": "Routine Monitoring"}
    return {"tier": "OPTIMAL", "provisional_action": "Normal Operation"}


def check_increasing_ammonia_trend(series: pd.Series) -> Dict[str, Any]:
    """Check if ammonia has been steadily increasing across consecutive observations."""
    clean_s = series.dropna()
    if len(clean_s) < 2:
        return {"is_increasing": False, "consecutive_count": 0, "deltas": []}

    # Inspect last 4 records
    recent = clean_s.tail(4).tolist()
    is_increasing = all(recent[i] > recent[i - 1] for i in range(1, len(recent)))
    deltas = [recent[i] - recent[i - 1] for i in range(1, len(recent))]

    return {
        "is_increasing": is_increasing and len(recent) >= 2 and deltas[-1] > 0.002,
        "consecutive_count": len(recent),
        "recent_values": recent,
        "deltas": deltas,
    }


def render_page() -> None:
    """Render the Water Quality & Toxicity page."""
    inject_custom_css()

    farm_type = get_active_farm_type()
    container_label = get_container_label(farm_type)
    container_id_label = get_container_id_label(farm_type)

    render_page_header(
        title="Water Quality & Toxicity",
        subtitle=f"Water-quality chemistry, morning DO hypoxia analysis, and toxicity risk forecasting ({farm_type}).",
        category_key="EXPERIMENTAL",
    )

    # 100% Free Platform & Operational Notice
    st.markdown(
        f"""
        <div style="background-color: #FFFFFF; border: 1px solid #DCE9E6; border-left: 4px solid #087F72; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.9rem; box-shadow: 0 1px 4px rgba(16,44,58,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.25rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-weight: 800; font-size: 0.85rem; color: #173747;">🧪 {farm_type} Water Chemistry & Toxicity</span>
                    <span style="background-color: #E3F6EE; color: #269B72; border: 1px solid #A6DEC8; font-size: 0.70rem; font-weight: 700; padding: 0.12rem 0.5rem; border-radius: 9999px;">
                        100% FREE ACCESS
                    </span>
                </div>
                <span style="font-size: 0.75rem; color: #087F72; font-weight: 600;">
                    Advisory decision-support • No payment required
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

    render_uploaded_context_notice(["ph", "temp_c", "emerson_nh3_mg_l", "exp1_est_nh3_mg_l", "exp2_mortality_risk_score", "exp3_next_visit_nh3_risk"])

    # ── Load Historical Dataset & Containers ──────────────────────────
    default_do, default_ph, default_temp, default_tan = 4.50, 7.80, 28.0, 0.50
    global_selected_pond = st.session_state.get("selected_pond", "Manual Entry")
    selected_pond = st.session_state.get("wq_pond_prefill", global_selected_pond)
    obs_date_label = "Manual Input"
    df_pond_hist = pd.DataFrame()
    pond_opts = ["Manual Entry"]

    try:
        df_tox = load_dataset("toxicity_analysis")
        unique_ponds = sorted(df_tox["pond_id"].dropna().astype(str).unique().tolist())
        pond_opts = ["Manual Entry"] + unique_ponds
        if selected_pond not in pond_opts:
            selected_pond = "Manual Entry"

        if selected_pond != "Manual Entry":
            df_pond_hist = df_tox[df_tox["pond_id"].astype(str) == selected_pond].copy()
            if "datetime" in df_pond_hist.columns:
                df_pond_hist["datetime"] = pd.to_datetime(df_pond_hist["datetime"], errors="coerce")
                df_pond_hist = df_pond_hist.dropna(subset=["datetime"]).sort_values("datetime")
            if not df_pond_hist.empty:
                latest = df_pond_hist.iloc[-1]
                obs_date_label = latest["datetime"].strftime("%Y-%m-%d")
                if pd.notna(latest.get("dissolved_oxygen_mg_l")):
                    default_do = float(latest["dissolved_oxygen_mg_l"])
                if pd.notna(latest.get("ph")):
                    default_ph = float(latest["ph"])
                if pd.notna(latest.get("temp_c")):
                    default_temp = float(latest["temp_c"])
                tan_col = "ammonia_tan_nh3_n_mg_l" if "ammonia_tan_nh3_n_mg_l" in df_pond_hist.columns else None
                if tan_col and pd.notna(latest.get(tan_col)):
                    default_tan = float(latest[tan_col])
    except Exception as exc:
        df_tox = pd.DataFrame()
        selected_pond = "Manual Entry"

    # Input parameters
    do_val = float(st.session_state.get("wq_do_val", default_do))
    ph_val = float(st.session_state.get("wq_ph_val", default_ph))
    temp_val = float(st.session_state.get("wq_temp_val", default_temp))
    tan_val = float(st.session_state.get("wq_tan_val", default_tan))
    tan_basis = st.session_state.get("wq_tan_basis", "TAN-N (Ammonia-Nitrogen, NH3-N)")
    revisit_days = int(st.session_state.get("wq_revisit_days", 21))
    turb_val = st.session_state.get("wq_turb_val", None)
    tds_val = st.session_state.get("wq_tds_val", None)

    # ── Emerson Chemistry Calculation ─────────────────────────────────
    pka = calculate_pka(temp_val)
    f_pct = calculate_unionized_fraction(ph_val, temp_val)
    if "TAN-N" in tan_basis:
        nh3_calc = calculate_nh3_from_tan_n(tan_val, ph_val, temp_val, round_digits=5)
        basis_formula = r"\text{NH}_3\text{ (mg/L)} = f \times \text{TAN-N} \times \frac{17.031}{14.007}"
        mw_applied = True
    else:
        nh3_calc = calculate_nh3_from_tan_nh3(tan_val, ph_val, temp_val, round_digits=5)
        basis_formula = r"\text{NH}_3\text{ (mg/L)} = f \times \text{TAN-NH}_3"
        mw_applied = False

    toxicity_info = classify_ammonia_toxicity(nh3_calc)
    nh3_tier = toxicity_info.get("tier", "UNKNOWN")
    nh3_action = toxicity_info.get("provisional_action", "N/A")

    # ── Check Consecutive Increasing Ammonia Trend ────────────────────
    trend_info = {"is_increasing": False}
    if not df_pond_hist.empty and "primary_calculated_nh3_mg_l" in df_pond_hist.columns:
        trend_info = check_increasing_ammonia_trend(df_pond_hist["primary_calculated_nh3_mg_l"])

    # ── Model Inferences ──────────────────────────────────────────────
    registry = get_model_registry()
    exp1_payload = {
        "dissolved_oxygen_mg_l": do_val,
        "ph": ph_val,
        "temp_c": temp_val,
        "turbidity_cm": turb_val,
        "tds_ppt": tds_val,
    }
    try:
        exp1_res = registry.predict_ammonia_soft_sensor(exp1_payload)
        exp1_nh3 = exp1_res.get("estimated_nh3_mg_l", float("nan"))
    except Exception as exc:
        exp1_res = {"error": str(exc)}
        exp1_nh3 = float("nan")

    exp2_payload = {
        "dissolved_oxygen_mg_l": do_val,
        "ph": ph_val,
        "temp_c": temp_val,
        "turbidity_cm": turb_val,
        "tds_ppt": tds_val,
    }
    try:
        exp2_res = registry.predict_mortality_diagnostic(exp2_payload)
        exp2_score = exp2_res.get("mortality_risk_score", float("nan"))
    except Exception as exc:
        exp2_res = {"error": str(exc)}
        exp2_score = float("nan")

    exp3_payload = {
        "curr_do": do_val,
        "curr_ph": ph_val,
        "curr_temp": temp_val,
        "curr_turbidity": turb_val,
        "curr_tds": tds_val,
        "gap_days": revisit_days,
    }
    try:
        exp3_res = registry.predict_next_visit_ammonia_risk(exp3_payload)
        exp3_score = exp3_res.get("next_visit_risk_score", float("nan"))
        exp3_horizon = exp3_res.get("revisit_interval_days", revisit_days)
    except Exception as exc:
        exp3_res = {"error": str(exc)}
        exp3_score = float("nan")
        exp3_horizon = revisit_days

    # Log to session
    log_prediction_event(
        analysis_type="Water Quality & Toxicity Risk",
        container_id=str(selected_pond),
        data_source="Manual Entry" if selected_pond == "Manual Entry" else "Historical Inspection",
        is_simulated=False,
        results_summary=f"Emerson NH3: {nh3_calc:.4f} mg/L ({nh3_tier}) | DO: {do_val:.2f} mg/L | Next-Visit Risk: {format_percentage(exp3_score)}",
        details={
            "emerson_nh3_mg_l": nh3_calc,
            "toxicity_tier": nh3_tier,
            "dissolved_oxygen_mg_l": do_val,
            "mortality_score": exp2_score,
            "next_visit_nh3_risk": exp3_score,
        },
        farm_type=farm_type,
    )

    # ── KEY ALERT: Consecutive Rising Ammonia Warning ─────────────────
    if trend_info.get("is_increasing", False):
        st.error(
            "⚠️ **Ammonia is increasing compared with previous observations. Review recent feeding activity and check water quality.**\n\n"
            f"**Consecutive Trend Analysis ({selected_pond}):** Historical records indicate successive upward steps in toxic ammonia concentration: "
            + " ➔ ".join([f"{v:.4f} mg/L" for v in trend_info.get("recent_values", [])])
            + ". Immediate mitigation: pause or reduce feeding, increase aeration, and verify biofilter/water exchange."
        )
    elif nh3_tier in ("ELEVATED", "CRITICAL", "EXTREME"):
        st.warning(
            f"⚠️ **Elevated Ammonia Toxicity Warning ({nh3_tier}):** Calculated un-ionized ammonia is `{nh3_calc:.4f} mg/L` "
            f"(≥ 0.05 mg/L threshold). Action: {nh3_action}."
        )

    # ── KEY ALERT: Morning DO Hypoxia Risk ────────────────────────────
    if do_val < 3.0:
        st.error(
            f"🚨 **Low Morning Dissolved Oxygen Risk (Hypoxia Stress):** Current reading is **{do_val:.2f} mg/L** (< 3.0 mg/L). "
            "Hypoxia impairs gill respiration, suppresses appetite, and severely worsens ammonia toxicity susceptibility. "
            "Recommended action: Activate mechanical aerators immediately and halt morning feeding."
        )
    elif do_val < 4.0:
        st.warning(
            f"⚠️ **Suboptimal Morning Dissolved Oxygen:** Current reading is **{do_val:.2f} mg/L** (3.0–4.0 mg/L). "
            "Fish may experience mild respiratory stress. Monitor aeration and consider a 20–25% feed reduction."
        )

    # ── Three Analytical Dimension KPI Cards ──────────────────────────
    st.markdown("#### Primary Environmental Screening Tiers")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_metric_card(
            title="Calculated Toxic NH₃",
            value=f"{nh3_calc:.4f} mg/L" if pd.notna(nh3_calc) else "N/A",
            subtitle=f"{nh3_tier} ({nh3_action})",
            benchmark_ref="Emerson (1975) Equilibrium",
            icon="🧪",
            accent="warning" if nh3_tier in ("ELEVATED", "CRITICAL", "EXTREME") else "success",
        )
    with c2:
        render_metric_card(
            title="Morning DO Hypoxia Tier",
            value=f"{do_val:.2f} mg/L",
            subtitle="Hypoxia (< 3.0 mg/L)" if do_val < 3.0 else ("Suboptimal (3.0–4.0)" if do_val < 4.0 else "Optimal (≥ 4.0 mg/L)"),
            benchmark_ref="06:00–08:30 AM Inspection",
            icon="🫁",
            accent="warning" if do_val < 3.0 else ("aqua" if do_val < 4.0 else "success"),
        )
    with c3:
        render_metric_card(
            title="Concurrent Mortality Diagnostic",
            value=format_percentage(exp2_score, decimals=1),
            subtitle="Statistical associative score",
            benchmark_ref="Exp 2 Holdout Model",
            icon="🩺",
            accent="teal",
        )
    with c4:
        render_metric_card(
            title=f"Next-Visit NH₃ Risk ({exp3_horizon}d)",
            value=format_percentage(exp3_score, decimals=1),
            subtitle="Next routine visit spike risk",
            benchmark_ref="Exp 3 Horizon Model",
            icon="🛡️",
            accent="warning" if pd.notna(exp3_score) and exp3_score > 0.4 else "aqua",
        )

    # ── Main Interactive Section: Container Selection & Parameters ────
    render_section_bar("Water Quality Parameters & Container Selection")
    col_sel, col_form = st.columns([1.2, 2.8])

    with col_sel:
        with st.container(border=True):
            st.markdown(f"##### Select Monitored {container_label}")
            chosen_p = st.selectbox(
                f"Choose {container_id_label}:",
                options=pond_opts,
                index=pond_opts.index(selected_pond) if selected_pond in pond_opts else 0,
                key="wq_pond_prefill",
            )
            if chosen_p != st.session_state.get("_wq_last_pond"):
                st.session_state["_wq_last_pond"] = chosen_p
                st.session_state["selected_pond"] = chosen_p
                for k in ["wq_do_val", "wq_ph_val", "wq_temp_val", "wq_tan_val"]:
                    st.session_state.pop(k, None)
                st.rerun()

            st.caption(
                f"**Observation Date:** `{obs_date_label}`\n\n"
                f"Switching containers automatically loads audited field measurements."
            )

            # Increasing ammonia tester for demonstration
            st.markdown("---")
            st.markdown("##### Consecutive Ammonia Trend Test")
            st.caption("Verify early warning detection on consecutive observations:")
            if st.button("Simulate Rising Ammonia (0.02 ➔ 0.04 ➔ 0.06)", use_container_width=True):
                st.session_state["wq_ph_val"] = 8.20
                st.session_state["wq_temp_val"] = 30.5
                st.session_state["wq_tan_val"] = 0.85
                st.rerun()

    with col_form:
        with st.container(border=True):
            st.markdown("##### Environmental Observations & What-If Adjustment")
            with st.form("water_quality_input_form"):
                f1, f2 = st.columns(2)
                with f1:
                    new_do = st.number_input("Morning Dissolved Oxygen (mg/L):", min_value=0.0, max_value=25.0, value=max(0.0, min(25.0, do_val)), step=0.1, format="%.2f")
                    new_ph = st.number_input("Water pH:", min_value=0.0, max_value=14.0, value=max(0.0, min(14.0, ph_val)), step=0.05, format="%.2f")
                    new_temp = st.number_input("Water Temperature (°C):", min_value=10.0, max_value=45.0, value=max(10.0, min(45.0, temp_val)), step=0.5, format="%.1f")
                with f2:
                    new_tan = st.number_input("Total Ammonia Nitrogen (TAN in mg/L):", min_value=0.0, max_value=20.0, value=max(0.0, min(20.0, tan_val)), step=0.05, format="%.2f")
                    new_basis = st.selectbox("TAN Chemical Basis:", options=["TAN-N (Ammonia-Nitrogen, NH3-N)", "TAN-NH3 (Molecular Ammonia)"], index=0 if "TAN-N" in tan_basis else 1)
                    new_revisit = st.slider("Next-Visit Forecast Horizon (days):", min_value=3, max_value=45, value=revisit_days, step=1)

                submit_wq = st.form_submit_button("🧪 Evaluate Chemistry & Forecast Risk", use_container_width=True)
                if submit_wq:
                    st.session_state["wq_do_val"] = new_do
                    st.session_state["wq_ph_val"] = new_ph
                    st.session_state["wq_temp_val"] = new_temp
                    st.session_state["wq_tan_val"] = new_tan
                    st.session_state["wq_tan_basis"] = new_basis
                    st.session_state["wq_revisit_days"] = new_revisit
                    for p_name, p_val in [("do", new_do), ("ph", new_ph), ("water_temp", new_temp), ("tan", new_tan)]:
                        ok, msg = validate_defensive_bounds(p_name, p_val)
                        if not ok and msg:
                            st.warning(msg)
                    st.rerun()

    # ── Explainable Risk Factors Breakdown ─────────────────────────────
    render_section_bar("Explainable Risk Factors & Causal Chemistry")
    exp_col1, exp_col2, exp_col3 = st.columns(3)

    with exp_col1:
        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.85rem; height: 100%;">
                <strong style="color: #0c2340; font-size: 0.88rem;">1. Temperature & pH Shift</strong><br>
                <span style="font-size: 0.80rem; color: #475569; line-height: 1.45;">
                    As temperature (<code>{temp_val:.1f} °C</code>) and pH (<code>{ph_val:.2f}</code>) rise, the chemical equilibrium constant shifts:
                    <strong>{format_percentage(f_pct, decimals=2)}</strong> of total ammonia exists in toxic un-ionized (<code>NH₃</code>) form,
                    versus non-toxic ammonium (<code>NH₄⁺</code>).
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with exp_col2:
        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.85rem; height: 100%;">
                <strong style="color: #0c2340; font-size: 0.88rem;">2. Feeding & Organic Loading</strong><br>
                <span style="font-size: 0.80rem; color: #475569; line-height: 1.45;">
                    Uneaten feed and fish protein excretion are the primary sources of TAN in aquaculture.
                    When TAN reaches <code>{tan_val:.2f} mg/L</code>, any increase in pH or temperature rapidly pushes toxic NH₃ above safe thresholds.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with exp_col3:
        st.markdown(
            f"""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 0.85rem; height: 100%;">
                <strong style="color: #0c2340; font-size: 0.88rem;">3. Hypoxia Compounding Effect</strong><br>
                <span style="font-size: 0.80rem; color: #475569; line-height: 1.45;">
                    Morning DO of <code>{do_val:.2f} mg/L</code> {'causes respiratory distress' if do_val < 3.0 else 'supports gill ventilation'}.
                    Under low DO, fish gill excretion efficiency drops by up to 40%, intensifying internal ammonia toxicity.
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Historical Parameter Trajectory for Selected Container ────────
    if not df_pond_hist.empty:
        render_section_bar(f"Historical Trajectory — {container_label} {selected_pond}")
        fig_trend = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=("Toxic NH₃ History (mg/L)", "Morning DO & Water Temperature"),
            horizontal_spacing=0.1,
        )

        if "primary_calculated_nh3_mg_l" in df_pond_hist.columns:
            nh3_clean = df_pond_hist.dropna(subset=["primary_calculated_nh3_mg_l"])
            fig_trend.add_trace(
                go.Scatter(
                    x=nh3_clean["datetime"],
                    y=nh3_clean["primary_calculated_nh3_mg_l"],
                    mode="lines+markers",
                    name="Calculated NH₃ (mg/L)",
                    line=dict(color="#D9534F", width=2),
                ),
                row=1,
                col=1,
            )
            fig_trend.add_hline(y=0.05, line_dash="dash", line_color="#D9534F", annotation_text="0.05 mg/L Toxicity", row=1, col=1)

        fig_trend.add_trace(
            go.Scatter(
                x=df_pond_hist["datetime"],
                y=df_pond_hist["dissolved_oxygen_mg_l"],
                mode="lines+markers",
                name="DO (mg/L)",
                line=dict(color="#087F72", width=2),
            ),
            row=1,
            col=2,
        )
        fig_trend.add_trace(
            go.Scatter(
                x=df_pond_hist["datetime"],
                y=df_pond_hist["temp_c"],
                mode="lines",
                name="Temp (°C)",
                line=dict(color="#E7A23B", width=1.5, dash="dot"),
            ),
            row=1,
            col=2,
        )
        fig_trend.add_hline(y=3.0, line_dash="dash", line_color="#E53E3E", annotation_text="3.0 mg/L Hypoxia", row=1, col=2)

        fig_trend.update_layout(height=280, template="plotly_white", margin=dict(l=30, r=20, t=35, b=25))
        st.plotly_chart(fig_trend, use_container_width=True)

    # ── Scientific Disclaimers & Technical Limitations ────────────────
    with st.expander("🧪 Chemical Formulation & Technical Disclaimers", expanded=False):
        st.markdown(
            f"**Chemical Formulation Note:** Basis: `{tan_basis}` | "
            f"MW conversion: `{'17.031 / 14.007 = 1.2159 (Applied)' if mw_applied else 'Not applied'}`. "
            "The value **2.0 mg/L TAN** represents a chemical test-kit graduation mark, NOT a validated biological toxicity threshold."
        )
        st.latex(basis_formula)
        st.markdown(
            r"""
**Experiment 1 — Ammonia Soft-Sensor (Random Forest):**
The Random Forest soft-sensor **demonstrates severe underprediction at elevated toxic ammonia levels**:
- Actual $NH_3 \ge 0.05\text{ mg/L}$: **79.59% underpredicted** ($N = 98$; mean bias $-0.0637\text{ mg/L}$).
- Actual $NH_3 \ge 0.10\text{ mg/L}$: **100.00% underpredicted** ($N = 33$; mean bias $-0.1336\text{ mg/L}$).
- Actual $NH_3 \ge 0.20\text{ mg/L}$: **100.00% underpredicted** ($N = 10$; mean bias $-0.2234\text{ mg/L}$).
**Prohibition:** This soft-sensor must **NEVER be used as an independent safety alarm** or aeration actuator.

---

**Experiment 2 — Mortality Diagnostic (Balanced Logistic Regression):**
Evaluates concurrent statistical association between environmental water conditions and mortality events:
- Extreme class imbalance: test prevalence is only **1.69%** (44 / 2,607 records).
- Low precision: **3.81%** (produces **227 false alarms** out of 236 alerts on chronological holdout).
- **Advisory Only:** Do NOT use this model for automated alarm dispatch.

---

**Experiment 3 — Next-Visit Ammonia Toxicity Risk (Random Forest Prognostic):**
Evaluates the probability of an un-ionized ammonia spike occurring at the next routine farm visit:
- **Multi-Week Horizon:** Farm revisits span **3 TO 45 DAYS** (median ~21 days).
- **Detection Breakdown:** Total true positives = 18. Newly developed spikes detected = **15 of 54 (27.8% sensitivity)**.
- **No Hourly/Overnight Claims:** This model does NOT provide continuous hourly or overnight forecasts.

---

**Chemical Basis Conventions:**
- **TAN-N (Ammonia-Nitrogen, NH3-N):** TAN expressed on a nitrogen mass basis; requires molecular weight conversion factor **17.031 / 14.007** = 1.2159.
- **TAN-NH3 (Molecular Ammonia):** TAN already expressed as molecular NH₃; no MW conversion needed.
- The value **2.0 mg/L TAN** represents a chemical test-kit graduation mark, NOT a validated biological toxicity threshold.

**Software Bounds & Sampling:**
Software validation bounds are **defensive integrity checks**, NOT validated biological safety thresholds.
Zero Real-Time Streaming: NOT live continuous telemetry; all observations reflect discrete morning visits (06:00–08:30 AM).
"""
        )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
