"""
Outil interne de gestion de projets — Pôle Structures
Version hiérarchique : Projet -> Sous-projet / phase -> Tâche.

Lancement local : streamlit run app.py
"""

import streamlit as st

st.set_page_config(
    page_title="Builders - Verticalsea - Gestion Structures",
    layout="wide",
    initial_sidebar_state="collapsed",
)

from data_service import load_data_cached
from ui.components import ui_container
from ui.header import render_header
from ui.styles import inject_brand_styles
from views.a_facturer import render_a_facturer
from views.calendrier import render_calendrier
from views.gantt import render_gantt
from views.nouveau_projet import render_nouveau_projet
from views.parametres import render_parametres
from views.tableau import render_tableau
from views.export_pdf import (
    build_tableau_pdf,
    current_tableau_filters,
    tableau_export_filename,
)


def _set_active_page(page_name: str):
    st.session_state["pbm_active_page"] = page_name


def _toggle_urgent_filter():
    st.session_state["pbm_urgent_only"] = not bool(
        st.session_state.get("pbm_urgent_only", False)
    )


try:
    data = load_data_cached()
except Exception as e:
    st.error(
        "Impossible de se connecter à la base de données partagée. "
        "Vérifiez que SUPABASE_URL et SUPABASE_KEY sont bien configurés "
        "dans les secrets de l'application (voir README.txt)."
    )
    st.exception(e)
    st.stop()

inject_brand_styles(data)
render_header()

if "pbm_active_page" not in st.session_state:
    st.session_state["pbm_active_page"] = "Tableau"
if "pbm_urgent_only" not in st.session_state:
    st.session_state["pbm_urgent_only"] = False

with ui_container("pbm_main_navigation", "nav"):
    nav_cols = st.columns(
        [1.0, 1.42, 1.05, 1.05, 0.85, 1.15, 2.10, 1.05, 1.20],
        gap="small",
    )
    nav_items = ["Tableau", "Nouveau projet", "À facturer", "Calendrier", "Gantt", "Paramètres"]
    for col, page_name in zip(nav_cols[:6], nav_items):
        with col:
            st.button(
                page_name,
                key=f"nav_{page_name}",
                use_container_width=True,
                type="primary" if st.session_state["pbm_active_page"] == page_name else "secondary",
                on_click=_set_active_page,
                args=(page_name,),
            )

    if st.session_state["pbm_active_page"] == "Tableau":
        urgent_active = bool(st.session_state.get("pbm_urgent_only", False))
        with nav_cols[7]:
            with ui_container(
                "pbm_urgent_filter",
                ["urgentfilter", "urgentfilteractive"] if urgent_active else "urgentfilter",
            ):
                st.button(
                    "Urgents ✓" if urgent_active else "Urgents",
                    key="toggle_urgent_filter",
                    use_container_width=True,
                    on_click=_toggle_urgent_filter,
                )

        pdf_filters = current_tableau_filters()
        pdf_bytes = build_tableau_pdf(data, pdf_filters)
        with nav_cols[8]:
            st.download_button(
                "Export PDF",
                data=pdf_bytes,
                file_name=tableau_export_filename(),
                mime="application/pdf",
                key="export_tableau_pdf",
                use_container_width=True,
            )

active_page = st.session_state["pbm_active_page"]

if active_page == "Tableau":
    render_tableau(data)
elif active_page == "Nouveau projet":
    render_nouveau_projet(data)
elif active_page == "À facturer":
    render_a_facturer(data)
elif active_page == "Calendrier":
    render_calendrier(data)
elif active_page == "Gantt":
    render_gantt(data)
elif active_page == "Paramètres":
    render_parametres(data)
