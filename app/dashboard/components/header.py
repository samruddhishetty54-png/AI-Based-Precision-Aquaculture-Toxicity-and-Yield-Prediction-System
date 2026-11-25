"""Header and section panel components for dashboard pages."""

import base64
from pathlib import Path
import streamlit as st
from app.dashboard.utils.helpers import CATEGORIES

_ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


@st.cache_data(show_spinner=False)
def get_asset_base64(filename: str) -> str:
    """Load an image asset as a base64 string for crisp local embedding."""
    path = _ASSETS_DIR / filename
    if not path.exists():
        return ""
    return base64.b64encode(path.read_bytes()).decode("ascii")


def render_page_header(
    title: str,
    subtitle: str,
    category_key: str,
) -> None:
    """Render consistent Deep Ocean + Emerald Aqua SaaS header with breadcrumb, fish-wave banner, and badge."""
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

    banner_b64 = get_asset_base64("header_fish_banner.jpg")
    bg_style = (
        f"background: linear-gradient(90deg, rgba(255,255,255,0.96) 0%, rgba(241,247,246,0.90) 58%, rgba(227,245,243,0.45) 100%), "
        f"url('data:image/jpeg;base64,{banner_b64}') right center / cover no-repeat !important;"
        if banner_b64
        else "background: linear-gradient(135deg, #FFFFFF 0%, #F1F7F6 60%, #E0F2F1 100%) !important;"
    )

    droplet_svg = (
        '<svg viewBox="0 0 36 36" width="34" height="34" style="flex-shrink:0; margin-top:2px;">'
        '<defs><linearGradient id="dropG" x1="0%" y1="0%" x2="100%" y2="100%">'
        '<stop offset="0%" stop-color="#43BFC0"/><stop offset="100%" stop-color="#0284C7"/>'
        '</linearGradient></defs>'
        '<path d="M18 3 C18 3 7 15.5 7 22.5 C7 28.6 11.9 33 18 33 C24.1 33 29 28.6 29 22.5 C29 15.5 18 3 18 3 Z" fill="url(#dropG)"/>'
        '<path d="M13.5 22 C13.5 25.5 15.5 27.5 17.5 28" stroke="#FFFFFF" stroke-width="2" fill="none" stroke-linecap="round" opacity="0.75"/>'
        '</svg>'
    )

    header_html = (
        f'<div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:0.5rem; margin-bottom:0.5rem;">'
        f'<div class="aqua-breadcrumb" style="margin-bottom:0;">'
        f'<span>🏠 Precision AquaDSS</span><span>›</span><strong>{title}</strong>'
        f'</div>'
        f'{badge_html}'
        f'</div>'
        f'<div class="aquaculture-header" style="{bg_style} position:relative; overflow:hidden;">'
        f'<div style="position:relative; z-index:1; display:flex; align-items:flex-start; gap:0.75rem; max-width:72%;">'
        f'{droplet_svg}'
        f'<div style="min-width:0; flex:1;">'
        f'<h1 class="hero-title">{title}</h1>'
        f'<p class="hero-subtitle">{subtitle}</p>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)


def render_section_bar(title: str) -> None:
    """Render a consistent Deep Ocean to Emerald Teal section header bar."""
    st.markdown(f'<div class="aqua-panel-bar">{title}</div>', unsafe_allow_html=True)
