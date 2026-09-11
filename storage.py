"""
Stockage Supabase de l'outil de gestion de projets.

Modèle v2 :
Projet -> Sous-projets / phases -> Tâches.
Les données restent stockées dans une seule ligne JSON afin de rester
compatibles avec le déploiement actuel. Une migration automatique transforme
les anciens projets/sous-tâches au premier chargement.
"""

import json
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st
from supabase import create_client, Client

BOARD_ID = 1
MODEL_VERSION = 2

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

DEFAULT_TYPES = ["DIAGNOSTIC", "APS", "APD", "PRO", "DCE", "EXE"]

TYPE_COLORS = {
    "DIAGNOSTIC": "#FBD9D3",
    "APS": "#FCE8C9",
    "APD": "#FBF3C4",
    "PRO": "#D9F0D6",
    "DCE": "#D6E6F5",
    "EXE": "#E5DAF2",
}

DEFAULT_DATA = {
    "collaborators": [],
    "statuses": DEFAULT_STATUSES.copy(),
    "status_colors": STATUS_COLORS.copy(),
    "types": DEFAULT_TYPES.copy(),
    "type_colors": TYPE_COLORS.copy(),
    "projects": [],
    "_meta": {"last_modified": None, "model_version": MODEL_VERSION},
}


def _now_iso():
    return datetime.now().astimezone().isoformat()


def _invoice_now_iso():
    return datetime.now(ZoneInfo("Europe/Paris")).isoformat()


def _invoice_defaults(item: dict):
    changed = False
    defaults = {
        "invoice_ready": False,
        "invoice_marked_at": None,
        "invoice_amount": None,
    }
    for key, value in defaults.items():
        if key not in item:
            item[key] = value
            changed = True
    return changed


def _clear_invoice(item: dict):
    item["invoice_ready"] = False
    item["invoice_marked_at"] = None
    item["invoice_amount"] = None


def _normalise_task(task: dict, fallback_status: str, fallback_due_date=None):
    changed = _invoice_defaults(task)
    defaults = {
        "id": uuid.uuid4().hex,
        "name": "Tâche",
        "assigned": [],
        "status": fallback_status,
        "due_date": fallback_due_date,
        "budget": 0.0,
        "estimated_time": 0.0,
        "remarks": "",
    }
    for key, value in defaults.items():
        if key not in task:
            task[key] = json.loads(json.dumps(value))
            changed = True
    if task.get("done") and task.get("status") != "Terminé":
        task["status"] = "Terminé"
        changed = True
    return changed


def _normalise_subproject(subproject: dict, fallback_status: str):
    changed = _invoice_defaults(subproject)
    defaults = {
        "id": uuid.uuid4().hex,
        "phase": subproject.get("name") or "Phase",
        "type": None,
        "assigned": [],
        "status": fallback_status,
        "due_date": None,
        "budget": 0.0,
        "estimated_time": 0.0,
        "remarks": "",
        "tasks": [],
    }
    for key, value in defaults.items():
        if key not in subproject:
            subproject[key] = json.loads(json.dumps(value))
            changed = True
    if "name" in subproject and not subproject.get("phase"):
        subproject["phase"] = subproject.get("name") or "Phase"
        changed = True
    for task in subproject.get("tasks", []):
        changed |= _normalise_task(
            task,
            subproject.get("status") or fallback_status,
            subproject.get("due_date"),
        )
    return changed


def _migrate_project(project: dict, statuses: list[str]):
    changed = _invoice_defaults(project)
    fallback_status = statuses[0] if statuses else "En cours"

    if "client" not in project:
        project["client"] = ""
        changed = True
    if "discipline" not in project:
        project["discipline"] = "Bois / Métal"
        changed = True
    if "project_number" not in project:
        project["project_number"] = None
        changed = True
    if "remarks" not in project:
        project["remarks"] = ""
        changed = True

    if "subprojects" not in project:
        old_subtasks = project.get("subtasks", [])
        has_legacy_operational_data = any(
            [
                project.get("type"),
                project.get("status"),
                project.get("assigned"),
                project.get("due_date"),
                project.get("budget"),
                project.get("estimated_time"),
                old_subtasks,
            ]
        )
        subprojects = []
        if has_legacy_operational_data:
            parent_status = project.get("status") or fallback_status
            phase = project.get("type") or "Phase initiale"
            tasks = []
            for old_task in old_subtasks:
                task_status = (
                    "Terminé"
                    if old_task.get("done") and "Terminé" in statuses
                    else parent_status
                )
                task = {
                    "id": old_task.get("id") or uuid.uuid4().hex,
                    "name": old_task.get("name") or "Tâche",
                    "assigned": old_task.get("assigned", []),
                    "status": task_status,
                    "due_date": project.get("due_date"),
                    "budget": float(old_task.get("budget", 0) or 0),
                    "estimated_time": float(old_task.get("estimated_time", 0) or 0),
                    "remarks": old_task.get("remarks", ""),
                    "invoice_ready": False,
                    "invoice_marked_at": None,
                    "invoice_amount": None,
                }
                tasks.append(task)

            subprojects.append(
                {
                    "id": uuid.uuid4().hex,
                    "phase": phase,
                    "type": project.get("type"),
                    "assigned": project.get("assigned", []),
                    "status": parent_status,
                    "due_date": project.get("due_date"),
                    "budget": float(project.get("budget", 0) or 0),
                    "estimated_time": float(project.get("estimated_time", 0) or 0),
                    "remarks": "",
                    "tasks": tasks,
                    "invoice_ready": False,
                    "invoice_marked_at": None,
                    "invoice_amount": None,
                }
            )
        project["subprojects"] = subprojects
        changed = True

    if "created_at" not in project:
        project["created_at"] = _now_iso()
        changed = True
    if "updated_at" not in project:
        project["updated_at"] = _now_iso()
        changed = True

    for subproject in project.get("subprojects", []):
        changed |= _normalise_subproject(subproject, fallback_status)

    return changed


def _migrate_data_model(data: dict):
    changed = False
    statuses = data.get("statuses") or DEFAULT_STATUSES
    for project in data.get("projects", []):
        changed |= _migrate_project(project, statuses)

    meta = data.setdefault("_meta", {})
    if meta.get("model_version") != MODEL_VERSION:
        meta["model_version"] = MODEL_VERSION
        changed = True
    return changed


@st.cache_resource
def _get_client() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def load_data(_path: str = None) -> dict:
    client = _get_client()
    res = client.table("app_data").select("data").eq("id", BOARD_ID).execute()
    if res.data:
        data = res.data[0]["data"]
    else:
        data = json.loads(json.dumps(DEFAULT_DATA))
        data["_meta"]["last_modified"] = _now_iso()
        client.table("app_data").insert({"id": BOARD_ID, "data": data}).execute()

    for key, value in DEFAULT_DATA.items():
        if key not in data:
            data[key] = json.loads(json.dumps(value))

    if _migrate_data_model(data):
        _atomic_write(_path, data)
    return data


def _atomic_write(_path: str, data: dict):
    data.setdefault("_meta", {})["last_modified"] = _now_iso()
    data["_meta"]["model_version"] = MODEL_VERSION
    client = _get_client()
    client.table("app_data").upsert({"id": BOARD_ID, "data": data}).execute()


def _mutate(path: str, mutator):
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
        for project in data["projects"]:
            for subproject in project.get("subprojects", []):
                if name in subproject.get("assigned", []):
                    subproject["assigned"].remove(name)
                for task in subproject.get("tasks", []):
                    if name in task.get("assigned", []):
                        task["assigned"].remove(name)

    return _mutate(path, m)


# ---------------------------------------------------------------------------
# Statuts
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
        for project in data["projects"]:
            for subproject in project.get("subprojects", []):
                if subproject.get("status") == name:
                    subproject["status"] = fallback_status
                for task in subproject.get("tasks", []):
                    if task.get("status") == name:
                        task["status"] = fallback_status

    return _mutate(path, m)


def _move_in_list(lst: list, item, delta: int):
    if item not in lst:
        return
    idx = lst.index(item)
    new_idx = idx + delta
    if 0 <= new_idx < len(lst):
        lst[idx], lst[new_idx] = lst[new_idx], lst[idx]


def move_status(path: str, name: str, delta: int):
    return _mutate(path, lambda data: _move_in_list(data["statuses"], name, delta))


# ---------------------------------------------------------------------------
# Types de projet
# ---------------------------------------------------------------------------

def add_type(path: str, name: str, color: str = "#eeeeee"):
    name = name.strip()

    def m(data):
        if name and name not in data["types"]:
            data["types"].append(name)
            data["type_colors"][name] = color

    return _mutate(path, m)


def remove_type(path: str, name: str):
    def m(data):
        if name in data["types"]:
            data["types"].remove(name)
        data["type_colors"].pop(name, None)
        for project in data["projects"]:
            for subproject in project.get("subprojects", []):
                if subproject.get("type") == name:
                    subproject["type"] = None

    return _mutate(path, m)


def move_type(path: str, name: str, delta: int):
    return _mutate(path, lambda data: _move_in_list(data["types"], name, delta))


# ---------------------------------------------------------------------------
# Projets
# ---------------------------------------------------------------------------

def new_project_dict(
    name: str,
    project_number=None,
    client: str = "",
    discipline: str = "Bois / Métal",
    remarks: str = "",
):
    return {
        "id": uuid.uuid4().hex,
        "project_number": project_number,
        "name": name,
        "client": client,
        "discipline": discipline,
        "remarks": remarks,
        "subprojects": [],
        "invoice_ready": False,
        "invoice_marked_at": None,
        "invoice_amount": None,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }


def add_project(path: str, project: dict):
    return _mutate(path, lambda data: data["projects"].append(project))


def update_project(path: str, project_id: str, updates: dict):
    def m(data):
        for project in data["projects"]:
            if project["id"] == project_id:
                project.update(updates)
                project["updated_at"] = _now_iso()
                break

    return _mutate(path, m)


def delete_project(path: str, project_id: str):
    def m(data):
        data["projects"] = [p for p in data["projects"] if p["id"] != project_id]

    return _mutate(path, m)


# ---------------------------------------------------------------------------
# Sous-projets / phases
# ---------------------------------------------------------------------------

def add_subproject(
    path: str,
    project_id: str,
    phase: str,
    project_type,
    assigned,
    status: str,
    due_date,
    budget: float,
    estimated_time: float,
    remarks: str = "",
):
    def m(data):
        for project in data["projects"]:
            if project["id"] == project_id:
                project["subprojects"].append(
                    {
                        "id": uuid.uuid4().hex,
                        "phase": phase,
                        "type": project_type,
                        "assigned": assigned or [],
                        "status": status,
                        "due_date": due_date,
                        "budget": float(budget or 0),
                        "estimated_time": float(estimated_time or 0),
                        "remarks": remarks,
                        "tasks": [],
                        "invoice_ready": False,
                        "invoice_marked_at": None,
                        "invoice_amount": None,
                    }
                )
                project["updated_at"] = _now_iso()
                break

    return _mutate(path, m)


def update_subproject(path: str, project_id: str, subproject_id: str, updates: dict):
    def m(data):
        for project in data["projects"]:
            if project["id"] != project_id:
                continue
            for subproject in project.get("subprojects", []):
                if subproject["id"] == subproject_id:
                    subproject.update(updates)
                    project["updated_at"] = _now_iso()
                    return

    return _mutate(path, m)


def delete_subproject(path: str, project_id: str, subproject_id: str):
    def m(data):
        for project in data["projects"]:
            if project["id"] == project_id:
                project["subprojects"] = [
                    sp for sp in project.get("subprojects", []) if sp["id"] != subproject_id
                ]
                project["updated_at"] = _now_iso()
                break

    return _mutate(path, m)


# ---------------------------------------------------------------------------
# Tâches
# ---------------------------------------------------------------------------

def add_task(
    path: str,
    project_id: str,
    subproject_id: str,
    name: str,
    assigned,
    status: str,
    due_date,
    budget: float,
    estimated_time: float,
    remarks: str = "",
):
    def m(data):
        for project in data["projects"]:
            if project["id"] != project_id:
                continue
            for subproject in project.get("subprojects", []):
                if subproject["id"] == subproject_id:
                    subproject["tasks"].append(
                        {
                            "id": uuid.uuid4().hex,
                            "name": name,
                            "assigned": assigned or [],
                            "status": status,
                            "due_date": due_date,
                            "budget": float(budget or 0),
                            "estimated_time": float(estimated_time or 0),
                            "remarks": remarks,
                            "invoice_ready": False,
                            "invoice_marked_at": None,
                            "invoice_amount": None,
                        }
                    )
                    project["updated_at"] = _now_iso()
                    return

    return _mutate(path, m)


def update_task(path: str, project_id: str, subproject_id: str, task_id: str, updates: dict):
    def m(data):
        for project in data["projects"]:
            if project["id"] != project_id:
                continue
            for subproject in project.get("subprojects", []):
                if subproject["id"] != subproject_id:
                    continue
                for task in subproject.get("tasks", []):
                    if task["id"] == task_id:
                        task.update(updates)
                        project["updated_at"] = _now_iso()
                        return

    return _mutate(path, m)


def delete_task(path: str, project_id: str, subproject_id: str, task_id: str):
    def m(data):
        for project in data["projects"]:
            if project["id"] != project_id:
                continue
            for subproject in project.get("subprojects", []):
                if subproject["id"] == subproject_id:
                    subproject["tasks"] = [
                        task for task in subproject.get("tasks", []) if task["id"] != task_id
                    ]
                    project["updated_at"] = _now_iso()
                    return

    return _mutate(path, m)


# ---------------------------------------------------------------------------
# Facturation
# ---------------------------------------------------------------------------

def _project_budget(project: dict) -> float:
    return sum(float(sp.get("budget", 0) or 0) for sp in project.get("subprojects", []))


def set_invoice_state(
    path: str,
    level: str,
    project_id: str,
    entity_id: str | None,
    checked: bool,
):
    def m(data):
        project = next((p for p in data["projects"] if p["id"] == project_id), None)
        if not project:
            return

        target = None
        amount = 0.0
        if level == "project":
            target = project
            amount = _project_budget(project)
        elif level == "subproject":
            target = next(
                (sp for sp in project.get("subprojects", []) if sp["id"] == entity_id),
                None,
            )
            if target:
                amount = float(target.get("budget", 0) or 0)
        elif level == "task":
            for subproject in project.get("subprojects", []):
                task = next(
                    (task for task in subproject.get("tasks", []) if task["id"] == entity_id),
                    None,
                )
                if task:
                    target = task
                    amount = float(task.get("budget", 0) or 0)
                    break

        if target is None:
            return

        if checked:
            target["invoice_ready"] = True
            target["invoice_marked_at"] = _invoice_now_iso()
            target["invoice_amount"] = amount

            if level == "project":
                for subproject in project.get("subprojects", []):
                    _clear_invoice(subproject)
                    for task in subproject.get("tasks", []):
                        _clear_invoice(task)
            elif level == "subproject":
                for task in target.get("tasks", []):
                    _clear_invoice(task)
        else:
            _clear_invoice(target)

        project["updated_at"] = _now_iso()

    return _mutate(path, m)
