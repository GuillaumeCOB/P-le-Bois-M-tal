"""
Outil interne de gestion de projets — Pôle BOIS/METAL
Inspiré de Monday.com : projets, sous-tâches, groupes par statut,
assignation de collaborateurs, budget, échéances, vues Calendrier & Gantt.

Lancement :  streamlit run app.py
"""

import calendar as cal
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

import storage as db

st.set_page_config(page_title="Pôle BOIS/METAL — Gestion de projets", layout="wide")

# ---------------------------------------------------------------------------
# Connexion aux données partagées (base Supabase, configurée via les secrets)
# ---------------------------------------------------------------------------

PATH = None  # conservé pour compatibilité avec storage.py, non utilisé (Supabase)

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
# Sidebar : gestion des collaborateurs et des statuts/groupes
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
    for status in data["statuses"]:
        c1, c2 = st.columns([4, 1])
        c1.markdown(
            f"<span style='background-color:{data['status_colors'].get(status,'#579bfc')};"
            f"color:white;padding:2px 8px;border-radius:4px;font-size:0.85em'>{status}</span>",
            unsafe_allow_html=True,
        )
        if c2.button("🗑️", key=f"del_status_{status}"):
            fallback = next((s for s in data["statuses"] if s != status), "En cours")
            db.remove_status(PATH, status, fallback)
            st.rerun()
    with st.form("add_status_form", clear_on_submit=True):
        new_status = st.text_input("Nouveau statut / groupe")
        new_color = st.color_picker("Couleur", value="#579bfc")
        if st.form_submit_button("Ajouter") and new_status.strip():
            db.add_status(PATH, new_status, new_color)
            st.rerun()

# ---------------------------------------------------------------------------
# Onglets principaux
# ---------------------------------------------------------------------------

tab_board, tab_add, tab_calendar, tab_gantt = st.tabs(
    ["📋 Tableau", "➕ Nouveau projet", "📅 Calendrier", "📊 Gantt"]
)

# ---------------------------------------------------------------------------
# Onglet Tableau — vue groupée par statut, façon Monday
# ---------------------------------------------------------------------------

with tab_board:
    if not data["projects"]:
        st.info("Aucun projet pour le moment. Ajoutez-en un depuis l'onglet **➕ Nouveau projet**.")

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
            budget_txt = f"{p.get('budget', 0):,.0f} €".replace(",", " ")
            due_txt = p.get("due_date") or "—"
            assigned_txt = ", ".join(p.get("assigned", [])) or "—"

            with st.expander(
                f"**{p['name']}**  ·  {assigned_txt}  ·  échéance {due_txt}  ·  {budget_txt}"
            ):
                with st.form(f"edit_form_{p['id']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        name = st.text_input("Nom du projet", value=p["name"])
                        new_status = st.selectbox(
                            "Statut", data["statuses"],
                            index=data["statuses"].index(p["status"]),
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
                    save = c1.form_submit_button("💾 Enregistrer")
                    delete = c2.form_submit_button("🗑️ Supprimer le projet")

                    if save:
                        db.update_project(PATH, p["id"], {
                            "name": name,
                            "status": new_status,
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

                # --- Sous-tâches ---
                st.markdown("##### Sous-tâches")
                if p.get("subtasks"):
                    for st_ in p["subtasks"]:
                        sc1, sc2, sc3, sc4 = st.columns([1, 4, 3, 1])
                        done = sc1.checkbox("", value=st_.get("done", False), key=f"done_{st_['id']}")
                        if done != st_.get("done", False):
                            db.update_subtask(PATH, p["id"], st_["id"], {"done": done})
                            st.rerun()
                        label = st_["name"]
                        if done:
                            label = f"~~{label}~~"
                        sc2.markdown(label)
                        sc3.caption(
                            f"{', '.join(st_.get('assigned', [])) or '—'} · "
                            f"{st_.get('estimated_time', 0)} h"
                        )
                        if sc4.button("🗑️", key=f"del_sub_{st_['id']}"):
                            db.delete_subtask(PATH, p["id"], st_["id"])
                            st.rerun()
                else:
                    st.caption("Aucune sous-tâche.")

                with st.form(f"add_subtask_{p['id']}", clear_on_submit=True):
                    sc1, sc2, sc3 = st.columns([3, 3, 2])
                    sub_name = sc1.text_input("Nouvelle sous-tâche")
                    sub_assigned = sc2.multiselect("Assignée à", data["collaborators"], key=f"sub_assign_{p['id']}")
                    sub_time = sc3.number_input("Temps (h)", min_value=0.0, step=0.5, key=f"sub_time_{p['id']}")
                    if st.form_submit_button("➕ Ajouter la sous-tâche") and sub_name.strip():
                        db.add_subtask(PATH, p["id"], sub_name, sub_assigned, sub_time)
                        st.rerun()

        # Total du groupe
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

    # Regrouper les projets par jour d'échéance
    by_day = {}
    for p in data["projects"]:
        if p.get("due_date"):
            by_day.setdefault(p["due_date"], []).append(p)

    month_matrix = cal.monthcalendar(st.session_state.cal_year, st.session_state.cal_month)
    days_header = st.columns(7)
    for i, name in enumerate(["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]):
        days_header[i].markdown(f"**{name}**")

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
            # à défaut de date de début, on estime une durée d'1 jour par tranche
            # de 8h de temps estimé (minimum 1 jour) avant l'échéance
            days = max(1, round((p.get("estimated_time", 0) or 0) / 8))
            start = end - timedelta(days=days)
        if start >= end:
            start = end - timedelta(days=1)
        rows.append({
            "Projet": p["name"],
            "Début": start,
            "Fin": end,
            "Statut": p["status"],
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
            hover_data=["Assigné"],
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(height=max(300, 40 * len(df)))
        st.plotly_chart(fig, use_container_width=True)
