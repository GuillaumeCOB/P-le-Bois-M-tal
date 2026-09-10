"""
Module de gestion des données pour l'outil de gestion de projets Pôle BOIS/METAL.

Les données sont stockées dans une table Supabase (une seule ligne contenant
tout le "tableau" au format JSON), ce qui garantit qu'elles persistent même
quand l'application Streamlit Cloud redémarre ou se met en veille.

Toutes les fonctions rechargent la ligne depuis Supabase juste avant d'écrire,
afin de limiter les conflits quand plusieurs personnes utilisent l'outil en
même temps.
"""

import json
import uuid
from datetime import datetime

import streamlit as st
from supabase import create_client, Client

BOARD_ID = 1  # une seule ligne = un seul tableau partagé par toute l'équipe

DEFAULT_STATUSES = [
    "Devis à faire",
    "Devis validé",
    "En attente",
    "En cours",
    "Terminé",
]

STATUS_COLORS = {
    "Devis à faire": "#8b8b8b",
    "Devis validé": "#a25ddc",
    "En attente": "#e2445c",
    "En cours": "#fdab3d",
    "Terminé": "#00c875",
}

DEFAULT_DATA = {
    "collaborators": [],
    "statuses": DEFAULT_STATUSES.copy(),
    "status_colors": STATUS_COLORS.copy(),
    "projects": [],
    "_meta": {"last_modified": None},
}


def _now_iso():
    return datetime.now().isoformat()


@st.cache_resource
def _get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def load_data(_path: str = None) -> dict:
    """Charge le tableau depuis Supabase. Le paramètre `_path` est conservé
    pour compatibilité avec le reste du code mais n'est plus utilisé (une
    seule ligne partagée = BOARD_ID)."""
    client = _get_client()
    res = client.table("app_data").select("data").eq("id", BOARD_ID).execute()
    if res.data:
        data = res.data[0]["data"]
    else:
        data = json.loads(json.dumps(DEFAULT_DATA))
        data["_meta"]["last_modified"] = _now_iso()
        client.table("app_data").insert({"id": BOARD_ID, "data": data}).execute()
    # Compatibilité si un champ manque (ex: données créées avec une version antérieure)
    for key, value in DEFAULT_DATA.items():
        if key not in data:
            data[key] = json.loads(json.dumps(value))
    return data


def _atomic_write(_path: str, data: dict):
    """Enregistre le tableau dans Supabase (upsert de la ligne partagée)."""
    data["_meta"]["last_modified"] = _now_iso()
    client = _get_client()
    client.table("app_data").upsert({"id": BOARD_ID, "data": data}).execute()


def _mutate(path: str, mutator):
    """Recharge les données fraîches depuis Supabase, applique la fonction
    `mutator(data)` qui modifie `data` en place, puis sauvegarde.
    Cela limite les conflits : seule la modification en cours est perdue en cas
    de collision exacte (même projet édité à la même seconde), pas les
    modifications faites par d'autres entre-temps."""
    data = load_data(path)
    mutator(data)
    _atomic_write(path, data)
    return data


# ---------------------------------------------------------------------------
# Collaborateurs
# ---------------------------------------------------------------------------

def add_collaborator(path: str, name: str):
    name = name.strip()

    def m(data):
        if name and name not in data["collaborators"]:
            data["collaborators"].append(name)

    return _mutate(path, m)


def remove_collaborator(path: str, name: str):
    def m(data):
        if name in data["collaborators"]:
            data["collaborators"].remove(name)
        # On retire aussi la personne des projets/sous-tâches où elle était assignée
        for p in data["projects"]:
            if name in p.get("assigned", []):
                p["assigned"].remove(name)
            for st in p.get("subtasks", []):
                if name in st.get("assigned", []):
                    st["assigned"].remove(name)

    return _mutate(path, m)


# ---------------------------------------------------------------------------
# Statuts / groupes
# ---------------------------------------------------------------------------

def add_status(path: str, name: str, color: str = "#579bfc"):
    name = name.strip()

    def m(data):
        if name and name not in data["statuses"]:
            data["statuses"].append(name)
            data["status_colors"][name] = color

    return _mutate(path, m)


def remove_status(path: str, name: str, fallback_status: str):
    def m(data):
        if name in data["statuses"]:
            data["statuses"].remove(name)
        data["status_colors"].pop(name, None)
        for p in data["projects"]:
            if p["status"] == name:
                p["status"] = fallback_status

    return _mutate(path, m)


# ---------------------------------------------------------------------------
# Projets
# ---------------------------------------------------------------------------

def new_project_dict(name, status, assigned=None, estimated_time=0.0,
                      start_date=None, due_date=None, budget=0.0, remarks=""):
    return {
        "id": uuid.uuid4().hex,
        "name": name,
        "status": status,
        "assigned": assigned or [],
        "estimated_time": estimated_time,
        "start_date": start_date,
        "due_date": due_date,
        "budget": budget,
        "remarks": remarks,
        "subtasks": [],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }


def add_project(path: str, project: dict):
    def m(data):
        data["projects"].append(project)

    return _mutate(path, m)


def update_project(path: str, project_id: str, updates: dict):
    def m(data):
        for p in data["projects"]:
            if p["id"] == project_id:
                p.update(updates)
                p["updated_at"] = _now_iso()
                break

    return _mutate(path, m)


def delete_project(path: str, project_id: str):
    def m(data):
        data["projects"] = [p for p in data["projects"] if p["id"] != project_id]

    return _mutate(path, m)


# ---------------------------------------------------------------------------
# Sous-tâches
# ---------------------------------------------------------------------------

def add_subtask(path: str, project_id: str, name: str, assigned=None,
                 estimated_time: float = 0.0):
    def m(data):
        for p in data["projects"]:
            if p["id"] == project_id:
                p["subtasks"].append({
                    "id": uuid.uuid4().hex,
                    "name": name,
                    "assigned": assigned or [],
                    "estimated_time": estimated_time,
                    "done": False,
                })
                p["updated_at"] = _now_iso()
                break

    return _mutate(path, m)


def update_subtask(path: str, project_id: str, subtask_id: str, updates: dict):
    def m(data):
        for p in data["projects"]:
            if p["id"] == project_id:
                for st in p["subtasks"]:
                    if st["id"] == subtask_id:
                        st.update(updates)
                        p["updated_at"] = _now_iso()
                        break

    return _mutate(path, m)


def delete_subtask(path: str, project_id: str, subtask_id: str):
    def m(data):
        for p in data["projects"]:
            if p["id"] == project_id:
                p["subtasks"] = [s for s in p["subtasks"] if s["id"] != subtask_id]
                p["updated_at"] = _now_iso()
                break

    return _mutate(path, m)
