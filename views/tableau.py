from datetime import date, datetime

import streamlit as st

import storage as db
from config import (
    DISCIPLINE_COLORS,
    DISCIPLINES,
    PATH,
    PRIMARY,
    PRIMARY_DARK,
    PROJECT_ROW_LABELS,
    PROJECT_ROW_WIDTHS,
    SUBPROJECT_ROW_LABELS,
    SUBPROJECT_ROW_WIDTHS,
    TASK_ROW_LABELS,
    TASK_ROW_WIDTHS,
)
from data_service import (
    invalidate_data_cache,
    run_db_action,
    set_invoice_state_from_widget,
    toggle_session_flag,
)
from ui.components import (
    badge_cell,
    cell,
    display_amount,
    display_date,
    display_hours,
    project_number_cell,
    project_search_blob,
    project_totals,
    projects_totals,
    render_grid_header,
    render_project_group_total,
    ui_container,
)


def _set_summary_discipline(value):
    st.session_state["pbm_summary_discipline"] = value


def _set_summary_status(value):
    st.session_state["pbm_summary_status"] = value


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _project_matches_collaborator(project: dict, collaborator: str | None) -> bool:
    if collaborator is None:
        return True
    for subproject in project.get("subprojects", []):
        if collaborator in subproject.get("assigned", []):
            return True
        for task in subproject.get("tasks", []):
            if collaborator in task.get("assigned", []):
                return True
    return False


def _project_matches_type(project: dict, project_type: str | None) -> bool:
    if project_type is None:
        return True
    return any(
        (sp.get("type") or sp.get("phase")) == project_type
        for sp in project.get("subprojects", [])
    )


def _project_matches_status(project: dict, status: str | None) -> bool:
    if status is None:
        return True
    return project.get("status") == status


def _sort_projects(projects: list[dict]) -> list[dict]:
    return sorted(
        projects,
        key=lambda p: (
            str(p.get("project_number") or "999999999").casefold(),
            str(p.get("name") or "").casefold(),
        ),
    )


def _active_projects(data: dict) -> list[dict]:
    """Projets encore visibles dans le tableau principal."""
    return [p for p in data.get("projects", []) if not p.get("invoice_ready")]


@st.dialog("Modifier le projet")
def edit_project_dialog(project: dict, data: dict):
    with st.form(f"dialog_edit_project_{project['id']}"):
        c1, c2 = st.columns([1.0, 2.0])
        project_number = c1.text_input(
            "N° projet", value=str(project.get("project_number") or "")
        )
        name = c2.text_input("Nom du projet", value=str(project.get("name") or ""))

        c3, c4, c5 = st.columns([1.7, 1.1, 1.2])
        client = c3.text_input("Client", value=str(project.get("client") or ""))
        discipline = c4.selectbox(
            "Structure",
            DISCIPLINES,
            index=(
                DISCIPLINES.index(project.get("discipline"))
                if project.get("discipline") in DISCIPLINES
                else 0
            ),
        )
        current_status = project.get("status")
        status = c5.selectbox(
            "Statut",
            data["statuses"],
            index=(
                data["statuses"].index(current_status)
                if current_status in data["statuses"]
                else 0
            ),
        )
        remarks = st.text_area("Remarques", value=project.get("remarks", ""), height=110)

        b1, b2 = st.columns(2)
        save = b1.form_submit_button("💾 Enregistrer", use_container_width=True)
        delete = b2.form_submit_button("🗑️ Supprimer le projet", use_container_width=True)

    if save:
        if not name.strip():
            st.error("Le nom du projet est obligatoire.")
            return
        db.update_project(
            PATH,
            project["id"],
            {
                "project_number": project_number.strip() or None,
                "name": name.strip(),
                "client": client.strip(),
                "discipline": discipline,
                "status": status,
                "remarks": remarks,
            },
        )
        invalidate_data_cache()
        st.rerun()

    if delete:
        db.delete_project(PATH, project["id"])
        invalidate_data_cache()
        st.rerun()


@st.dialog("Modifier le sous-projet")
def edit_subproject_dialog(project: dict, subproject: dict, data: dict):
    with st.form(f"dialog_edit_subproject_{subproject['id']}"):
        current_type = subproject.get("type") or subproject.get("phase") or "(aucun)"
        type_options = ["(aucun)"] + list(data["types"])
        if current_type not in type_options:
            type_options.append(current_type)

        c0, c1 = st.columns([1.2, 1.8])
        project_type = c0.selectbox(
            "Type",
            type_options,
            index=type_options.index(current_type),
        )
        assigned = c1.multiselect(
            "Collaborateurs",
            data["collaborators"],
            default=[
                person
                for person in subproject.get("assigned", [])
                if person in data["collaborators"]
            ],
        )

        c2, c3, c4 = st.columns([1.2, 1.0, 1.0])
        due_date = c2.date_input(
            "Échéance",
            value=_parse_date(subproject.get("due_date")) or date.today(),
        )
        budget = c3.number_input(
            "Budget (€)",
            min_value=0.0,
            step=100.0,
            value=float(subproject.get("budget", 0) or 0),
        )
        estimated_time = c4.number_input(
            "Temps estimé (h)",
            min_value=0.0,
            step=0.5,
            value=float(subproject.get("estimated_time", 0) or 0),
        )
        remarks = st.text_area(
            "Remarques", value=subproject.get("remarks", ""), height=90
        )

        b1, b2 = st.columns(2)
        save = b1.form_submit_button("💾 Enregistrer", use_container_width=True)
        delete = b2.form_submit_button("🗑️ Supprimer le sous-projet", use_container_width=True)

    if save:
        selected_type = None if project_type == "(aucun)" else project_type
        run_db_action(
            "update_subproject",
            project["id"],
            subproject["id"],
            {
                # phase reste en miroir pour compatibilité avec les données v2.
                "phase": selected_type or "Sous-projet",
                "type": selected_type,
                "assigned": assigned,
                "due_date": due_date.isoformat() if due_date else None,
                "budget": budget,
                "estimated_time": estimated_time,
                "remarks": remarks,
            },
        )
        st.rerun()

    if delete:
        run_db_action("delete_subproject", project["id"], subproject["id"])
        st.rerun()


@st.dialog("Modifier la tâche")
def edit_task_dialog(project: dict, subproject: dict, task: dict, data: dict):
    with st.form(f"dialog_edit_task_{task['id']}"):
        name = st.text_input("Nom de la tâche", value=str(task.get("name") or ""))
        c1, c2 = st.columns([1.8, 1.2])
        assigned = c1.multiselect(
            "Collaborateurs",
            data["collaborators"],
            default=[
                person
                for person in task.get("assigned", [])
                if person in data["collaborators"]
            ],
        )
        due_date = c2.date_input(
            "Échéance", value=_parse_date(task.get("due_date")) or date.today()
        )

        c3, c4 = st.columns(2)
        budget = c3.number_input(
            "Budget (€)",
            min_value=0.0,
            step=100.0,
            value=float(task.get("budget", 0) or 0),
        )
        estimated_time = c4.number_input(
            "Temps estimé (h)",
            min_value=0.0,
            step=0.5,
            value=float(task.get("estimated_time", 0) or 0),
        )
        remarks = st.text_area("Remarques", value=task.get("remarks", ""), height=90)

        b1, b2 = st.columns(2)
        save = b1.form_submit_button("💾 Enregistrer", use_container_width=True)
        delete = b2.form_submit_button("🗑️ Supprimer la tâche", use_container_width=True)

    if save:
        if not name.strip():
            st.error("Le nom de la tâche est obligatoire.")
            return
        run_db_action(
            "update_task",
            project["id"],
            subproject["id"],
            task["id"],
            {
                "name": name.strip(),
                "assigned": assigned,
                "due_date": due_date.isoformat() if due_date else None,
                "budget": budget,
                "estimated_time": estimated_time,
                "remarks": remarks,
            },
        )
        st.rerun()

    if delete:
        run_db_action("delete_task", project["id"], subproject["id"], task["id"])
        st.rerun()


def render_side_summary(data: dict):
    if "pbm_summary_discipline" not in st.session_state:
        st.session_state["pbm_summary_discipline"] = None
    if "pbm_summary_status" not in st.session_state:
        st.session_state["pbm_summary_status"] = None

    selected_discipline = st.session_state.get("pbm_summary_discipline")
    selected_status = st.session_state.get("pbm_summary_status")
    all_projects = _active_projects(data)

    with ui_container("pbm_group_summary", "summary"):
        st.markdown('<div class="pbm-summary-title">Synthèse</div>', unsafe_allow_html=True)
        st.markdown('<div class="pbm-summary-section">Structure</div>', unsafe_allow_html=True)

        total_budget, _ = projects_totals(all_projects)
        with ui_container("pbm_summary_discipline_all", "summary-discipline-all"):
            st.button(
                "Toutes les structures",
                key="summary_discipline_all",
                use_container_width=True,
                type="primary" if selected_discipline is None else "secondary",
                on_click=_set_summary_discipline,
                args=(None,),
            )
            st.markdown(
                f'<div class="pbm-side-budget">{len(all_projects)} projet{"s" if len(all_projects) != 1 else ""} - {display_amount(total_budget)}</div>',
                unsafe_allow_html=True,
            )

        for i, discipline in enumerate(DISCIPLINES):
            discipline_projects = [
                p for p in all_projects if p.get("discipline") == discipline
            ]
            discipline_budget, _ = projects_totals(discipline_projects)
            with ui_container(
                f"pbm_summary_discipline_{i}", f"summary-discipline-{i}"
            ):
                st.button(
                    discipline,
                    key=f"summary_discipline_{i}",
                    use_container_width=True,
                    type="primary" if selected_discipline == discipline else "secondary",
                    on_click=_set_summary_discipline,
                    args=(discipline,),
                )
                st.markdown(
                    f'<div class="pbm-side-budget">{len(discipline_projects)} projet{"s" if len(discipline_projects) != 1 else ""} - {display_amount(discipline_budget)}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown(
            '<div class="pbm-summary-section second">Statut des projets</div>',
            unsafe_allow_html=True,
        )

        status_source_projects = [
            p
            for p in all_projects
            if selected_discipline is None or p.get("discipline") == selected_discipline
        ]
        all_status_budget, _ = projects_totals(status_source_projects)
        with ui_container("pbm_summary_status_all", "summary-status-all"):
            st.button(
                "Tous les statuts",
                key="summary_status_all",
                use_container_width=True,
                type="primary" if selected_status is None else "secondary",
                on_click=_set_summary_status,
                args=(None,),
            )
            st.markdown(
                f'<div class="pbm-side-budget">{len(status_source_projects)} projet{"s" if len(status_source_projects) != 1 else ""} - {display_amount(all_status_budget)}</div>',
                unsafe_allow_html=True,
            )

        for i, status in enumerate(data["statuses"]):
            status_projects = [
                p for p in status_source_projects if p.get("status") == status
            ]
            status_budget, _ = projects_totals(status_projects)
            with ui_container(f"pbm_summary_status_{i}", f"summary-status-{i}"):
                st.button(
                    status,
                    key=f"summary_status_{i}",
                    use_container_width=True,
                    type="primary" if selected_status == status else "secondary",
                    on_click=_set_summary_status,
                    args=(status,),
                )
                st.markdown(
                    f'<div class="pbm-side-budget">{len(status_projects)} projet{"s" if len(status_projects) != 1 else ""} - {display_amount(status_budget)}</div>',
                    unsafe_allow_html=True,
                )


def _render_add_task_form(project: dict, subproject: dict, data: dict):
    key = f"show_add_task_{subproject['id']}"
    if key not in st.session_state:
        st.session_state[key] = False

    st.button(
        "Masquer le formulaire" if st.session_state[key] else "Ajouter une tâche",
        key=f"toggle_add_task_{subproject['id']}",
        on_click=toggle_session_flag,
        args=(key,),
    )

    if not st.session_state[key]:
        return

    with st.form(f"add_task_{subproject['id']}", clear_on_submit=True):
        r1 = st.columns([2.4, 1.6])
        name = r1[0].text_input("Tâche", placeholder="Nom de la tâche")
        assigned = r1[1].multiselect("Collaborateur", data["collaborators"])
        r2 = st.columns([1.2, 1.0, 1.0])
        due_date = r2[0].date_input("Échéance", value=date.today())
        budget = r2[1].number_input("Budget (€)", min_value=0.0, step=100.0)
        hours = r2[2].number_input("Heures", min_value=0.0, step=0.5)
        if st.form_submit_button("Ajouter la tâche") and name.strip():
            # Le statut est porté par le projet. Le champ historique de la tâche
            # reçoit la même valeur uniquement pour compatibilité des données.
            db.add_task(
                PATH,
                project["id"],
                subproject["id"],
                name.strip(),
                assigned,
                project.get("status") or data["statuses"][0],
                due_date.isoformat() if due_date else None,
                budget,
                hours,
            )
            invalidate_data_cache()
            st.rerun()


def render_tasks(project: dict, subproject: dict, data: dict):
    tasks = [
        task for task in subproject.get("tasks", []) if not task.get("invoice_ready")
    ]
    with ui_container(f"pbm_tasks_{subproject['id']}", "tasks"):
        if tasks:
            render_grid_header(
                TASK_ROW_LABELS,
                TASK_ROW_WIDTHS,
                center_indices=(0, 1),
                right_indices=(5, 6),
            )
        else:
            st.caption("Aucune tâche active.")

        for task in tasks:
            with ui_container(f"pbm_taskrow_{task['id']}", "taskrow"):
                cols = st.columns(TASK_ROW_WIDTHS, gap="small", vertical_alignment="center")
                invoice_key = f"invoice_task_{task['id']}"
                cols[0].checkbox(
                    "À facturer",
                    value=False,
                    key=invoice_key,
                    label_visibility="collapsed",
                    help="Cocher pour envoyer cette tâche dans l'onglet À facturer.",
                    on_change=set_invoice_state_from_widget,
                    args=("task", project["id"], task["id"], invoice_key),
                )
                with cols[1]:
                    cell("↳", "center-cell")
                if cols[2].button(
                    task.get("name") or "Tâche",
                    key=f"task_name_{task['id']}",
                    use_container_width=True,
                    help="Modifier la tâche",
                ):
                    edit_task_dialog(project, subproject, task, data)
                with cols[3]:
                    cell(", ".join(task.get("assigned", [])) or "—")
                with cols[4]:
                    cell(display_date(task.get("due_date")))
                with cols[5]:
                    cell(display_amount(task.get("budget")), "number")
                with cols[6]:
                    cell(display_hours(task.get("estimated_time")), "number")

        _render_add_task_form(project, subproject, data)


def _render_add_subproject_form(project: dict, data: dict):
    key = f"show_add_subproject_{project['id']}"
    if key not in st.session_state:
        st.session_state[key] = False

    st.button(
        "Masquer le formulaire" if st.session_state[key] else "Ajouter un sous-projet",
        key=f"toggle_add_subproject_{project['id']}",
        on_click=toggle_session_flag,
        args=(key,),
    )

    if not st.session_state[key]:
        return

    with st.form(f"add_subproject_{project['id']}", clear_on_submit=True):
        r1 = st.columns([1.25, 1.75])
        type_options = ["(aucun)"] + list(data["types"])
        project_type = r1[0].selectbox("Type", type_options)
        assigned = r1[1].multiselect("Collaborateur", data["collaborators"])
        r2 = st.columns([1.2, 1.0, 1.0])
        due_date = r2[0].date_input("Échéance", value=date.today())
        budget = r2[1].number_input("Budget (€)", min_value=0.0, step=100.0)
        hours = r2[2].number_input("Heures", min_value=0.0, step=0.5)
        if st.form_submit_button("Ajouter le sous-projet"):
            selected_type = None if project_type == "(aucun)" else project_type
            db.add_subproject(
                PATH,
                project["id"],
                selected_type or "Sous-projet",
                selected_type,
                assigned,
                project.get("status") or data["statuses"][0],
                due_date.isoformat() if due_date else None,
                budget,
                hours,
            )
            invalidate_data_cache()
            st.rerun()


def render_subprojects(project: dict, data: dict):
    subprojects = [
        sp for sp in project.get("subprojects", []) if not sp.get("invoice_ready")
    ]
    with ui_container(f"pbm_subprojects_{project['id']}", "subprojects"):
        if subprojects:
            render_grid_header(
                SUBPROJECT_ROW_LABELS,
                SUBPROJECT_ROW_WIDTHS,
                center_indices=(0, 1),
                right_indices=(5, 6),
            )
        else:
            st.caption("Aucun sous-projet actif.")

        for subproject in subprojects:
            expand_key = f"expand_subproject_{subproject['id']}"
            if expand_key not in st.session_state:
                st.session_state[expand_key] = False

            display_type = subproject.get("type") or subproject.get("phase") or "—"
            type_color = data["type_colors"].get(display_type, PRIMARY)
            with ui_container(
                f"pbm_subprojectrow_{subproject['id']}",
                ["subprojectrow", f"subprojectclr-{subproject['id']}"],
            ):
                cols = st.columns(
                    SUBPROJECT_ROW_WIDTHS, gap="small", vertical_alignment="center"
                )
                invoice_key = f"invoice_subproject_{subproject['id']}"
                cols[0].checkbox(
                    "À facturer",
                    value=False,
                    key=invoice_key,
                    label_visibility="collapsed",
                    help="Cocher pour envoyer ce sous-projet dans l'onglet À facturer.",
                    on_change=set_invoice_state_from_widget,
                    args=("subproject", project["id"], subproject["id"], invoice_key),
                )
                arrow = "▾" if st.session_state[expand_key] else "▸"
                cols[1].button(
                    arrow,
                    key=f"arrow_subproject_{subproject['id']}",
                    on_click=toggle_session_flag,
                    args=(expand_key,),
                    help="Afficher / masquer les tâches",
                )
                if cols[2].button(
                    display_type,
                    key=f"subproject_name_{subproject['id']}",
                    use_container_width=True,
                    help="Modifier le sous-projet",
                ):
                    edit_subproject_dialog(project, subproject, data)
                with cols[3]:
                    cell(", ".join(subproject.get("assigned", [])) or "—")
                with cols[4]:
                    cell(display_date(subproject.get("due_date")))
                with cols[5]:
                    cell(display_amount(subproject.get("budget")), "number")
                with cols[6]:
                    cell(display_hours(subproject.get("estimated_time")), "number")

            if st.session_state[expand_key]:
                render_tasks(project, subproject, data)

        _render_add_subproject_form(project, data)


def render_project_row(project: dict, data: dict):
    project_id = project["id"]
    expand_key = f"expand_project_{project_id}"
    if expand_key not in st.session_state:
        st.session_state[expand_key] = False

    total_budget, total_hours = project_totals(project)
    discipline = project.get("discipline") or DISCIPLINES[0]
    status = project.get("status") or data["statuses"][0]

    with ui_container(f"pbm_project_{project_id}", "project"):
        with ui_container(
            f"pbm_projectrow_{project_id}",
            [
                "projectrow",
                f"discipline-row-{DISCIPLINES.index(discipline) if discipline in DISCIPLINES else 0}",
            ],
        ):
            cols = st.columns(PROJECT_ROW_WIDTHS, gap="small", vertical_alignment="center")
            invoice_key = f"invoice_project_{project_id}"
            cols[0].checkbox(
                "À facturer",
                value=False,
                key=invoice_key,
                label_visibility="collapsed",
                help="Cocher pour envoyer le projet complet dans l'onglet À facturer.",
                on_change=set_invoice_state_from_widget,
                args=("project", project_id, None, invoice_key),
            )
            arrow = "▾" if st.session_state[expand_key] else "▸"
            cols[1].button(
                arrow,
                key=f"arrow_project_{project_id}",
                help="Afficher / masquer les sous-projets",
                on_click=toggle_session_flag,
                args=(expand_key,),
            )
            with cols[2]:
                project_number_cell(project)
            if cols[3].button(
                project.get("name") or "Projet",
                key=f"project_name_{project_id}",
                use_container_width=True,
                help="Modifier le projet",
            ):
                edit_project_dialog(project, data)
            with cols[4]:
                cell(project.get("client") or "—")
            with cols[5]:
                badge_cell(
                    discipline,
                    DISCIPLINE_COLORS.get(discipline, PRIMARY),
                    PRIMARY_DARK,
                )
            with cols[6]:
                badge_cell(
                    status,
                    data["status_colors"].get(status, PRIMARY),
                    PRIMARY_DARK,
                )
            with cols[7]:
                cell(display_amount(total_budget), "number")
            with cols[8]:
                cell(display_hours(total_hours), "number")

        if st.session_state[expand_key]:
            render_subprojects(project, data)


def render_tableau(data: dict):
    left_col, main_col = st.columns([1.25, 6.75], gap="medium")

    with left_col:
        render_side_summary(data)

    with main_col:
        with ui_container("pbm_board", "board"):
            filters = st.columns([1.7, 1.0, 1.0], gap="small")
            query = filters[0].text_input(
                "Rechercher un projet",
                placeholder="Rechercher n°, projet, client, type, tâche...",
                label_visibility="collapsed",
                key="pbm_search",
            ).strip().casefold()
            person_filter = filters[1].selectbox(
                "Collaborateur",
                [None] + data["collaborators"],
                format_func=lambda x: "Tous les collaborateurs" if x is None else x,
                label_visibility="collapsed",
                key="pbm_person",
            )
            type_filter = filters[2].selectbox(
                "Type",
                [None] + data["types"],
                format_func=lambda x: "Tous les types" if x is None else x,
                label_visibility="collapsed",
                key="pbm_type",
            )

            discipline_filter = st.session_state.get("pbm_summary_discipline")
            status_filter = st.session_state.get("pbm_summary_status")

            projects = [
                project
                for project in _active_projects(data)
                if (not query or query in project_search_blob(project))
                and _project_matches_collaborator(project, person_filter)
                and _project_matches_type(project, type_filter)
                and _project_matches_status(project, status_filter)
                and (
                    discipline_filter is None
                    or project.get("discipline") == discipline_filter
                )
            ]

            if not _active_projects(data):
                st.info("Aucun projet actif. Les projets mis à facturer sont visibles dans l'onglet À facturer.")
            elif not projects:
                st.info("Aucun projet ne correspond aux filtres.")

            # Affichage principal trié par statut, dans l'ordre défini dans Paramètres.
            for status_index, status in enumerate(data["statuses"]):
                if status_filter is not None and status != status_filter:
                    continue

                status_projects = _sort_projects(
                    [p for p in projects if p.get("status") == status]
                )
                if not status_projects:
                    continue

                total_budget, total_hours = projects_totals(status_projects)
                count = len(status_projects)
                title = (
                    f"{status} · {count} projet{'s' if count != 1 else ''}"
                    f" · {display_amount(total_budget)} · {display_hours(total_hours)}"
                )
                with st.expander(title, expanded=True):
                    with ui_container(
                        f"pbm_status_group_{status_index}",
                        f"status-group-{status_index}",
                    ):
                        render_grid_header(
                            PROJECT_ROW_LABELS,
                            PROJECT_ROW_WIDTHS,
                            center_indices=(0, 1, 2),
                            right_indices=(7, 8),
                        )
                        for project in status_projects:
                            render_project_row(project, data)
                        render_project_group_total(
                            status_projects, PROJECT_ROW_WIDTHS
                        )
