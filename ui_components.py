"""
Shared UI design-system components for the Streamlit app.
Provides icons, badges, stat cards, nav buttons, and theme injection so
every page renders with a consistent look instead of hand-rolled markup.
"""

import streamlit as st

ICONS = {
    "dashboard": ":material/bar_chart:",
    "news": ":material/news:",
    "chat": ":material/chat:",
    "settings": ":material/settings:",
    "portfolio": ":material/trending_up:",
    "refresh": ":material/refresh:",
    "delete": ":material/delete:",
    "clean": ":material/cleaning_services:",
    "build": ":material/build:",
    "check": ":material/check_circle:",
    "cancel": ":material/cancel:",
    "link": ":material/link:",
    "sources": ":material/menu_book:",
    "warning": ":material/warning:",
    "add": ":material/add_circle:",
    "history": ":material/history:",
    "database": ":material/database:",
    "tune": ":material/tune:",
    "status": ":material/monitor_heart:",
    "price_chart": ":material/show_chart:",
    "movers": ":material/leaderboard:",
}

_BADGE_COLORS = {
    "success": {"bg": "var(--app-success-bg)", "fg": "var(--app-success-fg)"},
    "danger": {"bg": "var(--app-danger-bg)", "fg": "var(--app-danger-fg)"},
    "neutral": {"bg": "var(--app-neutral-bg)", "fg": "var(--app-neutral-fg)"},
    "info": {"bg": "var(--app-info-bg)", "fg": "var(--app-info-fg)"},
}


def section_header(text: str, icon_key: str = None):
    """Render a subheader with a Material icon prefix instead of an emoji."""
    icon = ICONS.get(icon_key, "")
    st.subheader(f"{icon} {text}".strip())


def badge(text: str, kind: str = "neutral", icon_key: str = None):
    """Render a colored pill badge. kind: success | danger | neutral | info."""
    colors = _BADGE_COLORS.get(kind, _BADGE_COLORS["neutral"])
    icon = ICONS.get(icon_key, "")
    label = f"{icon} {text}".strip()
    st.markdown(
        f"<span class='app-badge' style='background-color:{colors['bg']}; "
        f"color:{colors['fg']};'>{label}</span>",
        unsafe_allow_html=True,
    )


def stat_card(label: str, value, delta=None, icon_key: str = None):
    """Render an st.metric with an icon-prefixed label for visual consistency."""
    icon = ICONS.get(icon_key, "")
    st.metric(label=f"{icon} {label}".strip(), value=value, delta=delta)


def nav_button(label: str, icon_key: str, page_key: str, active_page: str) -> bool:
    """Render one sidebar nav item; returns True if it was just clicked."""
    icon = ICONS.get(icon_key, "")
    is_active = page_key == active_page
    return st.button(
        f"{icon}  {label}",
        key=f"nav_{page_key}",
        type="primary" if is_active else "secondary",
        use_container_width=True,
    )


def inject_theme_css(dark_mode: bool):
    """Inject CSS custom properties + overrides for a real runtime light/dark toggle."""
    if dark_mode:
        tokens = """
            --app-bg: #121110;
            --app-surface: #1C1A18;
            --app-surface-hover: #24211E;
            --app-border: #332F2B;
            --app-text: #F5F1EB;
            --app-text-muted: #A8A29A;
            --app-primary: #FBBF24;
            --app-primary-text: #1C1917;
            --app-primary-hover: #F59E0B;
            --app-success-bg: #123420; --app-success-fg: #22C55E;
            --app-danger-bg: #3A1212;  --app-danger-fg: #F87171;
            --app-neutral-bg: #221F1C; --app-neutral-fg: #A8A29A;
            --app-info-bg: #0B2A38;    --app-info-fg: #38BDF8;
        """
    else:
        tokens = """
            --app-bg: #FFFFFF;
            --app-surface: #FAF9F6;
            --app-surface-hover: #F3F0EA;
            --app-border: #E7E2D9;
            --app-text: #1C1917;
            --app-text-muted: #78716C;
            --app-primary: #D97706;
            --app-primary-text: #1C1917;
            --app-primary-hover: #B45309;
            --app-success-bg: #EAF7EE; --app-success-fg: #16A34A;
            --app-danger-bg: #FDECEC;  --app-danger-fg: #DC2626;
            --app-neutral-bg: #F3F1EE; --app-neutral-fg: #6B6357;
            --app-info-bg: #E6F6FC;    --app-info-fg: #0EA5E9;
        """

    st.markdown(
        f"""
        <style>
        :root {{
            {tokens}
        }}

        html, body, [data-testid="stApp"] {{
            background-color: var(--app-bg);
        }}

        [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stBottom"],
        [data-testid="stBottomBlockContainer"], [data-testid="stBottomBlockContainer"] > div {{
            background-color: var(--app-bg);
            color: var(--app-text);
        }}

        [data-testid="stSidebar"] {{
            background-color: var(--app-surface);
            border-right: 1px solid var(--app-border);
        }}

        [data-testid="stAppViewContainer"] * ,
        [data-testid="stSidebar"] * {{
            color: var(--app-text);
        }}

        button[kind="primary"], [data-testid="stBaseButton-primary"] {{
            background-color: var(--app-primary) !important;
            color: var(--app-primary-text) !important;
            border: 1px solid var(--app-primary) !important;
        }}
        button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover {{
            background-color: var(--app-primary-hover) !important;
            border-color: var(--app-primary-hover) !important;
            color: var(--app-primary-text) !important;
        }}
        button[kind="secondary"], [data-testid="stBaseButton-secondary"] {{
            background-color: var(--app-surface) !important;
            color: var(--app-text) !important;
            border: 1px solid var(--app-border) !important;
        }}
        button[kind="secondary"]:hover, [data-testid="stBaseButton-secondary"]:hover {{
            background-color: var(--app-surface-hover) !important;
            border-color: var(--app-primary) !important;
            color: var(--app-primary) !important;
        }}
        button[kind="primary"] p, button[kind="secondary"] p,
        [data-testid="stBaseButton-primary"] p, [data-testid="stBaseButton-secondary"] p {{
            color: inherit !important;
        }}

        /* Text inputs, selectboxes, sliders, and the chat input all use
           BaseWeb/react-aria internals with their own hardcoded colors that
           the wildcard text-color rule above doesn't reliably win against -
           override each one explicitly so typed/selected values stay legible. */
        [data-testid="stTextInputRootElement"],
        [data-testid="stSelectbox"] [role="group"],
        [data-testid="stChatInput"], [data-testid="stChatInput"] > div {{
            background-color: var(--app-surface) !important;
            border: 1px solid var(--app-border) !important;
        }}
        [data-testid="stTextInputField"],
        [data-testid="stSelectbox"] input,
        [data-testid="stChatInputTextArea"] {{
            background-color: transparent !important;
            color: var(--app-text) !important;
            caret-color: var(--app-text) !important;
        }}
        [data-testid="stSelectbox"] button svg,
        [data-testid="stChatInput"] svg {{
            color: var(--app-text) !important;
        }}
        [data-testid="stChatInputSubmitButton"] {{
            background-color: var(--app-primary) !important;
        }}
        [data-testid="stChatInputSubmitButton"] svg {{
            color: var(--app-primary-text) !important;
        }}
        ::placeholder {{
            color: var(--app-text-muted) !important;
            opacity: 1 !important;
        }}

        [data-testid="stMetric"], [data-testid="stExpander"], .app-card {{
            background-color: var(--app-surface);
            border: 1px solid var(--app-border);
            border-radius: 10px;
            padding: 0.6rem 0.9rem;
        }}

        [data-testid="stMetricLabel"] {{
            color: var(--app-text-muted) !important;
        }}

        .app-badge {{
            display: inline-block;
            padding: 3px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        [data-testid="stChatMessage"] {{
            background-color: var(--app-surface);
            border: 1px solid var(--app-border);
            border-radius: 10px;
        }}

        hr {{
            border-color: var(--app-border) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
