"""Page 2: Water Quality Chemistry & Experimental Toxicity Screening.

Operational Category: EXPERIMENTAL (Emerson Equilibrium Chemistry & Experimental Screening Models).
Matches the approved Precision AquaDSS reference layout while preserving all registered models,
inputs, scientific calculations, and governance disclosures:
1. Breadcrumb + Aqua-Wave Fish Header
2. 3 Prediction KPI Cards in a single horizontal row (Estimated NH3, Mortality Score, Next-Visit NH3 Risk)
3. Two horizontal expandable sections (Interpretation + Experimental Risk Screening Inputs & Chemistry)
4. Two-column Main Analytics Layout (Left: Risk Trend Analysis card; Right: Select a Historical Pond card)
5. Two bottom full-width expandable cards (Explainable Input-Factor Breakdown & Technical Limitations)
"""

from typing import Dict, Any, Optional
import math
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.core.data_manager import load_dataset
from app.dashboard.utils.styles import inject_custom_css, PALETTE
from app.dashboard.utils.helpers import (
    format_float,
    format_percentage,
    validate_defensive_bounds,
    detect_simulation_source,
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


def render_page() -> None:
    """Render the Water Quality Chemistry & Toxicity Screening page."""
    inject_custom_css()

    render_page_header(
        title="Water Quality Chemistry & Experimental Toxicity Screening",
        subtitle="Analyse pond water quality and screen for toxicity risks using AI models.",
        category_key="EXPERIMENTAL",
    )

    render_uploaded_context_notice(["ph", "temp_c", "emerson_nh3_mg_l", "exp1_est_nh3_mg_l", "exp2_mortality_risk_score", "exp3_next_visit_nh3_risk"])

    # Load historical pond list & pre-fill values from session state or dataset
    default_do, default_ph, default_temp, default_tan = 4.50, 7.80, 28.0, 0.50
    selected_pond = st.session_state.get("wq_pond_prefill", "Manual Entry")
    obs_date_label = "Manual Input"
    df_pond_hist = pd.DataFrame()
    pond_opts = ["Manual Entry"]

    try:
        df_tox = load_dataset("toxicity_analysis")
        pond_opts = ["Manual Entry"] + sorted(df_tox["pond_id"].dropna().astype(str).unique().tolist())
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
    except Exception:
        selected_pond = "Manual Entry"

    # Read current input values (from session state if user adjusted form, else pond defaults)
    do_val = float(st.session_state.get("wq_do_val", default_do))
    ph_val = float(st.session_state.get("wq_ph_val", default_ph))
    temp_val = float(st.session_state.get("wq_temp_val", default_temp))
    tan_val = float(st.session_state.get("wq_tan_val", default_tan))
    tan_basis = st.session_state.get("wq_tan_basis", "TAN-N (Ammonia-Nitrogen, NH3-N)")
    revisit_days = int(st.session_state.get("wq_revisit_days", 21))
    turb_val = st.session_state.get("wq_turb_val", None)
    tds_val = st.session_state.get("wq_tds_val", None)
    mode = st.session_state.get("wq_mode", "Manual Field Inspection Entry (Operational)")
    is_simulated = "Simulated" in mode
    _, status_tag, operational_permitted = detect_simulation_source(is_simulated_flag=is_simulated)

    if is_simulated:
        render_simulation_warning_banner()
        st.warning(
            f"**Operational Gating Status:** `{status_tag}`. "
            f"Operational farm use permitted = `{operational_permitted}`."
        )

    # Emerson Chemistry
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

    # Model inference
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

    # ── 1. Three Equally Sized Prediction KPI Cards ──────────────────────
    exp_c1, exp_c2, exp_c3 = st.columns(3)
    with exp_c1:
        render_metric_card(
            title="Estimated NH3 (Soft-Sensor)",
            value=f"{exp1_nh3:.4f} mg/L" if pd.notna(exp1_nh3) else "Unavailable",
            subtitle="RF Proxy from Physical Parameters",
            icon="🧪",
            accent="aqua",
        )
    with exp_c2:
        render_metric_card(
            title="Concurrent Mortality Score",
            value=format_percentage(exp2_score, decimals=1),
            subtitle="Balanced Logistic Regression",
            icon="🩺",
            accent="teal",
        )
    with exp_c3:
        render_metric_card(
            title=f"Next-Visit NH3 Risk ({exp3_horizon} Days)",
            value=format_percentage(exp3_score, decimals=1),
            subtitle="Spike Risk at Next Routine Visit",
            icon="🛡️",
            accent="warning",
        )

    # ── 2. Two Horizontal Expandable Sections ────────────────────────────
    with st.expander(
        f"ℹ️ Interpretation: ({selected_pond} | {obs_date_label}) — Emerson NH3 = {nh3_calc:.4f} mg/L ({nh3_tier} — {nh3_action})",
        expanded=False,
    ):
        st.caption(
            "Screening scores are exploratory decision-support indicators only; "
            "the ammonia soft-sensor underpredicts elevated NH3 and the mortality diagnostic carries a high false-alarm rate."
        )
        chem_c1, chem_c2, chem_c3, chem_c4 = st.columns(4)
        with chem_c1:
            render_metric_card("Equilibrium pKa", f"{pka:.3f}" if pd.notna(pka) else "N/A", f"At {temp_val:.1f} °C", "Emerson et al. (1975)", icon="⚗️", accent="aqua")
        with chem_c2:
            render_metric_card("Un-ionized Fraction (f)", format_percentage(f_pct, decimals=2), f"pH {ph_val:.2f} & {temp_val:.1f} °C", "Equilibrium Ratio", icon="💧", accent="teal")
        with chem_c3:
            render_metric_card("Molecular Toxic NH3", f"{nh3_calc:.4f} mg/L" if pd.notna(nh3_calc) else "N/A", "Toxic Un-ionized Ammonia", "Calculated Value", icon="🧪", accent="aqua")
        with chem_c4:
            render_metric_card("Toxicity Classification", nh3_tier, nh3_action, "Provisional Heuristic", icon="🏷️", accent="warning" if nh3_tier in ("ELEVATED", "CRITICAL", "EXTREME") else "success")

        st.markdown(
            f"**Chemical Formulation Note:** Basis: `{tan_basis}` | "
            f"MW conversion: `{'17.031 / 14.007 = 1.2159 (Applied)' if mw_applied else 'Not applied'}`. "
            "The value **2.0 mg/L TAN** represents a chemical test-kit graduation mark, NOT a validated biological toxicity threshold."
        )
        st.latex(basis_formula)
        render_decision_support_banner()
        render_multi_week_observation_banner()

    with st.expander("🧪 Experimental Risk Screening Scores (%) — Observation Inputs & Parameters", expanded=False):
        st.caption("Software validation bounds are defensive integrity checks, NOT validated biological safety thresholds.")
        mode = st.radio(
            "Operating Mode:",
            options=["Manual Field Inspection Entry (Operational)", "Simulated Benchmark Scenario (Demonstration Only)"],
            index=0 if not is_simulated else 1,
            horizontal=True,
            key="wq_mode",
        )
        with st.form("water_quality_input_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                new_do = st.number_input("Dissolved Oxygen (DO in mg/L):", min_value=0.0, max_value=25.0, value=max(0.0, min(25.0, do_val)), step=0.1, format="%.2f")
                new_ph = st.number_input("Water pH (standard units):", min_value=0.0, max_value=14.0, value=max(0.0, min(14.0, ph_val)), step=0.05, format="%.2f")
            with col2:
                new_temp = st.number_input("Water Temperature (°C):", min_value=10.0, max_value=45.0, value=max(10.0, min(45.0, temp_val)), step=0.5, format="%.1f")
                new_tan = st.number_input("Total Ammonia Nitrogen (TAN in mg/L):", min_value=0.0, max_value=20.0, value=max(0.0, min(20.0, tan_val)), step=0.05, format="%.2f")
            with col3:
                new_basis = st.selectbox("TAN Chemical Basis:", options=["TAN-N (Ammonia-Nitrogen, NH3-N)", "TAN-NH3 (Molecular Ammonia)"], index=0 if "TAN-N" in tan_basis else 1)
                new_revisit = st.slider("Revisit Horizon for Risk Estimate (days):", min_value=3, max_value=45, value=revisit_days, step=1)

            opt_c1, opt_c2 = st.columns(2)
            with opt_c1:
                turb_enabled = st.checkbox("Include Secchi Turbidity (cm)", value=turb_val is not None)
                new_turb = st.number_input("Turbidity (cm):", min_value=0.0, max_value=150.0, value=float(turb_val) if turb_val is not None else 25.0, disabled=not turb_enabled) if turb_enabled else None
            with opt_c2:
                tds_enabled = st.checkbox("Include Total Dissolved Solids (TDS, ppt)", value=tds_val is not None)
                new_tds = st.number_input("TDS (ppt):", min_value=0.0, max_value=50.0, value=float(tds_val) if tds_val is not None else 1.2, disabled=not tds_enabled) if tds_enabled else None

            if st.form_submit_button("Calculate Chemistry & Run Experimental Screening", use_container_width=True):
                st.session_state["wq_do_val"] = new_do
                st.session_state["wq_ph_val"] = new_ph
                st.session_state["wq_temp_val"] = new_temp
                st.session_state["wq_tan_val"] = new_tan
                st.session_state["wq_tan_basis"] = new_basis
                st.session_state["wq_revisit_days"] = new_revisit
                st.session_state["wq_turb_val"] = new_turb
                st.session_state["wq_tds_val"] = new_tds
                for p_name, p_val in [("do", new_do), ("ph", new_ph), ("water_temp", new_temp), ("tan", new_tan)]:
                    ok, msg = validate_defensive_bounds(p_name, p_val)
                    if not ok and msg:
                        st.warning(msg)
                st.rerun()

    # ── 3. Two-Column Main Analytics Layout ──────────────────────────────
    rc1, rc2 = st.columns([1.4, 1])
    with rc1:
        with st.container(border=True):
            render_section_bar("📊 Risk Trend Analysis")
            fig_risk = go.Figure(
                data=[
                    go.Bar(
                        x=["Concurrent Mortality Risk", f"Next-Visit NH3 Spike Risk ({exp3_horizon}d)"],
                        y=[
                            (exp2_score * 100.0) if pd.notna(exp2_score) else 0.0,
                            (exp3_score * 100.0) if pd.notna(exp3_score) else 0.0,
                        ],
                        marker_color=["#073247", "#087F72"],
                        text=[
                            format_percentage(exp2_score, decimals=1),
                            format_percentage(exp3_score, decimals=1),
                        ],
                        textposition="outside",
                        width=0.45,
                    )
                ]
            )
            fig_risk.update_layout(
                yaxis=dict(title="Screening Score (%)", range=[0, 105], gridcolor="#DCE9E6"),
                template="plotly_white",
                height=265,
                margin=dict(l=35, r=15, t=20, b=35),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_risk, use_container_width=True)

    with rc2:
        with st.container(border=True):
            st.markdown(
                '<div style="display:flex; align-items:center; gap:0.5rem; margin-bottom:0.2rem;">'
                '<span style="font-size:1.15rem;">💡</span>'
                '<span style="font-size:1.02rem; font-weight:800; color:#173747;">Select a Historical Pond</span>'
                '</div>'
                '<div style="font-size:0.83rem; color:#526873; margin-bottom:0.55rem;">'
                'Choose a pond to inspect its recorded NH3 concentration trajectory and pre-fill parameters.'
                '</div>',
                unsafe_allow_html=True,
            )
            chosen_pond = st.selectbox(
                "Pre-fill from Historical Pond Record (Optional):",
                options=pond_opts,
                index=pond_opts.index(selected_pond) if selected_pond in pond_opts else 0,
                key="wq_pond_prefill",
                label_visibility="collapsed",
            )
            # Clear cached manual overrides when pond changes so pond values take effect
            if chosen_pond != st.session_state.get("_wq_last_pond"):
                st.session_state["_wq_last_pond"] = chosen_pond
                for k in ["wq_do_val", "wq_ph_val", "wq_temp_val", "wq_tan_val"]:
                    st.session_state.pop(k, None)
                if chosen_pond != selected_pond:
                    st.rerun()

            if chosen_pond != "Manual Entry" and not df_pond_hist.empty and "primary_calculated_nh3_mg_l" in df_pond_hist.columns:
                nh3_hist = df_pond_hist.dropna(subset=["primary_calculated_nh3_mg_l"])
                if not nh3_hist.empty:
                    fig_nh3 = go.Figure()
                    fig_nh3.add_trace(
                        go.Scatter(
                            x=nh3_hist["datetime"],
                            y=nh3_hist["primary_calculated_nh3_mg_l"],
                            mode="lines+markers",
                            name="Calculated NH3 (mg/L)",
                            line=dict(color="#D9534F", width=2),
                        )
                    )
                    fig_nh3.add_hline(y=0.05, line_dash="dash", line_color="#E7A23B", annotation_text="0.05 mg/L")
                    fig_nh3.update_layout(
                        title=dict(text=f"NH3 History ({chosen_pond})", font=dict(size=12, color="#173747")),
                        yaxis_title="NH3 (mg/L)",
                        template="plotly_white",
                        height=195,
                        margin=dict(l=30, r=10, t=32, b=20),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                    )
                    st.plotly_chart(fig_nh3, use_container_width=True)
                else:
                    st.info(f"No calculated NH3 time-series records available for `{chosen_pond}`.")
            else:
                pond_b64 = get_asset_base64("pond_cages.jpg")
                if pond_b64:
                    st.markdown(
                        f'<img src="data:image/jpeg;base64,{pond_b64}" '
                        f'style="width:100%; height:175px; object-fit:cover; border-radius:10px; display:block; margin-top:0.35rem;" '
                        f'alt="Aquaculture pond cages" />',
                        unsafe_allow_html=True,
                    )

    # ── 4. Bottom Full-Width Expandable Cards ────────────────────────────
    with st.expander("🧪 Explainable Input-Factor Breakdown (Chemistry & Model Inputs)", expanded=False):
        st.caption(
            "SHAP/LIME attributions are not implemented in the saved model wrappers; "
            "the breakdown below reports exact deterministic chemistry and model input factors."
        )
        st.markdown(
            f"- **Emerson Equilibrium Drivers:** At `T = {temp_val:.1f} °C` (`pKa = {pka:.3f}`) and `pH = {ph_val:.2f}`, "
            f"the un-ionized NH3 fraction is `{format_percentage(f_pct, decimals=2)}` (MW conversion: `{'17.031/14.007' if mw_applied else '1.0'}`).\n"
            f"- **Model Input Telemetry:** `DO = {do_val:.2f} mg/L`, `pH = {ph_val:.2f}`, `Temp = {temp_val:.1f} °C`, `Revisit = {revisit_days} days`.\n"
            f"- **Optional Telemetry:** Turbidity = `{f'{turb_val:.1f} cm' if turb_val is not None else 'Not provided (pipeline median-imputed)'}`, "
            f"TDS = `{f'{tds_val:.1f} ppt' if tds_val is not None else 'Not provided (pipeline median-imputed)'}`."
        )

    with st.expander("📄 Technical Limitations & Scientific Disclaimers", expanded=False):
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
