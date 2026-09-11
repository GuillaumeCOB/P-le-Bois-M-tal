from datetime import date

import streamlit as st

import storage as db
from config import PATH
from data_service import invalidate_data_cache
from ui.components import ui_container


def render_nouveau_projet(data: dict):
    with ui_container("pbm_form_add", "formcard"):
        st.subheader("Créer un nouveau projet")
        with st.form("new_project_form", clear_on_submit=True):
            top = st.columns([1, 1.6, 1.2])
            project_number = top[0].text_input("N° projet")
            name = top[1].text_input("Nom du projet *")
            type_options = ["(aucun)"] + data["types"]
            project_type = top[2].selectbox("Type de projet", type_options)

            col1, col2 = st.columns(2)
            with col1:
                status = st.selectbox("Statut / groupe", data["statuses"])
                assigned = st.multiselect("Personnes assignées", data["collaborators"])
                estimated_time = st.number_input("Temps estimé (h)", min_value=0.0, step=0.5)
            with col2:
                start_date_val = st.date_input("Date de début (optionnel)", value=None)
                due_date_val = st.date_input("Date d'échéance", value=date.today())
                budget = st.number_input("Budget (€)", min_value=0.0, step=100.0)
            remarks = st.text_area("Remarques", height=120)

            submitted = st.form_submit_button("➕ Créer le projet")
            if submitted:
                if not name.strip():
                    st.error("Le nom du projet est obligatoire.")
                else:
                    project = db.new_project_dict(
                        name=name,
                        status=status,
                        assigned=assigned,
                        estimated_time=estimated_time,
                        start_date=start_date_val.isoformat() if start_date_val else None,
                        due_date=due_date_val.isoformat() if due_date_val else None,
                        budget=budget,
                        remarks=remarks,
                        project_type=None if project_type == "(aucun)" else project_type,
                    )
                    project["project_number"] = project_number.strip() or None
                    db.add_project(PATH, project)
                    invalidate_data_cache()
                    st.success(f"Projet « {name} » créé.")
                    st.rerun()
