from datetime import date, datetime

import streamlit as st

import storage as db
from config import PATH, PRIMARY, PRIMARY_DARK, ROW_WIDTHS
from data_service import (
    invalidate_data_cache,
    run_db_action,
    set_subtask_done,
    toggle_session_flag,
)
from ui.components import (
    badge_cell,
    cell,
    display_amount,
    display_date,
    display_hours,
    get_group_totals,
    project_number_cell,
    project_search_blob,
    render_group_header,
    render_group_total_html,
    ui_container,
)


def _set_summary_status(status):
    st.session_state["pbm_summary_status"] = status


@st.dialog("Modifier le projet")
def edit_project_dialog(p: dict, data: dict):
    with st.form(f"dialog_edit_{p['id']}"):
        c0, c1, c2 = st.columns([1, 1.2, 1.2])
        project_number = c0.text_input("N° projet", value=str(p.get("project_number") or ""))
        name = c1.text_input("Nom du projet", value=p["name"])
        type_options = ["(aucun)"] + data["types"]
        current_type = p.get("type") or "(aucun)"
        type_idx = type_options.index(current_type) if current_type in type_options else 0
        project_type = c2.selectbox("Type", type_options, index=type_idx)

        col1, col2 = st.columns(2)
        with col1:
            status = st.selectbox(
                "Statut", data["statuses"], index=data["statuses"].index(p["status"])
            )
            assigned = st.multiselect(
                "Personnes assignées",
                data["collaborators"],
                default=[a for a in p.get("assigned", []) if a in data["collaborators"]],
            )
            estimated_time = st.number_input(
                "Temps estimé (h)", min_value=0.0, step=0.5,
                value=float(p.get("estimated_time", 0.0)),
            )
        with col2:
            start_date_val = st.date_input(
                "Date de début (optionnel)",
                value=(
                    datetime.strptime(p["start_date"], "%Y-%m-%d").date()
                    if p.get("start_date") else None
                ),
            )
            due_date_val = st.date_input(
                "Date d'échéance",
                value=(
                    datetime.strptime(p["due_date"], "%Y-%m-%d").date()
                    if p.get("due_date") else date.today()
                ),
            )
            budget = st.number_input(
                "Budget (€)", min_value=0.0, step=100.0,
                value=float(p.get("budget", 0.0)),
            )
        remarks = st.text_area("Remarques", value=p.get("remarks", ""), height=120)

        b1, b2 = st.columns(2)
        save = b1.form_submit_button("💾 Enregistrer", use_container_width=True)
        delete = b2.form_submit_button("🗑️ Supprimer le projet", use_container_width=True)

    if save:
        db.update_project(PATH, p["id"], {
            "project_number": project_number.strip() or None,
            "name": name,
            "type": None if project_type == "(aucun)" else project_type,
            "status": status,
            "assigned": assigned,
            "estimated_time": estimated_time,
            "start_date": start_date_val.isoformat() if start_date_val else None,
            "due_date": due_date_val.isoformat() if due_date_val else None,
            "budget": budget,
            "remarks": remarks,
        })
        invalidate_data_cache()
        st.rerun()
    if delete:
        db.delete_project(PATH, p["id"])
        invalidate_data_cache()
        st.rerun()


@st.dialog("Modifier la sous-tâche")
def edit_subtask_dialog(project_id: str, subtask: dict, data: dict):
    with st.form(f"dialog_edit_subtask_{subtask['id']}"):
        name = st.text_input("Nom de la sous-tâche", value=str(subtask.get("name") or ""))
        assigned = st.multiselect(
            "Personnes assignées",
            data["collaborators"],
            default=[
                person
                for person in subtask.get("assigned", [])
                if person in data["collaborators"]
            ],
        )
        estimated_time = st.number_input(
            "Temps estimé (h)",
            min_value=0.0,
            step=0.5,
            value=float(subtask.get("estimated_time", 0.0) or 0.0),
        )
        done = st.checkbox("Sous-tâche terminée", value=bool(subtask.get("done", False)))

        save = st.form_submit_button("💾 Enregistrer", use_container_width=True)

    if save:
        if not name.strip():
            st.error("Le nom de la sous-tâche est obligatoire.")
            return
        run_db_action(
            "update_subtask",
            project_id,
            subtask["id"],
            {
                "name": name.strip(),
                "assigned": assigned,
                "estimated_time": estimated_time,
                "done": done,
            },
        )
        st.rerun()


def project_matches_collaborator(project: dict, collaborator: str | None) -> bool:
    if collaborator is None:
        return True
    if collaborator in project.get("assigned", []):
        return True
    return any(
        collaborator in subtask.get("assigned", [])
        for subtask in project.get("subtasks", [])
    )


def render_group_summary(data: dict):
    if "pbm_summary_status" not in st.session_state:
        st.session_state["pbm_summary_status"] = None

    selected_status = st.session_state.get("pbm_summary_status")
    with ui_container("pbm_group_summary", "summary"):
        st.markdown('<div class="pbm-summary-title">Synthèse par groupe</div>', unsafe_allow_html=True)

        all_projects = data.get("projects", [])
        all_budget, _ = get_group_totals(all_projects)
        with ui_container("pbm_summary_all", "summary-all"):
            st.button(
                "Tous les groupes",
                key="summary_all_groups",
                use_container_width=True,
                type="primary" if selected_status is None else "secondary",
                on_click=_set_summary_status,
                args=(None,),
            )
            st.markdown(
                f'<div class="pbm-side-budget">{len(all_projects)} projet{"s" if len(all_projects) != 1 else ""} - {display_amount(all_budget)}</div>'
                f'<div class="pbm-side-meta" style="visibility:hidden">&nbsp;</div>',
                unsafe_allow_html=True,
            )

        for i, status in enumerate(data["statuses"]):
            group_projects = [p for p in all_projects if p.get("status") == status]
            group_budget, _ = get_group_totals(group_projects)
            with ui_container(f"pbm_summary_{i}", f"summary-{i}"):
                st.button(
                    status,
                    key=f"summary_status_{i}",
                    use_container_width=True,
                    type="primary" if selected_status == status else "secondary",
                    on_click=_set_summary_status,
                    args=(status,),
                )
                st.markdown(
                    f'<div class="pbm-side-budget">{len(group_projects)} projet{"s" if len(group_projects) != 1 else ""} - {display_amount(group_budget)}</div>'
                    f'<div class="pbm-side-meta" style="visibility:hidden">&nbsp;</div>',
                    unsafe_allow_html=True,
                )


def render_subtasks(p: dict, data: dict):
    pid = p["id"]
    subtasks = p.get("subtasks", [])
    with ui_container(f"pbm_children_{pid}", "children"):
        if not subtasks:
            st.caption("Aucune sous-tâche.")
        for i, s in enumerate(subtasks):
            with ui_container(f"pbm_subrow_{s['id']}", "subrow"):
                sc = st.columns([0.34, 0.34, 0.38, 3.90, 1.55, 1.15, 1.00, 0.95, 0.38], gap="small", vertical_alignment="center")
                sc[0].button(
                    "▴",
                    key=f"subup_{s['id']}",
                    disabled=(i == 0),
                    help="Monter",
                    on_click=run_db_action,
                    args=("move_subtask", pid, s["id"], -1),
                )
                sc[1].button(
                    "▾",
                    key=f"subdown_{s['id']}",
                    disabled=(i == len(subtasks) - 1),
                    help="Descendre",
                    on_click=run_db_action,
                    args=("move_subtask", pid, s["id"], 1),
                )
                done_key = f"subdone_{s['id']}"
                sc[2].checkbox(
                    f"Terminer : {s['name']}",
                    value=s.get("done", False),
                    key=done_key,
                    label_visibility="collapsed",
                    on_change=set_subtask_done,
                    args=(pid, s["id"], done_key),
                )
                subtask_label = f"~~{s['name']}~~" if s.get("done") else s["name"]
                if sc[3].button(
                    subtask_label,
                    key=f"subname_{s['id']}",
                    use_container_width=True,
                    help="Modifier la sous-tâche",
                ):
                    edit_subtask_dialog(pid, s, data)
                with sc[4]:
                    cell(", ".join(s.get("assigned", [])) or "—")
                with sc[5]:
                    cell("")
                with sc[6]:
                    cell("")
                with sc[7]:
                    cell(display_hours(s.get("estimated_time")), "number")
                sc[8].button(
                    "×",
                    key=f"subdel_{s['id']}",
                    help="Supprimer la sous-tâche",
                    on_click=run_db_action,
                    args=("delete_subtask", pid, s["id"]),
                )

        add_key = f"show_add_subtask_{pid}"
        if add_key not in st.session_state:
            st.session_state[add_key] = False
        add_label = "Masquer le formulaire" if st.session_state[add_key] else "Ajouter une sous-tâche"
        st.button(
            add_label,
            key=f"toggle_add_subtask_{pid}",
            on_click=toggle_session_flag,
            args=(add_key,),
        )
        if st.session_state[add_key]:
            with st.form(f"add_subtask_{pid}", clear_on_submit=True):
                fc1, fc2, fc3, fc4 = st.columns([3.1, 2, 1.2, 1])
                sub_name = fc1.text_input(
                    "Nouvelle sous-tâche", label_visibility="collapsed",
                    placeholder="Nouvelle sous-tâche",
                )
                sub_assigned = fc2.multiselect(
                    "Assignée à", data["collaborators"], label_visibility="collapsed",
                    placeholder="Assignée à", key=f"sub_assign_{pid}",
                )
                sub_time = fc3.number_input(
                    "Temps (h)", min_value=0.0, step=0.5, label_visibility="collapsed",
                    key=f"sub_time_{pid}",
                )
                if fc4.form_submit_button("Ajouter") and sub_name.strip():
                    db.add_subtask(PATH, pid, sub_name, sub_assigned, sub_time)
                    invalidate_data_cache()
                    st.rerun()


def render_project_row(p: dict, data: dict):
    pid = p["id"]
    expand_key = f"expand_{pid}"
    if expand_key not in st.session_state:
        st.session_state[expand_key] = False

    with ui_container(f"pbm_project_{pid}", "project"):
        with ui_container(f"pbm_row_{pid}", ["row", f"rowclr-{pid}"]):
            cols = st.columns(ROW_WIDTHS, gap="small", vertical_alignment="center")
            arrow = "▾" if st.session_state[expand_key] else "▸"
            cols[0].button(
                arrow,
                key=f"arrow_{pid}",
                help="Afficher / masquer les sous-tâches",
                on_click=toggle_session_flag,
                args=(expand_key,),
            )
            with cols[1]:
                project_number_cell(p)
            if cols[2].button(p["name"], key=f"name_{pid}", use_container_width=True, help=p["name"]):
                edit_project_dialog(p, data)
            with cols[3]:
                ptype = p.get("type")
                if ptype:
                    badge_cell(ptype, data["type_colors"].get(ptype, PRIMARY_DARK), PRIMARY_DARK)
                else:
                    cell("—")
            with cols[4]:
                cell(", ".join(p.get("assigned", [])) or "—")
            with cols[5]:
                badge_cell(p["status"], data["status_colors"].get(p["status"], PRIMARY), PRIMARY_DARK)
            with cols[6]:
                cell(display_date(p.get("due_date")))
            with cols[7]:
                cell(display_amount(p.get("budget")), "number")
            with cols[8]:
                cell(display_hours(p.get("estimated_time")), "number")
            with cols[9]:
                subtasks = p.get("subtasks", [])
                done = sum(1 for s in subtasks if s.get("done"))
                cell(
                    f"{done}/{len(subtasks)}" if subtasks else "—",
                    "progress",
                    f"{done} sur {len(subtasks)} sous-tâches terminées",
                )
        if st.session_state[expand_key]:
            render_subtasks(p, data)


def render_tableau(data: dict):
    left_col, main_col = st.columns([1.25, 6.75], gap="medium")

    with left_col:
        render_group_summary(data)

    with main_col:
        with ui_container("pbm_board", "board"):
            filters = st.columns([1.7, 1.0, 1.0], gap="small")
            query = filters[0].text_input(
                "Rechercher un projet", placeholder="Rechercher nom, numéro, remarques...",
                label_visibility="collapsed", key="pbm_search",
            ).strip().casefold()
            person_filter = filters[1].selectbox(
                "Collaborateur", [None] + data["collaborators"],
                format_func=lambda x: "Tous les collaborateurs" if x is None else x,
                label_visibility="collapsed", key="pbm_person",
            )
            type_filter = filters[2].selectbox(
                "Type", [None] + data["types"],
                format_func=lambda x: "Tous les types" if x is None else x,
                label_visibility="collapsed", key="pbm_type",
            )

            summary_status = st.session_state.get("pbm_summary_status")
            projects = [
                p for p in data["projects"]
                if (not query or query in project_search_blob(p))
                and project_matches_collaborator(p, person_filter)
                and (summary_status is None or p.get("status") == summary_status)
                and (type_filter is None or p.get("type") == type_filter)
            ]
            active_filters = bool(
                query
                or person_filter is not None
                or summary_status is not None
                or type_filter is not None
            )

            if not data["projects"]:
                st.info("Aucun projet. Utilisez l'onglet Nouveau projet pour en créer un.")
            elif not projects:
                st.info("Aucun projet ne correspond aux filtres.")

            for group_index, status in enumerate(data["statuses"]):
                if summary_status is not None and status != summary_status:
                    continue

                projects_in_group = [p for p in projects if p["status"] == status]
                if active_filters and not projects_in_group:
                    continue

                count = len(projects_in_group)
                total_budget, total_hours = get_group_totals(projects_in_group)
                title = (
                    f"{status} · {count} projet{'s' if count != 1 else ''}"
                    f" · {display_amount(total_budget)} · {display_hours(total_hours)}"
                )
                with st.expander(title, expanded=bool(projects_in_group)):
                    with ui_container(f"pbm_group_{group_index}", "group"):
                        st.markdown(
                            f'<span class="pbm-marker pbm-group-{group_index}"></span>',
                            unsafe_allow_html=True,
                        )
                        if not projects_in_group:
                            st.caption("Aucun projet dans ce groupe.")
                            continue
                        render_group_header()
                        for p in projects_in_group:
                            render_project_row(p, data)
                        render_group_total_html(projects_in_group)
