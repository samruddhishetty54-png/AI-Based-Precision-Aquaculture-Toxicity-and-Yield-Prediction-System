"""Page 3: Next-Visit Morning DO and Hypoxia Screening.

Operational Category: BENCHMARK (Model Benchmark & Experimental Screening).
Provides:
1. Operational Point Regression Benchmark: Historical Training Mean DO (3.50 mg/L, exact 3.4984 mg/L).
   - Prominently labeled as a CONSTANT HISTORICAL BENCHMARK, NOT A DYNAMIC PREDICTION.
   - Lowest chronological test error (MAE = 0.3963 mg/L, RMSE = 0.6450 mg/L) vs Persistence (MAE = 0.5334 mg/L)
     and ML regressors (RF MAE = 0.4172 mg/L, GBDT MAE = 0.4260 mg/L).
2. Multi-Week Sampling Horizon (3–45 days) & Morning Observation Window (06:00–08:30 AM).
   - Explicitly NOT verified pre-dawn daily minimum DO.
   - Zero claims of real-time sensor streaming, diurnal cycling, or overnight forecasts.
3. Exploratory Moderate Hypoxia Screening (< 3.0 mg/L, Gradient Boosting Classifier).
   - Retained solely as an exploratory screening score for inspection queues, NEVER an automated alarm.
   - Full disclosure of audited false alarm burden: 50.25% alarm rate, 91.00% False Discovery Rate at p* = 0.090.
4. Transparent Educational Rejection of Severe Hypoxia Classifier (< 2.0 mg/L, Random Forest).
   - Rejected as degenerate (99.56% false alarm rate due to class_weight probability distortion).
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
from app.models.do_hypoxia import (
    HISTORICAL_TRAIN_MEAN_DO,
    HISTORICAL_TRAIN_MEAN_DISPLAY,
    FROZEN_HIGH_RECALL_THRESHOLD,
    FROZEN_MAX_F1_THRESHOLD,
)


def render_mae_comparison_chart() -> go.Figure:
    """Render Plotly bar chart comparing prospective test MAE across DO models."""
    models = [
        "Historical Mean (Baseline)",
        "Random Forest Regressor",
        "GBDT Regressor",
        "Persistence Baseline",
    ]
    maes = [0.3963, 0.4172, 0.4260, 0.5334]
    colors = ["#0284c7", "#64748b", "#94a3b8", "#cbd5e1"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=models,
                y=maes,
                marker_color=colors,
                text=[f"{v:.4f} mg/L" for v in maes],
                textposition="auto",
            )
        ]
    )
    fig.update_layout(
        title="Prospective Chronological Holdout MAE Comparison (Experiment 5)",
        yaxis_title="Mean Absolute Error (mg/L)",
        xaxis_title="Forecasting Method",
        template="plotly_white",
        height=320,
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig


def render_page() -> None:
    """Render the Next-Visit Morning DO and Hypoxia Screening page."""
    inject_custom_css()

    render_page_header(
        title="Next-Visit Morning DO and Hypoxia Screening",
        subtitle="Historical mean DO benchmark and exploratory Gradient Boosting moderate-hypoxia screening.",
        category_key="BENCHMARK",
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

    # Section 2: Pond Inspection Observation Form
    st.markdown("### 2. Pond Water Quality Telemetry & Revisit Parameters")
    st.caption(
        "Enter physical pond observations. Software validation bounds are defensive integrity checks, "
        "NOT validated biological safety thresholds."
    )

    with st.form("do_hypoxia_input_form"):
        c1, c2 = st.columns(2)
        with c1:
            do_val = st.number_input(
                "Current Morning DO (mg/L):",
                min_value=0.0,
                max_value=25.0,
                value=4.20,
                step=0.1,
                format="%.2f",
                help="Morning DO observation (06:00–08:30 AM). Software boundary: 0.0 - 25.0 mg/L.",
            )
            revisit_days = st.slider(
                "Farm Revisit Interval (days):",
                min_value=3,
                max_value=45,
                value=21,
                step=1,
                help="Discrete farm inspection interval. Audited range: 3 to 45 days (median ~21 days).",
            )

        with c2:
            st.markdown(
                """
                <div style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #0284c7; padding: 0.75rem 1rem; border-radius: 4px; font-size: 0.88rem; color: #0f172a; line-height: 1.45;">
                    <strong>Observation Protocol Disclaimers:</strong><br>
                    • <strong>Time Window:</strong> Standard morning inspection observations (<strong>06:00–08:30 AM</strong>).<br>
                    • <strong>NOT Daily Minimum DO:</strong> These readings are <strong>NOT verified pre-dawn daily minimum DO</strong>.<br>
                    • <strong>Zero Real-Time Streaming:</strong> No continuous sensor streaming, diurnal cycle tracking, or overnight forecasts.<br>
                    • <strong>Horizon:</strong> Forecast applies to the <strong>next routine visit ({revisit_days} days)</strong>, not tomorrow morning.
                </div>
                """.format(revisit_days=revisit_days),
                unsafe_allow_html=True,
            )

        with st.expander("Optional Auxiliary Pond Parameters (Water Temp, pH, Feed, Biomass)", expanded=False):
            opt_c1, opt_c2, opt_c3 = st.columns(3)
            with opt_c1:
                temp_val = st.number_input("Water Temperature (°C):", min_value=10.0, max_value=45.0, value=28.0, step=0.5)
                ph_val = st.number_input("Water pH:", min_value=0.0, max_value=14.0, value=7.80, step=0.05)
                turb_val = st.number_input("Secchi Turbidity (cm):", min_value=0.0, max_value=150.0, value=25.0, step=1.0)
            with opt_c2:
                tds_val = st.number_input("TDS (ppt):", min_value=0.0, max_value=50.0, value=1.2, step=0.1)
                feed_val = st.number_input("Current Daily Feed (kg):", min_value=0.0, max_value=2000.0, value=25.0, step=1.0)
                density_val = st.number_input("Stocking Density (fish/acre):", min_value=0.0, max_value=50000.0, value=5000.0, step=500.0)
            with opt_c3:
                weight_val = st.number_input("Average Fish Weight (g):", min_value=0.0, max_value=5000.0, value=150.0, step=10.0)
                area_val = st.number_input("Pond Area (acres):", min_value=0.0, max_value=50.0, value=1.0, step=0.1)
                weather_opt = st.selectbox("Current Weather:", options=["Sunny", "Cloudy", "Rainy", "Windy"], index=0)

        submitted = st.form_submit_button("Run DO Evaluation & Hypoxia Screening", use_container_width=True)

    # Input defensive validation
    val_errs = []
    for p_name, p_val in [("do", do_val), ("water_temp", temp_val), ("ph", ph_val), ("revisit_interval", revisit_days)]:
        ok, msg = validate_defensive_bounds(p_name, p_val)
        if not ok and msg:
            val_errs.append(msg)

    if val_errs:
        for err in val_errs:
            st.warning(err)

    # Backend Model Execution
    registry = get_model_registry()
    payload = {
        "curr_do": float(do_val),
        "gap_days": float(revisit_days),
        "curr_temp_c": float(temp_val),
        "curr_ph": float(ph_val),
        "curr_turbidity_cm": float(turb_val),
        "curr_tds_ppt": float(tds_val),
        "curr_feed_amount_kg": float(feed_val),
        "curr_stocking_density": float(density_val),
        "curr_weight": float(weight_val),
        "pond_area_acres": float(area_val),
        "curr_weather": weather_opt,
        "is_simulated": is_simulated,
        "data_source": "benchmark_simulation" if is_simulated else "field_inspection",
    }

    try:
        res = registry.predict_do_hypoxia(payload)
    except Exception as exc:
        st.error(f"Error during DO & Hypoxia evaluation: {exc}")
        return

    # Section 3: Primary Operational Point Regression Benchmark: Historical Mean DO
    st.markdown("---")
    st.markdown("### 3. Primary Operational Point Regression Benchmark")
    st.markdown(
        r"""
        <div style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; background-color: #f8fafc; border: 2px solid #0284c7; border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 1rem;">
            <div style="font-size: 0.8rem; text-transform: uppercase; color: #0284c7; font-weight: 700; letter-spacing: 0.05em;">
                Designated Operational Primary Baseline
            </div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #0f172a; margin-top: 0.25rem;">
                Historical Training Mean Baseline: 3.50 mg/L
            </div>
            <div style="font-size: 0.88rem; color: #1e293b; font-weight: 500; margin-top: 0.25rem;">
                Exact unconditional training mean: <code>3.4984 mg/L</code> (N = 3,066 training pairs, 2021–2024).
            </div>
            <div style="background-color: #fee2e2; border-left: 4px solid #ef4444; padding: 0.5rem 0.75rem; border-radius: 4px; margin-top: 0.75rem; font-size: 0.8rem; color: #991b1b;">
                <strong>MANDATORY SCIENTIFIC DISCLAIMER:</strong> This is an <strong>unconditional constant historical benchmark, NOT a dynamic biological prediction</strong>.
                It represents the central statistical attractor of commercial morning observations across irregular 3–45 day revisit intervals.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    bc1, bc2, bc3, bc4 = st.columns(4)
    with bc1:
        render_metric_card(
            title="Point Benchmark",
            value=f"{HISTORICAL_TRAIN_MEAN_DISPLAY:.2f} mg/L",
            subtitle="Unconditional Constant Mean",
            benchmark_ref="Exact: 3.4984 mg/L",
        )
    with bc2:
        render_metric_card(
            title="Holdout MAE",
            value="0.3963 mg/L",
            subtitle="RMSE = 0.6450 mg/L",
            benchmark_ref="Lowest Error in Exp 5",
        )
    with bc3:
        render_metric_card(
            title="Persistence Baseline",
            value="0.5334 mg/L",
            subtitle="R² = -0.7071 (p < 10⁻¹²)",
            benchmark_ref="Persistence Outperformed",
        )
    with bc4:
        render_metric_card(
            title="Complex ML Regressors",
            value="RF: 0.4172 mg/L",
            subtitle="GBDT: 0.4260 mg/L",
            benchmark_ref="ML Failed to Beat Mean",
        )

    # Plotly Chart & Contextual Explanation
    st.plotly_chart(render_mae_comparison_chart(), use_container_width=True)

    with st.expander("Why did the constant historical mean beat complex machine learning models on commercial ponds?", expanded=False):
        st.markdown(
            """
            **Audited Finding from Experiment 5:**
            1. **Multi-Week Sampling Decoupling:** Routine commercial farm visits occur at irregular intervals of **3 to 45 days (median ~21 days)**. At this multi-week time scale, diurnal dissolved oxygen kinetics (respiration and photosynthesis cycles occurring over hours) are completely decoupled from current readings.
            2. **Unmeasured Farm Interventions:** Farmers operate emergency aerators, pump fresh canal water, exchange pond water, or apply lime between scheduled visits without logging telemetry. These unrecorded physical interventions disrupt continuous regression models.
            3. **Statistical Dominance:** On holdout commercial ponds (2025–2026), predicting the unconditional training mean ($3.4984\\text{ mg/L}$) achieved an **MAE of 0.3963 mg/L**, statistically superior to persistence (MAE = 0.5334 mg/L, $p < 10^{-12}$) and superior to Random Forest (MAE = 0.4172 mg/L) and GBDT (MAE = 0.4260 mg/L).
            4. **Scientific Honesty:** Rather than presenting an illusion of high-tech machine learning precision, the system transparently deploys the historical training mean as the primary point benchmark.
            """
        )

    # Section 4: Exploratory Moderate Hypoxia Screening (< 3.0 mg/L)
    st.markdown("---")
    st.markdown("### 4. Exploratory Moderate Hypoxia Screening (< 3.0 mg/L)")
    st.caption("Gradient Boosting Classifier for inspection queue risk prioritization. Strictly exploratory; never an automated emergency alert.")

    hyp_screening = res.get("exploratory_hypoxia_screening", {})
    hyp_score = hyp_screening.get("hypoxia_risk_score")
    is_flagged = hyp_screening.get("screening_flag")

    hc1, hc2, hc3, hc4 = st.columns(4)
    with hc1:
        render_metric_card(
            title="Hypoxia Risk Score",
            value=format_percentage(hyp_score, decimals=1) if hyp_score is not None else "0.095 PR-AUC",
            subtitle="Gradient Boosting Probability",
            benchmark_ref="No-Skill Baseline = 0.0846",
        )
    with hc2:
        render_metric_card(
            title="High-Recall Cutoff (p* = 0.090)",
            value="ALERT FLAGGED" if is_flagged else "UNFLAGGED",
            subtitle="Screening Threshold: 0.090",
            benchmark_ref="50.25% Alarm Rate",
        )
    with hc3:
        render_metric_card(
            title="False Discovery Rate",
            value="91.00% FDR",
            subtitle="930 false alarms / 1,022 alerts",
            benchmark_ref="Unsustainable for Actuation",
        )
    with hc4:
        render_metric_card(
            title="Operational Verdict",
            value="EXPLORATORY ONLY",
            subtitle="Manual queue sorting only",
            benchmark_ref="Zero Automated Actuation",
        )

    # Audited False Alarm Burden Callout
    st.markdown(
        """
        <div style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; background-color: #fffbeb; border: 1px solid #f59e0b; border-left: 5px solid #d97706; padding: 1rem 1.25rem; border-radius: 6px; margin-top: 0.5rem; font-size: 0.85rem; color: #92400e;">
            <strong>AUDITED FALSE ALARM BURDEN DISCLOSURE (Experiment 5 Holdout, N = 2,034 visits):</strong><br>
            • <strong>High-Recall Cutoff (p* = 0.090):</strong> Detects <strong>53.49% of crises</strong> (92 / 172 true hypoxia visits), but triggers an unsustainable <strong>50.25% alarm rate</strong> (1,022 / 2,034 visits) with a <strong>91.00% False Discovery Rate</strong> (930 false alarms, 80 false negatives).<br>
            • <strong>Max F1 Cutoff (p* = 0.220):</strong> Alarm rate drops to 8.55% (174 visits), but recall collapses to <strong>9.30%</strong> (only 16 / 172 crises caught; 158 false alarms, FDR = 90.80%).<br>
            • <strong>STRICT PROHIBITION:</strong> This classifier must <strong>NEVER be used as an independent safety alarm, automated aerator trigger, or emergency actuator</strong>. It is retained solely as an exploratory risk index for manual inspection queue prioritization.
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Section 5: Transparent Rejection of Severe Hypoxia Classifier (< 2.0 mg/L)
    st.markdown("---")
    st.markdown("### 5. Transparent Rejection of Severe Hypoxia Classifier (< 2.0 mg/L)")
    st.markdown(
        """
        <div style="box-sizing: border-box; width: 100%; max-width: 100%; overflow-wrap: break-word; background-color: #fef2f2; border: 1px solid #f87171; border-left: 5px solid #dc2626; padding: 1rem 1.25rem; border-radius: 6px; font-size: 0.85rem; color: #991b1b;">
            <div style="font-size: 1rem; font-weight: 700; margin-bottom: 0.25rem;">
                Model Status: REJECTED AS DEGENERATE / DISABLED BY SYSTEM GOVERNANCE
            </div>
            <strong>Candidate Model:</strong> Random Forest Classifier (< 2.0 mg/L Severe Hypoxia).<br>
            <strong>Audit Ground Truth:</strong>
            <ul>
                <li>At prospective cutoff <code>p = 0.10</code>, the model flagged <strong>99.56% of test visits</strong> (2,025 out of 2,034 commercial visits) as positive crises.</li>
                <li><strong>Mathematical Root Cause:</strong> Severe hypoxia is an extreme rare-event condition (only 91 positive cases vs 1,943 negatives in the test set). Applying <code>class_weight='balanced'</code> severely inflated predicted probabilities across the entire feature space, destroying model specificity (specificity = <code>0.0041</code>, generating <strong>1,934 false alarms</strong>).</li>
                <li><strong>Operational Verdict:</strong> The model is mathematically degenerate and completely unviable for operational deployment. It is permanently disabled and preserved in the audit catalog solely for educational transparency.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Section 6: Scientific Limitations and Boundaries
    st.markdown("---")
    st.markdown("### 6. Scientific Limitations & Governance Boundaries")
    st.markdown(
        """
        - **Sampling Horizon:** All observations and projections reflect discrete routine farm visits scheduled **3 to 45 days apart (median ~21 days)**.
        - **Observation Window:** Telemetry is gathered during standard **morning farm visits (06:00–08:30 AM)**. These readings **are NOT verified pre-dawn daily minimum DO**.
        - **Zero Real-Time Claims:** The system strictly disclaims real-time continuous sensor streaming, diurnal kinetics, hourly forecasts, or overnight minimum DO prediction.
        - **Human Oversight Required:** All outputs are provisional decision-support benchmarks. No automatic equipment control or aerator commands are executed.
        """
    )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
