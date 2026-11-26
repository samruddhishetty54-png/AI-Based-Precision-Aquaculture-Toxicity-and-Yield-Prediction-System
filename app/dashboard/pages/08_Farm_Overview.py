"""Page 2: Farm Management – Precision AquaDSS.

Operational Category: HISTORICAL & CONFIGURATION (Multi-Environment Farm & Container Management).
Supports:
1. Indoor and Outdoor Aquaculture Environment Switching & Profile Context.
2. Interactive Registration: Add new farms, add ponds/tanks, view existing inventory.
3. Active Container Selection: Pick a specific pond or tank for global session analysis.
4. Indoor vs Outdoor specific tracking:
   - Indoor: Tanks, tank identification, water quality (pH, temp, ammonia, DO), feeding records, fish growth observations.
   - Outdoor: Ponds, pond identification, water quality (pH, temp, ammonia, DO), weather context, feeding records, fish growth observations.
5. Integrated CSV Dataset Upload with automatic field mapping (supporting tank_id / pond_id).
6. 100% Free Platform: Zero subscription or tier restrictions.
"""

from typing import Dict, Any, List, Optional
import datetime
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
from app.dashboard.utils.upload_processor import (
    detect_and_map_columns,
    validate_mapped_dataframe,
    save_uploaded_dataset_to_session,
    generate_validation_report_markdown,
)


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
    """Render the Farm Management page."""
    inject_custom_css()

    current_farm_type = get_active_farm_type()
    container_label = get_container_label(current_farm_type)
    container_id_label = get_container_id_label(current_farm_type)

    render_page_header(
        title="Farm Management",
        subtitle=f"Register and manage {current_farm_type.lower()} facilities, {container_label.lower()}s, and observation datasets.",
        category_key="HISTORICAL",
    )

    # ── Farm Environment Selector & 100% Free Platform Banner ─────────
    st.markdown(
        f"""
        <div style="background-color: #FFFFFF; border: 1px solid #DCE9E6; border-left: 4px solid #087F72; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.9rem; box-shadow: 0 1px 4px rgba(16,44,58,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 0.35rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="font-weight: 800; font-size: 0.85rem; color: #173747;">🏢 Farm Environment: {current_farm_type}</span>
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
                <span style="color: #64748b;"><strong>Scientific Boundary:</strong> {get_farm_type_disclaimer(current_farm_type)}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Environment Selection Controls
    env_col1, env_col2 = st.columns([1.2, 2.8])
    with env_col1:
        new_env = st.radio(
            "Select Farm Environment:",
            options=["Outdoor Aquaculture", "Indoor Aquaculture"],
            index=0 if current_farm_type == "Outdoor Aquaculture" else 1,
            horizontal=True,
            key="farm_mgmt_env_radio",
        )
        if new_env != current_farm_type:
            st.session_state["active_farm_type"] = new_env
            st.rerun()

    with env_col2:
        if new_env == "Indoor Aquaculture":
            st.info(
                "🏢 **Indoor Aquaculture Mode Selected:** Configured for closed fish tanks, recirculating systems (RAS), "
                "or indoor hatcheries. Tracks tank IDs, water quality (pH, temp, NH₃, DO), feeding logs, and fish growth. "
                "Note: Standard water quality models apply; environmental variables are not assumed to be strictly uniform."
            )
        else:
            st.info(
                "🌊 **Outdoor Aquaculture Mode Selected:** Configured for open earthen ponds and commercial culture ponds. "
                "Tracks pond IDs, water quality (pH, temp, NH₃, DO), ambient weather conditions when recorded, feeding logs, and fish growth."
            )

    # ── Load Historical Data ──────────────────────────────────────────
    try:
        df_tox = load_dataset("toxicity_analysis")
        df_enrolled = load_dataset("enrolled_ponds")
        df_growth = load_dataset("fish_health_growth")
        df_feeding = load_dataset("feeding_analysis")
    except Exception as exc:
        st.error(f"Failed to load datasets: {exc}")
        return

    df_tox["datetime_dt"] = pd.to_datetime(df_tox["datetime"], errors="coerce")

    # Initialize Session State Registries if missing
    if "registered_farms" not in st.session_state:
        st.session_state["registered_farms"] = [
            {"farm_id": "FARM-NORTH", "name": "Northern Aqua Cluster", "environment": "Outdoor Aquaculture", "region": "North Delta", "container_count": 48},
            {"farm_id": "FARM-SOUTH", "name": "Southern River Valley", "environment": "Outdoor Aquaculture", "region": "South Delta", "container_count": 62},
            {"farm_id": "FARM-INDOOR-01", "name": "Precision RAS Facility A", "environment": "Indoor Aquaculture", "region": "Central Hub", "container_count": 24},
        ]
    if "registered_ponds" not in st.session_state:
        st.session_state["registered_ponds"] = []

    # ── Top Action Tabs ───────────────────────────────────────────────
    tab_view, tab_add_farm, tab_add_container, tab_upload = st.tabs([
        f"📋 Existing Farms & {container_label}s",
        "➕ Add New Farm",
        f"➕ Add {container_label}",
        "📤 Import Custom Dataset",
    ])

    # ── TAB 1: Existing Farms & Containers ────────────────────────────
    with tab_view:
        st.markdown(f"#### Active {current_farm_type} Inventory")

        # Global Container Selector
        all_ponds = sorted(df_tox["pond_id"].dropna().astype(str).unique().tolist())
        # add any session registered ponds
        for p in st.session_state["registered_ponds"]:
            if p["container_id"] not in all_ponds:
                all_ponds.append(p["container_id"])

        current_selected = st.session_state.get("selected_pond", all_ponds[0] if all_ponds else "POND-001")
        if current_selected not in all_ponds and all_ponds:
            current_selected = all_ponds[0]

        sel_col1, sel_col2 = st.columns([1.5, 2.5])
        with sel_col1:
            chosen_container = st.selectbox(
                f"Select Active {container_id_label} for Analysis across all pages:",
                options=all_ponds,
                index=all_ponds.index(current_selected) if current_selected in all_ponds else 0,
                key="farm_mgmt_active_container_select",
            )
            st.session_state["selected_pond"] = chosen_container
            st.session_state["active_container_id"] = chosen_container

        with sel_col2:
            st.caption(
                f"**Active Container:** `{chosen_container}` ({current_farm_type}). "
                f"Selecting this updates the active scope for Water Quality, Feeding & Growth, and Historical Reports."
            )

        # Container Details Card
        df_pond_wq = df_tox[df_tox["pond_id"].astype(str) == chosen_container].sort_values("datetime_dt")
        df_pond_growth = df_growth[df_growth["pond_id"].astype(str) == chosen_container]
        df_pond_feed = df_feeding[df_feeding["pond_id"].astype(str) == chosen_container] if not df_feeding.empty and "pond_id" in df_feeding.columns else pd.DataFrame()

        if not df_pond_wq.empty:
            latest_row = df_pond_wq.iloc[-1]
            last_date = str(latest_row.get("datetime", ""))[:10]
            last_do = latest_row.get("dissolved_oxygen_mg_l", float("nan"))
            last_ph = latest_row.get("ph", float("nan"))
            last_temp = latest_row.get("temp_c", float("nan"))
            last_nh3 = latest_row.get("primary_calculated_nh3_mg_l", float("nan"))
            weather_val = latest_row.get("Weather", "Not Recorded") if current_farm_type == "Outdoor Aquaculture" else "Indoor Environment (Ambient)"

            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                render_metric_card(
                    title=f"Active {container_label}",
                    value=chosen_container,
                    subtitle=f"{current_farm_type}",
                    benchmark_ref="System ID",
                    icon="🏷️",
                    accent="teal",
                )
            with m2:
                render_metric_card(
                    title="Latest Morning DO",
                    value=f"{last_do:.2f} mg/L" if pd.notna(last_do) else "N/A",
                    subtitle="06:00–08:30 AM Log",
                    benchmark_ref="Safe: > 4.0 mg/L",
                    icon="💧",
                    accent="success" if (pd.notna(last_do) and last_do >= 4.0) else "warning",
                )
            with m3:
                render_metric_card(
                    title="Latest Water pH",
                    value=f"{last_ph:.2f}" if pd.notna(last_ph) else "N/A",
                    subtitle=f"Temp: {last_temp:.1f} °C" if pd.notna(last_temp) else "N/A",
                    benchmark_ref="Safe: 6.5–8.5",
                    icon="🧪",
                    accent="teal",
                )
            with m4:
                render_metric_card(
                    title="Calculated NH₃",
                    value=f"{last_nh3:.4f} mg/L" if pd.notna(last_nh3) else "N/A",
                    subtitle=_classify_nh3_tier(last_nh3),
                    benchmark_ref="Toxic threshold: 0.05",
                    icon="⚠️" if (pd.notna(last_nh3) and last_nh3 >= 0.05) else "✅",
                    accent="warning" if (pd.notna(last_nh3) and last_nh3 >= 0.05) else "aqua",
                )
            with m5:
                render_metric_card(
                    title="Observation Context",
                    value=str(weather_val)[:15],
                    subtitle=f"Observed: {last_date}",
                    benchmark_ref="Field Visit Log",
                    icon="🌤️" if current_farm_type == "Outdoor Aquaculture" else "🏢",
                    accent="teal",
                )

            # Trajectory Chart for Selected Container
            st.markdown(f"##### Historical Parameter Trajectory for `{chosen_container}`")
            fig_p = px.line(
                df_pond_wq,
                x="datetime_dt",
                y=["dissolved_oxygen_mg_l", "ph", "temp_c"],
                markers=True,
                labels={"datetime_dt": "Date", "value": "Reading", "variable": "Parameter"},
                title=f"Water Quality Trends — {container_label} {chosen_container}",
                color_discrete_map={
                    "dissolved_oxygen_mg_l": "#087F72",
                    "ph": "#43BFC0",
                    "temp_c": "#E7A23B",
                },
            )
            fig_p.update_layout(height=280, template="plotly_white", margin=dict(l=20, r=20, t=35, b=20))
            st.plotly_chart(fig_p, use_container_width=True)

        # Registered Farms Table
        st.markdown("##### Registered Farm Facilities")
        farms_df = pd.DataFrame(st.session_state["registered_farms"])
        st.dataframe(farms_df, use_container_width=True, hide_index=True)

    # ── TAB 2: Add New Farm ───────────────────────────────────────────
    with tab_add_farm:
        st.markdown("#### Register a New Farm")
        st.caption("Create a new commercial farm profile in the system. Stored in your active session.")

        with st.form("add_farm_form", clear_on_submit=True):
            f_col1, f_col2 = st.columns(2)
            with f_col1:
                f_name = st.text_input("Farm Name / Facility Title:", placeholder="e.g. Apex Aquaculture Hatchery")
                f_region = st.text_input("Region / Geographical Location:", placeholder="e.g. Delta Sector 4")
            with f_col2:
                f_env = st.selectbox("Operational Environment:", ["Outdoor Aquaculture", "Indoor Aquaculture"], index=0 if current_farm_type == "Outdoor Aquaculture" else 1)
                f_notes = st.text_area("Operational Notes:", placeholder="Water source, aeration setup, species cultured...")

            submit_farm = st.form_submit_button("➕ Register Farm", use_container_width=True)
            if submit_farm:
                if f_name.strip():
                    new_farm_entry = {
                        "farm_id": f"FARM-{len(st.session_state['registered_farms']) + 1:03d}",
                        "name": f_name.strip(),
                        "environment": f_env,
                        "region": f_region.strip() or "Standard Region",
                        "container_count": 0,
                    }
                    st.session_state["registered_farms"].append(new_farm_entry)
                    st.success(f"✅ Farm **{f_name}** successfully registered ({new_farm_entry['farm_id']})!")
                    st.rerun()
                else:
                    st.error("Please enter a valid farm name.")

    # ── TAB 3: Add Container (Pond / Tank) ─────────────────────────────
    with tab_add_container:
        st.markdown(f"#### Add a New {container_label}")
        st.caption(f"Add a new {container_label.lower()} to your registered facilities.")

        with st.form("add_container_form", clear_on_submit=True):
            farm_names = [f["name"] for f in st.session_state["registered_farms"]]
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                target_farm = st.selectbox("Assign to Farm:", options=farm_names if farm_names else ["Default Farm"])
                container_id_input = st.text_input(
                    f"{container_id_label}:",
                    placeholder=f"e.g. {'TANK-101' if current_farm_type == 'Indoor Aquaculture' else 'POND-050'}",
                )
            with c_col2:
                c_system = st.selectbox(
                    "System Type:",
                    [
                        "Recirculating Aquaculture System (RAS)",
                        "Indoor Fiberglass Tank",
                        "Indoor Concrete Cistern",
                        "Open Earthen Pond",
                        "HDPE Lined Pond",
                        "Raceway System",
                    ]
                    if current_farm_type == "Indoor Aquaculture"
                    else [
                        "Open Earthen Pond",
                        "HDPE Lined Pond",
                        "Semi-Intensive Embankment Pond",
                        "Irrigation Canal Cage",
                    ],
                )
                species = st.selectbox("Target Cultured Species:", ["Nile Tilapia", "African Catfish", "Common Carp", "Pangasius", "Tiger Shrimp", "Other"])

            submit_container = st.form_submit_button(f"➕ Register {container_label}", use_container_width=True)
            if submit_container:
                if container_id_input.strip():
                    cid = container_id_input.strip().upper()
                    st.session_state["registered_ponds"].append({
                        "container_id": cid,
                        "farm": target_farm,
                        "environment": current_farm_type,
                        "system": c_system,
                        "species": species,
                        "date_added": str(datetime.date.today()),
                    })
                    st.session_state["selected_pond"] = cid
                    st.success(f"✅ {container_label} **{cid}** successfully registered and selected for active analysis!")
                    st.rerun()
                else:
                    st.error(f"Please enter a valid {container_id_label}.")

    # ── TAB 4: Upload Custom Field Dataset ─────────────────────────────
    with tab_upload:
        st.markdown("#### Import Custom Aquaculture Field Logs")
        st.caption(
            "Upload your own CSV inspection records. Supports both indoor tanks (`tank_id`, `system_id`) "
            "and outdoor ponds (`pond_id`). All analyses run locally in your session."
        )

        uploaded_file = st.file_uploader(
            "Choose a CSV file containing aquaculture observations:",
            type=["csv"],
            key="farm_mgmt_csv_uploader",
        )

        if uploaded_file is not None:
            try:
                raw_df = pd.read_csv(uploaded_file)
                st.write(f"**Loaded {len(raw_df):,} rows and {len(raw_df.columns)} columns.**")
                st.dataframe(raw_df.head(5), use_container_width=True)

                # Automated column detection and mapping
                mapped_df, mapping_report = detect_and_map_columns(raw_df)
                validation_results = validate_mapped_dataframe(mapped_df)

                if validation_results["is_valid"]:
                    st.success("✅ Dataset successfully validated against precision aquaculture schema!")
                    if st.button("Apply Dataset to Active Session Analysis", use_container_width=True):
                        save_uploaded_dataset_to_session(uploaded_file.name, raw_df, mapped_df, validation_results)
                        st.success("🎉 Dataset loaded! Active ponds/tanks are now available across all pages.")
                        st.rerun()
                else:
                    st.warning("⚠️ Some required fields could not be mapped automatically:")
                    st.markdown(generate_validation_report_markdown(validation_results))

            except Exception as exc:
                st.error(f"Error processing CSV file: {exc}")

    # ── Governance and Scope Footer ───────────────────────────────────
    with st.expander("Farm Management Scope & Data Governance", expanded=False):
        st.markdown(
            "- **No Separate ML Models Claim:** Analytical and predictive algorithms evaluate standard physical-chemical water quality metrics (pH, Temperature, Ammonia, Dissolved Oxygen). No unvalidated separate machine learning model is fabricated for indoor vs outdoor environments.\n"
            "- **Zero Actuation:** Precision AquaDSS provides advisory analytics only (`is_automatic_control = False`). Aerators, feeders, and recirculating pumps must be verified and operated by qualified personnel.\n"
            "- **Data Segregation:** Uploaded session files and simulation runs are strictly segregated from audited commercial baseline datasets."
        )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
