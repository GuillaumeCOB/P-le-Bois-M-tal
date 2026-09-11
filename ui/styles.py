import streamlit as st

from config import BORDER, MUTED, PRIMARY, PRIMARY_DARK, SURFACE, SURFACE_ALT, TEXT
from ui.components import css_scope, hex_to_rgba, safe_color

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
        padding-top: 5rem;
        padding-bottom: 1.25rem;
        padding-left: 1.25rem;
        padding-right: 1.25rem;
        max-width: none;
    }}
    h1, h2, h3 {{color: var(--pbm-primary-dark); letter-spacing: -0.02em;}}
    h1 {{font-size: 1.35rem !important; line-height: 1.12 !important; padding: 0 !important; margin: 0 !important;}}
    h3 {{font-size: 1rem !important;}}
    {nav} {{
        margin: 0rem 0 0rem 0;
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
    .pbm-headline {{display:flex; flex-direction:column; gap:0.05rem;}}
    .pbm-eyebrow {{color: var(--pbm-primary); font-weight: 700; font-size: 0.72rem; line-height: 1.1; text-transform: uppercase; letter-spacing: 0.08em;}}
    .pbm-subline {{color: var(--pbm-muted); font-size: 0.78rem; line-height: 1.15;}}
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
        font-size: 0.84rem;
        line-height: 1.2;
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
    .pbm-grid-header-wrap {{
        display: block;
        width: 100%;
        box-sizing: border-box;
        padding-bottom: 22px;
    }}
    .pbm-grid-header {{
        min-height: 42px;
        padding: 0.34rem 0.36rem;
        margin: 0.18rem 0 0;
        background: rgba(59,56,245,0.065);
        border: 1px solid rgba(59,56,245,0.14);
        border-radius: 10px;
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
        margin: 0.20rem 0 0.70rem;
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
    {actionbar} [data-testid="stImage"] {{
        overflow: visible !important;
    }}
    {actionbar} [data-testid="stImage"] img {{
        max-height: 72px !important;
        height: auto !important;
        width: auto !important;
        max-width: 100% !important;
        object-fit: contain !important;
        object-position: left center !important;
        display: block !important;
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
    {project} {{margin-bottom: 0.22rem;}}
    {row} {{
        padding: 2px 0.34rem;
        min-height: 38px;
        border-bottom: 1px solid rgba(64,51,140,0.06);
        border-radius: 12px;
        transition: background 0.15s ease;
    }}
    {row}:hover {{background: rgba(64,51,140,0.06);}}
    {row} [data-testid="stHorizontalBlock"],
    {subrow} [data-testid="stHorizontalBlock"] {{gap: 8px !important; align-items: center !important;}}
    {row} [data-testid="stHorizontalBlock"] > div {{
        display: flex !important;
        align-items: center !important;
        min-height: 30px !important;
    }}
    {subrow} [data-testid="stHorizontalBlock"] > div {{
        display: flex !important;
        align-items: center !important;
        min-height: 34px !important;
    }}
    {row} [data-testid="stHorizontalBlock"] > div > div,
    {subrow} [data-testid="stHorizontalBlock"] > div > div {{
        width: 100% !important;
    }}
    {row} [data-testid="stVerticalBlock"],
    {subrow} [data-testid="stVerticalBlock"] {{gap: 0 !important; min-width: 0;}}
    {row} :is([data-testid="stColumn"], [data-testid="column"]),
    {subrow} :is([data-testid="stColumn"], [data-testid="column"]) {{min-width: 0;}}
    {row} [data-testid="stMarkdownContainer"] p,
    {subrow} [data-testid="stMarkdownContainer"] p {{margin: 0;}}
    {row} [data-testid="stButton"] button {{
        min-height: 30px;
        height: 30px;
        display: flex;
        align-items: center;
        padding: 0 0.35rem;
        border: 1px solid transparent;
        border-radius: 8px;
        background: transparent;
    }}
    {subrow} [data-testid="stButton"] button {{
        min-height: 32px;
        height: 32px;
        display: flex;
        align-items: center;
        padding: 0 0.35rem;
        border: 1px solid transparent;
        border-radius: 8px;
        background: transparent;
    }}
    {row} :is(.element-container, [data-testid="stElementContainer"]),
    {row} [data-testid="stMarkdownContainer"] {{
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
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
        margin: 0 0 0.80rem 0.08rem;
    }}
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
        font-size: 0.92rem !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: ellipsis !important;
    }}
    {summary} .pbm-side-budget {{
        margin: 0.20rem 0.46rem 0.20rem;
        color: var(--pbm-primary-dark);
        font-size: 0.92rem;
        line-height: 1.05;
        font-weight: 800;
        font-variant-numeric: tabular-nums;
    }}
    {summary} .pbm-side-meta {{
        margin: 0.08rem 0.46rem 0.10rem;
        color: var(--pbm-muted);
        font-size: 0.72rem;
        line-height: 1.15;
        font-variant-numeric: tabular-nums;
    }}
    @media (max-width: 760px) {{
        .block-container {{padding-left: 0.7rem; padding-right: 0.7rem;}}
    }}
    """

    for i, status in enumerate(data["statuses"]):
        color = safe_color(data["status_colors"].get(status), PRIMARY)
        # Liseré de statut sur le côté gauche de chaque groupe du tableau principal.
        # Le pseudo-élément garantit un rendu identique à la synthèse de gauche.
        css += (
            f'[data-testid="stExpander"]:has(.pbm-group-{i}) {{'
            'position: relative !important;'
            'overflow: hidden !important;'
            '}\n'
            f'[data-testid="stExpander"]:has(.pbm-group-{i})::before {{'
            'content: "";'
            'position: absolute;'
            'left: 0;'
            'top: 0;'
            'bottom: 0;'
            'width: 4px;'
            f'background: {color};'
            'z-index: 3;'
            'pointer-events: none;'
            '}\n'
        )
        side_scope = css_scope(f"summary-{i}")
        css += (
            f'{side_scope} {{'
            f'border-left: 4px solid {color};'
            'padding: 0.25rem 0.28rem 0.28rem 0.38rem;'
            'margin-bottom: 0.18rem;'
            'background: rgba(248,248,253,0.78);'
            'border-radius: 10px;'
            'gap: 0 !important;'
            '}\n'
        )
    all_scope = css_scope("summary-all")
    css += (
        f'{all_scope} {{'
        f'border-left: 4px solid {PRIMARY};'
        'padding: 0.25rem 0.28rem 0.28rem 0.38rem;'
        'margin-bottom: 0.26rem;'
        'background: rgba(59,56,245,0.045);'
        'border-radius: 10px;'
        'gap: 0 !important;'
        '}\n'
    )

    for p in data.get("projects", []):
        type_color = safe_color(data["type_colors"].get(p.get("type"), PRIMARY), PRIMARY)
        css += (
            f'{css_scope(f"rowclr-{p["id"]}")} '
            '{'
            f'background:{hex_to_rgba(type_color, 0.14)};'
            f'box-shadow: inset 0 0 0 1px {hex_to_rgba(type_color, 0.18)};'
            f'border-left: 4px solid {type_color};'
            '}\n'
            f'{css_scope(f"rowclr-{p["id"]}")}:hover '
            '{'
            f'background:{hex_to_rgba(type_color, 0.2)};'
            '}\n'
        )

    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


