"""Page 9: Central Dataset Import & Analysis Workspace.

Supports the primary organization workflow:
Upload CSV -> Preview -> Map Columns & Confirm Units -> Validate ->
Assess Model Compatibility -> Run Analysis -> View Results & Export.

Strict Data-Integrity & Scientific Rules:
1. CSV only (openpyxl is not installed, so Excel upload is not supported).
2. Never fills missing values with zero or fabricates missing readings.
3. Never assumes units from ambiguous column names without explicit confirmation.
4. Keeps uploaded data isolated in st.session_state["uploaded_analysis_state"].
5. Runs models ONLY when their actual required inputs and bounds are satisfied.
6. Unavailable outputs are shown as unavailable with explicit reasons.
"""

from typing import Dict, List, Optional
import hashlib
import pandas as pd
import plotly.express as px
import streamlit as st

from app.dashboard.components.banners import render_decision_support_banner
from app.dashboard.components.header import render_page_header, render_section_bar
from app.dashboard.components.metric_card import render_metric_card
from app.dashboard.utils.helpers import (
    format_float,
    get_active_farm_type,
    get_container_label,
    get_container_id_label,
    get_farm_type_disclaimer,
    log_prediction_event,
    FREE_PLATFORM_NOTICE,
)
from app.dashboard.utils.styles import PALETTE, inject_custom_css
from app.dashboard.utils.upload_processor import (
    CANONICAL_FIELDS,
    assess_model_compatibility,
    inspect_dataframe_profile,
    parse_uploaded_csv,
    run_batch_analysis,
    suggest_column_mapping,
    validate_mapped_dataset,
)
from app.models.registry import get_model_registry


def render_page() -> None:
    """Render the Dataset Import & Analysis Workspace."""
    inject_custom_css()

    farm_type = get_active_farm_type()
    container_label = get_container_label(farm_type)
    container_id_label = get_container_id_label(farm_type)

    render_page_header(
        title="Dataset Import & Analysis Workspace",
        subtitle=f"Upload {container_label.lower()} observation CSV files, validate schema and units, run compatible models, and export results ({farm_type}).",
        category_key="ADVISORY",
    )

    st.markdown(
        """
        <div style="display: flex; flex-wrap: wrap; gap: 0.35rem; margin-bottom: 1rem;">
            <span style="background:#FFFFFF; border:1px solid #DCE9E6; border-radius:9999px; padding:0.18rem 0.6rem; font-size:0.73rem; font-weight:700; color:#173747;">1. Upload CSV</span>
            <span style="background:#FFFFFF; border:1px solid #DCE9E6; border-radius:9999px; padding:0.18rem 0.6rem; font-size:0.73rem; font-weight:700; color:#173747;">2. Preview Dataset</span>
            <span style="background:#FFFFFF; border:1px solid #DCE9E6; border-radius:9999px; padding:0.18rem 0.6rem; font-size:0.73rem; font-weight:700; color:#173747;">3. View Columns</span>
            <span style="background:#FFFFFF; border:1px solid #DCE9E6; border-radius:9999px; padding:0.18rem 0.6rem; font-size:0.73rem; font-weight:700; color:#173747;">4. Map Columns</span>
            <span style="background:#FFFFFF; border:1px solid #DCE9E6; border-radius:9999px; padding:0.18rem 0.6rem; font-size:0.73rem; font-weight:700; color:#173747;">5. Validate Data</span>
            <span style="background:#FFFFFF; border:1px solid #DCE9E6; border-radius:9999px; padding:0.18rem 0.6rem; font-size:0.73rem; font-weight:700; color:#173747;">6. Missing / Bounds Audit</span>
            <span style="background:#FFFFFF; border:1px solid #DCE9E6; border-radius:9999px; padding:0.18rem 0.6rem; font-size:0.73rem; font-weight:700; color:#173747;">7. Model Compatibility</span>
            <span style="background:#FFFFFF; border:1px solid #DCE9E6; border-radius:9999px; padding:0.18rem 0.6rem; font-size:0.73rem; font-weight:700; color:#173747;">8. Select Analyses</span>
            <span style="background:#FFFFFF; border:1px solid #DCE9E6; border-radius:9999px; padding:0.18rem 0.6rem; font-size:0.73rem; font-weight:700; color:#173747;">9. Run Analysis</span>
            <span style="background:#E3F5F3; border:1px solid #AEE2DC; border-radius:9999px; padding:0.18rem 0.6rem; font-size:0.73rem; font-weight:700; color:#087F72;">10. Results & CSV Export</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info(f"**Operational Scope ({farm_type}):** {get_farm_type_disclaimer(farm_type)}")

    # Step 1: CSV Upload
    st.markdown(f"### 1. Upload {container_label} Observation Dataset (CSV)")
    st.caption(
        "Supported format: `.csv` (UTF-8 or Latin-1). Excel `.xlsx` upload is disabled because `openpyxl` "
        "is not installed in this environment. Uploaded files remain isolated in your current session."
    )

    uploaded_file = st.file_uploader(
        "Drag and drop or browse a CSV file",
        type=["csv"],
        accept_multiple_files=False,
        key="aqua_csv_uploader",
    )

    if uploaded_file is None:
        existing_state = st.session_state.get("uploaded_analysis_state")
        if existing_state:
            st.info(
                f"Previously loaded session dataset: **{existing_state.get('filename')}** "
                f"({existing_state.get('total_rows', 0)} rows)."
            )
            if st.button("Clear Uploaded Session Data", key="clear_upload_btn"):
                st.session_state.pop("uploaded_analysis_state", None)
                st.session_state.pop("uploaded_results_state", None)
                st.rerun()
        return

    file_bytes = uploaded_file.getvalue()
    file_sig = hashlib.sha256(file_bytes).hexdigest()[:12]
    df_raw, parse_err = parse_uploaded_csv(file_bytes, uploaded_file.name)
    if parse_err or df_raw is None:
        st.error(parse_err or "Unable to parse CSV file.")
        return

    # Clear stale results if the uploaded file changed
    prev_state = st.session_state.get("uploaded_analysis_state")
    if prev_state and prev_state.get("file_sig") != file_sig:
        st.session_state.pop("uploaded_results_state", None)

    # Step 2: Preview & Profile
    profile = inspect_dataframe_profile(df_raw)
    st.markdown("### 2. Dataset Preview & Integrity Profile")

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        render_metric_card("Uploaded Rows", f"{profile['total_rows']:,}", uploaded_file.name, icon="📄", accent="teal")
    with p2:
        render_metric_card("Columns", f"{profile['total_cols']}", "Raw CSV schema", icon="📊", accent="aqua")
    with p3:
        render_metric_card("Exact Duplicate Rows", f"{profile['duplicate_rows']:,}", "Preserved without removal", icon="🔁", accent="aqua")
    with p4:
        total_missing = int(df_raw.isna().sum().sum())
        render_metric_card("Missing Cells (NaN)", f"{total_missing:,}", "Never zero-filled", icon="🔍", accent="warning" if total_missing > 0 else "success")

    with st.expander("Preview Uploaded Records (First 15 Rows)", expanded=True):
        st.dataframe(df_raw.head(15), use_container_width=True, hide_index=True)

    with st.expander("Column Data Types & Missing-Value Summary", expanded=False):
        st.dataframe(profile["columns_df"], use_container_width=True, hide_index=True)

    # Step 3: Canonical Field Mapping & Unit Confirmation
    st.markdown("### 3. Column Mapping & Unit Confirmation")
    st.caption(
        "Map your CSV columns to canonical Precision AquaDSS fields. Ambiguous column names "
        "(without explicit units) are flagged and require your confirmation."
    )

    suggested_map, ambiguities = suggest_column_mapping(list(df_raw.columns))
    confirmed_ambiguous: List[str] = []

    if ambiguities:
        st.warning(
            f"Detected {len(ambiguities)} column(s) with ambiguous units/basis. "
            "Confirm units explicitly before mapping them."
        )
        for amb in ambiguities:
            col_name = amb["uploaded_column"]
            cand = amb["candidate_field"]
            label = CANONICAL_FIELDS[cand]["label"]
            if st.checkbox(
                f"Confirm `{col_name}` uses unit `{amb['expected_unit']}` for **{label}**",
                value=False,
                key=f"confirm_amb_{file_sig}_{col_name}_{cand}",
            ):
                confirmed_ambiguous.append(col_name)
                suggested_map[cand] = col_name

    col_options = ["(Not Mapped)"] + [str(c) for c in df_raw.columns]
    user_mapping: Dict[str, Optional[str]] = {}

    with st.expander("Configure Field Mapping", expanded=True):
        map_cols = st.columns(2)
        canon_keys = list(CANONICAL_FIELDS.keys())
        for idx, canon in enumerate(canon_keys):
            spec = CANONICAL_FIELDS[canon]
            default_src = suggested_map.get(canon)
            default_idx = col_options.index(default_src) if default_src in col_options else 0
            with map_cols[idx % 2]:
                chosen = st.selectbox(
                    f"{spec['label']} [{spec['unit']}]",
                    options=col_options,
                    index=default_idx,
                    key=f"map_sel_{file_sig}_{canon}",
                )
                user_mapping[canon] = None if chosen == "(Not Mapped)" else chosen

    # Step 4: Validate
    validation = validate_mapped_dataset(
        df=df_raw,
        mapping=user_mapping,
        filename=uploaded_file.name,
        confirmed_ambiguous_cols=confirmed_ambiguous,
    )
    work_df: pd.DataFrame = validation["canonical_df"]

    st.markdown("### 4. Schema, Pond Hierarchy & Validation Results")
    if validation["errors"]:
        for err in validation["errors"]:
            st.error(err)
    else:
        st.success("Schema and data-type checks passed.")

    if validation["warnings"]:
        for warn in validation["warnings"]:
            st.warning(warn)

    if not validation["out_of_bounds_df"].empty:
        with st.expander("Out-of-Bounds Software Defensive Check Summary", expanded=True):
            st.dataframe(validation["out_of_bounds_df"], use_container_width=True, hide_index=True)

    # Pond & Observation Date selection
    scope_col1, scope_col2 = st.columns(2)
    pond_filter: Optional[str] = None
    with scope_col1:
        if "pond_id" in work_df.columns and validation["pond_count"] > 0:
            ponds = sorted(work_df["pond_id"].dropna().astype(str).unique().tolist())
            pond_filter = st.selectbox(
                f"Select Pond to Analyse ({len(ponds)} pond ID(s) detected):",
                options=["All Ponds in Upload"] + ponds,
                index=0,
                key=f"upload_pond_selector_{file_sig}",
            )
            if pond_filter != "All Ponds in Upload":
                work_scoped = work_df[work_df["pond_id"].astype(str) == pond_filter].copy()
            else:
                work_scoped = work_df.copy()
        else:
            st.info("No `pond_id` column mapped — treating uploaded rows as pond-unspecified records (no IDs invented).")
            work_scoped = work_df.copy()

    selected_date_label = "All Dates"
    with scope_col2:
        if "datetime_parsed" in work_scoped.columns and work_scoped["datetime_parsed"].notna().any():
            valid_dates = sorted(work_scoped["datetime_parsed"].dropna().dt.strftime("%Y-%m-%d").unique().tolist())
            date_choice = st.selectbox(
                f"Select Observation Date ({len(valid_dates)} date(s) in scope):",
                options=["All Dates"] + valid_dates,
                index=0,
                key=f"upload_date_selector_{file_sig}",
            )
            selected_date_label = date_choice
            if date_choice != "All Dates":
                work_scoped = work_scoped[
                    work_scoped["datetime_parsed"].dt.strftime("%Y-%m-%d") == date_choice
                ].copy()
        else:
            st.info("No valid observation dates mapped — all rows in pond scope included (no dates invented).")

    current_scope_sig = f"{file_sig}|{pond_filter or 'All Records'}|{selected_date_label}"

    # Store validated dataset in session state (strictly isolated from historical/simulated)
    st.session_state["uploaded_analysis_state"] = {
        "filename": uploaded_file.name,
        "file_sig": file_sig,
        "scope_sig": current_scope_sig,
        "source_type": "UPLOADED_CSV",
        "is_valid": validation["is_valid"],
        "is_simulated": validation["is_simulated"],
        "operational_use_permitted": validation["operational_use_permitted"],
        "total_rows": len(work_df),
        "pond_count": validation["pond_count"],
        "farm_count": validation["farm_count"],
        "canonical_df": work_df,
        "scoped_df": work_scoped,
        "selected_pond": pond_filter or "All Records",
        "selected_date": selected_date_label,
        "mapping": user_mapping,
    }

    # Step 5: Model Compatibility Audit
    st.markdown("### 5. Model Compatibility & Run Analysis")
    compat_list = assess_model_compatibility(work_scoped)
    compat_df = pd.DataFrame([
        {
            "Module / Model": c["name"],
            "Category": c["category"],
            "Compatible": "YES" if c["compatible"] else "NO",
            "Eligible Rows": f"{c['eligible_rows']} / {c['total_rows']}",
            "Status & Requirements": c["reason"],
        }
        for c in compat_list
    ])
    st.dataframe(compat_df, use_container_width=True, hide_index=True)

    compatible_keys = [c["key"] for c in compat_list if c["compatible"]]
    name_by_key = {c["key"]: c["name"] for c in compat_list}

    selected_models = st.multiselect(
        "Select Compatible Modules to Execute:",
        options=compatible_keys,
        default=compatible_keys,
        format_func=lambda k: name_by_key.get(k, k),
        key="upload_selected_models",
    )

    default_gap_days = 21.0
    if "exp3_ammonia_risk" in selected_models and "gap_days" not in work_scoped.columns:
        default_gap_days = st.slider(
            "Revisit Interval for Next-Visit Ammonia Risk (days, 3–45):",
            min_value=3,
            max_value=45,
            value=21,
            key="upload_exp3_gap_days",
        )

    can_run = bool(validation["is_valid"] and len(selected_models) > 0 and len(work_scoped) > 0)
    run_clicked = st.button(
        "Run Analysis",
        disabled=not can_run,
        type="primary",
        key="run_upload_analysis_btn",
    )

    if run_clicked and can_run:
        registry = get_model_registry()
        results_df, run_summary = run_batch_analysis(
            work_df=work_scoped,
            registry=registry,
            selected_models=selected_models,
            default_gap_days=float(default_gap_days),
        )
        st.session_state["uploaded_results_state"] = {
            "results_df": results_df,
            "summary": run_summary,
            "compat_list": compat_list,
            "filename": uploaded_file.name,
            "file_sig": file_sig,
            "scope_sig": current_scope_sig,
            "selected_pond": pond_filter or "All Records",
            "selected_date": selected_date_label,
        }
        # Standardized history logging
        batch_summary = (
            f"Analyzed {run_summary['analyzed_rows']} rows across models: {', '.join(selected_models)}. "
            f"Scope: {pond_filter or 'All Records'} ({selected_date_label})."
        )
        log_prediction_event(
            analysis_type=f"Batch Upload Analysis ({len(selected_models)} models)",
            container_id=str(pond_filter or "All Records"),
            data_source=f"Uploaded CSV ({uploaded_file.name})",
            is_simulated=bool(validation.get("is_simulated", False)),
            results_summary=batch_summary,
            details={
                "executed_at": run_summary["executed_at"],
                "filename": uploaded_file.name,
                "analyzed_rows": run_summary["analyzed_rows"],
                "models_executed": ", ".join(selected_models),
                "median_do_mg_l": float(results_df["do_mg_l"].median()) if "do_mg_l" in results_df and results_df["do_mg_l"].notna().any() else None,
                "median_emerson_nh3_mg_l": float(results_df["emerson_nh3_mg_l"].median()) if "emerson_nh3_mg_l" in results_df and results_df["emerson_nh3_mg_l"].notna().any() else None,
                "median_mortality_score": float(results_df["exp2_mortality_risk_score"].median()) if "exp2_mortality_risk_score" in results_df and results_df["exp2_mortality_risk_score"].notna().any() else None,
                "median_next_visit_nh3_risk": float(results_df["exp3_next_visit_nh3_risk"].median()) if "exp3_next_visit_nh3_risk" in results_df and results_df["exp3_next_visit_nh3_risk"].notna().any() else None,
                "median_recommended_feed_kg": float(results_df["recommended_feed_kg"].median()) if "recommended_feed_kg" in results_df and results_df["recommended_feed_kg"].notna().any() else None,
            },
            farm_type=farm_type,
        )

    # Step 6: Results Workspace
    res_state = st.session_state.get("uploaded_results_state")
    if res_state and res_state.get("scope_sig") == current_scope_sig:
        results_df: pd.DataFrame = res_state["results_df"]
        run_summary = res_state["summary"]
        _render_results_workspace(results_df, run_summary, res_state["compat_list"], res_state["selected_pond"])
    elif res_state and res_state.get("file_sig") == file_sig:
        st.info("Pond or observation date selection changed. Click **Run Analysis** to refresh results for the new scope.")


def _render_results_workspace(
    results_df: pd.DataFrame,
    run_summary: Dict,
    compat_list: List[Dict],
    selected_pond: str,
) -> None:
    """Render structured analysis results and exportable report."""
    st.markdown("---")
    st.markdown("## 6. Analysis Results Workspace")
    st.caption(
        f"Source: Uploaded CSV • Scope: **{selected_pond}** • "
        f"Analyzed {run_summary['analyzed_rows']} row(s) at {run_summary['executed_at']}."
    )
    if run_summary.get("truncated_from"):
        st.info(
            f"Batch execution processed the first {run_summary['analyzed_rows']} rows out of "
            f"{run_summary['truncated_from']} rows in scope."
        )

    # Execution Status Summary (Successful, Skipped, Rejected)
    module_counts = run_summary.get("module_counts", {})
    executed_set = set(run_summary.get("models_executed", []))
    exec_rows = []
    for c in compat_list:
        m_key = c["key"]
        if m_key in executed_set:
            counts = module_counts.get(m_key, {"processed": 0, "rejected": run_summary["analyzed_rows"]})
            status_lbl = "Executed" if counts["processed"] > 0 else "Failed / No Valid Output"
            proc_n, rej_n = counts["processed"], counts["rejected"]
            reason_txt = "Processed using saved model wrapper & existing preprocessing."
        elif c["compatible"]:
            status_lbl = "Skipped (Unselected)"
            proc_n, rej_n = 0, run_summary["analyzed_rows"]
            reason_txt = "Compatible, but not selected by user."
        else:
            status_lbl = f"Skipped ({c['status']})"
            proc_n, rej_n = 0, run_summary["analyzed_rows"]
            reason_txt = c["reason"]
        exec_rows.append({
            "Analysis Module": c["name"],
            "Execution Status": status_lbl,
            "Processed Records": proc_n,
            "Rejected / Skipped": rej_n,
            "Details": reason_txt,
        })
    with st.expander("Execution Summary: Processed, Skipped & Rejected Records", expanded=True):
        st.dataframe(pd.DataFrame(exec_rows), use_container_width=True, hide_index=True)

    # Section A: Water Quality Summary
    st.markdown("### Water Quality Analysis")
    wq1, wq2, wq3, wq4 = st.columns(4)
    with wq1:
        val = results_df["do_mg_l"].median() if "do_mg_l" in results_df else None
        render_metric_card("Median DO", format_float(val, 2, "mg/L"), "Uploaded scope")
    with wq2:
        val = results_df["ph"].median() if "ph" in results_df else None
        render_metric_card("Median pH", format_float(val, 2), "Uploaded scope")
    with wq3:
        val = results_df["temp_c"].median() if "temp_c" in results_df else None
        render_metric_card("Median Temperature", format_float(val, 1, "°C"), "Uploaded scope")
    with wq4:
        if "emerson_nh3_mg_l" in results_df and results_df["emerson_nh3_mg_l"].notna().any():
            val = results_df["emerson_nh3_mg_l"].median()
            render_metric_card("Median Emerson NH3", format_float(val, 4, "mg/L"), "Theoretical equilibrium")
        else:
            render_metric_card("Emerson NH3", "Unavailable", "Requires pH, Temp & TAN basis")

    if "do_mg_l" in results_df and results_df["do_mg_l"].notna().any():
        fig = px.histogram(
            results_df.dropna(subset=["do_mg_l"]),
            x="do_mg_l",
            nbins=20,
            title="Uploaded Dissolved Oxygen Distribution (mg/L)",
            labels={"do_mg_l": "Dissolved Oxygen (mg/L)"},
        )
        fig.update_traces(marker_color=PALETTE["teal_primary"])
        fig.update_layout(template="plotly_white", height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    # Section B: Toxicity Screening
    st.markdown("### Toxicity Screening (Experimental & Advisory)")
    st.warning(
        "The ammonia soft-sensor underpredicts acute NH3 >= 0.05 mg/L; the mortality diagnostic has low holdout precision "
        "(high false alarms); next-visit ammonia risk is an exploratory multi-week screening score. "
        "Never use as autonomous safety alarms."
    )
    t1, t2, t3 = st.columns(3)
    with t1:
        if "exp1_est_nh3_mg_l" in results_df and results_df["exp1_est_nh3_mg_l"].notna().any():
            render_metric_card(
                "Median Est. NH3 (Soft-Sensor)",
                format_float(results_df["exp1_est_nh3_mg_l"].median(), 4, "mg/L"),
                "EXPERIMENTAL_SOFT_SENSOR",
            )
        else:
            render_metric_card("Ammonia Soft-Sensor", "Unavailable", "Requires DO, pH, Temp")
    with t2:
        if "exp2_mortality_risk_score" in results_df and results_df["exp2_mortality_risk_score"].notna().any():
            render_metric_card(
                "Median Mortality Risk Score",
                format_float(results_df["exp2_mortality_risk_score"].median(), 4),
                "ADVISORY_DIAGNOSTIC_ONLY",
            )
        else:
            render_metric_card("Mortality Diagnostic", "Unavailable", "Requires DO, pH, Temp")
    with t3:
        if "exp3_next_visit_nh3_risk" in results_df and results_df["exp3_next_visit_nh3_risk"].notna().any():
            render_metric_card(
                "Median Next-Visit NH3 Risk",
                format_float(results_df["exp3_next_visit_nh3_risk"].median(), 4),
                "EXPLORATORY (3–45d)",
            )
        else:
            render_metric_card("Next-Visit NH3 Risk", "Unavailable", "Requires DO, pH, Temp")

    # Section C: DO & Hypoxia + Growth & Feeding
    st.markdown("### DO Benchmark, Growth Persistence & Feeding Advisory")
    g1, g2, g3 = st.columns(3)
    with g1:
        if "exp5_benchmark_next_do_mg_l" in results_df and results_df["exp5_benchmark_next_do_mg_l"].notna().any():
            render_metric_card(
                "Constant Mean DO Benchmark",
                format_float(results_df["exp5_benchmark_next_do_mg_l"].iloc[0], 2, "mg/L"),
                "Constant historical benchmark (NOT dynamic)",
            )
        else:
            render_metric_card("DO Benchmark", "Unavailable", "Requires DO (mg/L)")
    with g2:
        if "exp4_persistence_next_weight_g" in results_df and results_df["exp4_persistence_next_weight_g"].notna().any():
            render_metric_card(
                "Median Next-Visit Cohort Weight",
                format_float(results_df["exp4_persistence_next_weight_g"].median(), 1, "g/fish"),
                "Persistence W(t+1)=W(t) (NOT harvest yield)",
            )
        else:
            render_metric_card("Cohort Weight Persistence", "Unavailable", "Requires Avg Fish Weight (g)")
    with g3:
        if "recommended_feed_kg" in results_df and results_df["recommended_feed_kg"].notna().any():
            render_metric_card(
                "Median Provisional Feed",
                format_float(results_df["recommended_feed_kg"].median(), 2, "kg/day"),
                "Provisional heuristic (no auto control)",
            )
        else:
            render_metric_card("Feeding Advisory", "Unavailable", "Requires DO + Feed or Biomass")

    # Pond-Wise Summary & Comparison (when pond_id is available)
    if "pond_id" in results_df.columns and results_df["pond_id"].nunique() > 1:
        st.markdown("### Pond-Wise Summary & Comparison")
        agg_spec = {"records": ("row_index", "count")}
        if "do_mg_l" in results_df:
            agg_spec["median_do_mg_l"] = ("do_mg_l", "median")
        if "emerson_nh3_mg_l" in results_df:
            agg_spec["median_nh3_mg_l"] = ("emerson_nh3_mg_l", "median")
        if "exp2_mortality_risk_score" in results_df:
            agg_spec["median_mortality_score"] = ("exp2_mortality_risk_score", "median")
        if "exp3_next_visit_nh3_risk" in results_df:
            agg_spec["median_next_visit_risk"] = ("exp3_next_visit_nh3_risk", "median")
        if "recommended_feed_kg" in results_df:
            agg_spec["median_feed_kg"] = ("recommended_feed_kg", "median")
        pond_summary = results_df.groupby("pond_id", as_index=False).agg(**agg_spec)
        st.dataframe(pond_summary, use_container_width=True, hide_index=True)
        if "median_do_mg_l" in pond_summary.columns:
            fig_p = px.bar(
                pond_summary.sort_values("median_do_mg_l").head(20),
                x="pond_id",
                y="median_do_mg_l",
                title="Uploaded Pond Comparison — Median Dissolved Oxygen (mg/L)",
                labels={"pond_id": "Pond ID", "median_do_mg_l": "Median DO (mg/L)"},
            )
            fig_p.update_traces(marker_color=PALETTE["teal_primary"])
            fig_p.update_layout(template="plotly_white", height=270, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_p, use_container_width=True)

    # Explainable Input-Factor Summary (Transparent Chemistry & Rule Factors)
    with st.expander("Explainable Input-Factor Summary (Chemistry & Rule Factors)", expanded=False):
        st.caption(
            "Note: SHAP/LIME feature attributions are not implemented in the saved model wrappers. "
            "Explanations below reflect exact deterministic chemistry and feeding-rule factors."
        )
        if {"ph", "temp_c"}.issubset(results_df.columns):
            st.markdown(
                f"- **Emerson NH3 Drivers:** Uploaded median `pH = {format_float(results_df['ph'].median(), 2)}` and "
                f"`Temp = {format_float(results_df['temp_c'].median(), 1, '°C')}` determine the un-ionized NH3 equilibrium fraction."
            )
        if "feeding_action" in results_df.columns:
            action_counts = results_df["feeding_action"].value_counts().to_dict()
            st.markdown(f"- **Feeding Rule Action Distribution:** `{action_counts}`")

    # Detailed Table + Download
    st.markdown("### Row-Level Results & Export")
    st.dataframe(results_df.head(100), use_container_width=True, hide_index=True)

    csv_bytes = results_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Analysis Results (CSV)",
        data=csv_bytes,
        file_name="precision_aquadss_upload_analysis.csv",
        mime="text/csv",
        key="download_upload_results_btn",
    )


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
