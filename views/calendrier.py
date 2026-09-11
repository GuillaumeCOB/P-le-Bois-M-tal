import calendar as cal
import math
from datetime import date, timedelta
from html import escape

import streamlit as st

from config import BORDER, PRIMARY, PRIMARY_DARK, TEXT
from ui.components import hex_to_rgba, safe_color

WEEKDAY_LABELS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
HOURS_PER_DAY = 8
MOIS_FR = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]


def _change_calendar_month(delta: int):
    month = st.session_state.cal_month + delta
    year = st.session_state.cal_year
    if month == 0:
        month, year = 12, year - 1
    elif month == 13:
        month, year = 1, year + 1
    st.session_state.cal_month = month
    st.session_state.cal_year = year


def _calendar_styles():
    st.markdown(
        f"""
        <style>
        .pbm-calendar-grid {{
            display:grid; grid-template-columns:repeat(7,minmax(0,1fr)); width:100%;
            border-top:1px solid {BORDER}; border-left:1px solid {BORDER};
            border-radius:12px; overflow:hidden; background:#fff;
            box-shadow:0 6px 20px rgba(64,51,140,.035);
        }}
        .pbm-calendar-head {{
            box-sizing:border-box; padding:.48rem .4rem; border-right:1px solid {BORDER};
            border-bottom:1px solid {BORDER}; background:rgba(59,56,245,.055);
            color:{PRIMARY_DARK}; font-size:.76rem; font-weight:750; text-align:center;
            text-transform:uppercase; letter-spacing:.04em;
        }}
        .pbm-calendar-head.weekend {{background:rgba(64,51,140,.075);}}
        .pbm-calendar-day {{
            position:relative; box-sizing:border-box; min-width:0; min-height:100px;
            padding:.42rem .42rem .5rem; border-right:1px solid {BORDER};
            border-bottom:1px solid {BORDER}; background:rgba(255,255,255,.96); overflow:hidden;
        }}
        .pbm-calendar-day.weekend {{background:rgba(64,51,140,.028);}}
        .pbm-calendar-day.empty {{background:rgba(112,117,154,.025);}}
        .pbm-calendar-day.today {{
            background:{hex_to_rgba(PRIMARY,.055)};
            box-shadow:inset 0 0 0 2px {hex_to_rgba(PRIMARY,.55)};
        }}
        .pbm-calendar-number {{
            display:flex; justify-content:flex-end; align-items:center; min-height:24px;
            margin-bottom:.18rem; color:{PRIMARY_DARK}; font-size:.78rem; font-weight:750;
        }}
        .pbm-calendar-day.today .pbm-calendar-number span {{
            display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px;
            border-radius:999px; background:{PRIMARY}; color:#fff;
        }}
        .pbm-calendar-event {{
            box-sizing:border-box; width:100%; margin-top:.28rem; padding:.28rem .38rem;
            border-radius:7px; color:{TEXT}; font-size:.69rem; line-height:1.18; overflow:hidden;
        }}
        .pbm-calendar-event.due {{box-shadow:inset -2px 0 0 {PRIMARY_DARK};}}
        .pbm-calendar-event strong {{color:{PRIMARY_DARK}; font-weight:800;}}
        .pbm-calendar-event-name {{overflow:hidden; text-overflow:ellipsis; white-space:nowrap;}}
        @media (max-width:980px) {{
            .pbm-calendar-day {{min-height:105px; padding:.32rem;}}
            .pbm-calendar-event {{padding:.24rem .3rem; font-size:.64rem;}}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _workdays(item: dict):
    due = _parse_date(item.get("due_date"))
    if due is None:
        return [], None
    try:
        hours = float(item.get("estimated_time", 0) or 0)
    except (TypeError, ValueError):
        hours = 0
    duration = max(1, math.ceil(hours / HOURS_PER_DAY))
    days = []
    current = due
    while len(days) < duration:
        if current.weekday() < 5:
            days.append(current)
        current -= timedelta(days=1)
    days.reverse()
    return days, due


def _planning_items(data: dict):
    items = []
    for project in data.get("projects", []):
        for subproject in project.get("subprojects", []):
            tasks = subproject.get("tasks", [])
            if tasks:
                for task in tasks:
                    items.append(
                        {
                            **task,
                            "display_name": f"{subproject.get('type') or subproject.get('phase') or 'Sous-projet'} · {task.get('name') or 'Tâche'}",
                            "project_number": project.get("project_number"),
                            "project_name": project.get("name"),
                            "type": subproject.get("type"),
                        }
                    )
            else:
                items.append(
                    {
                        **subproject,
                        "display_name": subproject.get("type") or subproject.get("phase") or "Sous-projet",
                        "project_number": project.get("project_number"),
                        "project_name": project.get("name"),
                    }
                )
    return items


def _item_card(item: dict, data: dict, current_date: date, due_date: date) -> str:
    color = safe_color(data.get("type_colors", {}).get(item.get("type"), PRIMARY), PRIMARY)
    number = escape(str(item.get("project_number") or "—"), quote=True)
    project_name = escape(str(item.get("project_name") or ""), quote=True)
    display_name = escape(str(item.get("display_name") or ""), quote=True)
    try:
        hours = float(item.get("estimated_time", 0) or 0)
    except (TypeError, ValueError):
        hours = 0
    tooltip = escape(
        f"{item.get('project_number') or '—'} · {item.get('project_name') or ''} · {item.get('display_name') or ''} · {hours:g} h",
        quote=True,
    )
    due_class = " due" if current_date == due_date else ""
    return (
        f'<div class="pbm-calendar-event{due_class}" title="{tooltip}" '
        f'style="background:{hex_to_rgba(color,.14)};border-left:4px solid {color};">'
        f'<div class="pbm-calendar-event-name"><strong>{number}</strong> · {project_name} · {display_name}</div>'
        f'</div>'
    )


def _items_by_day(data: dict):
    by_day = {}
    for item in _planning_items(data):
        workdays, due = _workdays(item)
        if not workdays or due is None:
            continue
        for current in workdays:
            by_day.setdefault(current, []).append((item, due))
    return by_day


def _render_calendar_grid(data: dict):
    year = st.session_state.cal_year
    month = st.session_state.cal_month
    today = date.today()
    by_day = _items_by_day(data)
    month_matrix = cal.monthcalendar(year, month)
    html = ['<div class="pbm-calendar-grid">']

    for index, label in enumerate(WEEKDAY_LABELS):
        weekend = " weekend" if index >= 5 else ""
        html.append(f'<div class="pbm-calendar-head{weekend}">{escape(label)}</div>')

    for week in month_matrix:
        for weekday_index, day in enumerate(week):
            classes = ["pbm-calendar-day"]
            if weekday_index >= 5:
                classes.append("weekend")
            if day == 0:
                classes.append("empty")
                html.append(f'<div class="{" ".join(classes)}"></div>')
                continue
            current_date = date(year, month, day)
            if current_date == today:
                classes.append("today")
            html.append(f'<div class="{" ".join(classes)}">')
            html.append(f'<div class="pbm-calendar-number"><span>{day}</span></div>')
            if weekday_index < 5:
                for item, due_date in by_day.get(current_date, []):
                    html.append(_item_card(item, data, current_date, due_date))
            html.append("</div>")

    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_calendrier(data: dict):
    _calendar_styles()
    st.subheader("Vue calendrier (charge estimée)")

    if "cal_month" not in st.session_state:
        today = date.today()
        st.session_state.cal_month = today.month
        st.session_state.cal_year = today.year

    nav1, nav2, nav3 = st.columns([1, 2, 1], vertical_alignment="center")
    nav1.button("◀ Mois précédent", on_click=_change_calendar_month, args=(-1,), use_container_width=True)
    nav2.markdown(
        f"<h4 style='text-align:center;color:{PRIMARY_DARK}'>{MOIS_FR[st.session_state.cal_month]} {st.session_state.cal_year}</h4>",
        unsafe_allow_html=True,
    )
    nav3.button("Mois suivant ▶", on_click=_change_calendar_month, args=(1,), use_container_width=True)
    _render_calendar_grid(data)
