from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st


def render_gantt(data: dict):
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
            "Projet": f"{p.get('project_number') or '—'} · {p['name']}",
            "Début": start,
            "Fin": end,
            "Statut": p["status"],
            "Type": p.get("type") or "—",
            "Assigné": ", ".join(p.get("assigned", [])) or "—",
        })

    if not rows:
        st.info("Aucun projet avec une date d'échéance à afficher.")
        return

    df = pd.DataFrame(rows)
    fig = px.timeline(
        df,
        x_start="Début",
        x_end="Fin",
        y="Projet",
        color="Statut",
        color_discrete_map=data["status_colors"],
        hover_data=["Type", "Assigné"],
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_layout(height=max(320, 40 * len(df)))
    st.plotly_chart(fig, use_container_width=True)
