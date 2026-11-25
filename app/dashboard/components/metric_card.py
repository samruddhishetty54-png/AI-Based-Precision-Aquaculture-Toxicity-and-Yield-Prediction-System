"""Professional metric card component for aquaculture indicators."""

from typing import Optional
import streamlit as st


_ACCENT_STYLES = {
    "aqua": ("#43BFC0", "#E3F5F3", "#087F72"),
    "teal": ("#087F72", "#E3F5F3", "#087F72"),
    "success": ("#269B72", "#E3F6EE", "#269B72"),
    "warning": ("#E7A23B", "#FFF8EB", "#B97A12"),
    "danger": ("#D9534F", "#FDECEB", "#D9534F"),
}


def render_metric_card(
    title: str,
    value: str,
    subtitle: Optional[str] = None,
    benchmark_ref: Optional[str] = None,
    icon: Optional[str] = None,
    accent: str = "aqua",
) -> None:
    """Render a clean, modern card container displaying a single key metric."""
    border_color, icon_bg, icon_fg = _ACCENT_STYLES.get(accent, _ACCENT_STYLES["aqua"])
    sub_html = f'<div class="aqua-metric-subtitle">{subtitle}</div>' if subtitle else ""
    ref_html = (
        f'<div style="font-size: 0.72rem; color: #526873; font-weight: 500; margin-top: 0.35rem; '
        f'border-top: 1px dashed #DCE9E6; padding-top: 0.3rem;"><em>Benchmark: {benchmark_ref}</em></div>'
        if benchmark_ref
        else ""
    )
    icon_html = (
        f'<div style="width: 34px; height: 34px; border-radius: 10px; background-color: {icon_bg}; '
        f'color: {icon_fg}; display: flex; align-items: center; justify-content: center; '
        f'font-size: 1.05rem; flex-shrink: 0; border: 1px solid #DCE9E6;">{icon}</div>'
        if icon
        else ""
    )

    # Keep HTML flush-left (no 4-space indentation) so CommonMark never parses inner tags as a code block
    card_html = (
        f'<div class="aqua-metric-card" style="border-bottom: 3px solid {border_color};">'
        f'<div style="display: flex; align-items: flex-start; gap: 0.7rem;">'
        f'{icon_html}'
        f'<div style="min-width: 0; flex: 1;">'
        f'<div class="aqua-metric-title">{title}</div>'
        f'<div class="aqua-metric-value">{value}</div>'
        f'{sub_html}'
        f'</div>'
        f'</div>'
        f'{ref_html}'
        f'</div>'
    )
    st.markdown(card_html, unsafe_allow_html=True)
