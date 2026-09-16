import streamlit as st

import storage as db
from config import PATH, PRIMARY, PRIMARY_DARK
from data_service import invalidate_data_cache, run_db_action
from ui.components import badge


@st.dialog("Modifier le statut", width="medium")
def edit_status_dialog(status: str, data: dict):
    current_color = data["status_colors"].get(status, PRIMARY)
    with st.form(f"edit_status_{status}"):
        new_name = st.text_input("Nom du statut / groupe", value=status)
        new_color = st.color_picker("Couleur", value=current_color)
        save = st.form_submit_button("Enregistrer", use_container_width=True)

    if save:
        clean_name = new_name.strip()
        if not clean_name:
            st.error("Le nom du statut est obligatoire.")
            return
        if clean_name != status and clean_name in data["statuses"]:
            st.error("Ce statut existe deja.")
            return
        run_db_action("update_status", status, clean_name, new_color)
        st.rerun()


@st.dialog("Modifier le type de sous-projet", width="medium")
def edit_type_dialog(project_type: str, data: dict):
    current_color = data["type_colors"].get(project_type, PRIMARY_DARK)
    with st.form(f"edit_type_{project_type}"):
        new_name = st.text_input("Nom du type", value=project_type)
        new_color = st.color_picker("Couleur", value=current_color)
        save = st.form_submit_button("Enregistrer", use_container_width=True)

    if save:
        clean_name = new_name.strip().upper()
        if not clean_name:
            st.error("Le nom du type est obligatoire.")
            return
        if clean_name != project_type and clean_name in data["types"]:
            st.error("Ce type existe deja.")
            return
        run_db_action("update_type", project_type, clean_name, new_color)
        st.rerun()


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
            c1, c2, c3, c4, c5 = st.columns([3, 0.7, 0.7, 0.7, 0.7])
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
            if c4.button(
                "✏️",
                key=f"edit_status_{status}",
            ):
                edit_status_dialog(status, data)
            fallback = next((s for s in data["statuses"] if s != status), "En cours")
            c5.button(
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
        st.markdown("### 🏗️ Types de sous-projet")
        st.caption("Le type correspond à la phase : DIAGNOSTIC, APS, APD, PRO, DCE, EXE…")
        n_types = len(data["types"])
        for i, t in enumerate(data["types"]):
            c1, c2, c3, c4, c5 = st.columns([3, 0.7, 0.7, 0.7, 0.7])
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
            if c4.button(
                "✏️",
                key=f"edit_type_{t}",
            ):
                edit_type_dialog(t, data)
            c5.button(
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
