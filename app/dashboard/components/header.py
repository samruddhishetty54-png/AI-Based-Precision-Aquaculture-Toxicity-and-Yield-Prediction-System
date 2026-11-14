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
    <div class="aquaculture-header" style="box-sizing: border-box; width: 100%; max-width: 100%; overflow: hidden;">
        <h1 class="hero-title" style="color: #ffffff !important; -webkit-text-fill-color: #ffffff !important; margin: 0; font-size: 1.85rem; font-weight: 800; letter-spacing: -0.02em; line-height: 1.25; text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);">{title}</h1>
        <p class="hero-subtitle" style="color: #f8fafc !important; -webkit-text-fill-color: #f8fafc !important; font-size: 0.95rem; margin: 0.4rem 0 0 0; font-weight: 400; line-height: 1.4;">{subtitle}</p>
        <div style="margin-top: 0.6rem; display: flex; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
            {badge_html}
            <span style="font-size: 0.82rem; color: #e2e8f0; font-weight: 500;">
                {cat_info["description"]}
            </span>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

