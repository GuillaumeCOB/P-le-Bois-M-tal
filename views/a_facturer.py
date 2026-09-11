from datetime import datetime

import pandas as pd
import streamlit as st

from config import DISCIPLINES
from ui.components import display_amount

MOIS_FR = [
    "",
    "Janvier",
    "Février",
    "Mars",
    "Avril",
    "Mai",
    "Juin",
    "Juillet",
    "Août",
    "Septembre",
    "Octobre",
    "Novembre",
    "Décembre",
]


def _parse_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def _month_label(key: str) -> str:
    year, month = key.split("-")
    return f"{MOIS_FR[int(month)]} {year}"


def _invoice_entries(data: dict) -> list[dict]:
    entries = []

    for project in data.get("projects", []):
        base = {
            "N°": project.get("project_number") or "—",
            "Projet": project.get("name") or "—",
            "Client": project.get("client") or "—",
            "Structure": project.get("discipline") or "—",
        }

        if project.get("invoice_ready"):
            marked_at = _parse_datetime(project.get("invoice_marked_at"))
            if marked_at:
                entries.append(
                    {
                        **base,
                        "Niveau": "Projet",
                        "Élément": project.get("name") or "Projet",
                        "Montant": float(project.get("invoice_amount") or 0),
                        "Date": marked_at,
                    }
                )
            continue

        for subproject in project.get("subprojects", []):
            if subproject.get("invoice_ready"):
                marked_at = _parse_datetime(subproject.get("invoice_marked_at"))
                if marked_at:
                    entries.append(
                        {
                            **base,
                            "Niveau": "Sous-projet",
                            "Élément": subproject.get("type") or subproject.get("phase") or "Sous-projet",
                            "Montant": float(subproject.get("invoice_amount") or 0),
                            "Date": marked_at,
                        }
                    )
                continue

            for task in subproject.get("tasks", []):
                if not task.get("invoice_ready"):
                    continue
                marked_at = _parse_datetime(task.get("invoice_marked_at"))
                if not marked_at:
                    continue
                entries.append(
                    {
                        **base,
                        "Niveau": "Tâche",
                        "Élément": f"{subproject.get('type') or subproject.get('phase') or 'Sous-projet'} · {task.get('name') or 'Tâche'}",
                        "Montant": float(task.get("invoice_amount") or 0),
                        "Date": marked_at,
                    }
                )

    return sorted(entries, key=lambda item: item["Date"], reverse=True)


def render_a_facturer(data: dict):
    st.subheader("À facturer")

    entries = _invoice_entries(data)
    if not entries:
        st.info(
            "Aucun élément à facturer. Cochez la case de facturation d'un projet, "
            "d'un sous-projet ou d'une tâche dans le Tableau."
        )
        return

    for entry in entries:
        entry["Mois"] = entry["Date"].strftime("%Y-%m")

    month_keys = sorted({entry["Mois"] for entry in entries}, reverse=True)
    filters = st.columns([1.2, 1.2, 3.0], gap="small")
    month_filter = filters[0].selectbox(
        "Mois de facturation",
        [None] + month_keys,
        format_func=lambda value: "Tous les mois" if value is None else _month_label(value),
    )
    discipline_filter = filters[1].selectbox(
        "Structure",
        [None] + DISCIPLINES,
        format_func=lambda value: "Toutes les structures" if value is None else value,
    )

    filtered = [
        entry
        for entry in entries
        if (month_filter is None or entry["Mois"] == month_filter)
        and (discipline_filter is None or entry["Structure"] == discipline_filter)
    ]

    if not filtered:
        st.info("Aucun élément ne correspond aux filtres.")
        return

    total = sum(entry["Montant"] for entry in filtered)
    st.markdown(
        f"**{len(filtered)} élément{'s' if len(filtered) != 1 else ''} · {display_amount(total)}**"
    )

    grouped_months = sorted({entry["Mois"] for entry in filtered}, reverse=True)
    for month_key in grouped_months:
        month_entries = [entry for entry in filtered if entry["Mois"] == month_key]
        month_total = sum(entry["Montant"] for entry in month_entries)
        with st.expander(
            f"{_month_label(month_key)} · {len(month_entries)} élément{'s' if len(month_entries) != 1 else ''} · {display_amount(month_total)}",
            expanded=True,
        ):
            rows = []
            for entry in month_entries:
                rows.append(
                    {
                        "Niveau": entry["Niveau"],
                        "N°": entry["N°"],
                        "Projet": entry["Projet"],
                        "Client": entry["Client"],
                        "Structure": entry["Structure"],
                        "Élément": entry["Élément"],
                        "Montant": display_amount(entry["Montant"]),
                        "Mise à facturer": entry["Date"].strftime("%d/%m/%Y %H:%M"),
                    }
                )
            st.dataframe(
                pd.DataFrame(rows),
                use_container_width=True,
                hide_index=True,
            )
