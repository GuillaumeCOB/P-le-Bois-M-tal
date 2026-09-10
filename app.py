
"""
Outil interne de gestion de projets — Pôle BOIS/METAL
Version interface v6 : onglets arrondis, alignements renforcés, entêtes/totaux stabilisés.

Lancement local : streamlit run app.py
"""

import calendar as cal
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from html import escape
import inspect
from pathlib import Path
import re

import pandas as pd
import plotly.express as px
import streamlit as st

import storage as db

st.set_page_config(
    page_title="Builders verticalsea - Gestion de projets",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PATH = None
PRIMARY = "#3B38F5"
PRIMARY_DARK = "#40338C"
SURFACE = "#F5F4F7"
SURFACE_ALT = "#FFFFFF"
TEXT = "#1F2340"
MUTED = "#70759A"
BORDER = "#D8D9E5"
LOGO_PATH = Path(__file__).parent / "assets" / "logo_builders_verticalsea.png"

ROW_WIDTHS = [0.38, 0.78, 2.85, 0.95, 1.55, 1.15, 1.0, 0.95, 0.95, 0.72]
ROW_LABELS = ["", "N°", "Projet", "Type", "Collaborateurs", "Statut", "Échéance", "Budget", "Heures", "Tâches"]
TOTAL_WIDTHS = [0.38, 0.78, 2.85, 0.95, 1.55, 1.15, 1.0, 0.95, 0.95, 0.72]

_HAS_CONTAINER_KEY = "key" in inspect.signature(st.container).parameters


def safe_color(value: str, fallback: str = PRIMARY) -> str:
    return value if isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?", value) else fallback


def hex_to_rgba(value: str, alpha: float) -> str:
    color = safe_color(value)
    color = color.lstrip("#")
    if len(color) == 3:
        color = "".join(ch * 2 for ch in color)
    r = int(color[0:2], 16)
    g = int(color[2:4], 16)
    b = int(color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


@contextmanager
def ui_container(key: str, kinds):
    if isinstance(kinds, str):
        kinds = [kinds]
    options = {"border": False}
    if _HAS_CONTAINER_KEY:
        options["key"] = key
    with st.container(**options):
        for kind in kinds:
            st.markdown(
                f'<span class="pbm-marker pbm-{kind}-marker"></span>',
                unsafe_allow_html=True,
            )
        yield


def css_scope(kind: str) -> str:
    return (
        '[data-testid="stVerticalBlock"]:has(> '
        ':is(.element-container, [data-testid="stElementContainer"]) '
        f'.pbm-{kind}-marker)'
    )


def inject_brand_styles(data: dict):
    board = css_scope("board")
    group = css_scope("group")
    project = css_scope("project")
    row = css_scope("row")
    header = css_scope("header")
    total = css_scope("total")
    children = css_scope("children")
    subrow = css_scope("subrow")
    actionbar = css_scope("actionbar")
    formcard = css_scope("formcard")
    nav = css_scope("nav")

    css = f"""
    :root {{
        --pbm-primary: {PRIMARY};
        --pbm-primary-dark: {PRIMARY_DARK};
        --pbm-surface: {SURFACE};
        --pbm-surface-alt: {SURFACE_ALT};
        --pbm-text: {TEXT};
        --pbm-muted: {MUTED};
        --pbm-border: {BORDER};
    }}
    .stApp {{
        background: linear-gradient(180deg, #ffffff 0%, #fafafe 65%, #f6f6fb 100%);
        color: var(--pbm-text);
    }}
    .block-container {{
        padding-top: 1.1rem;
        padding-bottom: 1.25rem;
        padding-left: 1.25rem;
        padding-right: 1.25rem;
        max-width: none;
    }}
    h1, h2, h3 {{color: var(--pbm-primary-dark); letter-spacing: -0.02em;}}
    h1 {{font-size: 1.55rem !important; padding: 0 !important; margin: 0 !important;}}
    h3 {{font-size: 1rem !important;}}
    {nav} {{
        margin: 0.45rem 0 0.75rem 0;
        padding: 0 !important;
        gap: 0 !important;
    }}
    {nav} [data-testid="stHorizontalBlock"] {{
        gap: 0.55rem !important;
        align-items: center !important;
    }}
    {nav} [data-testid="stButton"] button {{
        min-height: 2.5rem !important;
        height: 2.5rem !important;
        padding: 0 0.9rem !important;
        border-radius: 12px !important;
        border: 1px solid rgba(59, 56, 245, 0.22) !important;
        box-shadow: 0 2px 7px rgba(64, 51, 140, 0.05) !important;
        font-weight: 650 !important;
    }}
    {nav} [data-testid="stButton"] button[kind="secondary"] {{
        background: #ffffff !important;
        color: var(--pbm-text) !important;
    }}
    {nav} [data-testid="stButton"] button[kind="primary"] {{
        background: rgba(59, 56, 245, 0.13) !important;
        color: var(--pbm-primary-dark) !important;
        border-color: rgba(59, 56, 245, 0.38) !important;
    }}
    {nav} [data-testid="stButton"] button p {{
        margin: 0 !important;
        white-space: nowrap !important;
        font-size: 0.88rem !important;
    }}
    :is(.element-container, [data-testid="stElementContainer"]):has(.pbm-marker) {{
        display: none !important;
    }}
    [data-testid="stButton"] button,
    [data-testid="stDownloadButton"] button {{
        border-radius: 10px;
    }}
    .pbm-headline {{display:flex; flex-direction:column; gap:0.15rem;}}
    .pbm-eyebrow {{color: var(--pbm-primary); font-weight: 700; font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.08em;}}
    .pbm-subline {{color: var(--pbm-muted); font-size: 0.85rem;}}
    .pbm-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        height: 27px;
        min-height: 27px;
        max-height: 27px;
        box-sizing: border-box;
        max-width: 100%;
        padding: 0.22rem 0.52rem;
        border-radius: 999px;
        font-size: 0.76rem;
        line-height: 1.25;
        font-weight: 700;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        border: 1px solid rgba(0,0,0,0.04);
    }}
    .pbm-cell {{
        display: flex;
        align-items: center;
        width: 100%;
        height: 34px;
        min-height: 34px;
        max-height: 34px;
        box-sizing: border-box;
        font-size: 0.84rem;
        line-height: 1;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: var(--pbm-text);
        padding: 0 0.28rem;
    }}
    .pbm-cell.number {{justify-content:flex-end; text-align:right; font-variant-numeric: tabular-nums; font-weight: 600;}}
    .pbm-cell.progress {{justify-content:center; text-align:center; opacity: 0.78; font-variant-numeric: tabular-nums;}}
    .pbm-cell.badge-cell {{justify-content:flex-start;}}
    .pbm-cell.center-cell {{justify-content:center;}}
    .pbm-cell.done {{text-decoration: line-through; opacity: 0.6;}}
    .pbm-project-number {{
        display:inline-flex;
        align-items:center;
        height: 27px;
        min-height: 27px;
        max-height: 27px;
        box-sizing: border-box;
        justify-content:center;
        min-width: 2.3rem;
        padding: 0.18rem 0.45rem;
        background: rgba(255,255,255,0.72);
        border: 1px solid rgba(59,56,245,0.16);
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 700;
        color: var(--pbm-primary-dark);
    }}
    .pbm-summary-card {{
        background: rgba(255,255,255,0.75);
        border: 1px solid var(--pbm-border);
        border-radius: 16px;
        padding: 0.85rem 1rem;
    }}
    .pbm-summary-card strong {{color: var(--pbm-primary-dark);}}
    .pbm-summary-label {{font-size:0.76rem; text-transform:uppercase; letter-spacing:0.05em; color:var(--pbm-muted);}}
    .pbm-grid-row {{
        display: grid;
        gap: 8px;
        width: 100%;
        box-sizing: border-box;
        align-items: center;
    }}
    .pbm-grid-cell {{
        display: flex;
        align-items: center;
        min-width: 0;
        min-height: 32px;
        padding: 0.28rem 0.32rem;
        box-sizing: border-box;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        color: var(--pbm-text);
    }}
    .pbm-grid-cell.right {{justify-content: flex-end; text-align: right;}}
    .pbm-grid-cell.center {{justify-content: center; text-align: center;}}
    .pbm-grid-header {{
        min-height: 42px;
        padding: 0.34rem 0.36rem;
        margin: 0.18rem 0 0 !important;
        background: rgba(59,56,245,0.065);
        border: 1px solid rgba(59,56,245,0.14);
        border-radius: 10px;
    }}
    :is(.element-container, [data-testid="stElementContainer"]):has(.pbm-grid-header) {{
        padding-bottom: 12px !important;
        margin-bottom: 0 !important;
    }}
    .pbm-grid-header .pbm-grid-cell {{
        min-height: 30px;
        font-size: 0.73rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--pbm-muted);
    }}
    .pbm-grid-total {{
        min-height: 42px;
        padding: 0.34rem 0.36rem;
        margin: 0.38rem 0 0.12rem;
        background: rgba(59,56,245,0.07);
        border: 1px solid rgba(59,56,245,0.16);
        border-radius: 10px;
    }}
    .pbm-grid-total .pbm-grid-cell {{
        min-height: 30px;
        font-size: 0.82rem;
        font-weight: 700;
        color: var(--pbm-primary-dark);
    }}
    .pbm-header-project-gap {
        display: block;
        width: 100%;
        height: 10px;
        min-height: 10px;
    }
    :is(.element-container, [data-testid="stElementContainer"]):has(.pbm-header-project-gap) {
        height: 10px !important;
        min-height: 10px !important;
        margin: 0 !important;
        padding: 0 !important;
    }

    /* Project rows: use Streamlit's container key class instead of :has() marker scopes.
       This controls the actual row wrapper and avoids the oversized blank vertical space. */
    [class*="st-key-pbm_project_"] {
        margin: 0 0 5px 0 !important;
        padding: 0 !important;
    }
    [class*="st-key-pbm_project_"] > div,
    [class*="st-key-pbm_project_"] [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    [class*="st-key-pbm_row_"] {
        box-sizing: border-box !important;
        min-height: 40px !important;
        height: 40px !important;
        max-height: 40px !important;
        margin: 0 !important;
        padding: 4px 0.34rem !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    [class*="st-key-pbm_row_"] > div,
    [class*="st-key-pbm_row_"] [data-testid="stVerticalBlock"] {
        min-height: 32px !important;
        height: 32px !important;
        max-height: 32px !important;
        gap: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    [class*="st-key-pbm_row_"] [data-testid="stHorizontalBlock"] {
        min-height: 32px !important;
        height: 32px !important;
        max-height: 32px !important;
        gap: 8px !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    [class*="st-key-pbm_row_"] [data-testid="stHorizontalBlock"] > div {
        display: flex !important;
        align-items: center !important;
        min-height: 32px !important;
        height: 32px !important;
        max-height: 32px !important;
        margin: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        overflow: hidden !important;
    }
    [class*="st-key-pbm_row_"] :is(.element-container, [data-testid="stElementContainer"]) {
        display: flex !important;
        align-items: center !important;
        min-height: 32px !important;
        height: 32px !important;
        max-height: 32px !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }
    [class*="st-key-pbm_row_"] .pbm-cell {
        height: 32px !important;
        min-height: 32px !important;
        max-height: 32px !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    [class*="st-key-pbm_row_"] [data-testid="stMarkdownContainer"] {
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        min-height: 32px !important;
        height: 32px !important;
        max-height: 32px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    [class*="st-key-pbm_row_"] [data-testid="stButton"] {
        width: 100% !important;
        min-height: 30px !important;
        height: 30px !important;
        max-height: 30px !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    [class*="st-key-pbm_row_"] [data-testid="stButton"] button {
        min-height: 30px !important;
        height: 30px !important;
        max-height: 30px !important;
        margin: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        display: flex !important;
        align-items: center !important;
    }
    [class*="st-key-pbm_row_"] .pbm-badge,
    [class*="st-key-pbm_row_"] .pbm-project-number {
        height: 25px !important;
        min-height: 25px !important;
        max-height: 25px !important;
    }
    {actionbar} {{
        padding: 0.9rem 1rem 0.7rem;
        margin-bottom: 0.55rem;
        background: rgba(255,255,255,0.84);
        border: 1px solid var(--pbm-border);
        border-radius: 18px;
        box-shadow: 0 8px 28px rgba(64,51,140,0.05);
    }}
    {board} {{gap: 0.45rem !important;}}
    {board} [data-testid="stExpander"] {{
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(64,51,140,0.08);
        background: rgba(255,255,255,0.82);
        box-shadow: 0 10px 30px rgba(64,51,140,0.04);
    }}
    {board} [data-testid="stExpander"] summary {{padding: 0.55rem 0.75rem; min-height: 2.3rem;}}
    {board} [data-testid="stExpanderDetails"] {{padding: 0 0.55rem 0.55rem;}}
    {group}, {project}, {row}, {header}, {children}, {subrow}, {total}, {formcard} {{gap: 0 !important;}}
    {header} {{
        padding: 0.34rem 0.28rem 0.42rem;
        background: rgba(59,56,245,0.05);
        border-radius: 10px;
        border: 1px solid rgba(59,56,245,0.08);
        margin-bottom: 0.55rem;
    }}
    {header} .pbm-cell {{
        font-size: 0.73rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--pbm-muted);
    }}
    {project} {{margin-bottom: 0.28rem;}}
    {row} {{
        padding: 5px 0.34rem !important;
        min-height: 44px !important;
        height: 44px !important;
        box-sizing: border-box;
        border-bottom: 1px solid rgba(64,51,140,0.06);
        border-radius: 12px;
        transition: background 0.15s ease;
        overflow: hidden;
    }}
    {row}:hover {{background: rgba(64,51,140,0.06);}}
    {row} [data-testid="stHorizontalBlock"] {{
        gap: 8px !important;
        align-items: center !important;
        min-height: 34px !important;
        height: 34px !important;
    }}
    {subrow} [data-testid="stHorizontalBlock"] {{gap: 8px !important; align-items: center !important;}}
    {row} [data-testid="stHorizontalBlock"] > div {{
        display: flex !important;
        align-items: center !important;
        justify-content: stretch !important;
        min-height: 34px !important;
        height: 34px !important;
        max-height: 34px !important;
        overflow: hidden !important;
    }}
    {subrow} [data-testid="stHorizontalBlock"] > div {{
        display: flex !important;
        align-items: center !important;
        min-height: 36px !important;
    }}
    {row} [data-testid="stHorizontalBlock"] > div > div,
    {subrow} [data-testid="stHorizontalBlock"] > div > div {{
        width: 100% !important;
    }}
    {row} :is(.element-container, [data-testid="stElementContainer"]) {{
        display: flex !important;
        align-items: center !important;
        min-height: 34px !important;
        height: 34px !important;
        max-height: 34px !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }}
    {row} [data-testid="stMarkdownContainer"] {{
        display: flex !important;
        align-items: center !important;
        width: 100% !important;
        min-height: 34px !important;
        height: 34px !important;
        margin: 0 !important;
        padding: 0 !important;
    }}
    {row} [data-testid="stVerticalBlock"],
    {subrow} [data-testid="stVerticalBlock"] {{gap: 0 !important; min-width: 0;}}
    {row} :is([data-testid="stColumn"], [data-testid="column"]),
    {subrow} :is([data-testid="stColumn"], [data-testid="column"]) {{min-width: 0;}}
    {row} [data-testid="stMarkdownContainer"] p,
    {subrow} [data-testid="stMarkdownContainer"] p {{margin: 0;}}
    {row} [data-testid="stButton"] button,
    {subrow} [data-testid="stButton"] button {{
        min-height: 34px !important;
        height: 34px !important;
        max-height: 34px !important;
        display: flex !important;
        align-items: center !important;
        padding: 0 0.35rem !important;
        border: 1px solid transparent;
        border-radius: 8px;
        background: transparent;
    }}
    {row} [data-testid="stButton"] button:hover,
    {subrow} [data-testid="stButton"] button:hover {{background: rgba(255,255,255,0.5); border-color: rgba(64,51,140,0.08);}}
    {row} [data-testid="stButton"] button p,
    {subrow} [data-testid="stButton"] button p {{
        font-size: 0.84rem;
        line-height: 1.32;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display:block;
        margin:0;
    }}
    {row} [data-testid="stHorizontalBlock"] > :nth-child(3) [data-testid="stButton"] button {{
        justify-content:flex-start;
        text-align:left;
        font-weight: 700;
    }}
    {children} {{
        margin: 0.12rem 0 0.42rem 1.18rem;
        width: calc(100% - 1.18rem);
        padding: 0.2rem 0.62rem 0.42rem 0.72rem;
        border-left: 2px solid rgba(59,56,245,0.22);
        background: rgba(255,255,255,0.58);
        border-radius: 0 0 12px 12px;
    }}
    {subrow} {{
        padding: 0.18rem 0.16rem;
        min-height: 34px;
        border-bottom: 1px solid rgba(64,51,140,0.08);
    }}
    {subrow}:last-child {{border-bottom: none;}}
    {subrow} [data-testid="stCheckbox"] {{min-height: 30px;}}
    {subrow} [data-testid="stCheckbox"] label {{margin: 0; min-height: 30px;}}
    {children} [data-testid="stExpander"] {{border: 0; margin-top: 0.25rem; background: transparent; box-shadow: none;}}
    {children} [data-testid="stExpander"] summary {{padding: 0.18rem 0;}}
    {children} [data-testid="stExpander"] summary p {{font-size: 0.78rem; color: var(--pbm-primary-dark);}}
    {children} [data-testid="stForm"] {{
        padding: 0.6rem;
        background: rgba(59,56,245,0.04);
        border-radius: 12px;
        border: 1px dashed rgba(59,56,245,0.14);
        margin-top: 0.35rem;
    }}
    {total} {{
        margin-top: 0.36rem;
        padding: 0.3rem 0.3rem 0.15rem;
        background: rgba(59,56,245,0.05);
        border: 1px solid rgba(59,56,245,0.08);
        border-radius: 12px;
    }}
    {total} .pbm-cell {{font-weight: 700;}}
    {formcard} {{
        background: rgba(255,255,255,0.84);
        border: 1px solid var(--pbm-border);
        border-radius: 18px;
        padding: 1rem;
        box-shadow: 0 10px 30px rgba(64,51,140,0.04);
    }}
    @media (max-width: 760px) {{
        .block-container {{padding-left: 0.7rem; padding-right: 0.7rem;}}
    }}
    """

    for i, status in enumerate(data["statuses"]):
        color = safe_color(data["status_colors"].get(status), PRIMARY)
        css += f'[data-testid="stExpander"]:has(.pbm-group-{i}) {{border-left: 4px solid {color};}}\n'

    for p in data.get("projects", []):
        type_color = safe_color(data["type_colors"].get(p.get("type"), PRIMARY), PRIMARY)
        css += (
            f'[class*="st-key-pbm_row_{p["id"]}"] '
            '{'
            f'background:{hex_to_rgba(type_color, 0.14)} !important;'
            f'box-shadow: inset 0 0 0 1px {hex_to_rgba(type_color, 0.18)} !important;'
            f'border-left: 4px solid {type_color} !important;'
            '}\n'
            f'[class*="st-key-pbm_row_{p["id"]}"]:hover '
            '{'
            f'background:{hex_to_rgba(type_color, 0.2)} !important;'
            '}\n'
        )

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def badge(text: str, color: str, text_color: str = "white") -> str:
    background = safe_color(color)
    foreground = text_color if text_color in ("white", "black") else safe_color(text_color)
    label = escape(str(text))
    border = hex_to_rgba(background, 0.18)
    return (
        f'<span class="pbm-badge" title="{label}" '
        f'style="background-color:{hex_to_rgba(background, 0.16)};'
        f'color:{foreground}; border-color:{border};">{label}</span>'
    )


def cell(text, style: str = "", tooltip: str = ""):
    value = str(text) if text not in (None, "") else "—"
    title = escape(tooltip or value, quote=True)
    st.markdown(
        f'<div class="pbm-cell {style}" title="{title}">{escape(value)}</div>',
        unsafe_allow_html=True,
    )


def badge_cell(text: str, color: str, text_color: str = "white"):
    st.markdown(
        f'<div class="pbm-cell badge-cell">{badge(text, color, text_color)}</div>',
        unsafe_allow_html=True,
    )


def project_number_cell(project: dict):
    st.markdown(
        f'<div class="pbm-cell center-cell">{project_number_markup(project)}</div>',
        unsafe_allow_html=True,
    )


def grid_template(widths) -> str:
    return " ".join(f"{float(w):g}fr" for w in widths)


def render_group_header():
    classes = []
    for idx, label in enumerate(ROW_LABELS):
        extra = " right" if idx in (7, 8) else " center" if idx in (0, 1, 9) else ""
        classes.append(
            f'<div class="pbm-grid-cell{extra}">{escape(label)}</div>'
        )
    st.markdown(
        f'<div class="pbm-grid-row pbm-grid-header" '
        f'style="grid-template-columns:{grid_template(ROW_WIDTHS)}">'
        + "".join(classes)
        + "</div>",
        unsafe_allow_html=True,
    )


def render_group_total_html(projects_in_group: list[dict]):
    total_budget, total_hours = get_group_totals(projects_in_group)
    count = len(projects_in_group)
    values = [
        "",
        "",
        "TOTAL DU GROUPE",
        "",
        "",
        "",
        f"{count} projet{'s' if count > 1 else ''}",
        display_amount(total_budget),
        display_hours(total_hours),
        "",
    ]
    cells = []
    for idx, value in enumerate(values):
        extra = " right" if idx in (7, 8) else " center" if idx in (0, 1, 9) else ""
        cells.append(f'<div class="pbm-grid-cell{extra}">{escape(value)}</div>')
    st.markdown(
        f'<div class="pbm-grid-row pbm-grid-total" '
        f'style="grid-template-columns:{grid_template(TOTAL_WIDTHS)}">'
        + "".join(cells)
        + "</div>",
        unsafe_allow_html=True,
    )


def display_date(value) -> str:
    if not value:
        return "—"
    try:
        return date.fromisoformat(str(value)).strftime("%d/%m/%Y")
    except ValueError:
        return str(value)


def display_amount(value) -> str:
    return f"{float(value or 0):,.0f} €".replace(",", " ")


def display_hours(value) -> str:
    return f"{float(value or 0):.1f} h".replace(".", ",")


def project_number_markup(project: dict) -> str:
    number = project.get("project_number") or "—"
    return f'<span class="pbm-project-number">{escape(str(number))}</span>'


def get_group_totals(projects_in_group: list[dict]) -> tuple[float, float]:
    total_budget = sum(float(p.get("budget", 0) or 0) for p in projects_in_group)
    total_hours = sum(float(p.get("estimated_time", 0) or 0) for p in projects_in_group)
    return total_budget, total_hours


def project_search_blob(project: dict) -> str:
    return " ".join([
        str(project.get("project_number") or ""),
        str(project.get("name") or ""),
        str(project.get("remarks") or ""),
        str(project.get("type") or ""),
    ]).casefold()


try:
    data = db.load_data(PATH)
except Exception as e:
    st.error(
        "Impossible de se connecter à la base de données partagée. "
        "Vérifiez que SUPABASE_URL et SUPABASE_KEY sont bien configurés "
        "dans les secrets de l'application (voir README.md)."
    )
    st.exception(e)
    st.stop()

inject_brand_styles(data)


def render_header():
    with ui_container("top_actionbar", "actionbar"):
        c1, c2, c3 = st.columns([1.35, 4.2, 1.1], vertical_alignment="center")
        with c1:
            if LOGO_PATH.exists():
                st.image(str(LOGO_PATH), use_container_width=True)
        with c2:
            st.markdown(
                """
                <div class="pbm-headline">
                    <div class="pbm-eyebrow">Builders · verticalsea</div>
                    <h1>Suivi de projets bâtiment</h1>
                    <div class="pbm-subline">Tableau de bord compact, filtrable et aligné sur la charte graphique.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.write("")
            if st.button("🔄 Rafraîchir", use_container_width=True):
                st.rerun()


render_header()


@st.dialog("Modifier le projet")
def edit_project_dialog(p: dict):
    with st.form(f"dialog_edit_{p['id']}"):
        c0, c1, c2 = st.columns([1, 1.2, 1.2])
        project_number = c0.text_input("N° projet", value=str(p.get("project_number") or ""))
        name = c1.text_input("Nom du projet", value=p["name"])
        type_options = ["(aucun)"] + data["types"]
        current_type = p.get("type") or "(aucun)"
        type_idx = type_options.index(current_type) if current_type in type_options else 0
        project_type = c2.selectbox("Type", type_options, index=type_idx)

        col1, col2 = st.columns(2)
        with col1:
            status = st.selectbox(
                "Statut", data["statuses"], index=data["statuses"].index(p["status"])
            )
            assigned = st.multiselect(
                "Personnes assignées",
                data["collaborators"],
                default=[a for a in p.get("assigned", []) if a in data["collaborators"]],
            )
            estimated_time = st.number_input(
                "Temps estimé (h)", min_value=0.0, step=0.5,
                value=float(p.get("estimated_time", 0.0)),
            )
        with col2:
            start_date_val = st.date_input(
                "Date de début (optionnel)",
                value=(
                    datetime.strptime(p["start_date"], "%Y-%m-%d").date()
                    if p.get("start_date") else None
                ),
            )
            due_date_val = st.date_input(
                "Date d'échéance",
                value=(
                    datetime.strptime(p["due_date"], "%Y-%m-%d").date()
                    if p.get("due_date") else date.today()
                ),
            )
            budget = st.number_input(
                "Budget (€)", min_value=0.0, step=100.0,
                value=float(p.get("budget", 0.0)),
            )
        remarks = st.text_area("Remarques", value=p.get("remarks", ""), height=120)

        b1, b2 = st.columns(2)
        save = b1.form_submit_button("💾 Enregistrer", use_container_width=True)
        delete = b2.form_submit_button("🗑️ Supprimer le projet", use_container_width=True)

    if save:
        db.update_project(PATH, p["id"], {
            "project_number": project_number.strip() or None,
            "name": name,
            "type": None if project_type == "(aucun)" else project_type,
            "status": status,
            "assigned": assigned,
            "estimated_time": estimated_time,
            "start_date": start_date_val.isoformat() if start_date_val else None,
            "due_date": due_date_val.isoformat() if due_date_val else None,
            "budget": budget,
            "remarks": remarks,
        })
        st.rerun()
    if delete:
        db.delete_project(PATH, p["id"])
        st.rerun()


def _set_active_page(page_name: str):
    st.session_state["pbm_active_page"] = page_name


if "pbm_active_page" not in st.session_state:
    st.session_state["pbm_active_page"] = "Tableau"

with ui_container("pbm_main_navigation", "nav"):
    nav_cols = st.columns([1.0, 1.45, 1.1, 0.85, 1.15, 5.0], gap="small")
    nav_items = ["Tableau", "Nouveau projet", "Calendrier", "Gantt", "Paramètres"]
    for col, page_name in zip(nav_cols[:5], nav_items):
        with col:
            st.button(
                page_name,
                key=f"nav_{page_name}",
                use_container_width=True,
                type="primary" if st.session_state["pbm_active_page"] == page_name else "secondary",
                on_click=_set_active_page,
                args=(page_name,),
            )

active_page = st.session_state["pbm_active_page"]


def render_subtasks(p: dict):
    pid = p["id"]
    subtasks = p.get("subtasks", [])
    with ui_container(f"pbm_children_{pid}", "children"):
        if not subtasks:
            st.caption("Aucune sous-tâche.")
        for i, s in enumerate(subtasks):
            with ui_container(f"pbm_subrow_{s['id']}", "subrow"):
                sc = st.columns([0.34, 0.34, 0.38, 3.90, 1.55, 1.15, 1.00, 0.95, 0.38], gap="small", vertical_alignment="center")
                if sc[0].button("▴", key=f"subup_{s['id']}", disabled=(i == 0), help="Monter"):
                    db.move_subtask(PATH, pid, s["id"], -1)
                    st.rerun()
                if sc[1].button("▾", key=f"subdown_{s['id']}", disabled=(i == len(subtasks) - 1), help="Descendre"):
                    db.move_subtask(PATH, pid, s["id"], 1)
                    st.rerun()
                done = sc[2].checkbox(
                    f"Terminer : {s['name']}", value=s.get("done", False),
                    key=f"subdone_{s['id']}", label_visibility="collapsed",
                )
                if done != s.get("done", False):
                    db.update_subtask(PATH, pid, s["id"], {"done": done})
                    st.rerun()
                with sc[3]:
                    cell(s["name"], "done" if s.get("done") else "")
                with sc[4]:
                    cell(", ".join(s.get("assigned", [])) or "—")
                with sc[5]:
                    cell("")
                with sc[6]:
                    cell("")
                with sc[7]:
                    cell(display_hours(s.get("estimated_time")), "number")
                if sc[8].button("×", key=f"subdel_{s['id']}", help="Supprimer la sous-tâche"):
                    db.delete_subtask(PATH, pid, s["id"])
                    st.rerun()

        add_key = f"show_add_subtask_{pid}"
        if add_key not in st.session_state:
            st.session_state[add_key] = False
        add_label = "Masquer le formulaire" if st.session_state[add_key] else "Ajouter une sous-tâche"
        if st.button(add_label, key=f"toggle_add_subtask_{pid}"):
            st.session_state[add_key] = not st.session_state[add_key]
            st.rerun()
        if st.session_state[add_key]:
            with st.form(f"add_subtask_{pid}", clear_on_submit=True):
                fc1, fc2, fc3, fc4 = st.columns([3.1, 2, 1.2, 1])
                sub_name = fc1.text_input(
                    "Nouvelle sous-tâche", label_visibility="collapsed",
                    placeholder="Nouvelle sous-tâche",
                )
                sub_assigned = fc2.multiselect(
                    "Assignée à", data["collaborators"], label_visibility="collapsed",
                    placeholder="Assignée à", key=f"sub_assign_{pid}",
                )
                sub_time = fc3.number_input(
                    "Temps (h)", min_value=0.0, step=0.5, label_visibility="collapsed",
                    key=f"sub_time_{pid}",
                )
                if fc4.form_submit_button("Ajouter") and sub_name.strip():
                    db.add_subtask(PATH, pid, sub_name, sub_assigned, sub_time)
                    st.rerun()


def render_project_row(p: dict):
    pid = p["id"]
    expand_key = f"expand_{pid}"
    if expand_key not in st.session_state:
        st.session_state[expand_key] = False

    with st.container(key=f"pbm_project_{pid}", border=False):
        with st.container(key=f"pbm_row_{pid}", border=False):
            cols = st.columns(ROW_WIDTHS, gap="small", vertical_alignment="center")
            arrow = "▾" if st.session_state[expand_key] else "▸"
            if cols[0].button(arrow, key=f"arrow_{pid}", help="Afficher / masquer les sous-tâches"):
                st.session_state[expand_key] = not st.session_state[expand_key]
                st.rerun()
            with cols[1]:
                project_number_cell(p)
            if cols[2].button(p["name"], key=f"name_{pid}", use_container_width=True, help=p["name"]):
                edit_project_dialog(p)
            with cols[3]:
                ptype = p.get("type")
                if ptype:
                    badge_cell(ptype, data["type_colors"].get(ptype, PRIMARY_DARK), PRIMARY_DARK)
                else:
                    cell("—")
            with cols[4]:
                cell(", ".join(p.get("assigned", [])) or "—")
            with cols[5]:
                badge_cell(p["status"], data["status_colors"].get(p["status"], PRIMARY), "white")
            with cols[6]:
                cell(display_date(p.get("due_date")))
            with cols[7]:
                cell(display_amount(p.get("budget")), "number")
            with cols[8]:
                cell(display_hours(p.get("estimated_time")), "number")
            with cols[9]:
                subtasks = p.get("subtasks", [])
                done = sum(1 for s in subtasks if s.get("done"))
                cell(
                    f"{done}/{len(subtasks)}" if subtasks else "—",
                    "progress",
                    f"{done} sur {len(subtasks)} sous-tâches terminées",
                )
        if st.session_state[expand_key]:
            render_subtasks(p)


def render_group_total_row(projects_in_group: list[dict]):
    render_group_total_html(projects_in_group)


if active_page == "Tableau":
    with ui_container("pbm_board", "board"):
        filters = st.columns([1.5, 1.0, 1.0, 1.0], gap="small")
        query = filters[0].text_input(
            "Rechercher un projet", placeholder="Rechercher nom, numéro, remarques...",
            label_visibility="collapsed", key="pbm_search",
        ).strip().casefold()
        person_filter = filters[1].selectbox(
            "Collaborateur", [None] + data["collaborators"],
            format_func=lambda x: "Tous les collaborateurs" if x is None else x,
            label_visibility="collapsed", key="pbm_person",
        )
        status_filter = filters[2].selectbox(
            "Statut", [None] + data["statuses"],
            format_func=lambda x: "Tous les statuts" if x is None else x,
            label_visibility="collapsed", key="pbm_status",
        )
        type_filter = filters[3].selectbox(
            "Type", [None] + data["types"],
            format_func=lambda x: "Tous les types" if x is None else x,
            label_visibility="collapsed", key="pbm_type",
        )

        projects = [
            p for p in data["projects"]
            if (not query or query in project_search_blob(p))
            and (person_filter is None or person_filter in p.get("assigned", []))
            and (status_filter is None or p.get("status") == status_filter)
            and (type_filter is None or p.get("type") == type_filter)
        ]
        active_filters = bool(query or person_filter is not None or status_filter is not None or type_filter is not None)

        if not data["projects"]:
            st.info("Aucun projet. Utilisez l'onglet Nouveau projet pour en créer un.")
        elif not projects:
            st.info("Aucun projet ne correspond aux filtres.")

        for group_index, status in enumerate(data["statuses"]):
            projects_in_group = [p for p in projects if p["status"] == status]
            if active_filters and not projects_in_group:
                continue
            count = len(projects_in_group)
            total_budget, total_hours = get_group_totals(projects_in_group)
            title = (
                f"{status} · {count} projet{'s' if count != 1 else ''}"
                f" · {display_amount(total_budget)} · {display_hours(total_hours)}"
            )
            with st.expander(title, expanded=bool(projects_in_group)):
                with ui_container(f"pbm_group_{group_index}", "group"):
                    st.markdown(f'<span class="pbm-marker pbm-group-{group_index}"></span>', unsafe_allow_html=True)
                    if not projects_in_group:
                        st.caption("Aucun projet dans ce groupe.")
                        continue
                    render_group_header()
                    st.markdown('<div class="pbm-header-project-gap"></div>', unsafe_allow_html=True)
                    for p in projects_in_group:
                        render_project_row(p)
                    render_group_total_row(projects_in_group)

if active_page == "Nouveau projet":
    with ui_container("pbm_form_add", "formcard"):
        st.subheader("Créer un nouveau projet")
        with st.form("new_project_form", clear_on_submit=True):
            top = st.columns([1, 1.6, 1.2])
            project_number = top[0].text_input("N° projet")
            name = top[1].text_input("Nom du projet *")
            type_options = ["(aucun)"] + data["types"]
            project_type = top[2].selectbox("Type de projet", type_options)

            col1, col2 = st.columns(2)
            with col1:
                status = st.selectbox("Statut / groupe", data["statuses"])
                assigned = st.multiselect("Personnes assignées", data["collaborators"])
                estimated_time = st.number_input("Temps estimé (h)", min_value=0.0, step=0.5)
            with col2:
                start_date_val = st.date_input("Date de début (optionnel)", value=None)
                due_date_val = st.date_input("Date d'échéance", value=date.today())
                budget = st.number_input("Budget (€)", min_value=0.0, step=100.0)
            remarks = st.text_area("Remarques", height=120)

            submitted = st.form_submit_button("➕ Créer le projet")
            if submitted:
                if not name.strip():
                    st.error("Le nom du projet est obligatoire.")
                else:
                    project = db.new_project_dict(
                        name=name,
                        status=status,
                        assigned=assigned,
                        estimated_time=estimated_time,
                        start_date=start_date_val.isoformat() if start_date_val else None,
                        due_date=due_date_val.isoformat() if due_date_val else None,
                        budget=budget,
                        remarks=remarks,
                        project_type=None if project_type == "(aucun)" else project_type,
                    )
                    project["project_number"] = project_number.strip() or None
                    db.add_project(PATH, project)
                    st.success(f"Projet « {name} » créé.")
                    st.rerun()

if active_page == "Calendrier":
    st.subheader("Vue calendrier (par date d'échéance)")

    if "cal_month" not in st.session_state:
        today = date.today()
        st.session_state.cal_month = today.month
        st.session_state.cal_year = today.year

    nav1, nav2, nav3 = st.columns([1, 2, 1])
    if nav1.button("◀ Mois précédent"):
        m = st.session_state.cal_month - 1
        y = st.session_state.cal_year
        if m == 0:
            m, y = 12, y - 1
        st.session_state.cal_month, st.session_state.cal_year = m, y
        st.rerun()
    nav2.markdown(
        f"<h4 style='text-align:center; color:{PRIMARY_DARK}'>{cal.month_name[st.session_state.cal_month]} {st.session_state.cal_year}</h4>",
        unsafe_allow_html=True,
    )
    if nav3.button("Mois suivant ▶"):
        m = st.session_state.cal_month + 1
        y = st.session_state.cal_year
        if m == 13:
            m, y = 1, y + 1
        st.session_state.cal_month, st.session_state.cal_year = m, y
        st.rerun()

    by_day = {}
    for p in data["projects"]:
        if p.get("due_date"):
            by_day.setdefault(p["due_date"], []).append(p)

    month_matrix = cal.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
    days_header = st.columns(7)
    for i, dname in enumerate(["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]):
        days_header[i].markdown(f"**{dname}**")

    for week in month_matrix:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.write("")
                    continue
                day_str = date(st.session_state.cal_year, st.session_state.cal_month, day).isoformat()
                st.markdown(f"**{day}**")
                for p in by_day.get(day_str, []):
                    color = safe_color(data["type_colors"].get(p.get("type"), PRIMARY))
                    st.markdown(
                        f"<div style='background-color:{hex_to_rgba(color, 0.14)}; color:{TEXT};"
                        f"border-left:4px solid {color}; border-radius:8px; padding:3px 6px;"
                        f"font-size:0.74em; margin-bottom:4px'>"
                        f"<strong>{escape(str(p.get('project_number') or '—'))}</strong> · {escape(p['name'])}</div>",
                        unsafe_allow_html=True,
                    )

if active_page == "Gantt":
    st.subheader("Vue Gantt / échéancier")

    rows = []
    for p in data["projects"]:
        if not p.get("due_date"):
            continue
        end = datetime.strptime(p["due_date"], "%Y-%m-%d")
        if p.get("start_date"):
            start = datetime.strptime(p["start_date"], "%Y-%m-%d")
        else:
            days = max(1, round((p.get("estimated_time", 0) or 0) / 8))
            start = end - timedelta(days=days)
        if start >= end:
            start = end - timedelta(days=1)
        rows.append({
            "Projet": f"{p.get('project_number') or '—'} · {p['name']}",
            "Début": start,
            "Fin": end,
            "Statut": p["status"],
            "Type": p.get("type") or "—",
            "Assigné": ", ".join(p.get("assigned", [])) or "—",
        })

    if not rows:
        st.info("Aucun projet avec une date d'échéance à afficher.")
    else:
        df = pd.DataFrame(rows)
        color_map = data["status_colors"]
        fig = px.timeline(
            df,
            x_start="Début",
            x_end="Fin",
            y="Projet",
            color="Statut",
            color_discrete_map=color_map,
            hover_data=["Type", "Assigné"],
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=max(320, 40 * len(df)))
        st.plotly_chart(fig, use_container_width=True)

if active_page == "Paramètres":
    settings_cols = st.columns([1, 1.15, 1.15], gap="medium")
    with settings_cols[0]:
        st.markdown("### 👥 Collaborateurs")
        for person in data["collaborators"]:
            c1, c2 = st.columns([4, 1])
            c1.write(person)
            if c2.button("🗑️", key=f"del_collab_{person}"):
                db.remove_collaborator(PATH, person)
                st.rerun()
        with st.form("add_collab_form", clear_on_submit=True):
            new_person = st.text_input("Ajouter une personne")
            if st.form_submit_button("Ajouter") and new_person.strip():
                db.add_collaborator(PATH, new_person)
                st.rerun()
    with settings_cols[1]:
        st.markdown("### 🏷️ Statuts / groupes")
        st.caption("L'ordre ici définit l'ordre des groupes dans le tableau.")
        n_statuses = len(data["statuses"])
        for i, status in enumerate(data["statuses"]):
            c1, c2, c3, c4 = st.columns([3, 0.7, 0.7, 0.7])
            c1.markdown(
                badge(status, data["status_colors"].get(status, PRIMARY), "white"),
                unsafe_allow_html=True,
            )
            if c2.button("▲", key=f"statusup_{status}", disabled=(i == 0)):
                db.move_status(PATH, status, -1)
                st.rerun()
            if c3.button("▼", key=f"statusdown_{status}", disabled=(i == n_statuses - 1)):
                db.move_status(PATH, status, 1)
                st.rerun()
            if c4.button("🗑️", key=f"del_status_{status}"):
                fallback = next((s for s in data["statuses"] if s != status), "En cours")
                db.remove_status(PATH, status, fallback)
                st.rerun()
        with st.form("add_status_form", clear_on_submit=True):
            new_status = st.text_input("Nouveau statut / groupe")
            new_color = st.color_picker("Couleur", value=PRIMARY)
            if st.form_submit_button("Ajouter") and new_status.strip():
                db.add_status(PATH, new_status, new_color)
                st.rerun()
    with settings_cols[2]:
        st.markdown("### 🏗️ Types de projet")
        st.caption("Ex. DIAGNOSTIC, APS, APD, PRO, DCE, EXE…")
        n_types = len(data["types"])
        for i, t in enumerate(data["types"]):
            c1, c2, c3, c4 = st.columns([3, 0.7, 0.7, 0.7])
            c1.markdown(
                badge(t, data["type_colors"].get(t, PRIMARY_DARK), PRIMARY_DARK),
                unsafe_allow_html=True,
            )
            if c2.button("▲", key=f"typeup_{t}", disabled=(i == 0)):
                db.move_type(PATH, t, -1)
                st.rerun()
            if c3.button("▼", key=f"typedown_{t}", disabled=(i == n_types - 1)):
                db.move_type(PATH, t, 1)
                st.rerun()
            if c4.button("🗑️", key=f"del_type_{t}"):
                db.remove_type(PATH, t)
                st.rerun()
        with st.form("add_type_form", clear_on_submit=True):
            new_type = st.text_input("Nouveau type")
            new_type_color = st.color_picker("Couleur", value="#D6E6F5")
            if st.form_submit_button("Ajouter") and new_type.strip():
                db.add_type(PATH, new_type.strip().upper(), new_type_color)
                st.rerun()
