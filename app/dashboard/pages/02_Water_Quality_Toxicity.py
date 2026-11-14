"""Page 2: Water Quality Chemistry & Experimental Toxicity Screening.

Operational Category: EXPERIMENTAL (Emerson Equilibrium Chemistry & Experimental Screening Models).
Provides:
1. Emerson et al. (1975) equilibrium ammonia calculator distinguishing TAN-N from TAN-NH3.
2. Experiment 1 Random Forest Ammonia Soft-Sensor with tiered underprediction warnings.
3. Experiment 2 Balanced Logistic Regression Mortality Diagnostic with low-precision warnings.
4. Experiment 3 Random Forest Next-Visit Ammonia Toxicity Risk (3–45 days) with spike detection breakdown.
"""

from typing import Dict, Any, Optional
import math
import pandas as pd
import streamlit as st

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
        subtitle="Emerson dissociation equilibrium calculations and experimental ML screening proxies.",
        category_key="EXPERIMENTAL",
    )

    render_decision_support_banner()
    render_multi_week_observation_banner()

    # Data Source Mode Toggle
    st.markdown("### 1. Data Source & Operational Context")
    mode = st.radio(
        "Select Operating Mode:",
        options=["Manual Field Inspection Entry (Operational)", "Simulated Benchmark Scenario (Demonstration Only)"],
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

    # Input Form
    st.markdown("### 2. Physical & Chemical Water Parameters")
    st.caption(
        "Enter physical pond measurements. Software validation bounds are defensive integrity checks, "
        "NOT validated biological safety thresholds."
    )

    with st.form("water_quality_input_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            do_val = st.number_input(
                "Dissolved Oxygen (DO in mg/L):",
                min_value=0.0,
                max_value=25.0,
                value=4.50,
                step=0.1,
                format="%.2f",
                help="Morning DO reading. Software boundary: 0.0 - 25.0 mg/L.",
            )
            ph_val = st.number_input(
                "Water pH (standard units):",
                min_value=0.0,
                max_value=14.0,
                value=7.80,
                step=0.05,
                format="%.2f",
                help="Water pH. Software boundary: 0.0 - 14.0.",
            )

        with col2:
            temp_val = st.number_input(
                "Water Temperature (°C):",
                min_value=10.0,
                max_value=45.0,
                value=28.0,
                step=0.5,
                format="%.1f",
                help="Water temperature in °C. Software boundary: 10.0 - 45.0 °C.",
            )
            tan_val = st.number_input(
                "Total Ammonia Nitrogen (TAN in mg/L):",
                min_value=0.0,
                max_value=20.0,
                value=0.50,
                step=0.05,
                format="%.2f",
                help="Total ammonia test-kit reading. Software boundary: 0.0 - 20.0 mg/L.",
            )

        with col3:
            tan_basis = st.selectbox(
                "TAN Chemical Basis:",
                options=["TAN-N (Ammonia-Nitrogen, NH3-N)", "TAN-NH3 (Molecular Ammonia)"],
                index=0,
                help="Specifies molecular mass basis. TAN-N applies MW conversion ratio (17.031/14.007).",
            )
            revisit_days = st.slider(
                "Revisit Horizon for Risk Estimate (days):",
                min_value=3,
                max_value=45,
                value=21,
                step=1,
                help="Discrete farm revisit interval. Audited range: 3 to 45 days (median ~21 days).",
            )

        # Optional auxiliary measurements
        with st.expander("Optional Physical Telemetry (Turbidity & TDS)", expanded=False):
            opt_c1, opt_c2 = st.columns(2)
            with opt_c1:
                turb_enabled = st.checkbox("Include Secchi Turbidity (cm)", value=False)
                turb_val = st.number_input(
                    "Turbidity (cm):",
                    min_value=0.0,
                    max_value=150.0,
                    value=25.0,
                    disabled=not turb_enabled,
                ) if turb_enabled else None
            with opt_c2:
                tds_enabled = st.checkbox("Include Total Dissolved Solids (TDS, ppt)", value=False)
                tds_val = st.number_input(
                    "TDS (ppt):",
                    min_value=0.0,
                    max_value=50.0,
                    value=1.2,
                    disabled=not tds_enabled,
                ) if tds_enabled else None

        submitted = st.form_submit_button("Calculate Chemistry & Run Experimental Screening", use_container_width=True)

    # Perform Calculations and Model Inference
    # Defensive software bound validations
    val_errs = []
    for p_name, p_val in [("do", do_val), ("ph", ph_val), ("water_temp", temp_val), ("tan", tan_val)]:
        ok, msg = validate_defensive_bounds(p_name, p_val)
        if not ok and msg:
            val_errs.append(msg)

    if val_errs:
        for err in val_errs:
            st.warning(err)

    # Section 3: Emerson Ammonia Dissociation Calculator
    st.markdown("---")
    st.markdown("### 3. Emerson (1975) Aqueous Ammonia Dissociation")
    st.caption("Analytical chemical equilibrium calculation. Un-ionized NH3 fraction depends dynamically on pH and temperature.")

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

    chem_c1, chem_c2, chem_c3, chem_c4 = st.columns(4)
    with chem_c1:
        render_metric_card(
            title="Equilibrium pKa",
            value=f"{pka:.3f}" if pd.notna(pka) else "N/A",
            subtitle=f"At {temp_val:.1f} °C",
            benchmark_ref="Emerson et al. (1975)",
        )
    with chem_c2:
        render_metric_card(
            title="Un-ionized Fraction (f)",
            value=format_percentage(f_pct, decimals=2),
            subtitle=f"pH {ph_val:.2f} & {temp_val:.1f} °C",
            benchmark_ref="Equilibrium Ratio",
        )
    with chem_c3:
        render_metric_card(
            title="Molecular Toxic NH3",
            value=f"{nh3_calc:.4f} mg/L" if pd.notna(nh3_calc) else "N/A",
            subtitle="Toxic Un-ionized Ammonia",
            benchmark_ref="Calculated Value",
        )
    with chem_c4:
        render_metric_card(
            title="Toxicity Classification",
            value=nh3_tier,
            subtitle=nh3_action,
            benchmark_ref="Provisional Heuristic",
        )

    st.markdown(
        f"""
        <div style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 0.75rem 1rem; margin-top: 0.5rem; font-size: 0.85rem; color: #0f172a; line-height: 1.45;">
            <strong>Chemical Formulation Note:</strong><br>
            • Basis selected: <code>{tan_basis}</code><br>
            • Active formula: $${basis_formula}$$<br>
            • Molecular weight conversion factor: <code>{"17.031 / 14.007 = 1.2159 (Applied)" if mw_applied else "Not applied (TAN already expressed as molecular NH3)"}</code>.<br>
            • <strong>Test-Kit Note:</strong> The value <strong>2.0 mg/L TAN</strong> represents a chemical test-kit graduation mark, NOT a validated biological toxicity threshold.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Section 4: Model Inference - Experiments 1, 2, 3
    st.markdown("---")
    st.markdown("### 4. Experimental Machine Learning Screening Diagnostics")
    st.caption("All models below are experimental research screening proxies. They are NOT certified laboratory assays or emergency alarms.")

    registry = get_model_registry()

    # Experiment 1: Ammonia Soft-Sensor
    st.markdown("#### Experiment 1: Ammonia Soft-Sensor Proxy (Random Forest)")
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

    e1_col1, e1_col2 = st.columns([1, 2])
    with e1_col1:
        render_metric_card(
            title="Estimated NH3 (Soft-Sensor)",
            value=f"{exp1_nh3:.4f} mg/L" if pd.notna(exp1_nh3) else "Unavailable",
            subtitle="RF Proxy from Physical Parameters",
            benchmark_ref="Holdout MAE = 0.0528 mg/L",
        )
    with e1_col2:
        st.warning(
            r"""
            ⚠️ **MANDATORY SCIENTIFIC LIMITATION NOTICE:**
            The Random Forest soft-sensor **demonstrates severe underprediction at elevated toxic ammonia levels**:
            • Actual $NH_3 \ge 0.05\text{ mg/L}$: **79.59% underpredicted** ($N = 98$; mean bias $-0.0637\text{ mg/L}$).
            • Actual $NH_3 \ge 0.10\text{ mg/L}$: **100.00% underpredicted** ($N = 33$; mean bias $-0.1336\text{ mg/L}$).
            • Actual $NH_3 \ge 0.20\text{ mg/L}$: **100.00% underpredicted** ($N = 10$; mean bias $-0.2234\text{ mg/L}$).
            **Prohibition:** This soft-sensor must NEVER be used as an independent safety alarm or aeration actuator.
            """
        )

    # Experiment 2: Fish Mortality Diagnostic
    st.markdown("#### Experiment 2: Fish Mortality Diagnostic (Balanced Logistic Regression)")
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

    e2_col1, e2_col2 = st.columns([1, 2])
    with e2_col1:
        render_metric_card(
            title="Concurrent Mortality Score",
            value=format_percentage(exp2_score, decimals=1),
            subtitle="Balanced Logistic Regression",
            benchmark_ref="ROC-AUC = 0.5917",
        )
    with e2_col2:
        st.info(
            """
            ℹ️ **DIAGNOSTIC ADVISORY LIMITATION:**
            Evaluates concurrent statistical association between environmental water conditions and mortality events:
            • Extreme class imbalance: test prevalence is only **1.69%** (44 / 2,607 records).
            • Low precision: **3.81%** (produces **227 false alarms** out of 236 alerts on chronological holdout).
            • **Advisory Only:** Do NOT use this model for automated alarm dispatch.
            """
        )

    # Experiment 3: Next-Visit Ammonia Toxicity Risk
    st.markdown("#### Experiment 3: Next-Visit Ammonia Toxicity Risk (Random Forest Prognostic)")
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

    e3_col1, e3_col2 = st.columns([1, 2])
    with e3_col1:
        render_metric_card(
            title=f"Next-Visit Risk ({exp3_horizon} Days)",
            value=format_percentage(exp3_score, decimals=1),
            subtitle="Spike Risk at Next Routine Visit",
            benchmark_ref="ROC-AUC = 0.6874",
        )
    with e3_col2:
        st.info(
            """
            🗓️ **MULTI-WEEK HORIZON CONTEXT (3 TO 45 DAYS):**
            Evaluates the probability of an un-ionized ammonia spike occurring at the next routine farm visit:
            • **Detection Breakdown:** Total true positives = 18. Newly developed spikes detected = **15 of 54 (27.8% sensitivity)**.
            • **No Hourly/Overnight Claims:** Farm revisits are multi-week intervals (median ~21 days). This model does NOT provide continuous hourly or overnight forecasts.
            """
        )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
