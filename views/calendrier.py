import calendar as cal
from datetime import date
from html import escape

import streamlit as st

from config import PRIMARY, PRIMARY_DARK, TEXT
from ui.components import hex_to_rgba, safe_color


def _change_calendar_month(delta: int):
    month = st.session_state.cal_month + delta
    year = st.session_state.cal_year
    if month == 0:
        month, year = 12, year - 1
    elif month == 13:
        month, year = 1, year + 1
    st.session_state.cal_month = month
    st.session_state.cal_year = year


def render_calendrier(data: dict):
    st.subheader("Vue calendrier (par date d'échéance)")

    if "cal_month" not in st.session_state:
        today = date.today()
        st.session_state.cal_month = today.month
        st.session_state.cal_year = today.year

    nav1, nav2, nav3 = st.columns([1, 2, 1])
    nav1.button(
        "◀ Mois précédent",
        on_click=_change_calendar_month,
        args=(-1,),
    )
    nav2.markdown(
        f"<h4 style='text-align:center; color:{PRIMARY_DARK}'>{cal.month_name[st.session_state.cal_month]} {st.session_state.cal_year}</h4>",
        unsafe_allow_html=True,
    )
    nav3.button(
        "Mois suivant ▶",
        on_click=_change_calendar_month,
        args=(1,),
    )

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
