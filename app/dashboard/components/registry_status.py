"""Model Registry status bar component."""

from typing import Any
import streamlit as st
from app.dashboard.utils.helpers import get_registry_health_summary


def render_registry_status_bar(registry: Any) -> None:
    """Render dynamic visual status indicators for all registered models."""
    summary = get_registry_health_summary(registry)
    status = summary.get("status", "UNAVAILABLE")
    ready_count = summary.get("ready_count", 0)
    total_count = summary.get("total_count", 0)
    model_health = summary.get("model_health", {})

    status_color = "#0d5c75" if status == "HEALTHY" else "#d97706"

    st.markdown(
        f"""
        <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 1rem;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 600; font-size: 0.85rem; color: #0c2340;">
                    Model Registry Status: <span style="color: {status_color}; font-weight: 700;">{status}</span> ({ready_count}/{total_count} models operational)
                </span>
                <span style="font-size: 0.75rem; color: #1e293b; font-weight: 500;">
                    Read-only artifacts • Zero runtime retraining
                </span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if model_health:
        cols = st.columns(len(model_health))
        for col, (model_name, health_data) in zip(cols, model_health.items()):
            is_loaded = health_data.get("loaded", False)
            pill_text = "READY" if is_loaded else "FAULT ISOLATED"
            pill_class = "health-pill-ready" if is_loaded else "health-pill-isolated"
            with col:
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 0.25rem;">
                        <div style="font-size: 0.75rem; font-weight: 600; color: #334155; margin-bottom: 0.2rem;">
                            {model_name}
                        </div>
                        <span class="{pill_class}">{pill_text}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
