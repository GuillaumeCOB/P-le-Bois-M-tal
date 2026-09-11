import calendar as cal
from datetime import date
from html import escape

import streamlit as st

from config import BORDER, PRIMARY, PRIMARY_DARK, TEXT
from ui.components import hex_to_rgba, safe_color


WEEKDAY_LABELS = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]


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
            display: grid;
            grid-template-columns: repeat(7, minmax(0, 1fr));
            width: 100%;
            border-top: 1px solid {BORDER};
            border-left: 1px solid {BORDER};
            border-radius: 12px;
            overflow: hidden;
            background: #ffffff;
            box-shadow: 0 6px 20px rgba(64, 51, 140, 0.035);
        }}

        .pbm-calendar-head {{
            box-sizing: border-box;
            padding: 0.48rem 0.4rem;
            border-right: 1px solid {BORDER};
            border-bottom: 1px solid {BORDER};
            background: rgba(59, 56, 245, 0.055);
            color: {PRIMARY_DARK};
            font-size: 0.76rem;
            font-weight: 750;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }}

        .pbm-calendar-head.weekend {{
            background: rgba(64, 51, 140, 0.075);
        }}

        .pbm-calendar-day {{
            position: relative;
            box-sizing: border-box;
            min-width: 0;
            min-height: 100px;
            padding: 0.42rem 0.42rem 0.5rem;
            border-right: 1px solid {BORDER};
            border-bottom: 1px solid {BORDER};
            background: rgba(255, 255, 255, 0.96);
            overflow: hidden;
        }}

        .pbm-calendar-day.weekend {{
            background: rgba(64, 51, 140, 0.028);
        }}

        .pbm-calendar-day.empty {{
            background: rgba(112, 117, 154, 0.025);
        }}

        .pbm-calendar-day.today {{
            background: {hex_to_rgba(PRIMARY, 0.055)};
            box-shadow: inset 0 0 0 2px {hex_to_rgba(PRIMARY, 0.55)};
        }}

        .pbm-calendar-number {{
            display: flex;
            justify-content: flex-end;
            align-items: center;
            min-height: 24px;
            margin-bottom: 0.18rem;
            color: {PRIMARY_DARK};
            font-size: 0.78rem;
            font-weight: 750;
            font-variant-numeric: tabular-nums;
        }}

        .pbm-calendar-day.today .pbm-calendar-number span {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 24px;
            height: 24px;
            border-radius: 999px;
            background: {PRIMARY};
            color: #ffffff;
        }}

        .pbm-calendar-event {{
            box-sizing: border-box;
            width: 100%;
            margin-top: 0.28rem;
            padding: 0.28rem 0.38rem;
            border-radius: 7px;
            color: {TEXT};
            font-size: 0.71rem;
            line-height: 1.18;
            overflow: hidden;
        }}

        .pbm-calendar-event strong {{
            color: {PRIMARY_DARK};
            font-weight: 800;
        }}

        .pbm-calendar-event-name {{
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        @media (max-width: 980px) {{
            .pbm-calendar-day {{
                min-height: 105px;
                padding: 0.32rem;
            }}
            .pbm-calendar-event {{
                padding: 0.24rem 0.3rem;
                font-size: 0.66rem;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _project_card(project: dict, data: dict) -> str:
    project_type = project.get("type")
    color = safe_color(data["type_colors"].get(project_type, PRIMARY), PRIMARY)
    number = escape(str(project.get("project_number") or "—"), quote=True)
    name = escape(str(project.get("name") or ""), quote=True)
    tooltip = escape(
        f"{project.get('project_number') or '—'} · {project.get('name') or ''}",
        quote=True,
    )

    return (
        f'<div class="pbm-calendar-event" title="{tooltip}" '
        f'style="background:{hex_to_rgba(color, 0.14)}; '
        f'border-left:4px solid {color};">'
        f'<div class="pbm-calendar-event-name"><strong>{number}</strong> · {name}</div>'
        f'</div>'
    )


def _render_calendar_grid(data: dict):
    year = st.session_state.cal_year
    month = st.session_state.cal_month
    today = date.today()

    by_day = {}
    for project in data.get("projects", []):
        due_date = project.get("due_date")
        if due_date:
            by_day.setdefault(due_date, []).append(project)

    month_matrix = cal.monthcalendar(year, month)

    html = ['<div class="pbm-calendar-grid">']

    for index, label in enumerate(WEEKDAY_LABELS):
        weekend_class = " weekend" if index >= 5 else ""
        html.append(
            f'<div class="pbm-calendar-head{weekend_class}">{escape(label)}</div>'
        )

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

            day_str = current_date.isoformat()
            html.append(f'<div class="{" ".join(classes)}">')
            html.append(
                f'<div class="pbm-calendar-number"><span>{day}</span></div>'
            )

            for project in by_day.get(day_str, []):
                html.append(_project_card(project, data))

            html.append("</div>")

    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


def render_calendrier(data: dict):
    _calendar_styles()

    st.subheader("Vue calendrier (par date d'échéance)")

    if "cal_month" not in st.session_state:
        today = date.today()
        st.session_state.cal_month = today.month
        st.session_state.cal_year = today.year

    nav1, nav2, nav3 = st.columns([1, 2, 1], vertical_alignment="center")
    nav1.button(
        "◀ Mois précédent",
        on_click=_change_calendar_month,
        args=(-1,),
        use_container_width=True,
    )
    nav2.markdown(
        f"<h4 style='text-align:center; color:{PRIMARY_DARK}; margin:0;'>"
        f"{cal.month_name[st.session_state.cal_month]} {st.session_state.cal_year}</h4>",
        unsafe_allow_html=True,
    )
    nav3.button(
        "Mois suivant ▶",
        on_click=_change_calendar_month,
        args=(1,),
        use_container_width=True,
    )

    _render_calendar_grid(data)
