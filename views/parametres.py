import streamlit as st

import storage as db
from config import PATH, PRIMARY, PRIMARY_DARK
from data_service import invalidate_data_cache, run_db_action
from ui.components import badge


def render_parametres(data: dict):
    settings_cols = st.columns([1, 1.15, 1.15], gap="medium")

    with settings_cols[0]:
        st.markdown("### 👥 Collaborateurs")
        for person in data["collaborators"]:
            c1, c2 = st.columns([4, 1])
            c1.write(person)
            c2.button(
                "🗑️",
                key=f"del_collab_{person}",
                on_click=run_db_action,
                args=("remove_collaborator", person),
            )
        with st.form("add_collab_form", clear_on_submit=True):
            new_person = st.text_input("Ajouter une personne")
            if st.form_submit_button("Ajouter") and new_person.strip():
                db.add_collaborator(PATH, new_person)
                invalidate_data_cache()
                st.rerun()

    with settings_cols[1]:
        st.markdown("### 🏷️ Statuts / groupes")
        st.caption("L'ordre ici définit l'ordre des groupes dans le tableau.")
        n_statuses = len(data["statuses"])
        for i, status in enumerate(data["statuses"]):
            c1, c2, c3, c4 = st.columns([3, 0.7, 0.7, 0.7])
            c1.markdown(
                badge(status, data["status_colors"].get(status, PRIMARY), PRIMARY_DARK),
                unsafe_allow_html=True,
            )
            c2.button(
                "▲",
                key=f"statusup_{status}",
                disabled=(i == 0),
                on_click=run_db_action,
                args=("move_status", status, -1),
            )
            c3.button(
                "▼",
                key=f"statusdown_{status}",
                disabled=(i == n_statuses - 1),
                on_click=run_db_action,
                args=("move_status", status, 1),
            )
            fallback = next((s for s in data["statuses"] if s != status), "En cours")
            c4.button(
                "🗑️",
                key=f"del_status_{status}",
                on_click=run_db_action,
                args=("remove_status", status, fallback),
            )
        with st.form("add_status_form", clear_on_submit=True):
            new_status = st.text_input("Nouveau statut / groupe")
            new_color = st.color_picker("Couleur", value=PRIMARY)
            if st.form_submit_button("Ajouter") and new_status.strip():
                db.add_status(PATH, new_status, new_color)
                invalidate_data_cache()
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
            c2.button(
                "▲",
                key=f"typeup_{t}",
                disabled=(i == 0),
                on_click=run_db_action,
                args=("move_type", t, -1),
            )
            c3.button(
                "▼",
                key=f"typedown_{t}",
                disabled=(i == n_types - 1),
                on_click=run_db_action,
                args=("move_type", t, 1),
            )
            c4.button(
                "🗑️",
                key=f"del_type_{t}",
                on_click=run_db_action,
                args=("remove_type", t),
            )
        with st.form("add_type_form", clear_on_submit=True):
            new_type = st.text_input("Nouveau type")
            new_type_color = st.color_picker("Couleur", value="#D6E6F5")
            if st.form_submit_button("Ajouter") and new_type.strip():
                db.add_type(PATH, new_type.strip().upper(), new_type_color)
                invalidate_data_cache()
                st.rerun()
