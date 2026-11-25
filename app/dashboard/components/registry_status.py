"""Model Registry status bar component."""

import textwrap
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

    status_badge_bg = "#E3F6EE" if status == "HEALTHY" else "#FFF8EB"
    status_badge_text = "#269B72" if status == "HEALTHY" else "#9A6411"
    status_badge_border = "#A6DEC8" if status == "HEALTHY" else "#F3D396"

    st.markdown(
        textwrap.dedent(f"""
        <div style="background-color: #FFFFFF; border: 1px solid #DCE9E6; border-radius: 10px; padding: 0.75rem 1rem; margin-bottom: 0.85rem; box-shadow: 0 1px 4px rgba(16,44,58,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                <div style="display: flex; align-items: center; gap: 0.6rem;">
                    <span style="font-weight: 700; font-size: 0.88rem; color: #173747;">
                        Model Registry Status
                    </span>
                    <span style="background-color: {status_badge_bg}; color: {status_badge_text}; border: 1px solid {status_badge_border}; font-size: 0.72rem; font-weight: 700; padding: 0.15rem 0.55rem; border-radius: 9999px;">
                        {status} ({ready_count}/{total_count} operational)
                    </span>
                </div>
                <span style="font-size: 0.76rem; color: #526873; font-weight: 500;">
                    Read-only artifacts • Zero runtime retraining
                </span>
            </div>
        </div>
        """).strip(),
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
                    textwrap.dedent(f"""
                    <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.5rem 0.4rem; text-align: center; box-shadow: 0 1px 2px rgba(0,0,0,0.02);">
                        <div style="font-size: 0.72rem; font-weight: 700; color: #334155; margin-bottom: 0.25rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{model_name}">
                            {model_name}
                        </div>
                        <span class="{pill_class}">{pill_text}</span>
                    </div>
                    """).strip(),
                    unsafe_allow_html=True,
                )
