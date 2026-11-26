"""Page 1: Dashboard – Precision AquaDSS Main Landing Page.

Operational Category: HISTORICAL (Farm Field Status, Analytics & Model Health).
Provides:
1. Executive Farm Overview KPI Bar:
   - Total farms
   - Total ponds / tanks
   - Current farm type (Indoor vs Outdoor)
   - Current toxicity status
   - Average pH, Average Temperature, Average Ammonia, Average Dissolved Oxygen
2. Recent Alerts: Real-time risk alerts for containers with active hypoxia (< 3.0 mg/L)
   or elevated un-ionized ammonia (≥ 0.05 mg/L).
3. Historical Water-Quality Trend Graphs: Interactive Plotly trends for DO, pH, Temperature, and Ammonia.
4. Fish Growth Trend: Longitudinal cohort average weight trajectory (grams/fish).
5. Inspection Priority Queue: Historical inspection priority ranked by urgency.
6. Scientific Governance Disclaimers: Zero real-time claims, zero automated actuation (is_automatic_control = False),
   and discrete multi-week sampling window (3 to 45 days, 06:00–08:30 AM morning observations).
"""

from typing import Dict, Any, List
import textwrap
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

from app.dashboard.utils.styles import inject_custom_css, PALETTE
from app.dashboard.utils.helpers import (
    format_float,
    format_percentage,
    get_registry_health_summary,
    get_active_farm_type,
    get_container_label,
    get_container_id_label,
    get_farm_type_disclaimer,
    FREE_PLATFORM_NOTICE,
)
from app.dashboard.components.header import render_page_header, render_section_bar
from app.dashboard.components.banners import (
    render_decision_support_banner,
    render_multi_week_observation_banner,
    render_uploaded_context_notice,
)
from app.dashboard.components.registry_status import render_registry_status_bar
from app.dashboard.components.metric_card import render_metric_card
from app.core.data_manager import load_dataset
from app.models.registry import get_model_registry


def classify_pond_priority(row: pd.Series) -> str:
    """Classifies pond inspection urgency based on historical morning observations."""
    do = row.get("dissolved_oxygen_mg_l")
    nh3 = row.get("primary_calculated_nh3_mg_l")

    if pd.notna(do) and do < 3.0:
        return "Priority 1: Hypoxia Stress (< 3.0 mg/L)"
    if pd.notna(nh3) and nh3 >= 0.05:
        return "Priority 1: Ammonia Toxicity (≥ 0.05 mg/L)"
    if pd.notna(do) and do < 4.0:
        return "Priority 2: Suboptimal DO (3.0–4.0 mg/L)"
    return "Priority 3: Routine Inspection"


def render_page() -> None:
    """Render the Dashboard main landing page."""
    inject_custom_css()

    farm_type = get_active_farm_type()
    container_label = get_container_label(farm_type)
    container_id_label = get_container_id_label(farm_type)

    render_page_header(
        title="Dashboard",
        subtitle=f"Multi-{container_label.lower()} status overview, water-quality trends, and decision-support summary ({farm_type}).",
        category_key="HISTORICAL",
    )

    # ── Free Platform & Operational Scope Notice ────────────────────────
    farm_disclaimer = get_farm_type_disclaimer(farm_type)
    st.markdown(
        f"""
        <div style="background-color: #FFFFFF; border: 1px solid #DCE9E6; border-left: 4px solid #087F72; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.9rem; box-shadow: 0 1px 4px rgba(16,44,58,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.25rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-weight: 800; font-size: 0.85rem; color: #173747;">🏢 Farm Environment: {farm_type}</span>
                    <span style="background-color: #E3F6EE; color: #269B72; border: 1px solid #A6DEC8; font-size: 0.70rem; font-weight: 700; padding: 0.12rem 0.5rem; border-radius: 9999px;">
                        100% FREE ACCESS
                    </span>
                </div>
                <span style="font-size: 0.75rem; color: #087F72; font-weight: 600;">
                    All features freely accessible • No subscriptions or upgrades
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #526873; line-height: 1.45;">
                <strong>Platform Notice:</strong> {FREE_PLATFORM_NOTICE}<br>
                <span style="color: #64748b;"><strong>Scope Note:</strong> {farm_disclaimer}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_uploaded_context_notice(["do_mg_l", "ph", "temp_c", "emerson_nh3_mg_l"])

    # ── Load Historical Datasets ───────────────────────────────────────
    try:
        df_enrolled = load_dataset("enrolled_ponds")
        df_tox = load_dataset("toxicity_analysis")
        df_growth = load_dataset("fish_health_growth")

        # Custom farms registered in session
        registered_farms = st.session_state.get("registered_farms", [])
        registered_ponds = st.session_state.get("registered_ponds", [])

        total_farms = max(len(registered_farms), df_enrolled["region"].nunique() if "region" in df_enrolled else 8)
        enrolled_count = len(df_enrolled) + len(registered_ponds)
        total_inspections = len(df_tox)

        avg_do = df_tox["dissolved_oxygen_mg_l"].mean()
        avg_ph = df_tox["ph"].mean()
        avg_temp = df_tox["temp_c"].mean()
        avg_nh3 = df_tox["primary_calculated_nh3_mg_l"].mean()
        median_weight = df_growth["average_fish_weight_g"].median()

        # Determine overall toxicity status across latest records
        df_latest = df_tox.sort_values("datetime").groupby("pond_id").last().reset_index()
        elevated_count = (df_latest["primary_calculated_nh3_mg_l"] >= 0.05).sum()
        hypoxia_count = (df_latest["dissolved_oxygen_mg_l"] < 3.0).sum()

        if elevated_count > 5 or hypoxia_count > 10:
            overall_status = "Action Required"
            status_accent = "warning"
        elif elevated_count > 0 or hypoxia_count > 0:
            overall_status = "Attention Needed"
            status_accent = "aqua"
        else:
            overall_status = "Optimal"
            status_accent = "success"

    except Exception as exc:
        st.error(f"Error loading dashboard datasets: {exc}")
        total_farms = 8
        enrolled_count = 324
        total_inspections = 12399
        avg_do = 3.54
        avg_ph = 7.81
        avg_temp = 28.7
        avg_nh3 = 0.016
        median_weight = 150.0
        overall_status = "Attention Needed"
        status_accent = "aqua"
        df_latest = pd.DataFrame()

    # ── Row 1 KPI Metrics ─────────────────────────────────────────────
    st.markdown(f"#### Overview Summary ({farm_type})")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

    with kpi_col1:
        render_metric_card(
            title="Total Farms",
            value=f"{total_farms} Registered",
            subtitle=f"{farm_type} operations",
            benchmark_ref="Commercial clusters",
            icon="🏢",
            accent="teal",
        )
    with kpi_col2:
        render_metric_card(
            title=f"Total {container_label}s",
            value=f"{enrolled_count} {container_label}s",
            subtitle=f"Active monitored {container_label.lower()} units",
            benchmark_ref="enrolled_ponds_v2.csv",
            icon="🐟",
            accent="aqua",
        )
    with kpi_col3:
        render_metric_card(
            title="Farm Environment",
            value=farm_type.replace(" Aquaculture", ""),
            subtitle="Current active environment",
            benchmark_ref="Selected in navigation",
            icon="🌐",
            accent="teal",
        )
    with kpi_col4:
        render_metric_card(
            title="Toxicity Status",
            value=overall_status,
            subtitle=f"{elevated_count} elevated NH₃, {hypoxia_count} low DO",
            benchmark_ref="Audited Field Logs",
            icon="🛡️",
            accent=status_accent,
        )

    # ── Row 2 Water Quality Parameters ────────────────────────────────
    w_col1, w_col2, w_col3, w_col4 = st.columns(4)
    with w_col1:
        render_metric_card(
            title="Average pH",
            value=f"{avg_ph:.2f}",
            subtitle="Optimal range: 6.5–8.5",
            benchmark_ref="Historical mean across ponds",
            icon="🧪",
            accent="teal",
        )
    with w_col2:
        render_metric_card(
            title="Average Temperature",
            value=f"{avg_temp:.1f} °C",
            subtitle="Optimal range: 24.0–32.0 °C",
            benchmark_ref="Historical mean across ponds",
            icon="🌡️",
            accent="teal",
        )
    with w_col3:
        render_metric_card(
            title="Average Ammonia (NH₃)",
            value=f"{avg_nh3:.4f} mg/L",
            subtitle="Un-ionized Emerson NH₃",
            benchmark_ref="Threshold: < 0.05 mg/L",
            icon="⚠️" if avg_nh3 >= 0.05 else "💧",
            accent="warning" if avg_nh3 >= 0.05 else "aqua",
        )
    with w_col4:
        render_metric_card(
            title="Average Dissolved Oxygen",
            value=f"{avg_do:.2f} mg/L",
            subtitle="Morning inspection visits",
            benchmark_ref="Historical mean (3.50 mg/L)",
            icon="🫁",
            accent="success" if avg_do >= 4.0 else "warning",
        )

    # ── Recent Alerts Section ─────────────────────────────────────────
    render_section_bar("Recent Alerts & Priority Water-Safety Warnings")

    if not df_latest.empty:
        df_latest["priority_tier"] = df_latest.apply(classify_pond_priority, axis=1)
        alert_rows = df_latest[df_latest["priority_tier"].str.contains("Priority 1")].copy()

        if not alert_rows.empty:
            st.warning(
                f"⚠️ **{len(alert_rows)} {container_label.lower()} units flagged with active water-quality stress:** "
                "Immediate field inspection and management review recommended."
            )
            alert_cols = st.columns(min(3, len(alert_rows)))
            for idx, (_, row) in enumerate(alert_rows.head(3).iterrows()):
                col = alert_cols[idx % 3]
                p_id = row.get("pond_id", "N/A")
                p_do = row.get("dissolved_oxygen_mg_l", float("nan"))
                p_nh3 = row.get("primary_calculated_nh3_mg_l", float("nan"))
                p_date = str(row.get("datetime", ""))[:10]

                reasons = []
                if pd.notna(p_do) and p_do < 3.0:
                    reasons.append(f"Low DO: {p_do:.2f} mg/L (< 3.0 mg/L Hypoxia)")
                if pd.notna(p_nh3) and p_nh3 >= 0.05:
                    reasons.append(f"Elevated NH₃: {p_nh3:.3f} mg/L (≥ 0.05 mg/L Toxicity)")

                with col:
                    st.markdown(
                        f"""
                        <div style="background: #FFF5F5; border: 1px solid #FEB2B2; border-left: 4px solid #E53E3E; border-radius: 8px; padding: 0.75rem 0.9rem; margin-bottom: 0.6rem;">
                            <div style="font-weight: 700; color: #9B2C2C; font-size: 0.85rem;">🚨 {container_id_label}: {p_id}</div>
                            <div style="font-size: 0.76rem; color: #742A2A; margin: 0.3rem 0;">
                                {' • '.join(reasons)}
                            </div>
                            <div style="font-size: 0.70rem; color: #A0AEC0;">
                                Observed: {p_date} • Action: Aerate & Cease/Reduce Feed
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.success(f"✅ All {container_label.lower()} units currently within standard operational safety thresholds.")
    else:
        st.info("No active alerts logged.")

    # ── Historical Water-Quality Trend Graphs ──────────────────────────
    render_section_bar("Historical Water-Quality Trends")
    st.caption("Longitudinal parameter trajectories across historical morning inspection visits (2021–2026).")

    try:
        df_tox["datetime_dt"] = pd.to_datetime(df_tox["datetime"], errors="coerce")
        df_clean_time = df_tox.dropna(subset=["datetime_dt"]).sort_values("datetime_dt")

        # Aggregate by month for smooth visualization
        monthly_wq = (
            df_clean_time.groupby(pd.Grouper(key="datetime_dt", freq="ME"))
            .agg(
                mean_do=("dissolved_oxygen_mg_l", "mean"),
                mean_ph=("ph", "mean"),
                mean_temp=("temp_c", "mean"),
                mean_nh3=("primary_calculated_nh3_mg_l", "mean"),
            )
            .reset_index()
        )

        fig_wq = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Dissolved Oxygen (mg/L)",
                "Water pH",
                "Water Temperature (°C)",
                "Toxic Un-ionized Ammonia NH₃ (mg/L)",
            ),
            vertical_spacing=0.15,
            horizontal_spacing=0.08,
        )

        # DO
        fig_wq.add_trace(
            go.Scatter(
                x=monthly_wq["datetime_dt"],
                y=monthly_wq["mean_do"],
                mode="lines+markers",
                name="Morning DO",
                line=dict(color="#087F72", width=2),
                marker=dict(size=4),
            ),
            row=1,
            col=1,
        )
        fig_wq.add_hline(y=3.0, line_dash="dash", line_color="#E53E3E", annotation_text="Hypoxia (3.0 mg/L)", row=1, col=1)

        # pH
        fig_wq.add_trace(
            go.Scatter(
                x=monthly_wq["datetime_dt"],
                y=monthly_wq["mean_ph"],
                mode="lines+markers",
                name="pH",
                line=dict(color="#43BFC0", width=2),
                marker=dict(size=4),
            ),
            row=1,
            col=2,
        )

        # Temperature
        fig_wq.add_trace(
            go.Scatter(
                x=monthly_wq["datetime_dt"],
                y=monthly_wq["mean_temp"],
                mode="lines+markers",
                name="Temperature (°C)",
                line=dict(color="#E7A23B", width=2),
                marker=dict(size=4),
            ),
            row=2,
            col=1,
        )

        # Ammonia
        fig_wq.add_trace(
            go.Scatter(
                x=monthly_wq["datetime_dt"],
                y=monthly_wq["mean_nh3"],
                mode="lines+markers",
                name="Toxic NH₃ (mg/L)",
                line=dict(color="#D9534F", width=2),
                marker=dict(size=4),
            ),
            row=2,
            col=2,
        )
        fig_wq.add_hline(y=0.05, line_dash="dash", line_color="#D9534F", annotation_text="Elevated (0.05 mg/L)", row=2, col=2)

        fig_wq.update_layout(
            height=460,
            showlegend=False,
            margin=dict(l=40, r=40, t=40, b=40),
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        fig_wq.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
        fig_wq.update_yaxes(showgrid=True, gridcolor="#f1f5f9")

        st.plotly_chart(fig_wq, use_container_width=True)

    except Exception as exc:
        st.error(f"Error rendering water quality trend charts: {exc}")

    # ── Fish Growth Trend ─────────────────────────────────────────────
    render_section_bar("Fish Growth Trajectory")
    st.caption("Longitudinal cohort average fish body weight (grams/fish) over inspection rounds. Note: Somatic weight, NOT harvest yield.")

    try:
        df_growth["datetime_dt"] = pd.to_datetime(df_growth["datetime"], errors="coerce")
        df_g_clean = df_growth.dropna(subset=["datetime_dt", "average_fish_weight_g"]).sort_values("datetime_dt")

        monthly_growth = (
            df_g_clean.groupby(pd.Grouper(key="datetime_dt", freq="ME"))
            .agg(
                mean_weight=("average_fish_weight_g", "mean"),
                median_weight=("average_fish_weight_g", "median"),
                obs_count=("average_fish_weight_g", "count"),
            )
            .reset_index()
        )

        fig_g = go.Figure()
        fig_g.add_trace(
            go.Scatter(
                x=monthly_growth["datetime_dt"],
                y=monthly_growth["mean_weight"],
                mode="lines+markers",
                name="Mean Cohort Body Weight (g/fish)",
                line=dict(color="#087F72", width=2.5),
                marker=dict(size=5, color="#087F72"),
            )
        )
        fig_g.add_trace(
            go.Scatter(
                x=monthly_growth["datetime_dt"],
                y=monthly_growth["median_weight"],
                mode="lines",
                name="Median Cohort Body Weight (g/fish)",
                line=dict(color="#43BFC0", width=1.8, dash="dot"),
            )
        )

        fig_g.update_layout(
            height=300,
            margin=dict(l=40, r=40, t=30, b=40),
            template="plotly_white",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis_title="Inspection Timeline",
            yaxis_title="Cohort Weight (grams/fish)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig_g.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
        fig_g.update_yaxes(showgrid=True, gridcolor="#f1f5f9")

        st.plotly_chart(fig_g, use_container_width=True)

    except Exception as exc:
        st.error(f"Error rendering fish growth trajectory: {exc}")

    # ── Inspection Priority Queue ─────────────────────────────────────
    render_section_bar("Inspection Priority Queue")
    st.caption(
        f"Commercial {container_label.lower()} units ranked by latest historical morning DO and estimated ammonia toxicity tier. "
        "Allows farm supervisors to plan physical inspection rounds. All records show actual historical observation dates."
    )

    try:
        df_queue = df_latest.sort_values(
            by=["priority_tier", "dissolved_oxygen_mg_l"],
            ascending=[True, True],
        )

        f_col1, f_col2 = st.columns(2)
        with f_col1:
            tier_filter = st.selectbox(
                f"Filter by Inspection Priority ({container_label}s):",
                options=[f"All {container_label}s", "Priority 1 Only (Hypoxia or Ammonia)", "Priority 2 & 3 (Suboptimal & Routine)"],
                index=0,
            )
        with f_col2:
            search_pond = st.text_input(f"Search {container_id_label}:", value="", placeholder=f"e.g. POND-012")

        filtered_queue = df_queue.copy()
        if "Priority 1 Only" in tier_filter:
            filtered_queue = filtered_queue[filtered_queue["priority_tier"].str.contains("Priority 1")]
        elif "Priority 2 & 3" in tier_filter:
            filtered_queue = filtered_queue[~filtered_queue["priority_tier"].str.contains("Priority 1")]

        if search_pond.strip():
            filtered_queue = filtered_queue[
                filtered_queue["pond_id"].str.contains(search_pond.strip(), case=False, na=False)
            ]

        filtered_queue["obs_date"] = pd.to_datetime(filtered_queue["datetime"]).dt.strftime("%Y-%m-%d")
        filtered_queue["obs_time"] = pd.to_datetime(filtered_queue["datetime"]).dt.strftime("%H:%M AM")

        display_cols = [
            "pond_id",
            "obs_date",
            "obs_time",
            "region",
            "dissolved_oxygen_mg_l",
            "ph",
            "temp_c",
            "primary_calculated_nh3_mg_l",
            "priority_tier",
        ]
        rename_map = {
            "pond_id": container_id_label,
            "obs_date": "Last Observation Date",
            "obs_time": "Inspection Time",
            "region": "Region",
            "dissolved_oxygen_mg_l": "Morning DO (mg/L)",
            "ph": "Water pH",
            "temp_c": "Temp (°C)",
            "primary_calculated_nh3_mg_l": "Toxic NH₃ (mg/L)",
            "priority_tier": "Inspection Priority Tier",
        }

        st.dataframe(
            filtered_queue[display_cols].rename(columns=rename_map).head(50),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            f"Showing {min(50, len(filtered_queue))} of {len(filtered_queue)} monitored commercial {container_label.lower()}s. "
            "Data reflects audited historical field logs (2021–2026). Readings are strictly NOT live telemetry."
        )

    except Exception as exc:
        st.error(f"Error rendering inspection priority queue: {exc}")

    # ── Expanders: Technical Details & Model Governance ───────────────
    with st.expander("Central Model Registry Health & Governance", expanded=False):
        st.caption("Cryptographically verified, read-only analytical baselines and experimental screening pipelines.")
        registry = get_model_registry()
        render_registry_status_bar(registry)

    with st.expander("System Governance & Operational Boundaries", expanded=False):
        st.caption(
            "Historical observations aggregated from commercial pond inspection logs. "
            "Strictly reflects discrete morning visits (06:00–08:30 AM); NOT live or continuous streaming telemetry."
        )
        st.markdown(
            textwrap.dedent("""
            <div class="saas-card" style="line-height: 1.55; font-size: 0.86rem; color: #1e293b;">
                <div style="font-weight: 800; font-size: 0.88rem; color: #0c2340; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 0.75rem;">
                    Mandatory System Governance Notice
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.85rem;">
                        <strong style="color: #0c2340;">No Real-Time Monitoring:</strong><br>
                        The system does NOT connect to active live IoT sensors or stream real-time measurements. All displayed parameters represent discrete historical inspection visits.
                    </div>
                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.85rem;">
                        <strong style="color: #0c2340;">Sampling Protocol:</strong><br>
                        Observations reflect standard morning visits (<strong>06:00–08:30 AM</strong>) scheduled <strong>3 to 45 days</strong> apart (median ~21 days). They are NOT verified pre-dawn daily minimum DO readings.
                    </div>
                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.85rem;">
                        <strong style="color: #0c2340;">Negative Scope:</strong><br>
                        Somatic average body weight per fish is tracked; commercial harvest yield in kg/ha or total pond biomass is strictly unsupported (<strong>NOT harvest yield</strong>, <strong>0% total yield labels</strong> in dataset).
                    </div>
                    <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.85rem;">
                        <strong style="color: #0c2340;">Zero Automated Actuation:</strong><br>
                        All model outputs and rule-based feeding adjustments are provisional decision-support aids requiring qualified human verification. No automated control commands (aerators, feeders, pumps) are executed (<code>is_automatic_control = False</code>).
                    </div>
                </div>
            </div>
            """).strip(),
            unsafe_allow_html=True,
        )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
