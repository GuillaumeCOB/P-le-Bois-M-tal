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

from contextlib import contextmanager
from html import escape
import inspect
import re

st.set_page_config(page_title="Pôle BOIS/METAL - Gestion de projets", layout="wide", initial_sidebar_state="collapsed")
PATH = None
ROW_WIDTHS = [0.32, 3.15, 0.85, 1.65, 1.15, 1.1, 0.95, 0.85, 0.7]
ROW_LABELS = ["", "Projet", "Type", "Collaborateurs", "Statut", "Échéance", "Budget", "Charge", "Tâches"]


# Presentation only: the existing storage API and data format are unchanged.
_HAS_CONTAINER_KEY = "key" in inspect.signature(st.container).parameters


@contextmanager
def ui_container(key: str, kind: str):
    """Named CSS scopes; compatible with Streamlit 1.38 (without container.key)."""
    options = {"border": False}
    if _HAS_CONTAINER_KEY:
        options["key"] = key
    with st.container(**options):
        st.markdown(
            f'<span class="pbm-marker pbm-{kind}-marker"></span>',
            unsafe_allow_html=True,
        )
        yield


def css_scope(kind: str) -> str:
    return (
        '[data-testid="stVerticalBlock"]:has(> '
        ':is(.element-container, [data-testid="stElementContainer"]) '
        f'.pbm-{kind}-marker)'
    )


def safe_color(value: str, fallback: str = "#64748b") -> str:
    return value if isinstance(value, str) and re.fullmatch(r"#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?", value) else fallback


def inject_compact_styles():
    # Semantic marker scopes avoid applying table sizing to edit forms.
    board = css_scope("board")
    group = css_scope("group")
    project = css_scope("project")
    row = css_scope("row")
    header = css_scope("header")
    children = css_scope("children")
    subrow = css_scope("subrow")
    css = """
    .block-container {
        padding-top: 3.7rem;
        padding-bottom: 1.2rem;
        padding-left: 1.5rem;
        padding-right: 1.5rem;
        max-width: none;
    }
    h1 {font-size: 1.55rem !important; padding: 0 0 0.35rem !important;}
    [data-testid="stTabs"] [data-baseweb="tab-list"] {gap: 1rem;}
    [data-testid="stTabs"] [data-baseweb="tab"] {height: 2.2rem; padding: 0 0.25rem;}
    :is(.element-container, [data-testid="stElementContainer"]):has(.pbm-marker) {
        display: none !important;
    }
    .pbm-cell {
        font-size: 0.875rem;
        line-height: 1.35;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        padding: 2px 3px;
    }
    .pbm-cell.number {text-align: right; font-variant-numeric: tabular-nums;}
    .pbm-cell.progress {text-align: center; opacity: 0.75; font-variant-numeric: tabular-nums;}
    .pbm-cell.done {text-decoration: line-through; opacity: 0.55;}
    .pbm-badge {
        display: inline-block;
        max-width: 100%;
        vertical-align: middle;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 0.8rem;
        line-height: 1.4;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .pbm-summary {font-size: 0.77rem; opacity: 0.72; padding: 6px 4px 0;}
    """
    css += f"""
    {board} {{gap: 0.5rem !important;}}
    {board} [data-testid="stExpander"] {{border-radius: 5px;}}
    {board} [data-testid="stExpander"] summary {{padding: 0.35rem 0.5rem; min-height: 2rem;}}
    {board} [data-testid="stExpanderDetails"] {{padding: 0 0.45rem 0.4rem;}}
    {group}, {project}, {row}, {header}, {children}, {subrow} {{gap: 0 !important;}}
    {project} {{border-bottom: 1px solid rgba(128, 128, 128, 0.2);}}
    {row} {{padding: 3px 0; min-height: 38px;}}
    {row}:hover {{background: rgba(128, 128, 128, 0.055);}}
    {header} {{background: rgba(128, 128, 128, 0.065); padding: 5px 0; border-bottom: 1px solid rgba(128, 128, 128, 0.23);}}
    {header} .pbm-cell {{font-size: 0.76rem; font-weight: 600; opacity: 0.8;}}
    {row} [data-testid="stHorizontalBlock"],
    {header} [data-testid="stHorizontalBlock"],
    {subrow} [data-testid="stHorizontalBlock"] {{gap: 6px !important; align-items: center;}}
    {row} [data-testid="stVerticalBlock"],
    {subrow} [data-testid="stVerticalBlock"] {{gap: 0 !important; min-width: 0;}}
    {row} :is([data-testid="stColumn"], [data-testid="column"]),
    {header} :is([data-testid="stColumn"], [data-testid="column"]),
    {subrow} :is([data-testid="stColumn"], [data-testid="column"]) {{min-width: 0;}}
    {row} [data-testid="stMarkdownContainer"] p,
    {subrow} [data-testid="stMarkdownContainer"] p {{margin: 0;}}
    {row} [data-testid="stButton"] button,
    {subrow} [data-testid="stButton"] button {{
        min-height: 28px;
        height: 28px;
        padding: 2px 4px;
        border: 1px solid transparent;
        border-radius: 3px;
        background: transparent;
    }}
    {row} [data-testid="stButton"] button:hover,
    {subrow} [data-testid="stButton"] button:hover {{background: rgba(128, 128, 128, 0.1);}}
    {row} [data-testid="stButton"] button p {{
        font-size: 0.875rem;
        line-height: 1.3;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        display: block;
        margin: 0;
    }}
    {row} [data-testid="stButton"] button [data-testid="stMarkdownContainer"] {{min-width: 0; overflow: hidden;}}
    {row} [data-testid="stHorizontalBlock"] > :nth-child(2) [data-testid="stButton"] button {{justify-content: flex-start; text-align: left; font-weight: 600;}}
    {children} {{
        margin: 0 0 6px 16px;
        width: calc(100% - 16px);
        padding: 2px 8px 4px 10px;
        border-left: 2px solid rgba(128, 128, 128, 0.45);
        background: rgba(128, 128, 128, 0.045);
    }}
    {subrow} {{padding: 1px 0; min-height: 30px; border-bottom: 1px solid rgba(128, 128, 128, 0.12);}}
    {subrow} [data-testid="stCheckbox"] {{min-height: 28px;}}
    {subrow} [data-testid="stCheckbox"] label {{margin: 0; min-height: 28px;}}
    {children} [data-testid="stExpander"] {{border: 0; margin-top: 2px; background: transparent;}}
    {children} [data-testid="stExpander"] summary {{padding: 0.15rem 0;}}
    {children} [data-testid="stExpander"] summary p {{font-size: 0.8rem;}}
    {children} [data-testid="stForm"] {{padding: 0.5rem;}}
    """
    # Only hexadecimal colors from settings are interpolated in CSS.
    for i, status in enumerate(data["statuses"]):
        color = safe_color(data["status_colors"].get(status))
        css += f'[data-testid="stExpander"]:has(.pbm-group-{i}) {{border-left: 3px solid {color};}}\n'
    css += """
    @media (max-width: 760px) {
        .block-container {padding-left: 0.75rem; padding-right: 0.75rem;}
    }
    """
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def badge(text: str, color: str, text_color: str = "white") -> str:
    background = safe_color(color)
    foreground = text_color if text_color in ("white", "black") else safe_color(text_color)
    label = escape(str(text))
    return (
        f'<span class="pbm-badge" title="{label}" '
        f'style="background-color:{background};color:{foreground}">{label}</span>'
    )


def cell(text, style: str = "", tooltip: str = ""):
    value = str(text) if text is not None else "—"
    title = escape(tooltip or value, quote=True)
    st.markdown(
        f'<div class="pbm-cell {style}" title="{title}">{escape(value)}</div>',
        unsafe_allow_html=True,
    )


def display_date(value) -> str:
    if not value:
        return "—"
    try:
        return date.fromisoformat(str(value)).strftime("%d/%m/%Y")
    except ValueError:
        return str(value)


def display_amount(value) -> str:
    return f"{float(value or 0):,.0f} €".replace(",", " ")


def display_hours(value) -> str:
    return f"{float(value or 0):.1f} h".replace(".", ",")

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

inject_compact_styles()
st.title("Pôle BOIS/METAL - Suivi de projets")

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

tab_board, tab_add, tab_calendar, tab_gantt, tab_settings = st.tabs(
    ["Tableau", "Nouveau projet", "Calendrier", "Gantt", "Paramètres"]
)


def render_subtasks(p: dict):
    pid = p["id"]
    subtasks = p.get("subtasks", [])
    with ui_container(f"pbm_children_{pid}", "children"):
        if not subtasks:
            st.caption("Aucune sous-tâche.")
        for i, s in enumerate(subtasks):
            with ui_container(f"pbm_subrow_{s['id']}", "subrow"):
                sc = st.columns([0.35, 0.35, 0.4, 3.6, 2, 1, 0.4], gap="small", vertical_alignment="center")
                if sc[0].button("▴", key=f"subup_{s['id']}", disabled=(i == 0), help="Monter"):
                    db.move_subtask(PATH, pid, s["id"], -1)
                    st.rerun()
                if sc[1].button("▾", key=f"subdown_{s['id']}", disabled=(i == len(subtasks) - 1), help="Descendre"):
                    db.move_subtask(PATH, pid, s["id"], 1)
                    st.rerun()
                done = sc[2].checkbox(
                    f"Terminer : {s['name']}", value=s.get("done", False),
                    key=f"subdone_{s['id']}", label_visibility="collapsed",
                )
                if done != s.get("done", False):
                    db.update_subtask(PATH, pid, s["id"], {"done": done})
                    st.rerun()
                with sc[3]:
                    cell(s["name"], "done" if s.get("done") else "")
                with sc[4]:
                    cell(", ".join(s.get("assigned", [])) or "—")
                with sc[5]:
                    cell(display_hours(s.get("estimated_time")), "number")
                if sc[6].button("×", key=f"subdel_{s['id']}", help="Supprimer la sous-tâche"):
                    db.delete_subtask(PATH, pid, s["id"])
                    st.rerun()

        # Keep the creation form out of the way until explicitly opened.
        add_key = f"show_add_subtask_{pid}"
        if add_key not in st.session_state:
            st.session_state[add_key] = False
        add_label = "Masquer le formulaire" if st.session_state[add_key] else "Ajouter une sous-tâche"
        if st.button(add_label, key=f"toggle_add_subtask_{pid}"):
            st.session_state[add_key] = not st.session_state[add_key]
            st.rerun()
        if st.session_state[add_key]:
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
                if fc4.form_submit_button("Ajouter") and sub_name.strip():
                    db.add_subtask(PATH, pid, sub_name, sub_assigned, sub_time)
                    st.rerun()


def render_project_row(p: dict):
    pid = p["id"]
    expand_key = f"expand_{pid}"
    if expand_key not in st.session_state:
        st.session_state[expand_key] = False

    with ui_container(f"pbm_project_{pid}", "project"):
        with ui_container(f"pbm_row_{pid}", "row"):
            cols = st.columns(ROW_WIDTHS, gap="small", vertical_alignment="center")
            arrow = "▾" if st.session_state[expand_key] else "▸"
            if cols[0].button(arrow, key=f"arrow_{pid}", help="Afficher / masquer les sous-tâches"):
                st.session_state[expand_key] = not st.session_state[expand_key]
                st.rerun()
            # The project name is the edit action: no duplicate pencil column.
            if cols[1].button(p["name"], key=f"name_{pid}", use_container_width=True, help=p["name"]):
                edit_project_dialog(p)
            with cols[2]:
                ptype = p.get("type")
                if ptype:
                    st.markdown(badge(ptype, data["type_colors"].get(ptype, "#eeeeee"), "#3b3b3b"), unsafe_allow_html=True)
                else:
                    cell("—")
            with cols[3]:
                cell(", ".join(p.get("assigned", [])) or "—")
            with cols[4]:
                st.markdown(badge(p["status"], data["status_colors"].get(p["status"], "#579bfc")), unsafe_allow_html=True)
            with cols[5]:
                cell(display_date(p.get("due_date")))
            with cols[6]:
                cell(display_amount(p.get("budget")), "number")
            with cols[7]:
                cell(display_hours(p.get("estimated_time")), "number")
            with cols[8]:
                subtasks = p.get("subtasks", [])
                done = sum(1 for s in subtasks if s.get("done"))
                cell(
                    f"{done}/{len(subtasks)}" if subtasks else "—", "progress",
                    f"{done} sur {len(subtasks)} sous-tâches terminées",
                )
        if st.session_state[expand_key]:
            render_subtasks(p)


with tab_board:
    with ui_container("pbm_board", "board"):
        fc = st.columns([2.5, 1.4, 1.4, 1.4], gap="small")
        query = fc[0].text_input(
            "Rechercher un projet", placeholder="Rechercher un projet...",
            label_visibility="collapsed", key="pbm_search",
        ).strip().casefold()
        person_filter = fc[1].selectbox(
            "Collaborateur", [None] + data["collaborators"],
            format_func=lambda x: "Tous les collaborateurs" if x is None else x,
            label_visibility="collapsed", key="pbm_person",
        )
        status_filter = fc[2].selectbox(
            "Statut", [None] + data["statuses"],
            format_func=lambda x: "Tous les statuts" if x is None else x,
            label_visibility="collapsed", key="pbm_status",
        )
        type_filter = fc[3].selectbox(
            "Type", [None] + data["types"],
            format_func=lambda x: "Tous les types" if x is None else x,
            label_visibility="collapsed", key="pbm_type",
        )
        projects = [
            p for p in data["projects"]
            if (not query or query in (p.get("name", "") + " " + (p.get("remarks") or "")).casefold())
            and (person_filter is None or person_filter in p.get("assigned", []))
            and (status_filter is None or p.get("status") == status_filter)
            and (type_filter is None or p.get("type") == type_filter)
        ]
        active_filters = bool(query or person_filter is not None or status_filter is not None or type_filter is not None)
        if not data["projects"]:
            st.info("Aucun projet. Utilisez l'onglet Nouveau projet pour en créer un.")
        elif not projects:
            st.info("Aucun projet ne correspond aux filtres.")

        for group_index, status in enumerate(data["statuses"]):
            projects_in_group = [p for p in projects if p["status"] == status]
            if active_filters and not projects_in_group:
                continue
            count = len(projects_in_group)
            title = f"{status}  ·  {count} projet{'s' if count != 1 else ''}"
            with st.expander(title, expanded=bool(projects_in_group)):
                with ui_container(f"pbm_group_{group_index}", "group"):
                    st.markdown(f'<span class="pbm-marker pbm-group-{group_index}"></span>', unsafe_allow_html=True)
                    if not projects_in_group:
                        st.caption("Aucun projet dans ce groupe.")
                        continue
                    with ui_container(f"pbm_header_{group_index}", "header"):
                        header_cols = st.columns(ROW_WIDTHS, gap="small", vertical_alignment="center")
                        for idx, (c, label) in enumerate(zip(header_cols, ROW_LABELS)):
                            with c:
                                cell(label, "number" if idx in (6, 7) else "progress" if idx == 8 else "")
                    for p in projects_in_group:
                        render_project_row(p)
                    total_budget = sum(p.get("budget", 0) or 0 for p in projects_in_group)
                    total_time = sum(p.get("estimated_time", 0) or 0 for p in projects_in_group)
                    st.markdown(
                        '<div class="pbm-summary">Total des projets affichés : '
                        f'{display_amount(total_budget)} · {display_hours(total_time)}</div>',
                        unsafe_allow_html=True,
                    )

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
                    color = safe_color(data["status_colors"].get(p["status"], "#579bfc"))
                    st.markdown(
                        f"<div style='background-color:{color};color:white;"
                        f"border-radius:3px;padding:1px 4px;font-size:0.7em;margin-bottom:2px'>"
                        f"{escape(p['name'])}</div>",
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

with tab_settings:
    settings_cols = st.columns([1, 1.2, 1.2], gap="medium")
    with settings_cols[0]:
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
    with settings_cols[1]:
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
    with settings_cols[2]:
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

