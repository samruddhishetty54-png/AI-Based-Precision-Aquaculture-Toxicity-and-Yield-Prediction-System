"""Page 7: Model Registry Governance & Audit Benchmark Catalog.

Operational Category: BENCHMARK (Model Benchmarks, Disclaimers & Governance Controls).
Provides full scientific transparency:
1. Live ModelRegistry operational status and model metadata.
2. Complete audited holdout benchmark tables for Experiments 1 through 5.
3. Emerson (1975) aqueous ammonia dissociation chemistry formulas.
4. Live cryptographic SHA-256 verification of datasets and pre-trained models.
5. System-wide operational safeguards and governance checklist.
"""

import hashlib
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import streamlit as st

from app.dashboard.utils.styles import inject_custom_css
from app.dashboard.components.header import render_page_header
from app.dashboard.components.banners import render_decision_support_banner
from app.dashboard.components.metric_card import render_metric_card
from app.dashboard.components.registry_status import render_registry_status_bar
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
    """Render the Model Registry Governance & Audit Benchmark Catalog page."""
    inject_custom_css()

    render_page_header(
        title="Model Registry Governance & Audit Benchmark Catalog",
        subtitle="Audited empirical benchmarks, chemical equilibrium equations, and scientific disclosures.",
        category_key="BENCHMARK",
    )

    render_decision_support_banner()

    # Section 1: System Safeguards & Governance Checklist
    st.subheader("1. System Safeguards & Operational Guardrails")
    with st.expander("🛡️ View Complete Operational Guardrails & Limitations", expanded=True):
        st.markdown(
            """
            - **Decision-Support Only:** The system executes **zero automated control commands** (`is_automatic_control = False`). No automated feeding, aeration, or water-exchange actuators.
            - **No Real-Time Monitoring:** The system does NOT connect to active live IoT sensors or stream real-time telemetry. All displayed parameters represent discrete historical inspection visits.
            - **Discrete Multi-Week Horizon:** Data represents scheduled routine commercial visits (**3 to 45 days interval**; median ~21 days) with **morning DO observations (06:00–08:30 AM)**.
            - **Not Pre-Dawn Minimum DO:** Morning observations are **NOT verified pre-dawn daily minimum DO**. All continuous real-time streaming, diurnal cycling, and overnight predictions are strictly disclaimed.
            - **Fish Weight Target Scope:** The target is strictly **next-visit pond-cohort average fish weight (grams/fish)**. It is **NOT individual fish growth**, **NOT harvest biomass**, and **NOT total commercial harvest yield in kg/ha**.
            - **Application Boundaries vs Biological Safety:** Form entry boundaries are software defensive checks to reject numeric corruption; they are **NEVER described as validated biological safety thresholds**.
            - **Provisional Feeding Heuristics:** Feeding rules are **provisional decision-support heuristics requiring human verification**; **TAN 2.0 mg/L** is strictly a chemical test-kit graduation, NOT a validated toxicity threshold.
            - **Simulation Isolation:** Synthetic data (`iot_water_model_v2.csv`) is permanently tagged with `status = "SIMULATED_SCENARIO_ONLY"` and `operational_use_permitted = False`.
            - **Zero Runtime Training:** Pre-trained model artifacts and analytical baselines are loaded strictly read-only.
            """
        )

    # Section 2: Model Registry Operational State
    st.subheader("2. Central Model Registry Operational State")
    registry = get_model_registry()
    render_registry_status_bar(registry)

    registry_models = registry.list_models()
    tabs = st.tabs([f"Model {i+1}: {k}" for i, k in enumerate(registry_models.keys())])
    for tab, (m_key, m_info) in zip(tabs, registry_models.items()):
        with tab:
            st.markdown(f"**Target Variable:** `{m_info.get('target', 'N/A')}`")
            st.markdown(f"**Algorithm / Framework:** `{m_info.get('algorithm', 'N/A')}`")
            st.markdown(f"**Operational Role:** `{m_info.get('role', 'N/A')}`")
            st.markdown(f"**Governance Status:** `{m_info.get('status', 'N/A')}`")
            st.markdown(f"**Artifact Source:** `{m_info.get('model_path', 'Internal Baseline / Rules')}`")
            st.info(f"**Audited Empirical Limitations:**\n{m_info.get('limitations', 'N/A')}")

    # Section 3: Audited Benchmark Reference Tables
    st.subheader("3. Audited Scientific Benchmarks Catalog")
    b_col1, b_col2 = st.columns(2)

    with b_col1:
        st.markdown("#### Experiment 1: Ammonia Soft-Sensor (RF)")
        st.caption("Target: Un-ionized Ammonia ($NH_3$ mg/L) from physical water parameters.")
        exp1_df = pd.DataFrame([
            {"Metric": "Chronological Holdout MAE", "Value": "0.0528 mg/L"},
            {"Metric": "Chronological Holdout RMSE", "Value": "0.0768 mg/L"},
            {"Metric": "Underprediction (NH3 ≥ 0.05 mg/L)", "Value": "79.59% (78 / 98 cases)"},
            {"Metric": "Underprediction (NH3 ≥ 0.10 mg/L)", "Value": "100.00% (33 / 33 cases)"},
            {"Metric": "Underprediction (NH3 ≥ 0.20 mg/L)", "Value": "100.00% (10 / 10 cases)"},
            {"Metric": "Operational Classification", "Value": "Exploratory Screening Only (No Alarms)"},
        ])
        st.table(exp1_df)

        st.markdown("#### Experiment 3: Next-Visit Ammonia Toxicity Risk (RF)")
        st.caption("Target: Ammonia spike occurrence at next routine farm visit (3–45 days).")
        exp3_df = pd.DataFrame([
            {"Metric": "Revisit Horizon", "Value": "3 to 45 Days (Median ~21 Days)"},
            {"Metric": "Chronological Holdout ROC-AUC", "Value": "0.6874"},
            {"Metric": "Total True Positives Detected", "Value": "18 TP"},
            {"Metric": "Newly Developed Spikes Detected", "Value": "15 of 54 (27.8% Sensitivity)"},
            {"Metric": "Chronological Holdout Precision", "Value": "26.47%"},
            {"Metric": "Operational Role", "Value": "Multi-Week Screening (No Hourly Claims)"},
        ])
        st.table(exp3_df)

        st.markdown("#### Experiment 5: Next-Visit DO & Hypoxia (Hist Mean & GBDT)")
        st.caption("Target: Next-visit morning DO observation (06:00–08:30 AM).")
        exp5_df = pd.DataFrame([
            {"Metric": "Point Benchmark (Hist Mean DO)", "Value": "3.4984 mg/L (MAE = 0.3963 mg/L)"},
            {"Metric": "Benchmark Nature", "Value": "Constant Historical Mean (NOT Dynamic Prediction)"},
            {"Metric": "Moderate Hypoxia Screening (<3.0)", "Value": "GBDT (p* = 0.090, 50.25% Alarm Rate)"},
            {"Metric": "GBDT False Discovery Rate", "Value": "91.00% (930 False Alarms / 1,022 Alerts)"},
            {"Metric": "Severe Hypoxia Classifier (<2.0)", "Value": "REJECTED AS DEGENERATE (99.56% Alarms)"},
            {"Metric": "Observation Horizon", "Value": "Morning DO (06:00–08:30 AM, 3–45 Days)"},
        ])
        st.table(exp5_df)

    with b_col2:
        st.markdown("#### Experiment 2: Fish Mortality Diagnostic (Balanced LR)")
        st.caption("Target: Concurrent acute mortality event diagnosis from water conditions.")
        exp2_df = pd.DataFrame([
            {"Metric": "Chronological Holdout ROC-AUC", "Value": "0.5917"},
            {"Metric": "Precision-Recall AUC (PR-AUC)", "Value": "0.0499"},
            {"Metric": "True Positive Recall", "Value": "20.45% (9 / 44 mortality events)"},
            {"Metric": "Diagnostic Precision", "Value": "3.81% (9 TP / 236 alerts)"},
            {"Metric": "False Alarm Burden", "Value": "227 False Positives"},
            {"Metric": "Operational Classification", "Value": "Advisory Diagnostic (No Automated Alarm)"},
        ])
        st.table(exp2_df)

        st.markdown("#### Experiment 4: Next-Visit Cohort Fish Weight (Persistence)")
        st.caption("Target: Next-visit pond-cohort average fish weight (grams/fish).")
        exp4_df = pd.DataFrame([
            {"Metric": "Persistence Baseline (W_t+1 = W_t)", "Value": "MAE = 93.38 g"},
            {"Metric": "Baseline Role", "Value": "Analytical Reference Standard"},
            {"Metric": "Dynamic Growth Model", "Value": "Rejected (No Validated Dynamics)"},
            {"Metric": "Commercial Harvest Yield", "Value": "DISCLAIMED (Not Total Yield kg/ha)"},
            {"Metric": "Pond Biomass Forecasting", "Value": "DISCLAIMED (Not Total Pond Biomass)"},
            {"Metric": "Biological Entity", "Value": "Cohort Average Somatic Weight per Fish"},
        ])
        st.table(exp4_df)

        st.markdown("#### Provisional Rule-Based Feeding Advisor")
        st.caption("Heuristic adjustments to mitigate biological oxygen demand (BOD).")
        feed_df = pd.DataFrame([
            {"Rule Condition", "Heuristic Feed Action"},
            {"DO < 2.0 mg/L", "Cease Feeding (100% Reduction, Critical Hypoxia)"},
            {"2.0 ≤ DO < 3.0 mg/L", "Substantial Reduction (50% Cut, Moderate Hypoxia)"},
            {"3.0 ≤ DO < 4.0 mg/L", "Moderate Reduction (20% Cut)"},
            {"NH3 ≥ 0.10 mg/L", "Cease Feeding (100% Reduction, Severe Toxicity)"},
            {"NH3 ≥ 0.05 mg/L", "Substantial Reduction (50% Cut)"},
            {"TAN ≥ 2.0 mg/L", "50% Reduction (Chemical Test-Kit Graduation Heuristic)"},
            {"Temp < 20°C or > 34°C", "Moderate Reduction (20% Cut, Thermal Stress)"},
            {"Causality Note", "Feed cut mitigates BOD; DOES NOT cure hypoxia directly"},
        ])
        st.table(feed_df)

    # Section 4: Chemical Formulations Reference
    st.subheader("4. Chemical Formulations Reference (Aqueous Ammonia)")
    with st.expander("🧪 Emerson et al. (1975) Aqueous Ammonia Dissociation Equations", expanded=False):
        st.markdown(
            r"""
            Un-ionized ammonia ($\text{NH}_3$) is calculated deterministically from Total Ammonia Nitrogen ($\text{TAN}$),
            water temperature ($T$ in $^\circ\text{C}$), and $\text{pH}$ using the Emerson et al. (1975) dissociation model:

            **1. Thermodynamic Dissociation Constant ($pK_a$):**
            $$pK_a = 0.09018 + \frac{2729.92}{273.15 + T}$$

            **2. Un-Ionized Ammonia Fraction ($f$):**
            $$f = \frac{1}{10^{(pK_a - \text{pH})} + 1}$$

            **3. Molecular Ammonia Concentration ($\text{NH}_3$ in mg/L):**
            $$\text{NH}_3\text{ (mg/L)} = \text{TAN (mg/L)} \times f \times \frac{17.031}{14.007}$$

            *Note: The molecular weight ratio $\frac{17.031}{14.007} \approx 1.2159$ converts nitrogen-basis ($\text{NH}_3\text{-N}$) to toxic molecular ammonia ($\text{NH}_3$).*
            *Scientific Disclaimer: The value **$2.0\text{ mg/L TAN}$** represents a common chemical test-kit graduation mark, NOT a validated biological toxicity threshold.*
            """
        )

    # Section 5: Cryptographic SHA-256 Immutability Audit Table
    st.subheader("5. Cryptographic SHA-256 Immutability Audit")
    st.caption("Live cryptographic hash verification against audited pre-Phase-4 baselines.")

    repo_root = Path(__file__).resolve().parent.parent.parent

    # Dataset Hashes
    dataset_rows: List[Dict[str, str]] = []
    for rel_path, expected_h in AUDITED_DATASET_HASHES.items():
        full_p = repo_root / rel_path
        actual_h = _compute_sha256(full_p)
        status = "MATCH (100% Unchanged)" if actual_h == expected_h else "MISMATCH"
        dataset_rows.append({
            "Dataset Artifact": rel_path,
            "Expected SHA-256 Hash": expected_h[:16] + "...",
            "Computed SHA-256 Hash": actual_h[:16] + "...",
            "Integrity Status": status,
        })
    st.markdown("**Cleaned Datasets (`processed_data_v2/`):**")
    st.dataframe(pd.DataFrame(dataset_rows), use_container_width=True)

    # Model Hashes
    model_rows: List[Dict[str, str]] = []
    for rel_path, expected_h in AUDITED_MODEL_HASHES.items():
        full_p = repo_root / rel_path
        actual_h = _compute_sha256(full_p)
        status = "MATCH (100% Unchanged)" if actual_h == expected_h else "MISMATCH"
        model_rows.append({
            "Model Pipeline (.joblib)": rel_path,
            "Expected SHA-256 Hash": expected_h[:16] + "...",
            "Computed SHA-256 Hash": actual_h[:16] + "...",
            "Integrity Status": status,
        })
    st.markdown("**Pre-Trained Model Artifacts (`.joblib`):**")
    st.dataframe(pd.DataFrame(model_rows), use_container_width=True)


if __name__ == "__main__" or "streamlit" in __name__:
    render_page()
