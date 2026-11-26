"""Page 8: Organization Overview (Default Landing Page).

Commercial SaaS executive landing page for Precision AquaDSS:
- Clean Organization Overview header and compact KPI summary
- Clickable Quick Action cards with icons
- Water-quality trend charts, toxicity risk overview, pond comparison, and fish growth trends
- Recent observations table and recent session prediction activity
- Lengthy scientific explanations moved into collapsed expanders
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from app.core.data_manager import load_dataset
from app.dashboard.components.header import render_page_header, render_section_bar
from app.dashboard.components.metric_card import render_metric_card
from app.dashboard.utils.helpers import (
    format_float,
    get_active_farm_type,
    get_container_label,
    get_container_id_label,
    get_farm_type_disclaimer,
    FREE_PLATFORM_NOTICE,
)
from app.dashboard.utils.styles import PALETTE, inject_custom_css


def _classify_nh3_tier(nh3_val: float) -> str:
    """Classify calculated Emerson NH3 into operational screening tiers."""
    if pd.isna(nh3_val):
        return "Missing"
    if nh3_val >= 0.10:
        return "Critical (≥0.10)"
    if nh3_val >= 0.05:
        return "Elevated (0.05–0.10)"
    if nh3_val >= 0.02:
        return "Caution (0.02–0.05)"
    return "Optimal (<0.02)"


def render_page() -> None:
    """Render the Organization Overview landing page."""
    inject_custom_css()

    farm_type = get_active_farm_type()
    container_label = get_container_label(farm_type)
    container_id_label = get_container_id_label(farm_type)

    render_page_header(
        title="Organization Overview",
        subtitle=f"{farm_type} water-quality analytics, toxicity risk screening, and decision-support workspace.",
        category_key="HISTORICAL",
    )

    # 100% Free Platform & Farm Type Mode Banner
    farm_disclaimer = get_farm_type_disclaimer(farm_type)
    st.markdown(
        f"""
        <div style="background-color: #FFFFFF; border: 1px solid #DCE9E6; border-left: 4px solid #087F72; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.9rem; box-shadow: 0 1px 4px rgba(16,44,58,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.35rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-weight: 800; font-size: 0.85rem; color: #173747;">🏢 Mode: {farm_type}</span>
                    <span style="background-color: #E3F6EE; color: #269B72; border: 1px solid #A6DEC8; font-size: 0.70rem; font-weight: 700; padding: 0.12rem 0.5rem; border-radius: 9999px;">
                        100% FREE ACCESS
                    </span>
                </div>
                <span style="font-size: 0.76rem; color: #087F72; font-weight: 600;">
                    Zero subscription fees • All features unlocked
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #526873; line-height: 1.45;">
                <strong>Platform Notice:</strong> {FREE_PLATFORM_NOTICE}<br>
                <span style="color: #64748b;"><strong>Scientific Context:</strong> {farm_disclaimer}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load Historical Datasets
    try:
        df_tox = load_dataset("toxicity_analysis")
        df_enrolled = load_dataset("enrolled_ponds")
        df_growth = load_dataset("fish_health_growth")
    except Exception as exc:
        st.error(f"Failed to load historical datasets: {exc}")
        return

    df_tox["datetime_dt"] = pd.to_datetime(df_tox["datetime"], errors="coerce")

    # Compact Filters Bar
    regions = sorted(df_tox["region"].dropna().astype(str).unique().tolist())
    sel_col1, sel_col2, sel_col3 = st.columns([1, 1, 1])
    with sel_col1:
        selected_region = st.selectbox(
            "Region Scope",
            options=["All Regions"] + regions,
            index=0,
            key="farm_overview_region",
        )

    df_scoped = df_tox if selected_region == "All Regions" else df_tox[df_tox["region"].astype(str) == selected_region]
    ponds_in_scope = sorted(df_scoped["pond_id"].dropna().astype(str).unique().tolist())

    with sel_col2:
        selected_pond = st.selectbox(
            f"{container_id_label}",
            options=[f"All {container_label}s in Scope"] + ponds_in_scope,
            index=0,
            key="farm_overview_pond",
        )

    valid_dates = df_scoped["datetime_dt"].dropna()
    with sel_col3:
        if not valid_dates.empty:
            min_d = valid_dates.min().date()
            max_d = valid_dates.max().date()
            date_range = st.date_input(
                "Observation Date Range",
                value=(min_d, max_d),
                min_value=min_d,
                max_value=max_d,
                key="farm_overview_date_range",
            )
        else:
            date_range = None

    all_in_scope_label = f"All {container_label}s in Scope"
    if selected_pond != all_in_scope_label:
        df_view = df_scoped[df_scoped["pond_id"].astype(str) == selected_pond]
        df_growth_view = df_growth[df_growth["pond_id"].astype(str) == selected_pond]
    else:
        df_view = df_scoped
        if selected_region != "All Regions":
            pond_set = set(ponds_in_scope)
            df_growth_view = df_growth[df_growth["pond_id"].astype(str).isin(pond_set)]
        else:
            df_growth_view = df_growth

    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_d, end_d = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]) + pd.Timedelta(days=1)
        df_view = df_view[(df_view["datetime_dt"] >= start_d) & (df_view["datetime_dt"] < end_d)]
        if "datetime" in df_growth_view.columns:
            g_dt = pd.to_datetime(df_growth_view["datetime"], errors="coerce")
            df_growth_view = df_growth_view[(g_dt >= start_d) & (g_dt < end_d)]

    # Active Session Upload Notice (compact)
    uploaded_state = st.session_state.get("uploaded_analysis_state")
    if uploaded_state and uploaded_state.get("is_valid"):
        st.info(
            f"Active session CSV: **{uploaded_state.get('filename')}** "
            f"({uploaded_state.get('total_rows', 0):,} rows, {uploaded_state.get('pond_count', 0)} {container_label.lower()}(s)) — "
            "kept separate from historical records."
        )

    # 4 Executive KPI Cards
    latest_dt = df_view["datetime_dt"].max()
    latest_date_str = latest_dt.strftime("%Y-%m-%d") if pd.notna(latest_dt) else "N/A"
    total_ponds_represented = df_view["pond_id"].nunique()
    total_enrolled = (
        df_enrolled[df_enrolled["region"].astype(str) == selected_region]["pond_id"].nunique()
        if selected_region != "All Regions"
        else df_enrolled["pond_id"].nunique()
    )
    median_do = df_view["dissolved_oxygen_mg_l"].median()
    median_ph = df_view["ph"].median()
    median_temp = df_view["temp_c"].median()
    median_nh3 = df_view["primary_calculated_nh3_mg_l"].median()

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_metric_card(
            title=f"{container_label}s Monitored",
            value=f"{total_ponds_represented}",
            subtitle=f"{total_enrolled} enrolled | {df_view['region'].nunique()} region(s)",
            benchmark_ref=f"Verified {container_label} IDs",
            icon="🐟",
            accent="teal",
        )
    with k2:
        render_metric_card(
            title="Latest Observation",
            value=latest_date_str,
            subtitle=f"{len(df_view):,} routine visit records",
            benchmark_ref="06:00–08:30 AM Logs",
            icon="📅",
            accent="aqua",
        )
    with k3:
        render_metric_card(
            title="Median Morning DO",
            value=format_float(median_do, 2, "mg/L"),
            subtitle=f"pH {format_float(median_ph, 2)} | Temp {format_float(median_temp, 1, '°C')}",
            benchmark_ref="Historical Mean: 3.50 mg/L",
            icon="💧",
            accent="success",
        )
    with k4:
        render_metric_card(
            title="Median NH3 & Weight",
            value=format_float(median_nh3, 4, "mg/L"),
            subtitle=(
                f"Cohort Weight: {format_float(df_growth_view['average_fish_weight_g'].median(), 1, 'g/fish')}"
                if not df_growth_view.empty
                else "No weight records in scope"
            ),
            benchmark_ref="Emerson Chemistry",
            icon="🧪",
            accent="aqua",
        )

    # Clickable Quick Action Cards
    render_section_bar("Quick Actions")
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        st.page_link(
            "app/dashboard/pages/09_Import_Dataset.py",
            label="Upload New Dataset",
            icon=":material/upload_file:",
            use_container_width=True,
        )
    with qa2:
        st.page_link(
            "app/dashboard/pages/02_Water_Quality_Toxicity.py",
            label="Toxicity Risk Screening",
            icon=":material/science:",
            use_container_width=True,
        )
    with qa3:
        st.page_link(
            "app/dashboard/pages/04_Growth_Feeding_Advisor.py",
            label="Feeding & Growth Advisor",
            icon=":material/scale:",
            use_container_width=True,
        )
    with qa4:
        st.page_link(
            "app/dashboard/pages/01_Overview.py",
            label="Pond Priority Queue",
            icon=":material/dashboard:",
            use_container_width=True,
        )

    # Primary Visual Analytics (Tabbed to keep overview compact without excessive scrolling)
    tab_wq, tab_risk, tab_obs = st.tabs([
        "Water Quality & Growth Trends",
        "Toxicity Risk & Pond Comparison",
        "Recent Observations & Activity",
    ])

    chart_df = df_view.dropna(subset=["datetime_dt"]).sort_values("datetime_dt")

    with tab_wq:
        if not chart_df.empty:
            if selected_pond == "All Ponds in Scope":
                trend = (
                    chart_df.set_index("datetime_dt")[["dissolved_oxygen_mg_l", "ph", "temp_c", "primary_calculated_nh3_mg_l"]]
                    .resample("ME")
                    .median()
                    .reset_index()
                )
                title_suffix = f"Monthly Median ({selected_region})"
            else:
                trend = chart_df[["datetime_dt", "dissolved_oxygen_mg_l", "ph", "temp_c", "primary_calculated_nh3_mg_l"]].copy()
                title_suffix = f"Pond {selected_pond}"

            c_left, c_right = st.columns(2)
            with c_left:
                fig_do = px.line(
                    trend,
                    x="datetime_dt",
                    y="dissolved_oxygen_mg_l",
                    markers=True,
                    title=f"Morning Dissolved Oxygen (mg/L) — {title_suffix}",
                    labels={"datetime_dt": "Date", "dissolved_oxygen_mg_l": "DO (mg/L)"},
                )
                fig_do.update_traces(line_color=PALETTE["teal_primary"], line_width=2.5)
                fig_do.add_hline(y=3.0, line_dash="dash", line_color="#E7A23B", annotation_text="3.0 mg/L Screening")
                fig_do.update_layout(template="plotly_white", height=300, margin=dict(l=20, r=20, t=42, b=20))
                st.plotly_chart(fig_do, use_container_width=True)

            with c_right:
                fig_temp = px.line(
                    trend,
                    x="datetime_dt",
                    y="temp_c",
                    markers=True,
                    title=f"Temperature (°C) & pH — {title_suffix}",
                    labels={"datetime_dt": "Date", "temp_c": "Temp (°C)"},
                )
                fig_temp.update_traces(line_color=PALETTE["navy_primary"], name="Temp (°C)", showlegend=True)
                fig_temp.add_scatter(
                    x=trend["datetime_dt"],
                    y=trend["ph"],
                    mode="lines+markers",
                    name="pH",
                    yaxis="y2",
                    line=dict(color=PALETTE["teal_accent"], dash="dot"),
                )
                fig_temp.update_layout(
                    template="plotly_white",
                    height=300,
                    margin=dict(l=20, r=40, t=42, b=20),
                    yaxis2=dict(title="pH", overlaying="y", side="right", showgrid=False),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                )
                st.plotly_chart(fig_temp, use_container_width=True)

            c_nh3, c_gw = st.columns(2)
            with c_nh3:
                nh3_trend = trend.dropna(subset=["primary_calculated_nh3_mg_l"])
                if not nh3_trend.empty:
                    fig_nh3 = px.line(
                        nh3_trend,
                        x="datetime_dt",
                        y="primary_calculated_nh3_mg_l",
                        markers=True,
                        title=f"Calculated NH3 Concentration (mg/L) — {title_suffix}",
                        labels={"datetime_dt": "Date", "primary_calculated_nh3_mg_l": "NH3 (mg/L)"},
                    )
                    fig_nh3.update_traces(line_color="#dc2626", line_width=2.2)
                    fig_nh3.update_layout(template="plotly_white", height=290, margin=dict(l=20, r=20, t=42, b=20))
                    st.plotly_chart(fig_nh3, use_container_width=True)
                else:
                    st.info("Insufficient NH3 records in the selected filter range.")

            with c_gw:
                if not df_growth_view.empty and "average_fish_weight_g" in df_growth_view.columns:
                    gw = df_growth_view.copy()
                    gw["dt"] = pd.to_datetime(gw["datetime"], errors="coerce")
                    gw = gw.dropna(subset=["dt", "average_fish_weight_g"]).sort_values("dt")
                    if not gw.empty:
                        if selected_pond == "All Ponds in Scope":
                            gw_plot = gw.set_index("dt")[["average_fish_weight_g"]].resample("ME").median().reset_index()
                            gw_title = f"Median Cohort Fish Weight (g/fish) — {selected_region}"
                        else:
                            gw_plot = gw
                            gw_title = f"Cohort Average Fish Weight (g/fish) — {selected_pond}"
                        fig_gw = px.line(
                            gw_plot,
                            x="dt",
                            y="average_fish_weight_g",
                            markers=True,
                            title=gw_title,
                            labels={"dt": "Date", "average_fish_weight_g": "Weight (g/fish)"},
                        )
                        fig_gw.update_traces(line_color=PALETTE["teal_primary"], line_width=2.2)
                        fig_gw.update_layout(template="plotly_white", height=290, margin=dict(l=20, r=20, t=42, b=20))
                        st.plotly_chart(fig_gw, use_container_width=True)
                    else:
                        st.info("No dated fish-weight records available in the selected range.")
                else:
                    st.info("No fish-weight records available in the selected scope.")
        else:
            st.warning("No dated water-quality observations available for the selected filter.")

    with tab_risk:
        r_left, r_right = st.columns(2)
        with r_left:
            tier_series = df_view["primary_calculated_nh3_mg_l"].apply(_classify_nh3_tier)
            tier_counts = (
                tier_series.value_counts()
                .reindex(["Optimal (<0.02)", "Caution (0.02–0.05)", "Elevated (0.05–0.10)", "Critical (≥0.10)", "Missing"], fill_value=0)
                .reset_index()
            )
            tier_counts.columns = ["Toxicity Tier", "Observations"]
            fig_tier = px.bar(
                tier_counts,
                x="Toxicity Tier",
                y="Observations",
                color="Toxicity Tier",
                color_discrete_map={
                    "Optimal (<0.02)": "#269B72",
                    "Caution (0.02–0.05)": "#43BFC0",
                    "Elevated (0.05–0.10)": "#E7A23B",
                    "Critical (≥0.10)": "#D9534F",
                    "Missing": "#94a3b8",
                },
                title="Ammonia Toxicity Screening Distribution (Emerson NH3)",
            )
            fig_tier.update_layout(template="plotly_white", height=320, showlegend=False, margin=dict(l=20, r=20, t=42, b=20))
            st.plotly_chart(fig_tier, use_container_width=True)

        with r_right:
            if df_view["pond_id"].nunique() > 1:
                pond_comp = (
                    df_view.groupby("pond_id", as_index=False)
                    .agg(median_do=("dissolved_oxygen_mg_l", "median"), median_nh3=("primary_calculated_nh3_mg_l", "median"))
                    .dropna(subset=["median_do"])
                    .sort_values("median_do", ascending=True)
                    .head(15)
                )
                fig_comp = px.bar(
                    pond_comp,
                    x="pond_id",
                    y="median_do",
                    color="median_nh3",
                    title=f"{container_label} Comparison (Lowest 15 Median DO)",
                    labels={"pond_id": f"{container_label} ID", "median_do": "Median DO (mg/L)", "median_nh3": "Median NH3"},
                    color_continuous_scale="Tealrose",
                )
                fig_comp.update_layout(template="plotly_white", height=320, margin=dict(l=20, r=20, t=42, b=20))
                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.info(f"Select 'All {container_label}s in Scope' to compare multiple {container_label.lower()}s side by side.")

    with tab_obs:
        obs_col, act_col = st.columns([1.4, 1])
        with obs_col:
            st.markdown(f"#### Recent {container_label} Observations")
            recent_cols = [
                "pond_id",
                "region",
                "datetime",
                "dissolved_oxygen_mg_l",
                "ph",
                "temp_c",
                "primary_calculated_nh3_mg_l",
                "dead_fish_count",
            ]
            avail_cols = [c for c in recent_cols if c in df_view.columns]
            recent_df = (
                df_view.sort_values("datetime_dt", ascending=False)[avail_cols]
                .head(15)
                .rename(columns={
                    "pond_id": f"{container_label} ID",
                    "region": "Region",
                    "datetime": "Date",
                    "dissolved_oxygen_mg_l": "DO (mg/L)",
                    "ph": "pH",
                    "temp_c": "Temp (°C)",
                    "primary_calculated_nh3_mg_l": "NH3 (mg/L)",
                    "dead_fish_count": "Dead Fish",
                })
            )
            st.dataframe(recent_df, use_container_width=True, hide_index=True)

        with act_col:
            st.markdown("#### Recent Prediction Activity")
            history = st.session_state.get("prediction_history", [])
            if history:
                hist_df = pd.DataFrame(history).iloc[::-1].head(10)
                st.dataframe(hist_df, use_container_width=True, hide_index=True)
            else:
                st.info("No batch predictions run in this session yet. Use **Upload New Dataset** to analyse new CSV observations.")

    # Collapsed Technical & Scope Notes
    with st.expander("About Historical Scope, Hierarchy & Governance", expanded=False):
        st.markdown(
            "- **Recorded Hierarchy:** The audited historical dataset records `region` and `pond_id` without a separate corporate farm parent table.\n"
            "- **Sampling Protocol:** Routine morning field visits (`06:00–08:30 AM`) spaced `3–45 days` apart; NOT live IoT streaming.\n"
            "- **Decision-Support Only:** All outputs are observational aids (`is_automatic_control = False`); zero automated equipment actuation."
        )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
