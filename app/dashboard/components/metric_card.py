"""Professional metric card component for aquaculture indicators."""

from typing import Optional
import streamlit as st


def render_metric_card(
    title: str,
    value: str,
    subtitle: Optional[str] = None,
    benchmark_ref: Optional[str] = None,
) -> None:
    """Render a clean, modern card container displaying a single key metric."""
    sub_html = f'<div class="aqua-metric-subtitle">{subtitle}</div>' if subtitle else ""
    ref_html = (
        f'<div style="font-size: 0.75rem; color: #334155; font-weight: 500; margin-top: 0.25rem;">'
        f'<em>Benchmark: {benchmark_ref}</em>'
        f'</div>'
        if benchmark_ref
        else ""
    )

    card_html = f"""
    <div class="aqua-metric-card">
        <div class="aqua-metric-title">{title}</div>
        <div class="aqua-metric-value">{value}</div>
        {sub_html}
        {ref_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

