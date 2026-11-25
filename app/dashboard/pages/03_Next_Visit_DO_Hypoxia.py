"""Page 3: Next-Visit Morning DO and Hypoxia Screening.

Operational Category: BENCHMARK (Model Benchmark & Experimental Screening).
Provides:
1. Operational Point Regression Benchmark: Historical Training Mean DO (3.50 mg/L, exact 3.4984 mg/L).
2. Exploratory Moderate Hypoxia Screening (< 3.0 mg/L, Gradient Boosting Classifier).
3. Pond-level historical morning DO trajectory and MAE comparison charts.
4. Expandable scientific disclaimers and transparent rejection of the degenerate < 2.0 mg/L classifier.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.core.data_manager import load_dataset
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_multi_week_observation_banner,
    render_simulation_warning_banner,
    render_uploaded_context_notice,
)
from app.dashboard.components.header import render_page_header, render_section_bar
from app.dashboard.components.metric_card import render_metric_card
from app.dashboard.utils.helpers import (
    detect_simulation_source,
    format_percentage,
    validate_defensive_bounds,
)
from app.dashboard.utils.styles import PALETTE, inject_custom_css
from app.models.do_hypoxia import (
    FROZEN_HIGH_RECALL_THRESHOLD,
    FROZEN_MAX_F1_THRESHOLD,
    HISTORICAL_TRAIN_MEAN_DISPLAY,
    HISTORICAL_TRAIN_MEAN_DO,
)
from app.models.registry import get_model_registry


def render_mae_comparison_chart() -> go.Figure:
    """Render Plotly bar chart comparing prospective test MAE across DO models."""
    models = [
        "Historical Mean (Baseline)",
        "Random Forest Regressor",
        "GBDT Regressor",
        "Persistence Baseline",
    ]
    maes = [0.3963, 0.4172, 0.4260, 0.5334]
    colors = ["#087F72", "#43BFC0", "#526873", "#DCE9E6"]

    fig = go.Figure(
        data=[
            go.Bar(
                x=models,
                y=maes,
                marker_color=colors,
                text=[f"{v:.4f} mg/L" for v in maes],
                textposition="auto",
                marker_line_width=0,
            )
        ]
    )
    fig.update_layout(
        title=dict(
            text="Prospective Holdout MAE Comparison (Experiment 5)",
            font=dict(size=14, color="#0c2340"),
        ),
        yaxis_title="Mean Absolute Error (mg/L)",
        xaxis_title="Forecasting Method",
        template="plotly_white",
        height=300,
        margin=dict(l=40, r=20, t=50, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#f1f5f9"),
    )
    return fig


def render_pond_do_history_chart(df_pond: pd.DataFrame, pond_label: str) -> go.Figure:
    """Render historical morning DO trajectory for the selected pond."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_pond["datetime"],
            y=df_pond["dissolved_oxygen_mg_l"],
            mode="lines+markers",
            name="Morning DO (mg/L)",
            line=dict(color=PALETTE["teal_primary"], width=2.5),
            marker=dict(size=6),
            hovertemplate="Date: %{x|%Y-%m-%d}<br>Morning DO: %{y:.2f} mg/L<extra></extra>",
        )
    )
    fig.add_hline(
        y=HISTORICAL_TRAIN_MEAN_DISPLAY,
        line_dash="dash",
        line_color="#0284c7",
        annotation_text="Benchmark Mean (3.50 mg/L)",
        annotation_position="top right",
    )
    fig.add_hline(
        y=3.0,
        line_dash="dot",
        line_color="#d97706",
        annotation_text="Screening Cutoff (<3.0 mg/L)",
        annotation_position="bottom right",
    )
    fig.update_layout(
        title=dict(
            text=f"Historical Morning DO Trend ({pond_label})",
            font=dict(size=14, color="#0c2340"),
        ),
        xaxis_title="Observation Date",
        yaxis_title="Dissolved Oxygen (mg/L)",
        template="plotly_white",
        height=300,
        margin=dict(l=40, r=20, t=50, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis=dict(gridcolor="#f1f5f9"),
        hovermode="x unified",
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

    render_uploaded_context_notice(["do_mg_l", "exp5_benchmark_next_do_mg_l"])

    with st.expander("Decision-Support & Sampling Context Notices", expanded=False):
        render_decision_support_banner()
        render_multi_week_observation_banner()
        st.caption(
            "Software validation bounds are defensive integrity checks, "
            "NOT validated biological safety thresholds."
        )

    # ── Observation Inputs & Pond Pre-fill ─────────────────────────────
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

    default_do = 4.20
    default_temp = 28.0
    default_ph = 7.80
    selected_pond = "Manual Entry"
    df_pond_hist = pd.DataFrame()

    with ctrl2:
        try:
            df_tox = load_dataset("toxicity_analysis")
            pond_opts = ["Manual Entry"] + sorted(df_tox["pond_id"].dropna().astype(str).unique().tolist())
            selected_pond = st.selectbox(
                "Pre-fill from Historical Pond Record (Optional):",
                options=pond_opts,
                index=0,
                key="do_pond_prefill",
            )
            if selected_pond != "Manual Entry":
                df_pond_hist = df_tox[df_tox["pond_id"].astype(str) == selected_pond].copy()
                if "datetime" in df_pond_hist.columns:
                    df_pond_hist["datetime"] = pd.to_datetime(df_pond_hist["datetime"], errors="coerce")
                    df_pond_hist = df_pond_hist.dropna(subset=["datetime"]).sort_values("datetime")
                valid_do = df_pond_hist.dropna(subset=["dissolved_oxygen_mg_l"])
                if not valid_do.empty:
                    latest_row = valid_do.iloc[-1]
                    default_do = float(latest_row["dissolved_oxygen_mg_l"])
                    if pd.notna(latest_row.get("temp_c")):
                        default_temp = float(latest_row["temp_c"])
                    if pd.notna(latest_row.get("ph")):
                        default_ph = float(latest_row["ph"])
        except Exception:
            selected_pond = "Manual Entry"

    with st.form("do_hypoxia_input_form"):
        c1, c2 = st.columns(2)
        with c1:
            do_val = st.number_input(
                "Current Morning DO (mg/L):",
                min_value=0.0,
                max_value=25.0,
                value=max(0.0, min(25.0, default_do)),
                step=0.1,
                format="%.2f",
                help="Morning observation (06:00–08:30 AM). Software boundary: 0.0 - 25.0 mg/L.",
            )
        with c2:
            revisit_days = st.slider(
                "Farm Revisit Interval (days):",
                min_value=3,
                max_value=45,
                value=21,
                step=1,
                help="Discrete routine farm revisit interval (3–45 days; median ~21 days).",
            )

        with st.expander("Optional Auxiliary Pond Parameters (Temp, pH, Feed, Biomass)", expanded=False):
            opt_c1, opt_c2, opt_c3 = st.columns(3)
            with opt_c1:
                temp_val = st.number_input(
                    "Water Temperature (°C):",
                    min_value=10.0,
                    max_value=45.0,
                    value=max(10.0, min(45.0, default_temp)),
                    step=0.5,
                )
                ph_val = st.number_input(
                    "Water pH:",
                    min_value=0.0,
                    max_value=14.0,
                    value=max(0.0, min(14.0, default_ph)),
                    step=0.05,
                )
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

    # Defensive input validation
    val_errs = []
    for p_name, p_val in [("do", do_val), ("water_temp", temp_val), ("ph", ph_val), ("revisit_interval", revisit_days)]:
        ok, msg = validate_defensive_bounds(p_name, p_val)
        if not ok and msg:
            val_errs.append(msg)
    if val_errs:
        for err in val_errs:
            st.warning(err)

    # Backend model execution
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

    # ── Analysis Results ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader("DO Benchmark & Hypoxia Screening Results")
    if is_simulated:
        st.caption(f"Mode: `{status_tag}` (operational_use_permitted = `{operational_permitted}`).")

    hyp_screening = res.get("exploratory_hypoxia_screening", {})
    hyp_score = hyp_screening.get("hypoxia_risk_score")
    is_flagged = hyp_screening.get("screening_flag")

    rc1, rc2, rc3, rc4 = st.columns(4)
    with rc1:
        render_metric_card(
            title="Next-Visit DO Benchmark",
            value=f"{HISTORICAL_TRAIN_MEAN_DISPLAY:.2f} mg/L",
            subtitle="Constant historical mean",
            benchmark_ref="Exact: 3.4984 mg/L",
        )
    with rc2:
        render_metric_card(
            title="Hypoxia Screening Score",
            value=format_percentage(hyp_score, decimals=1) if hyp_score is not None else "N/A",
            subtitle="Exploratory GBDT (< 3.0 mg/L)",
            benchmark_ref="PR-AUC = 0.095 (Base 0.085)",
        )
    with rc3:
        render_metric_card(
            title="Queue Screening Flag",
            value="FLAGGED" if is_flagged else "UNFLAGGED",
            subtitle=f"Cutoff p* = {FROZEN_HIGH_RECALL_THRESHOLD:.3f}",
            benchmark_ref="91.00% False Discovery Rate",
        )
    with rc4:
        render_metric_card(
            title="Severe Hypoxia (< 2.0)",
            value="DISABLED",
            subtitle="REJECTED AS DEGENERATE",
            benchmark_ref="99.56% false alarm rate",
        )

    # ── Historical Morning DO Trend ───────────────────────────────────
    if selected_pond != "Manual Entry" and not df_pond_hist.dropna(subset=["dissolved_oxygen_mg_l"]).empty:
        st.plotly_chart(
            render_pond_do_history_chart(df_pond_hist.dropna(subset=["dissolved_oxygen_mg_l"]), selected_pond),
            use_container_width=True,
        )
    else:
        st.info("Select a historical pond above to view its morning DO trend alongside the 3.50 mg/L benchmark.")

    # ── Expandable Technical Details & Disclaimers ────────────────────
    with st.expander("Primary Benchmark: Why Historical Mean Beats ML", expanded=False):
        st.markdown(
            """
            - **Historical Training Mean Baseline: 3.50 mg/L (`3.4984 mg/L`):** Unconditional training mean (N = 3,066 pairs, 2021–2024). It is a **constant historical benchmark, NOT a dynamic biological prediction**.
            - **Holdout Performance:** Achieved MAE = **0.3963 mg/L** (RMSE = 0.6450 mg/L), outperforming Persistence (MAE = 0.5334 mg/L, R² = -0.7071, p < 10⁻¹²), Random Forest (MAE = 0.4172 mg/L), and GBDT (MAE = 0.4260 mg/L).
            - **Root Cause:** Multi-week revisit intervals (**3–45 days**, median ~21 days) decouple diurnal DO kinetics, and unrecorded aeration/water-exchange interventions occur between visits.
            """
        )
        st.plotly_chart(render_mae_comparison_chart(), use_container_width=True)

    with st.expander("Hypoxia Screening: False Alarm Burden & Severe Classifier Rejection", expanded=False):
        st.markdown(
            """
            - **Moderate Hypoxia Screening (< 3.0 mg/L, GBDT — EXPLORATORY ONLY):** Retained strictly as an exploratory queue-sorting score (never an automated alarm).
              - At high-recall cutoff (`p* = 0.090`): 53.49% recall (92/172), **50.25% alarm rate** (1,022/2,034), and **91.00% False Discovery Rate** (930 false alarms).
              - At Max F1 cutoff (`p* = 0.220`): 8.55% alarm rate, 9.30% recall (16/172), 90.80% FDR.
            - **Severe Hypoxia Classifier (< 2.0 mg/L, Random Forest):** **REJECTED AS DEGENERATE** and disabled by governance. At `p = 0.10`, `class_weight='balanced'` inflated probabilities to flag **99.56% of test visits** (2,025/2,034; specificity = 0.0041; **1,934 false alarms**).
            """
        )

    with st.expander("Observation Protocol & Governance Boundaries", expanded=False):
        st.markdown(
            """
            - **Observation Window:** Morning inspection visits (**06:00–08:30 AM**); these are **NOT verified pre-dawn daily minimum DO** readings.
            - **Sampling Horizon:** Discrete multi-week intervals (**3 to 45 days**, median ~21 days). **Zero Real-Time Streaming**: no continuous sensor streaming, diurnal cycling, or overnight forecasts.
            - **Human Oversight:** All outputs are decision-support benchmarks with zero automated aerator or equipment actuation (`is_automatic_control = False`).
            """
        )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
