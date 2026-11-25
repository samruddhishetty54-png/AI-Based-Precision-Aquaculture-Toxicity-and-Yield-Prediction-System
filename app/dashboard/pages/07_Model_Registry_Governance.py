"""Page 7: System Status & Technical Governance.

Operational Category: BENCHMARK (System Status, Module Availability & Technical Reference).
Provides:
1. Compact System Status summary (Model availability, Analysis modules, Dataset status, Last session analysis).
2. Concise operational limitations for organization users.
3. Collapsed technical documentation (holdout benchmarks, feeding rules, guardrails, equations, SHA-256 audit).
"""

import hashlib
from pathlib import Path
from typing import Dict, List
import pandas as pd
import streamlit as st

from app.core.data_manager import DATASET_METADATA
from app.dashboard.components.banners import render_decision_support_banner
from app.dashboard.components.header import render_page_header, render_section_bar
from app.dashboard.components.metric_card import render_metric_card
from app.dashboard.components.registry_status import render_registry_status_bar
from app.dashboard.utils.helpers import get_registry_health_summary
from app.dashboard.utils.styles import inject_custom_css
from app.models.registry import get_model_registry

# Audited baseline SHA-256 hashes for datasets (processed_data_v2/)
AUDITED_DATASET_HASHES: Dict[str, str] = {
    "processed_data_v2/dropouts_v2.csv": "12b7e730aac7ae9e4eed0b89d3a98489ac6cd3c72d55cd4f9b4e3d6dd424d250",
    "processed_data_v2/enrolled_ponds_v2.csv": "94dae8de04c53891af6550afa39a8df8920b67f4b347d01cf9aa5f73aaa16e57",
    "processed_data_v2/feeding_analysis_v2.csv": "c6cf43d6449d81ed7d591f4bbcf5a74a880a6c0f89bcda126f065921a5b3a582",
    "processed_data_v2/fish_health_growth_analysis_v2.csv": "2ed226697d2b7999e3b15b1604ac574b005144598f6cf35fbacf8b7ba2f0023f",
    "processed_data_v2/iot_water_model_v2.csv": "4a577164b2836ffb77ab2f102eea2c8ab5a9898d88590c3cf969808b370ea5af",
    "processed_data_v2/preprocessing_v2_report.json": "b163443291beccefea488270e7dde780d20aad806ab95cd1b1f59ec5d6205333",
    "processed_data_v2/preprocessing_v2_report.md": "66775bbf0ee2a5c423f5d9e372cd0692cff432908d03f476a0e49c6c2323058c",
    "processed_data_v2/thresholds_config.json": "7aad8fc6df5cebfb311b0ca97d6764f25eb313c35814740ad0d8e6953cad3e94",
    "processed_data_v2/toxicity_analysis_v2.csv": "073f5ab11da085160dcb0821e4a16533d96555f8587261c0bd348f385c60c462",
    "processed_data_v2/water_quality_cleaned_v2.csv": "500b2d6fd032eeabb6d1b947dbc6d93b4464c146d41d9e91f4a0367f54f50e1b",
}

# Audited baseline SHA-256 hashes for pre-trained model pipelines (.joblib)
AUDITED_MODEL_HASHES: Dict[str, str] = {
    "baseline_toxicity_v1/models/experiment_1_rf_pipeline.joblib": "e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a",
    "experiment_1_sensor_ablation_v1/models/model_a_rf_pipeline.joblib": "e82656a66eecb47ae9538373ef51aa29070ec3de662d6d211ec5d0ba1b0e932a",
    "experiment_1_sensor_ablation_v1/models/model_b_rf_pipeline.joblib": "08907e58a01036eaadb44b6c10370e0219b920ddaa07279504b6e101a0f4a281",
    "experiment_2_mortality_v1/models/dummy_prior_pipeline.joblib": "c6259edd0a0908614ba93b3faa78256359098c4461576ec08d40ae46714985fa",
    "experiment_2_mortality_v1/models/logistic_regression_pipeline.joblib": "02c8a34ae4ff8b8d907beeed18be4ecd00bb463cd204e8298163f6864afcdadf",
    "experiment_2_mortality_v1/models/random_forest_pipeline.joblib": "464344d33ffc3cff26726bfa15ec73d6b8a59b773ae61083db3d3082f44b4216",
    "experiment_3_next_visit_risk_v1/models/dummy_prior_pipeline.joblib": "2a51e871bbf2fa4d0d5f7a3c1f0dcbfc49499418383cc887514112bf8fa0de8b",
    "experiment_3_next_visit_risk_v1/models/logistic_regression_pipeline.joblib": "957aea9b8cd0066e364c776c76b12128b7b8e63cafe9800cbda39a03d8486ad7",
    "experiment_3_next_visit_risk_v1/models/random_forest_pipeline.joblib": "2f7980756c02a5fa00e325919944c8dd416456d785af9f110135e10edd38853c",
}


def _compute_sha256(filepath: Path) -> str:
    """Safely compute SHA-256 hash of a file."""
    if not filepath.exists():
        return "FILE_NOT_FOUND"
    return hashlib.sha256(filepath.read_bytes()).hexdigest()


def render_page() -> None:
    """Render the compact System Status & Technical Governance page."""
    inject_custom_css()

    render_page_header(
        title="System Status & Operational Governance",
        subtitle="Model availability, active analysis modules, dataset readiness, and operational boundaries.",
        category_key="BENCHMARK",
    )

    render_decision_support_banner()

    registry = get_model_registry()
    health = get_registry_health_summary(registry)
    total_models = health.get("total_models", len(registry.list_models()))
    ready_models = health.get("ready_count", total_models)

    repo_root = Path(__file__).resolve().parent.parent.parent
    available_datasets = sum(
        1 for rel in AUDITED_DATASET_HASHES if rel.endswith(".csv") and (repo_root / rel).exists()
    )
    total_csv_datasets = sum(1 for rel in AUDITED_DATASET_HASHES if rel.endswith(".csv"))

    uploaded_state = st.session_state.get("uploaded_analysis_state")
    results_state = st.session_state.get("uploaded_results_state")
    if results_state and uploaded_state:
        last_val = uploaded_state.get("filename", "Session CSV")
        last_sub = f"{results_state.get('total_rows', 0)} rows | Scope: {results_state.get('pond_scope', 'All')}"
    elif uploaded_state and uploaded_state.get("is_valid"):
        last_val = uploaded_state.get("filename", "Session CSV")
        last_sub = f"Validated ({uploaded_state.get('total_rows', 0)} rows), analysis pending"
    else:
        last_val = "None in Session"
        last_sub = "Upload a CSV in Import & Analyse"

    # ── Compact System Status KPIs ────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_metric_card(
            title="Model Availability",
            value=f"{ready_models} / {total_models} Ready",
            subtitle="Read-only verified artifacts",
            benchmark_ref="Zero runtime retraining",
            icon="✅",
            accent="success",
        )
    with k2:
        render_metric_card(
            title="Analysis Modules",
            value="6 Modules Active",
            subtitle="Chemistry, Risk, DO, Weight, Feed",
            benchmark_ref="Severe DO Classifier Disabled",
            icon="⚙️",
            accent="teal",
        )
    with k3:
        render_metric_card(
            title="Dataset Status",
            value=f"{available_datasets} / {total_csv_datasets} CSVs",
            subtitle="Historical field & reference sets",
            benchmark_ref="processed_data_v2/",
            icon="🗄️",
            accent="aqua",
        )
    with k4:
        render_metric_card(
            title="Last Session Analysis",
            value=last_val,
            subtitle=last_sub,
            benchmark_ref="Session-isolated",
        )

    # ── Analysis Modules Availability ─────────────────────────────────
    render_section_bar("Available Analysis Modules")
    modules_df = pd.DataFrame([
        {"Module": "Emerson Aqueous Ammonia Chemistry", "Status": "Active (Deterministic)", "Required Inputs": "TAN, pH, Temperature"},
        {"Module": "Ammonia Soft-Sensor Proxy", "Status": "Active (Exploratory)", "Required Inputs": "DO, pH, Temperature"},
        {"Module": "Mortality Risk Diagnostic", "Status": "Active (Advisory)", "Required Inputs": "DO, pH, Temperature"},
        {"Module": "Next-Visit Ammonia Risk Screening", "Status": "Active (Multi-Week)", "Required Inputs": "DO, pH, Temperature"},
        {"Module": "Morning DO Benchmark & Hypoxia Screening", "Status": "Active (Benchmark + Exploratory)", "Required Inputs": "Morning DO"},
        {"Module": "Cohort Fish Weight & Feeding Advisor", "Status": "Active (Persistence + Heuristic)", "Required Inputs": "Fish Weight, DO / Feed"},
    ])
    st.dataframe(modules_df, use_container_width=True, hide_index=True)

    # ── Short Operational Limitations ─────────────────────────────────
    st.subheader("Operational Limitations")
    st.markdown(
        """
        - **Decision-Support Only:** Outputs require qualified human review; no automated aeration, feeding, or pump actuation (`is_automatic_control = False`).
        - **Discrete Morning Sampling:** Historical models reflect routine visits spaced **3 to 45 days** apart during **06:00–08:30 AM**, not continuous live sensors or pre-dawn minimum DO.
        - **Target Scope:** Fish-weight outputs represent pond-cohort average somatic weight (`g/fish`), not total pond biomass or commercial harvest yield (`kg/ha`).
        - **Simulation Quarantine:** Synthetic sandbox outputs are isolated and prohibited for live farm decisions.
        """
    )

    # ── Collapsed Technical Documentation & Audit Reference ───────────
    st.markdown("---")
    with st.expander("Technical Reference: Model Registry & Evaluation Benchmarks", expanded=False):
        render_registry_status_bar(registry)
        registry_models = registry.list_models()
        tabs = st.tabs([f"{i+1}. {k}" for i, k in enumerate(registry_models.keys())])
        for tab, (m_key, m_info) in zip(tabs, registry_models.items()):
            with tab:
                st.markdown(
                    f"**Target:** `{m_info.get('target', 'N/A')}` | "
                    f"**Algorithm:** `{m_info.get('algorithm', 'N/A')}` | "
                    f"**Role:** `{m_info.get('role', 'N/A')}` | "
                    f"**Status:** `{m_info.get('status', 'N/A')}`"
                )
                st.caption(f"Artifact: `{m_info.get('model_path', 'Internal Baseline / Rules')}` — {m_info.get('limitations', 'N/A')}")

        b_col1, b_col2 = st.columns(2)
        with b_col1:
            st.markdown("**Ammonia Soft-Sensor (RF) Benchmarks**")
            st.dataframe(pd.DataFrame([
                {"Metric": "Chronological Holdout MAE", "Value": "0.0528 mg/L"},
                {"Metric": "Chronological Holdout RMSE", "Value": "0.0768 mg/L"},
                {"Metric": "Underprediction (NH3 >= 0.05 mg/L)", "Value": "79.59% (78 / 98 cases)"},
                {"Metric": "Underprediction (NH3 >= 0.10 mg/L)", "Value": "100.00% (33 / 33 cases)"},
                {"Metric": "Operational Classification", "Value": "Exploratory Screening Only"},
            ]), use_container_width=True, hide_index=True)

            st.markdown("**Next-Visit Ammonia Risk (RF) Benchmarks**")
            st.dataframe(pd.DataFrame([
                {"Metric": "Revisit Horizon", "Value": "3 to 45 Days (Median ~21 Days)"},
                {"Metric": "Chronological Holdout ROC-AUC", "Value": "0.6874"},
                {"Metric": "Newly Developed Spikes Detected", "Value": "15 of 54 (27.8% Sensitivity)"},
                {"Metric": "Chronological Holdout Precision", "Value": "26.47%"},
            ]), use_container_width=True, hide_index=True)

            st.markdown("**Next-Visit DO & Hypoxia Benchmarks**")
            st.dataframe(pd.DataFrame([
                {"Metric": "Point Benchmark (Hist Mean DO)", "Value": "3.4984 mg/L (MAE = 0.3963 mg/L)"},
                {"Metric": "Moderate Hypoxia Screening (<3.0)", "Value": "GBDT (p* = 0.090, 50.25% Alarm Rate)"},
                {"Metric": "GBDT False Discovery Rate", "Value": "91.00% (930 False Alarms / 1,022 Alerts)"},
                {"Metric": "Severe Hypoxia Classifier (<2.0)", "Value": "REJECTED AS DEGENERATE (99.56% Alarms)"},
            ]), use_container_width=True, hide_index=True)

        with b_col2:
            st.markdown("**Mortality Diagnostic (Balanced LR) Benchmarks**")
            st.dataframe(pd.DataFrame([
                {"Metric": "Chronological Holdout ROC-AUC", "Value": "0.5917"},
                {"Metric": "Precision-Recall AUC (PR-AUC)", "Value": "0.0499"},
                {"Metric": "True Positive Recall", "Value": "20.45% (9 / 44 mortality events)"},
                {"Metric": "Diagnostic Precision", "Value": "3.81% (9 TP / 236 alerts)"},
                {"Metric": "False Alarm Burden", "Value": "227 False Positives"},
            ]), use_container_width=True, hide_index=True)

            st.markdown("**Cohort Fish Weight (Persistence) Benchmarks**")
            st.dataframe(pd.DataFrame([
                {"Metric": "Persistence Baseline (W_t+1 = W_t)", "Value": "MAE = 93.38 g"},
                {"Metric": "Dynamic Growth Model", "Value": "Rejected (No Validated Dynamics)"},
                {"Metric": "Commercial Harvest Yield", "Value": "DISCLAIMED (Not Total Yield kg/ha)"},
                {"Metric": "Pond Biomass Forecasting", "Value": "DISCLAIMED (Not Total Pond Biomass)"},
            ]), use_container_width=True, hide_index=True)

            st.markdown("**Provisional Feeding Advisor Rule Table**")
            st.dataframe(pd.DataFrame([
                {"Rule Condition": "DO < 2.0 mg/L", "Heuristic Feed Action": "Cease Feeding (100% Reduction)"},
                {"Rule Condition": "2.0 <= DO < 3.0 mg/L", "Heuristic Feed Action": "Substantial Reduction (50% Cut)"},
                {"Rule Condition": "3.0 <= DO < 4.0 mg/L", "Heuristic Feed Action": "Moderate Reduction (20% Cut)"},
                {"Rule Condition": "NH3 >= 0.10 mg/L", "Heuristic Feed Action": "Cease Feeding (100% Reduction)"},
                {"Rule Condition": "NH3 >= 0.05 mg/L", "Heuristic Feed Action": "Substantial Reduction (50% Cut)"},
                {"Rule Condition": "TAN >= 2.0 mg/L", "Heuristic Feed Action": "50% Reduction (Test-Kit Graduation Heuristic)"},
                {"Rule Condition": "Temp < 20°C or > 34°C", "Heuristic Feed Action": "Moderate Reduction (20% Cut)"},
            ]), use_container_width=True, hide_index=True)

    with st.expander("Technical Reference: Operational Guardrails & Boundaries", expanded=False):
        st.markdown(
            """
            - **Decision-Support Only:** The system executes **zero automated control commands** (`is_automatic_control = False`).
            - **No Real-Time Monitoring:** The system does NOT connect to active live IoT sensors or stream real-time telemetry.
            - **Discrete Multi-Week Horizon:** Data represents scheduled routine commercial visits (**3 to 45 days interval**; median ~21 days) with **morning DO observations (06:00–08:30 AM)**.
            - **Not Pre-Dawn Minimum DO:** Morning observations are **NOT verified pre-dawn daily minimum DO**.
            - **Fish Weight Target Scope:** Strictly **next-visit pond-cohort average fish weight (grams/fish)** — **NOT individual fish growth**, **NOT harvest biomass**, and **NOT total commercial harvest yield in kg/ha**.
            - **Application Boundaries vs Biological Safety:** Form entry boundaries are software defensive checks, **NEVER described as validated biological safety thresholds**.
            - **Provisional Feeding Heuristics:** Feeding rules are **provisional decision-support heuristics requiring human verification**; **TAN 2.0 mg/L** is strictly a chemical test-kit graduation, NOT a validated toxicity threshold.
            - **Simulation Isolation:** Synthetic data (`iot_water_model_v2.csv`) is permanently tagged with `status = "SIMULATED_SCENARIO_ONLY"` and `operational_use_permitted = False`.
            """
        )

    with st.expander("Technical Reference: Emerson et al. (1975) Dissociation Equations", expanded=False):
        st.markdown(
            r"""
            Un-ionized ammonia ($\text{NH}_3$) is calculated deterministically from Total Ammonia Nitrogen ($\text{TAN}$),
            water temperature ($T$ in $^\circ\text{C}$), and $\text{pH}$:

            - **Thermodynamic Dissociation Constant ($pK_a$):** $pK_a = 0.09018 + \frac{2729.92}{273.15 + T}$
            - **Un-Ionized Ammonia Fraction ($f$):** $f = \frac{1}{10^{(pK_a - \text{pH})} + 1}$
            - **Molecular Ammonia ($\text{NH}_3$ mg/L):** $\text{NH}_3 = \text{TAN} \times f \times \frac{17.031}{14.007}$
            """
        )

    with st.expander("Technical Reference: Cryptographic SHA-256 Integrity Audit", expanded=False):
        dataset_rows: List[Dict[str, str]] = []
        for rel_path, expected_h in AUDITED_DATASET_HASHES.items():
            actual_h = _compute_sha256(repo_root / rel_path)
            dataset_rows.append({
                "Dataset Artifact": rel_path,
                "Expected SHA-256": expected_h[:16] + "...",
                "Computed SHA-256": actual_h[:16] + "...",
                "Integrity Status": "MATCH (100% Unchanged)" if actual_h == expected_h else "MISMATCH",
            })
        st.dataframe(pd.DataFrame(dataset_rows), use_container_width=True, hide_index=True)

        model_rows: List[Dict[str, str]] = []
        for rel_path, expected_h in AUDITED_MODEL_HASHES.items():
            actual_h = _compute_sha256(repo_root / rel_path)
            model_rows.append({
                "Model Pipeline (.joblib)": rel_path,
                "Expected SHA-256": expected_h[:16] + "...",
                "Computed SHA-256": actual_h[:16] + "...",
                "Integrity Status": "MATCH (100% Unchanged)" if actual_h == expected_h else "MISMATCH",
            })
        st.dataframe(pd.DataFrame(model_rows), use_container_width=True, hide_index=True)


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
