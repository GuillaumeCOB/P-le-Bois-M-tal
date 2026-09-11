import math
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

HOURS_PER_DAY = 8


def _business_start(end: datetime, hours: float) -> datetime:
    days_needed = max(1, math.ceil(float(hours or 0) / HOURS_PER_DAY))
    current = end
    collected = 0
    while collected < days_needed:
        if current.weekday() < 5:
            collected += 1
        if collected < days_needed:
            current -= timedelta(days=1)
    return current


def render_gantt(data: dict):
    st.subheader("Vue Gantt / échéancier")

    rows = []
    for project in data.get("projects", []):
        for subproject in project.get("subprojects", []):
            planning_items = subproject.get("tasks", []) or [subproject]
            for item in planning_items:
                if not item.get("due_date"):
                    continue
                try:
                    end = datetime.strptime(item["due_date"], "%Y-%m-%d")
                except ValueError:
                    continue
                start = _business_start(end, float(item.get("estimated_time", 0) or 0))
                label = (
                    f"{project.get('project_number') or '—'} · {project.get('name') or ''} · "
                    f"{subproject.get('type') or subproject.get('phase') or 'Sous-projet'}"
                )
                if item is not subproject:
                    label += f" · {item.get('name') or 'Tâche'}"
                rows.append(
                    {
                        "Élément": label,
                        "Début": start,
                        "Fin": end + timedelta(days=1),
                        "Statut": project.get("status") or "—",
                        "Type": subproject.get("type") or "—",
                        "Assigné": ", ".join(item.get("assigned", [])) or "—",
                        "Client": project.get("client") or "—",
                        "Structure": project.get("discipline") or "—",
                    }
                )

    if not rows:
        st.info("Aucun sous-projet ou tâche avec une échéance à afficher.")
        return

    df = pd.DataFrame(rows)
    fig = px.timeline(
        df,
        x_start="Début",
        x_end="Fin",
        y="Élément",
        color="Statut",
        color_discrete_map=data.get("status_colors", {}),
        hover_data=["Type", "Assigné", "Client", "Structure"],
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=max(360, 36 * len(df)))
    st.plotly_chart(fig, use_container_width=True)
