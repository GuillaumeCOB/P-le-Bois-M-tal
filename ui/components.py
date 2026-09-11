from contextlib import contextmanager
from datetime import date
from html import escape
import inspect
import re

import streamlit as st

from config import PRIMARY, PRIMARY_DARK

_HAS_CONTAINER_KEY = "key" in inspect.signature(st.container).parameters


def safe_color(value: str, fallback: str = PRIMARY) -> str:
    return value if isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?", value) else fallback


def hex_to_rgba(value: str, alpha: float) -> str:
    color = safe_color(value).lstrip("#")
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


def project_number_cell(project: dict):
    st.markdown(
        f'<div class="pbm-cell center-cell">{project_number_markup(project)}</div>',
        unsafe_allow_html=True,
    )


def grid_template(widths) -> str:
    return " ".join(f"{float(w):g}fr" for w in widths)


def render_grid_header(labels, widths, center_indices=(), right_indices=()):
    cells = []
    for idx, label in enumerate(labels):
        extra = " right" if idx in right_indices else " center" if idx in center_indices else ""
        cells.append(f'<div class="pbm-grid-cell{extra}">{escape(label)}</div>')
    st.markdown(
        '<div class="pbm-grid-header-wrap">'
        + f'<div class="pbm-grid-row pbm-grid-header" style="grid-template-columns:{grid_template(widths)}">'
        + "".join(cells)
        + "</div></div>",
        unsafe_allow_html=True,
    )


def project_totals(project: dict) -> tuple[float, float]:
    budget = sum(float(sp.get("budget", 0) or 0) for sp in project.get("subprojects", []))
    hours = sum(float(sp.get("estimated_time", 0) or 0) for sp in project.get("subprojects", []))
    return budget, hours


def projects_totals(projects: list[dict]) -> tuple[float, float]:
    budget = 0.0
    hours = 0.0
    for project in projects:
        p_budget, p_hours = project_totals(project)
        budget += p_budget
        hours += p_hours
    return budget, hours


def project_search_blob(project: dict) -> str:
    values = [
        project.get("project_number"),
        project.get("name"),
        project.get("client"),
        project.get("discipline"),
        project.get("status"),
        project.get("remarks"),
    ]
    for subproject in project.get("subprojects", []):
        values.extend(
            [
                subproject.get("type"),
                subproject.get("phase"),  # compatibilité avec les données v2
                subproject.get("remarks"),
                " ".join(subproject.get("assigned", [])),
            ]
        )
        for task in subproject.get("tasks", []):
            values.extend(
                [
                    task.get("name"),
                    task.get("remarks"),
                    " ".join(task.get("assigned", [])),
                ]
            )
    return " ".join(str(v or "") for v in values).casefold()


def render_project_group_total(projects: list[dict], widths):
    total_budget, total_hours = projects_totals(projects)
    values = [
        "",
        "",
        "",
        "TOTAL",
        f"{len(projects)} projet{'s' if len(projects) != 1 else ''}",
        "",
        "",
        display_amount(total_budget),
        display_hours(total_hours),
    ]
    cells = []
    for idx, value in enumerate(values):
        extra = " right" if idx in (7, 8) else " center" if idx in (0, 1, 2) else ""
        cells.append(f'<div class="pbm-grid-cell{extra}">{escape(value)}</div>')
    st.markdown(
        f'<div class="pbm-grid-row pbm-grid-total" style="grid-template-columns:{grid_template(widths)}">'
        + "".join(cells)
        + "</div>",
        unsafe_allow_html=True,
    )
