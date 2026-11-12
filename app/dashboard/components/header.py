"""Header component for dashboard pages."""

import streamlit as st
from app.dashboard.utils.helpers import CATEGORIES


def render_page_header(
    title: str,
    subtitle: str,
    category_key: str,
) -> None:
    """Render consistent branded header banner with category badge."""
    cat_info = CATEGORIES.get(category_key, {
        "label": category_key,
        "description": "",
        "badge_class": "category-benchmark",
    })

    badge_html = (
        f'<span class="category-badge {cat_info["badge_class"]}">'
        f'{cat_info["label"]}'
        f'</span>'
    )

    header_html = f"""
    <div class="aquaculture-header">
        <h1>{title}</h1>
        <p>{subtitle}</p>
        <div style="margin-top: 0.6rem;">
            {badge_html}
            <span style="font-size: 0.8rem; color: #cbd5e1; margin-left: 0.5rem;">
                {cat_info["description"]}
            </span>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

