"""
Outil interne de gestion de projets — Pôle BOIS/METAL
Inspiré de Monday.com : projets, sous-tâches, groupes par statut,
assignation de collaborateurs, budget, échéances, types de projet,
vues Calendrier & Gantt.

Lancement local :  streamlit run app.py
"""

import calendar as cal
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import storage as db

st.set_page_config(page_title="Pôle BOIS/METAL — Gestion de projets", layout="wide")

PATH = None  # conservé pour compatibilité avec storage.py, non utilisé (Supabase)

ROW_WIDTHS = [0.45, 0.45, 2.6, 1.1, 1.7, 1.15, 1.0, 0.95, 0.85, 1.8]
ROW_LABELS = ["", "", "Tâche", "Type", "Assigné", "Statut", "Échéance", "Budget", "Temps est.", "Remarques"]


def badge(text: str, color: str, text_color: str = "white") -> str:
    return (
        f"<span style='background-color:{color};color:{text_color};"
        f"padding:2px 9px;border-radius:10px;font-size:0.8em;font-weight:500;"
        f"white-space:nowrap'>{text}</span>"
    )


# ---------------------------------------------------------------------------
# Connexion aux données partagées (base Supabase, configurée via les secrets)
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("### ⚙️ Données")
    st.caption("Connecté à la base de données partagée de l'équipe.")
    if st.button("🔄 Rafraîchir les données"):
        st.rerun()

try:
    data = db.load_data(PATH)
except Exception as e:
    st.error(
        "Impossible de se connecter à la base de données partagée. "
        "Vérifiez que SUPABASE_URL et SUPABASE_KEY sont bien configurés "
        "dans les secrets de l'application (voir README.md)."
    )
    st.exception(e)
    st.stop()

st.title("🪚 Pôle BOIS/METAL — Suivi de projets")

# ---------------------------------------------------------------------------
# Modale d'édition d'un projet
# ---------------------------------------------------------------------------

@st.dialog("Modifier le projet")
def edit_project_dialog(p: dict):
    with st.form(f"dialog_edit_{p['id']}"):
        name = st.text_input("Nom du projet", value=p["name"])
        col1, col2 = st.columns(2)
        with col1:
            type_options = ["(aucun)"] + data["types"]
            current_type = p.get("type") or "(aucun)"
            type_idx = type_options.index(current_type) if current_type in type_options else 0
            project_type = st.selectbox("Type", type_options, index=type_idx)
            status = st.selectbox(
                "Statut", data["statuses"], index=data["statuses"].index(p["status"])
            )
            assigned = st.multiselect(
                "Personnes assignées", data["collaborators"],
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
        remarks = st.text_area("Remarques", value=p.get("remarks", ""))

        c1, c2 = st.columns(2)
        save = c1.form_submit_button("💾 Enregistrer", use_container_width=True)
        delete = c2.form_submit_button("🗑️ Supprimer le projet", use_container_width=True)

    if save:
        db.update_project(PATH, p["id"], {
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
        st.rerun()
    if delete:
        db.delete_project(PATH, p["id"])
        st.rerun()


# ---------------------------------------------------------------------------
# Sidebar : gestion des collaborateurs, statuts/groupes et types de projet
# ---------------------------------------------------------------------------

with st.sidebar:
    st.markdown("---")
    st.markdown("### 👥 Collaborateurs")
    for person in data["collaborators"]:
        c1, c2 = st.columns([4, 1])
        c1.write(person)
        if c2.button("🗑️", key=f"del_collab_{person}"):
            db.remove_collaborator(PATH, person)
            st.rerun()
    with st.form("add_collab_form", clear_on_submit=True):
        new_person = st.text_input("Ajouter une personne")
        if st.form_submit_button("Ajouter") and new_person.strip():
            db.add_collaborator(PATH, new_person)
            st.rerun()

    st.markdown("---")
    st.markdown("### 🏷️ Statuts / groupes")
    st.caption("L'ordre ici définit l'ordre des groupes dans le tableau.")
    n_statuses = len(data["statuses"])
    for i, status in enumerate(data["statuses"]):
        c1, c2, c3, c4 = st.columns([3, 0.7, 0.7, 0.7])
        c1.markdown(
            badge(status, data["status_colors"].get(status, "#579bfc"), "white"),
            unsafe_allow_html=True,
        )
        if c2.button("▲", key=f"statusup_{status}", disabled=(i == 0)):
            db.move_status(PATH, status, -1)
            st.rerun()
        if c3.button("▼", key=f"statusdown_{status}", disabled=(i == n_statuses - 1)):
            db.move_status(PATH, status, 1)
            st.rerun()
        if c4.button("🗑️", key=f"del_status_{status}"):
            fallback = next((s for s in data["statuses"] if s != status), "En cours")
            db.remove_status(PATH, status, fallback)
            st.rerun()
    with st.form("add_status_form", clear_on_submit=True):
        new_status = st.text_input("Nouveau statut / groupe")
        new_color = st.color_picker("Couleur", value="#579bfc")
        if st.form_submit_button("Ajouter") and new_status.strip():
            db.add_status(PATH, new_status, new_color)
            st.rerun()

    st.markdown("---")
    st.markdown("### 🏗️ Types de projet")
    st.caption("Ex. DIAGNOSTIC, APS, APD, PRO, DCE, EXE…")
    n_types = len(data["types"])
    for i, t in enumerate(data["types"]):
        c1, c2, c3, c4 = st.columns([3, 0.7, 0.7, 0.7])
        c1.markdown(
            badge(t, data["type_colors"].get(t, "#eeeeee"), "#3b3b3b"),
            unsafe_allow_html=True,
        )
        if c2.button("▲", key=f"typeup_{t}", disabled=(i == 0)):
            db.move_type(PATH, t, -1)
            st.rerun()
        if c3.button("▼", key=f"typedown_{t}", disabled=(i == n_types - 1)):
            db.move_type(PATH, t, 1)
            st.rerun()
        if c4.button("🗑️", key=f"del_type_{t}"):
            db.remove_type(PATH, t)
            st.rerun()
    with st.form("add_type_form", clear_on_submit=True):
        new_type = st.text_input("Nouveau type")
        new_type_color = st.color_picker("Couleur", value="#D6E6F5")
        if st.form_submit_button("Ajouter") and new_type.strip():
            db.add_type(PATH, new_type.strip().upper(), new_type_color)
            st.rerun()

# ---------------------------------------------------------------------------
# Onglets principaux
# ---------------------------------------------------------------------------

tab_board, tab_add, tab_calendar, tab_gantt = st.tabs(
    ["📋 Tableau", "➕ Nouveau projet", "📅 Calendrier", "📊 Gantt"]
)


def render_subtasks(p: dict):
    pid = p["id"]
    subtasks = p.get("subtasks", [])
    with st.container(border=True):
        if not subtasks:
            st.caption("Aucune sous-tâche.")
        n_sub = len(subtasks)
        for i, s in enumerate(subtasks):
            sc = st.columns([0.35, 0.35, 0.4, 3, 2, 1, 0.4])
            if sc[0].button("▲", key=f"subup_{s['id']}", disabled=(i == 0)):
                db.move_subtask(PATH, pid, s["id"], -1)
                st.rerun()
            if sc[1].button("▼", key=f"subdown_{s['id']}", disabled=(i == n_sub - 1)):
                db.move_subtask(PATH, pid, s["id"], 1)
                st.rerun()
            done = sc[2].checkbox("", value=s.get("done", False), key=f"subdone_{s['id']}")
            if done != s.get("done", False):
                db.update_subtask(PATH, pid, s["id"], {"done": done})
                st.rerun()
            label = s["name"]
            if s.get("done"):
                label = f"~~{label}~~"
            sc[3].markdown(label)
            sc[4].caption(", ".join(s.get("assigned", [])) or "—")
            sc[5].caption(f"{s.get('estimated_time', 0)} h")
            if sc[6].button("🗑️", key=f"subdel_{s['id']}"):
                db.delete_subtask(PATH, pid, s["id"])
                st.rerun()

        with st.form(f"add_subtask_{pid}", clear_on_submit=True):
            fc1, fc2, fc3, fc4 = st.columns([3, 2, 1.3, 1])
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
            if fc4.form_submit_button("➕ Ajouter") and sub_name.strip():
                db.add_subtask(PATH, pid, sub_name, sub_assigned, sub_time)
                st.rerun()


def render_project_row(p: dict):
    pid = p["id"]
    expand_key = f"expand_{pid}"
    if expand_key not in st.session_state:
        st.session_state[expand_key] = False

    cols = st.columns(ROW_WIDTHS)

    arrow = "▼" if st.session_state[expand_key] else "▶"
    if cols[0].button(arrow, key=f"arrow_{pid}", help="Afficher/masquer les sous-tâches"):
        st.session_state[expand_key] = not st.session_state[expand_key]
        st.rerun()

    if cols[1].button("✏️", key=f"pencil_{pid}", help="Modifier le projet"):
        edit_project_dialog(p)

    with cols[2]:
        if st.button(p["name"], key=f"name_{pid}", use_container_width=True):
            edit_project_dialog(p)
        n_sub = len(p.get("subtasks", []))
        if n_sub:
            done = sum(1 for s in p["subtasks"] if s.get("done"))
            st.caption(f"{done}/{n_sub} sous-tâches")

    with cols[3]:
        ptype = p.get("type")
        if ptype:
            st.markdown(
                badge(ptype, data["type_colors"].get(ptype, "#eeeeee"), "#3b3b3b"),
                unsafe_allow_html=True,
            )
        else:
            st.write("—")

    cols[4].write(", ".join(p.get("assigned", [])) or "—")

    with cols[5]:
        st.markdown(
            badge(p["status"], data["status_colors"].get(p["status"], "#579bfc"), "white"),
            unsafe_allow_html=True,
        )

    cols[6].write(p.get("due_date") or "—")
    cols[7].write(f"{p.get('budget', 0):,.0f} €".replace(",", " "))
    cols[8].write(f"{p.get('estimated_time', 0):.1f} h")

    remarks = p.get("remarks") or ""
    cols[9].write(remarks if len(remarks) <= 45 else remarks[:42] + "…")

    if st.session_state[expand_key]:
        render_subtasks(p)


with tab_board:
    if not data["projects"]:
        st.info("Aucun projet pour le moment. Ajoutez-en un depuis l'onglet **➕ Nouveau projet**.")
    else:
        header_cols = st.columns(ROW_WIDTHS)
        for c, label in zip(header_cols, ROW_LABELS):
            if label:
                c.markdown(f"**{label}**")
        st.markdown("<hr style='margin-top:0.2em'>", unsafe_allow_html=True)

    for status in data["statuses"]:
        projects_in_group = [p for p in data["projects"] if p["status"] == status]
        color = data["status_colors"].get(status, "#579bfc")
        st.markdown(
            f"#### <span style='color:{color}'>●</span> {status} "
            f"<span style='color:#888;font-size:0.7em'>({len(projects_in_group)})</span>",
            unsafe_allow_html=True,
        )

        if not projects_in_group:
            st.caption("Aucun projet dans ce groupe.")
            continue

        for p in projects_in_group:
            render_project_row(p)

        total_budget = sum(p.get("budget", 0) for p in projects_in_group)
        total_time = sum(p.get("estimated_time", 0) for p in projects_in_group)
        st.caption(f"Sous-total groupe : {total_budget:,.0f} € · {total_time:.1f} h".replace(",", " "))
        st.markdown("---")

# ---------------------------------------------------------------------------
# Onglet Nouveau projet
# ---------------------------------------------------------------------------

with tab_add:
    st.subheader("Créer un nouveau projet")
    with st.form("new_project_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Nom du projet *")
            type_options = ["(aucun)"] + data["types"]
            project_type = st.selectbox("Type de projet", type_options)
            status = st.selectbox("Statut / groupe", data["statuses"])
            assigned = st.multiselect("Personnes assignées", data["collaborators"])
            estimated_time = st.number_input("Temps estimé (h)", min_value=0.0, step=0.5)
        with col2:
            start_date_val = st.date_input("Date de début (optionnel)", value=None)
            due_date_val = st.date_input("Date d'échéance", value=date.today())
            budget = st.number_input("Budget (€)", min_value=0.0, step=100.0)
            remarks = st.text_area("Remarques")

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
                db.add_project(PATH, project)
                st.success(f"Projet « {name} » créé.")
                st.rerun()

# ---------------------------------------------------------------------------
# Onglet Calendrier
# ---------------------------------------------------------------------------

with tab_calendar:
    st.subheader("Vue calendrier (par date d'échéance)")

    if "cal_month" not in st.session_state:
        today = date.today()
        st.session_state.cal_month = today.month
        st.session_state.cal_year = today.year

    nav1, nav2, nav3 = st.columns([1, 2, 1])
    if nav1.button("◀ Mois précédent"):
        m = st.session_state.cal_month - 1
        y = st.session_state.cal_year
        if m == 0:
            m, y = 12, y - 1
        st.session_state.cal_month, st.session_state.cal_year = m, y
        st.rerun()
    nav2.markdown(
        f"<h4 style='text-align:center'>{cal.month_name[st.session_state.cal_month]} "
        f"{st.session_state.cal_year}</h4>",
        unsafe_allow_html=True,
    )
    if nav3.button("Mois suivant ▶"):
        m = st.session_state.cal_month + 1
        y = st.session_state.cal_year
        if m == 13:
            m, y = 1, y + 1
        st.session_state.cal_month, st.session_state.cal_year = m, y
        st.rerun()

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
                    color = data["status_colors"].get(p["status"], "#579bfc")
                    st.markdown(
                        f"<div style='background-color:{color};color:white;"
                        f"border-radius:3px;padding:1px 4px;font-size:0.7em;margin-bottom:2px'>"
                        f"{p['name']}</div>",
                        unsafe_allow_html=True,
                    )

# ---------------------------------------------------------------------------
# Onglet Gantt
# ---------------------------------------------------------------------------

with tab_gantt:
    st.subheader("Vue Gantt / échéancier")

    rows = []
    for p in data["projects"]:
        if not p.get("due_date"):
            continue
        end = datetime.strptime(p["due_date"], "%Y-%m-%d")
        if p.get("start_date"):
            start = datetime.strptime(p["start_date"], "%Y-%m-%d")
        else:
            days = max(1, round((p.get("estimated_time", 0) or 0) / 8))
            start = end - timedelta(days=days)
        if start >= end:
            start = end - timedelta(days=1)
        rows.append({
            "Projet": p["name"],
            "Début": start,
            "Fin": end,
            "Statut": p["status"],
            "Type": p.get("type") or "—",
            "Assigné": ", ".join(p.get("assigned", [])) or "—",
        })

    if not rows:
        st.info("Aucun projet avec une date d'échéance à afficher.")
    else:
        df = pd.DataFrame(rows)
        color_map = data["status_colors"]
        fig = px.timeline(
            df, x_start="Début", x_end="Fin", y="Projet", color="Statut",
            color_discrete_map=color_map,
            hover_data=["Type", "Assigné"],
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=max(300, 40 * len(df)))
        st.plotly_chart(fig, use_container_width=True)
