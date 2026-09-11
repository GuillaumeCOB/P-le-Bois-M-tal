import streamlit as st

import storage as db
from config import DISCIPLINES, PATH
from data_service import invalidate_data_cache
from ui.components import ui_container


def render_nouveau_projet(data: dict):
    with ui_container("pbm_form_add", "formcard"):
        st.subheader("Créer un nouveau projet")
        with st.form("new_project_form", clear_on_submit=True):
            top = st.columns([1.0, 1.8, 1.5, 1.25])
            project_number = top[0].text_input("N° projet")
            name = top[1].text_input("Nom du projet *")
            client = top[2].text_input("Client")
            discipline = top[3].selectbox("Structure", DISCIPLINES)
            remarks = st.text_area("Remarques", height=120)

            submitted = st.form_submit_button("➕ Créer le projet")
            if submitted:
                if not name.strip():
                    st.error("Le nom du projet est obligatoire.")
                else:
                    project = db.new_project_dict(
                        name=name.strip(),
                        project_number=project_number.strip() or None,
                        client=client.strip(),
                        discipline=discipline,
                        remarks=remarks,
                    )
                    db.add_project(PATH, project)
                    invalidate_data_cache()
                    st.success(f"Projet « {name.strip()} » créé.")
                    st.rerun()
