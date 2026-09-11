import streamlit as st

from config import (
    BORDER,
    DISCIPLINE_COLORS,
    DISCIPLINES,
    MUTED,
    PRIMARY,
    PRIMARY_DARK,
    SURFACE,
    SURFACE_ALT,
    TEXT,
)
from ui.components import css_scope, hex_to_rgba, safe_color


def inject_brand_styles(data: dict):
    board = css_scope("board")
    project = css_scope("project")
    projectrow = css_scope("projectrow")
    subprojects = css_scope("subprojects")
    subprojectrow = css_scope("subprojectrow")
    tasks = css_scope("tasks")
    taskrow = css_scope("taskrow")
    actionbar = css_scope("actionbar")
    formcard = css_scope("formcard")
    nav = css_scope("nav")
    summary = css_scope("summary")

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
        padding-top: 3rem;
        padding-bottom: 1.25rem;
        padding-left: 1.25rem;
        padding-right: 1.25rem;
        max-width: none;
    }}

    h1, h2, h3 {{
        color: var(--pbm-primary-dark);
        letter-spacing: -0.02em;
    }}
    h1 {{
        font-size: 1.35rem !important;
        line-height: 1.12 !important;
        padding: 0 !important;
        margin: 0 !important;
    }}
    h3 {{font-size: 1rem !important;}}

    :is(.element-container, [data-testid="stElementContainer"]):has(.pbm-marker) {{
        display: none !important;
    }}

    [data-testid="stButton"] button,
    [data-testid="stDownloadButton"] button {{
        border-radius: 10px;
    }}

    .pbm-headline {{display:flex; flex-direction:column; gap:0.05rem;}}
    .pbm-eyebrow {{
        color: var(--pbm-primary);
        font-weight: 700;
        font-size: 0.72rem;
        line-height: 1.1;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }}
    .pbm-subline {{color: var(--pbm-muted); font-size: 0.78rem; line-height: 1.15;}}

    {actionbar} {{
        padding: 0.2rem 0.85rem 0.52rem;
        margin-bottom: 0.42rem;
        background: rgba(255,255,255,0.84);
        border: 1px solid var(--pbm-border);
        border-radius: 15px;
        box-shadow: 0 6px 20px rgba(64,51,140,0.045);
        overflow: visible !important;
    }}
    {actionbar} [data-testid="stHorizontalBlock"] {{
        min-height: 82px !important;
        align-items: center !important;
        overflow: visible !important;
    }}
    {actionbar} [data-testid="stImage"] {{overflow: visible !important;}}
    {actionbar} [data-testid="stImage"] img {{
        max-height: 72px !important;
        height: auto !important;
        width: auto !important;
        max-width: 100% !important;
        object-fit: contain !important;
        object-position: left center !important;
        display: block !important;
    }}

    {nav} {{
        margin: 0;
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
        border: 1px solid rgba(59,56,245,0.22) !important;
        box-shadow: 0 2px 7px rgba(64,51,140,0.05) !important;
        font-weight: 650 !important;
    }}
    {nav} [data-testid="stButton"] button[kind="secondary"] {{
        background: #ffffff !important;
        color: var(--pbm-text) !important;
    }}
    {nav} [data-testid="stButton"] button[kind="primary"] {{
        background: rgba(59,56,245,0.13) !important;
        color: var(--pbm-primary-dark) !important;
        border-color: rgba(59,56,245,0.38) !important;
    }}
    {nav} [data-testid="stButton"] button p {{
        margin: 0 !important;
        white-space: nowrap !important;
        font-size: 0.86rem !important;
    }}

    .pbm-badge {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 24px;
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
        min-height: 30px;
        box-sizing: border-box;
        font-size: 0.82rem;
        line-height: 1.2;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        color: var(--pbm-text);
        padding: 0 0.28rem;
    }}
    .pbm-cell.number {{
        justify-content:flex-end;
        text-align:right;
        font-variant-numeric: tabular-nums;
        font-weight: 600;
    }}
    .pbm-cell.badge-cell {{justify-content:flex-start;}}
    .pbm-cell.center-cell {{justify-content:center; text-align:center;}}

    .pbm-project-number {{
        display:inline-flex;
        align-items:center;
        min-height: 24px;
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
    .pbm-grid-cell.right {{justify-content:flex-end; text-align:right;}}
    .pbm-grid-cell.center {{justify-content:center; text-align:center;}}

    .pbm-grid-header-wrap {{
        display:block;
        width:100%;
        box-sizing:border-box;
        padding-bottom: 12px;
    }}
    .pbm-grid-header {{
        min-height: 40px;
        padding: 0.30rem 0.34rem;
        margin: 0.16rem 0 0;
        background: rgba(59,56,245,0.055);
        border: 1px solid rgba(59,56,245,0.12);
        border-radius: 9px;
    }}
    .pbm-grid-header .pbm-grid-cell {{
        min-height: 28px;
        font-size: 0.70rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: var(--pbm-muted);
    }}

    .pbm-grid-total {{
        min-height: 40px;
        padding: 0.30rem 0.34rem;
        margin: 0.32rem 0 0.62rem;
        background: rgba(59,56,245,0.07);
        border: 1px solid rgba(59,56,245,0.16);
        border-radius: 10px;
    }}
    .pbm-grid-total .pbm-grid-cell {{
        min-height: 28px;
        font-size: 0.80rem;
        font-weight: 700;
        color: var(--pbm-primary-dark);
    }}

    {board} {{gap: 0.45rem !important;}}
    {board} [data-testid="stExpander"] {{
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid rgba(64,51,140,0.08);
        background: rgba(255,255,255,0.82);
        box-shadow: 0 10px 30px rgba(64,51,140,0.04);
    }}
    {board} [data-testid="stExpander"] summary {{
        padding: 0.55rem 0.75rem;
        min-height: 2.3rem;
    }}
    {board} [data-testid="stExpanderDetails"] {{padding: 0 0.55rem 0.55rem;}}

    {project}, {projectrow}, {subprojects}, {subprojectrow}, {tasks}, {taskrow}, {formcard} {{
        gap: 0 !important;
    }}

    {project} {{margin-bottom: 0.25rem;}}

    {projectrow}, {subprojectrow}, {taskrow} {{
        padding: 2px 0.34rem;
        min-height: 38px;
        border-bottom: 1px solid rgba(64,51,140,0.06);
        border-radius: 11px;
        transition: background 0.15s ease;
    }}
    {projectrow} {{
        background: rgba(255,255,255,0.82);
        box-shadow: inset 0 0 0 1px rgba(64,51,140,0.07);
    }}
    {projectrow}:hover,
    {subprojectrow}:hover,
    {taskrow}:hover {{background: rgba(64,51,140,0.055);}}

    {projectrow} [data-testid="stHorizontalBlock"],
    {subprojectrow} [data-testid="stHorizontalBlock"],
    {taskrow} [data-testid="stHorizontalBlock"] {{
        gap: 8px !important;
        align-items: center !important;
    }}
    {projectrow} [data-testid="stHorizontalBlock"] > div,
    {subprojectrow} [data-testid="stHorizontalBlock"] > div,
    {taskrow} [data-testid="stHorizontalBlock"] > div {{
        display: flex !important;
        align-items: center !important;
        min-height: 30px !important;
        min-width: 0 !important;
    }}
    {projectrow} [data-testid="stHorizontalBlock"] > div > div,
    {subprojectrow} [data-testid="stHorizontalBlock"] > div > div,
    {taskrow} [data-testid="stHorizontalBlock"] > div > div {{
        width: 100% !important;
    }}
    {projectrow} [data-testid="stVerticalBlock"],
    {subprojectrow} [data-testid="stVerticalBlock"],
    {taskrow} [data-testid="stVerticalBlock"] {{
        gap: 0 !important;
        min-width: 0;
    }}
    {projectrow} [data-testid="stMarkdownContainer"] p,
    {subprojectrow} [data-testid="stMarkdownContainer"] p,
    {taskrow} [data-testid="stMarkdownContainer"] p {{margin: 0;}}

    /* Alignement vertical homogène sur les trois niveaux. */
    {projectrow} :is(.element-container, [data-testid="stElementContainer"]),
    {subprojectrow} :is(.element-container, [data-testid="stElementContainer"]),
    {taskrow} :is(.element-container, [data-testid="stElementContainer"]) {{
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        min-height: 30px !important;
        display: flex !important;
        align-items: center !important;
    }}
    {projectrow} [data-testid="stMarkdownContainer"],
    {subprojectrow} [data-testid="stMarkdownContainer"],
    {taskrow} [data-testid="stMarkdownContainer"] {{
        min-height: 30px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
    }}

    {projectrow} [data-testid="stButton"] button,
    {subprojectrow} [data-testid="stButton"] button,
    {taskrow} [data-testid="stButton"] button {{
        min-height: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        padding: 0 0.35rem;
        border: 1px solid transparent;
        border-radius: 8px;
        background: transparent;
    }}
    {projectrow} [data-testid="stButton"] button:hover,
    {subprojectrow} [data-testid="stButton"] button:hover,
    {taskrow} [data-testid="stButton"] button:hover {{
        background: rgba(255,255,255,0.58);
        border-color: rgba(64,51,140,0.08);
    }}
    {projectrow} [data-testid="stButton"] button p,
    {subprojectrow} [data-testid="stButton"] button p,
    {taskrow} [data-testid="stButton"] button p {{
        font-size: 0.82rem;
        line-height: 1.25;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block;
        margin: 0;
    }}
    {projectrow} [data-testid="stHorizontalBlock"] > :nth-child(4) [data-testid="stButton"] button,
    {subprojectrow} [data-testid="stHorizontalBlock"] > :nth-child(3) [data-testid="stButton"] button,
    {taskrow} [data-testid="stHorizontalBlock"] > :nth-child(3) [data-testid="stButton"] button {{
        justify-content:flex-start;
        text-align:left;
        font-weight:700;
    }}

    {projectrow} [data-testid="stCheckbox"],
    {subprojectrow} [data-testid="stCheckbox"],
    {taskrow} [data-testid="stCheckbox"] {{
        min-height: 30px !important;
        display:flex !important;
        align-items:center !important;
        justify-content:center !important;
        margin:0 !important;
        padding:0 !important;
    }}
    {projectrow} [data-testid="stCheckbox"] label,
    {subprojectrow} [data-testid="stCheckbox"] label,
    {taskrow} [data-testid="stCheckbox"] label {{
        min-height: 30px !important;
        display:flex !important;
        align-items:center !important;
        justify-content:center !important;
        margin:0 !important;
        padding:0 !important;
    }}

    {subprojects} {{
        margin: 0.14rem 0 0.48rem 1.15rem;
        width: calc(100% - 1.15rem);
        padding: 0.28rem 0.58rem 0.46rem 0.70rem;
        border-left: 2px solid rgba(59,56,245,0.22);
        background: rgba(255,255,255,0.58);
        border-radius: 0 0 12px 12px;
    }}

    {tasks} {{
        margin: 0.12rem 0 0.40rem 1.0rem;
        width: calc(100% - 1.0rem);
        padding: 0.24rem 0.46rem 0.38rem 0.62rem;
        border-left: 2px solid rgba(64,51,140,0.16);
        background: rgba(248,248,253,0.68);
        border-radius: 0 0 10px 10px;
    }}

    {taskrow} {{background: rgba(255,255,255,0.72);}}

    {subprojects} [data-testid="stForm"],
    {tasks} [data-testid="stForm"] {{
        padding: 0.65rem;
        background: rgba(59,56,245,0.035);
        border-radius: 12px;
        border: 1px dashed rgba(59,56,245,0.14);
        margin-top: 0.35rem;
    }}

    {formcard} {{
        background: rgba(255,255,255,0.84);
        border: 1px solid var(--pbm-border);
        border-radius: 18px;
        padding: 1rem;
        box-shadow: 0 10px 30px rgba(64,51,140,0.04);
    }}

    {summary} {{
        gap: 0.34rem !important;
        padding: 0.68rem 0.62rem 0.72rem;
        background: rgba(255,255,255,0.86);
        border: 1px solid var(--pbm-border);
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(64,51,140,0.045);
    }}
    {summary} .pbm-summary-title {{
        color: var(--pbm-primary-dark);
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.055em;
        text-transform: uppercase;
        margin: 0 0 0.55rem 0.08rem;
    }}
    {summary} .pbm-summary-section {{
        color: var(--pbm-muted);
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.055em;
        text-transform: uppercase;
        margin: 0.15rem 0 0.26rem 0.08rem;
    }}
    {summary} .pbm-summary-section.second {{margin-top: 0.75rem;}}
    {summary} [data-testid="stButton"] button {{
        min-height: 2.05rem !important;
        height: 2.05rem !important;
        padding: 0 0.55rem !important;
        justify-content: flex-start !important;
        text-align: left !important;
        border-radius: 8px !important;
        border: 1px solid rgba(59,56,245,0.11) !important;
        box-shadow: none !important;
        font-weight: 700 !important;
    }}
    {summary} [data-testid="stButton"] button[kind="secondary"] {{
        background: rgba(255,255,255,0.84) !important;
        color: var(--pbm-text) !important;
    }}
    {summary} [data-testid="stButton"] button[kind="primary"] {{
        background: rgba(59,56,245,0.12) !important;
        color: var(--pbm-primary-dark) !important;
        border-color: rgba(59,56,245,0.25) !important;
    }}
    {summary} [data-testid="stButton"] button p {{
        font-size: 0.86rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}
    {summary} .pbm-side-budget {{
        margin: 0.14rem 0.46rem 0.12rem;
        color: var(--pbm-primary-dark);
        font-size: 0.82rem;
        line-height: 1.05;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
    }}

    @media (max-width: 900px) {{
        .block-container {{padding-left: 0.7rem; padding-right: 0.7rem;}}
    }}
    """

    for i, discipline in enumerate(DISCIPLINES):
        color = safe_color(DISCIPLINE_COLORS.get(discipline), PRIMARY)
        group_scope = css_scope(f"discipline-group-{i}")
        row_scope = css_scope(f"discipline-row-{i}")
        side_scope = css_scope(f"summary-discipline-{i}")
        css += (
            f'[data-testid="stExpander"]:has(.pbm-discipline-group-{i}-marker) '
            f'{{border-left:4px solid {color} !important;}}\n'
            f'{row_scope} {{border-left:4px solid {color};}}\n'
            f'{side_scope} {{border-left:4px solid {color};padding:0.25rem 0.28rem 0.28rem 0.38rem;'
            'margin-bottom:0.18rem;background:rgba(248,248,253,0.78);border-radius:10px;gap:0 !important;}\n'
        )

    all_discipline_scope = css_scope("summary-discipline-all")
    css += (
        f'{all_discipline_scope} {{border-left:4px solid {PRIMARY};padding:0.25rem 0.28rem 0.28rem 0.38rem;'
        'margin-bottom:0.26rem;background:rgba(59,56,245,0.045);border-radius:10px;gap:0 !important;}\n'
    )

    all_status_scope = css_scope("summary-status-all")
    css += (
        f'{all_status_scope} {{border-left:4px solid {PRIMARY};padding:0.25rem 0.28rem 0.28rem 0.38rem;'
        'margin-bottom:0.26rem;background:rgba(59,56,245,0.045);border-radius:10px;gap:0 !important;}\n'
    )

    for i, status in enumerate(data.get("statuses", [])):
        color = safe_color(data.get("status_colors", {}).get(status), PRIMARY)
        side_scope = css_scope(f"summary-status-{i}")
        css += (
            f'[data-testid="stExpander"]:has(.pbm-status-group-{i}-marker) '
            f'{{border-left:4px solid {color} !important;}}\n'
            f'{side_scope} {{border-left:4px solid {color};padding:0.25rem 0.28rem 0.28rem 0.38rem;'
            'margin-bottom:0.18rem;background:rgba(248,248,253,0.78);border-radius:10px;gap:0 !important;}\n'
        )

    for project in data.get("projects", []):
        for subproject in project.get("subprojects", []):
            type_color = safe_color(
                data.get("type_colors", {}).get(subproject.get("type")), PRIMARY
            )
            row_scope = css_scope(f"subprojectclr-{subproject['id']}")
            css += (
                f'{row_scope} {{'
                f'background:{hex_to_rgba(type_color, 0.12)};'
                f'box-shadow:inset 0 0 0 1px {hex_to_rgba(type_color, 0.16)};'
                f'border-left:4px solid {type_color};'
                '}\n'
            )

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
