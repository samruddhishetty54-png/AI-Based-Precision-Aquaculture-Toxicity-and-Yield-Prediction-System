"""Page 5: Historical Field Observations Explorer.

Operational Category: HISTORICAL (Historical Field Observations).
Provides transparent exploration of longitudinal commercial aquaculture data:
1. Safe cached loading via app.core.data_manager (preserves NaNs).
2. Longitudinal trajectory plots (DO, pH, temperature, cohort weight) using Plotly.
3. Empirical missingness profiles and data quality distribution.
4. Filterable raw field inspection records.
"""

from typing import List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.dashboard.utils.styles import inject_custom_css, PALETTE
from app.dashboard.utils.helpers import (
    format_float,
    format_percentage,
    get_active_farm_type,
    get_container_label,
    get_container_id_label,
    get_farm_type_disclaimer,
)
from app.dashboard.components.header import render_page_header, render_section_bar
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_multi_week_observation_banner,
    render_uploaded_context_notice,
)
from app.dashboard.components.metric_card import render_metric_card
from app.core.data_manager import load_dataset, DATASET_METADATA


AVAILABLE_DATASETS = {
    "water_quality": "Cleaned Water Quality Field Logs",
    "toxicity_analysis": "Audited Toxicity & Emerson Ammonia Records",
    "fish_health_growth": "Fish Health & Cohort Weight Observations",
    "feeding_analysis": "Pond Feeding Records",
    "enrolled_ponds": "Enrolled Ponds Farm Metadata",
    "dropouts": "Program Dropout Records",
}


def _render_missingness_summary(df: pd.DataFrame) -> None:
    """Render summary table of missing values across dataset columns."""
    total_rows = len(df)
    records = []
    for col in df.columns:
        n_missing = int(df[col].isna().sum())
        pct_missing = (n_missing / total_rows) * 100.0 if total_rows > 0 else 0.0
        
        # Numeric stats if applicable
        if pd.api.types.is_numeric_dtype(df[col]):
            non_na = df[col].dropna()
            min_v = f"{non_na.min():.2f}" if not non_na.empty else "N/A"
            med_v = f"{non_na.median():.2f}" if not non_na.empty else "N/A"
            max_v = f"{non_na.max():.2f}" if not non_na.empty else "N/A"
        else:
            min_v, med_v, max_v = "Categorical", "—", "—"

        records.append({
            "Column Name": col,
            "Total Entries": total_rows,
            "Missing Count (NaN)": n_missing,
            "Missingness (%)": f"{pct_missing:.1f}%",
            "Observed Min": min_v,
            "Observed Median": med_v,
            "Observed Max": max_v,
        })

    summary_df = pd.DataFrame(records)
    st.dataframe(summary_df, use_container_width=True)


def _render_trajectory_chart(df: pd.DataFrame, dataset_key: str, selected_pond: str) -> None:
    """Render interactive longitudinal trajectory chart for selected pond."""
    # Filter by pond if selected
    plot_df = df.copy()
    if "datetime" in plot_df.columns:
        plot_df["datetime"] = pd.to_datetime(plot_df["datetime"], errors="coerce")
        plot_df = plot_df.dropna(subset=["datetime"]).sort_values("datetime")

    if selected_pond != "All Ponds" and "pond_id" in plot_df.columns:
        plot_df = plot_df[plot_df["pond_id"] == selected_pond]

    if plot_df.empty:
        st.warning(f"No timestamped records available for {selected_pond}.")
        return

    fig = go.Figure()

    if dataset_key == "water_quality":
        if "DO (mg/L)" in plot_df.columns:
            fig.add_trace(go.Scatter(
                x=plot_df["datetime"],
                y=plot_df["DO (mg/L)"],
                mode="lines+markers",
                name="Morning DO (mg/L)",
                line=dict(color=PALETTE["teal_accent"], width=2),
                marker=dict(size=5),
            ))
        if "pH" in plot_df.columns:
            fig.add_trace(go.Scatter(
                x=plot_df["datetime"],
                y=plot_df["pH"],
                mode="lines+markers",
                name="pH",
                line=dict(color=PALETTE["navy_primary"], width=2, dash="dash"),
                marker=dict(size=5),
                yaxis="y2",
            ))
        if "Temp (in °C)" in plot_df.columns:
            fig.add_trace(go.Scatter(
                x=plot_df["datetime"],
                y=plot_df["Temp (in °C)"],
                mode="lines+markers",
                name="Temperature (°C)",
                line=dict(color="#d97706", width=1.5, dash="dot"),
                marker=dict(size=4),
            ))

        fig.update_layout(
            title=dict(
                text=f"Water Quality Parameter Trajectory ({selected_pond})",
                font=dict(size=14, color="#0c2340"),
            ),
            xaxis_title="Visit Inspection Date",
            yaxis_title="DO (mg/L) / Temp (°C)",
            yaxis2=dict(title="pH", overlaying="y", side="right", range=[4.0, 11.0], showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=50, b=40),
            hovermode="x unified",
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#f1f5f9"),
        )

    elif dataset_key == "toxicity_analysis":
        if "dissolved_oxygen_mg_l" in plot_df.columns:
            fig.add_trace(go.Scatter(
                x=plot_df["datetime"],
                y=plot_df["dissolved_oxygen_mg_l"],
                mode="lines+markers",
                name="Morning DO (mg/L)",
                line=dict(color=PALETTE["teal_primary"], width=2),
            ))
        if "primary_calculated_nh3_mg_l" in plot_df.columns:
            fig.add_trace(go.Scatter(
                x=plot_df["datetime"],
                y=plot_df["primary_calculated_nh3_mg_l"],
                mode="lines+markers",
                name="Emerson NH3 (mg/L)",
                line=dict(color="#dc2626", width=2),
                yaxis="y2",
            ))

        fig.update_layout(
            title=dict(
                text=f"Dissolved Oxygen & Emerson Ammonia Trajectory ({selected_pond})",
                font=dict(size=14, color="#0c2340"),
            ),
            xaxis_title="Visit Inspection Date",
            yaxis_title="DO (mg/L)",
            yaxis2=dict(title="NH3 (mg/L)", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=50, b=40),
            hovermode="x unified",
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#f1f5f9"),
        )

    elif dataset_key == "fish_health_growth":
        if "average_fish_weight_g" in plot_df.columns:
            fig.add_trace(go.Scatter(
                x=plot_df["datetime"],
                y=plot_df["average_fish_weight_g"],
                mode="lines+markers",
                name="Pond-cohort average weight (g/fish)",
                line=dict(color=PALETTE["teal_primary"], width=2.5),
                marker=dict(size=6),
            ))

        fig.update_layout(
            title=dict(
                text=f"Next-Visit Pond-Cohort Average Fish Weight Trajectory ({selected_pond})",
                font=dict(size=14, color="#0c2340"),
            ),
            xaxis_title="Sampling Date",
            yaxis_title="Average Weight (grams/fish)",
            margin=dict(l=40, r=40, t=50, b=40),
            hovermode="x unified",
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#f1f5f9"),
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Pond-cohort average fish weight (grams/fish); does not represent total biomass or harvest yield (kg/ha).")
        return

    elif dataset_key == "feeding_analysis":
        if "feed_amount_kg" in plot_df.columns:
            fig.add_trace(go.Bar(
                x=plot_df["datetime"],
                y=plot_df["feed_amount_kg"],
                name="Reported Feed Amount (kg/day)",
                marker_color=PALETTE["teal_accent"],
            ))

        fig.update_layout(
            title=dict(
                text=f"Historical Feed Input Trajectory ({selected_pond})",
                font=dict(size=14, color="#0c2340"),
            ),
            xaxis_title="Inspection Date",
            yaxis_title="Feed Amount (kg/day)",
            margin=dict(l=40, r=40, t=50, b=40),
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            yaxis=dict(gridcolor="#f1f5f9"),
        )

    else:
        st.info("Visual trajectory plotting is active for longitudinal parameter tables.")
        return

    st.plotly_chart(fig, use_container_width=True)


def render_page() -> None:
    """Render the Historical Field Observations Explorer page."""
    inject_custom_css()

    farm_type = get_active_farm_type()
    container_label = get_container_label(farm_type)
    container_id_label = get_container_id_label(farm_type)

    render_page_header(
        title="Prediction History & Field Reports",
        subtitle=f"Longitudinal multi-week field inspection records and audited session prediction reports ({farm_type}).",
        category_key="HISTORICAL",
    )

    render_uploaded_context_notice()

    with st.expander("Decision-Support & Sampling Context Notices", expanded=False):
        render_decision_support_banner()
        render_multi_week_observation_banner()
        st.info(f"**Operational Scope ({farm_type}):** {get_farm_type_disclaimer(farm_type)}")

    tab_history, tab_baseline = st.tabs([
        "📑 Session Prediction History & Audited Reports",
        f"📊 {container_label} Field Observations & Baselines",
    ])

    with tab_history:
        pred_history = st.session_state.get("prediction_history", [])
        total_runs = len(pred_history)
        sim_runs = sum(1 for p in pred_history if "YES" in str(p.get("is_simulated", "")))
        field_runs = total_runs - sim_runs

        h1, h2, h3, h4 = st.columns(4)
        with h1:
            render_metric_card("Total Analyses Logged", f"{total_runs}", "Session records", icon="📑", accent="teal")
        with h2:
            render_metric_card("Field / Uploaded Runs", f"{field_runs}", "Operational predictions", icon="🐟", accent="aqua")
        with h3:
            render_metric_card("Simulation Runs", f"{sim_runs}", "Quarantined benchmarks", icon="🧪", accent="warning" if sim_runs > 0 else "success")
        with h4:
            render_metric_card("Active Environment", farm_type, "Selected in sidebar", icon="🏢", accent="teal")

        if pred_history:
            hist_df = pd.DataFrame(pred_history)

            f_col1, f_col2 = st.columns(2)
            with f_col1:
                farm_filter = st.selectbox(
                    "Filter by Farm Type:",
                    options=["All Environments"] + sorted(hist_df["farm_type"].dropna().unique().tolist()),
                    index=0,
                    key="hist_filter_farm",
                )
            with f_col2:
                sim_filter = st.selectbox(
                    "Filter by Simulation Status:",
                    options=["All Records", "Field / Real Predictions Only", "Simulated Scenarios Only"],
                    index=0,
                    key="hist_filter_sim",
                )

            filtered_hist = hist_df.copy()
            if farm_filter != "All Environments":
                filtered_hist = filtered_hist[filtered_hist["farm_type"] == farm_filter]
            if sim_filter == "Field / Real Predictions Only":
                filtered_hist = filtered_hist[~filtered_hist["is_simulated"].astype(str).str.contains("YES")]
            elif sim_filter == "Simulated Scenarios Only":
                filtered_hist = filtered_hist[filtered_hist["is_simulated"].astype(str).str.contains("YES")]

            st.dataframe(filtered_hist, use_container_width=True, hide_index=True)

            csv_data = filtered_hist.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Prediction History (CSV)",
                data=csv_data,
                file_name="precision_aquadss_prediction_history.csv",
                mime="text/csv",
                key="download_pred_history_btn",
                type="primary",
            )
        else:
            st.info(
                "No prediction runs recorded yet in this session. Use **Water Quality & Toxicity Risk**, "
                "**DO & Hypoxia Screening**, **Fish Growth & Feeding Advisor**, or **Upload New Dataset** to execute analyses."
            )

    with tab_baseline:
        # --- Inputs: Dataset selector + pond filter ---
        col_sel, col_pond = st.columns([2, 1])
        with col_sel:
            selected_key = st.selectbox(
                f"Select Field Dataset to Inspect ({container_label} Basis):",
                options=list(AVAILABLE_DATASETS.keys()),
                format_func=lambda k: f"{AVAILABLE_DATASETS[k]} ({k})",
                index=0,
            )

        # Load dataset safely via core data manager
        try:
            df = load_dataset(selected_key, use_cache=True)
        except Exception as exc:
            st.error(f"Failed to load dataset '{selected_key}': {exc}")
            return

        with col_pond:
            if "pond_id" in df.columns:
                all_ponds = sorted(list(df["pond_id"].dropna().unique()))
                pond_choice = st.selectbox(f"{container_id_label}:", options=[f"All {container_label}s"] + all_ponds, index=0)
            else:
                pond_choice = f"All {container_label}s"

        # --- Results: KPI metric cards ---
        meta = DATASET_METADATA.get(selected_key, {})
        total_records = len(df)
        unique_ponds = df["pond_id"].nunique() if "pond_id" in df.columns else 0
        total_cells = df.size
        total_na = int(df.isna().sum().sum())
        na_pct = (total_na / total_cells * 100.0) if total_cells > 0 else 0.0

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render_metric_card(
                title="Total Inspections",
                value=f"{total_records:,}",
                subtitle=f"{meta.get('title', selected_key)}",
                benchmark_ref="Cleaned Field Data v2",
                icon="📋",
                accent="teal",
            )
        with c2:
            render_metric_card(
                title=f"Monitored {container_label}s",
                value=f"{unique_ponds} {container_label}s" if unique_ponds > 0 else "N/A",
                subtitle=f"Commercial {container_label.lower()} cohort",
                benchmark_ref="AP Farm Network",
                icon="🐟",
                accent="aqua",
            )
        with c3:
            render_metric_card(
                title="Overall Missingness",
                value=f"{na_pct:.1f}%",
                subtitle="Preserved natural NaNs",
                benchmark_ref="Zero Silent Zero-Filling",
                icon="🔍",
                accent="warning" if na_pct > 30 else "success",
            )
        with c4:
            render_metric_card(
                title="Data Nature",
                value="Field Logs",
                subtitle="Irregular multi-week visits",
                benchmark_ref="3 to 45 Day Revisits",
                icon="🗓️",
                accent="aqua",
            )

        # --- Trajectory Chart ---
        selected_pond_param = pond_choice if pond_choice != f"All {container_label}s" else "All Ponds"
        render_section_bar(f"Longitudinal Trajectory: {AVAILABLE_DATASETS[selected_key]}")
        _render_trajectory_chart(df, selected_key, selected_pond_param)

        # --- Missingness & Records ---
        with st.expander("📊 Missingness & Parameter Distribution", expanded=False):
            st.caption("Detailed column-wise inventory showing true sampling missingness (NaNs preserved).")
            _render_missingness_summary(df)

        with st.expander(f"📋 Field Inspection Records Preview ({container_label} Scope)", expanded=False):
            st.caption(f"Showing up to 100 records for inspection review (Total: {len(df):,} rows).")
            display_df = df if pond_choice == f"All {container_label}s" or "pond_id" not in df.columns else df[df["pond_id"] == pond_choice]
            st.dataframe(display_df.head(100), use_container_width=True)

    # --- Technical Details: Sampling context & immutability ---
    with st.expander("ℹ️ Field Sampling Context & Immutability Rules", expanded=False):
        import textwrap
        st.markdown(
            textwrap.dedent("""
            <div class="saas-card" style="font-size: 0.86rem; color: #1e293b; line-height: 1.55;">
                <strong style="color: #0c2340;">Field Sampling Context & Immutability Rules:</strong><br>
                • <strong>Sampling Cadence:</strong> Discrete routine commercial farm visits (<strong>revisit interval: 3 to 45 days</strong>; median ~21 days).<br>
                • <strong>Measurement Window:</strong> Morning field records (<strong>06:00–08:30 AM</strong>). These are <em>NOT verified pre-dawn daily minimum DO</em>.<br>
                • <strong>Missingness Policy:</strong> Natural missing values (NaNs) are strictly preserved as recorded during physical sampling. <em>No synthetic zero-filling or smoothing is applied</em>.<br>
                • <strong>Simulation Quarantine:</strong> Displays historical field observations from Andhra Pradesh commercial ponds only; <em>strictly segregated from synthetic simulation models</em>.
            </div>
            """).strip(),
            unsafe_allow_html=True,
        )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
