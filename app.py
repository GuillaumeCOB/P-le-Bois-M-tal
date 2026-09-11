"""
Outil interne de gestion de projets — Pôle BOIS/METAL
Version modulaire : app.py pilote l'application, les vues et styles sont séparés.

Lancement local : streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Builders - Verticalsea - Gestion Pôle BOIS",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from data_service import load_data_cached
from ui.components import ui_container
from ui.header import render_header
from ui.styles import inject_brand_styles
from views.calendrier import render_calendrier
from views.gantt import render_gantt
from views.nouveau_projet import render_nouveau_projet
from views.parametres import render_parametres
from views.tableau import render_tableau


def _set_active_page(page_name: str):
    st.session_state["pbm_active_page"] = page_name


try:
    data = load_data_cached()
except Exception as e:
    st.error(
        "Impossible de se connecter à la base de données partagée. "
        "Vérifiez que SUPABASE_URL et SUPABASE_KEY sont bien configurés "
        "dans les secrets de l'application (voir README.md)."
    )
    st.exception(e)
    st.stop()

inject_brand_styles(data)
render_header()

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

if active_page == "Tableau":
    render_tableau(data)
elif active_page == "Nouveau projet":
    render_nouveau_projet(data)
elif active_page == "Calendrier":
    render_calendrier(data)
elif active_page == "Gantt":
    render_gantt(data)
elif active_page == "Paramètres":
    render_parametres(data)
