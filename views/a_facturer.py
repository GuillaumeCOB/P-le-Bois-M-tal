from datetime import datetime
from html import escape

import streamlit as st

from config import DISCIPLINES
from data_service import run_db_action
from ui.components import css_scope, display_amount, ui_container

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


def _detail_entry(base: dict, *, level: str, element: str, amount: float, date: datetime, depth: int) -> dict:
    return {
        **base,
        "Niveau": level,
        "Élément": element,
        "Montant": float(amount or 0),
        "Date": date,
        "_level": None,
        "_entity_id": None,
        "_is_detail": True,
        "_detail_depth": depth,
    }


def _invoice_entries(data: dict) -> list[dict]:
    """Construit les lignes facturées + les lignes de détail informatives.

    Les lignes de détail ne sont jamais intégrées aux totaux et n'ont pas de bouton
    d'annulation. Elles servent uniquement à expliquer ce qui est inclus dans un
    projet ou un sous-projet mis à facturer.
    """
    entries = []

    for project in data.get("projects", []):
        base = {
            "N°": project.get("project_number") or "—",
            "Projet": project.get("name") or "—",
            "Client": project.get("client") or "—",
            "Structure": project.get("discipline") or "—",
            "_project_id": project.get("id"),
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
                        "_level": "project",
                        "_entity_id": None,
                        "_is_detail": False,
                        "_detail_depth": 0,
                    }
                )

                # Projet complet : afficher tous les sous-projets puis leurs tâches.
                for subproject in project.get("subprojects", []):
                    subproject_label = (
                        subproject.get("type")
                        or subproject.get("phase")
                        or "Sous-projet"
                    )
                    entries.append(
                        _detail_entry(
                            base,
                            level="Sous-projet inclus",
                            element=subproject_label,
                            amount=float(subproject.get("budget", 0) or 0),
                            date=marked_at,
                            depth=1,
                        )
                    )
                    for task in subproject.get("tasks", []):
                        entries.append(
                            _detail_entry(
                                base,
                                level="Tâche incluse",
                                element=task.get("name") or "Tâche",
                                amount=float(task.get("budget", 0) or 0),
                                date=marked_at,
                                depth=2,
                            )
                        )
            continue

        for subproject in project.get("subprojects", []):
            if subproject.get("invoice_ready"):
                marked_at = _parse_datetime(subproject.get("invoice_marked_at"))
                if marked_at:
                    subproject_label = (
                        subproject.get("type")
                        or subproject.get("phase")
                        or "Sous-projet"
                    )
                    entries.append(
                        {
                            **base,
                            "Niveau": "Sous-projet",
                            "Élément": subproject_label,
                            "Montant": float(subproject.get("invoice_amount") or 0),
                            "Date": marked_at,
                            "_level": "subproject",
                            "_entity_id": subproject.get("id"),
                            "_is_detail": False,
                            "_detail_depth": 0,
                        }
                    )

                    # Sous-projet complet : afficher ses tâches comme détail inclus.
                    for task in subproject.get("tasks", []):
                        entries.append(
                            _detail_entry(
                                base,
                                level="Tâche incluse",
                                element=task.get("name") or "Tâche",
                                amount=float(task.get("budget", 0) or 0),
                                date=marked_at,
                                depth=1,
                            )
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
                        "Élément": (
                            f"{subproject.get('type') or subproject.get('phase') or 'Sous-projet'}"
                            f" · {task.get('name') or 'Tâche'}"
                        ),
                        "Montant": float(task.get("invoice_amount") or 0),
                        "Date": marked_at,
                        "_level": "task",
                        "_entity_id": task.get("id"),
                        "_is_detail": False,
                        "_detail_depth": 0,
                    }
                )

    # Chaque bloc parent + détails reste groupé. Le tri par date suffit car les
    # lignes d'un même bloc partagent exactement la même date de facturation.
    return sorted(entries, key=lambda item: item["Date"], reverse=True)


def _cancel_invoice(entry: dict):
    if entry.get("_is_detail"):
        return
    run_db_action(
        "set_invoice_state",
        entry["_level"],
        entry["_project_id"],
        entry["_entity_id"],
        False,
    )


def _invoice_cell(col, value, *, bold=False, align="left", detail_depth=0, muted=False):
    text = escape(str(value if value not in (None, "") else "—"))
    weight = "700" if bold else "400"
    justify = {"left": "flex-start", "center": "center", "right": "flex-end"}.get(
        align, "flex-start"
    )
    padding_left = 0.18 + (0.70 * detail_depth)
    color = "#7A7F9F" if muted else "#1F2340"
    col.markdown(
        f'<div class="pbm-invoice-cell" '
        f'style="justify-content:{justify};font-weight:{weight};'
        f'padding-left:{padding_left:.2f}rem;color:{color};">{text}</div>',
        unsafe_allow_html=True,
    )


def _invoice_blocks(entries: list[dict]) -> list[dict]:
    """Regroupe chaque ligne facturée avec ses éventuelles lignes de détail."""
    blocks = []
    current = None
    for entry in entries:
        if not entry.get("_is_detail"):
            current = {"parent": entry, "details": []}
            blocks.append(current)
        elif current is not None:
            current["details"].append(entry)
    return blocks


def _render_invoice_table(entries: list[dict], month_key: str):
    # 1re colonne = flèche d'ouverture du détail ; dernière colonne = annulation.
    widths = [0.38, 0.94, 0.72, 1.65, 1.35, 1.05, 2.10, 0.92, 1.30, 0.62]

    with ui_container(f"invoice_header_{month_key}", "invoiceheader"):
        header = st.columns(widths, gap="small", vertical_alignment="center")
        labels = [
            "",
            "Niveau",
            "N°",
            "Projet",
            "Client",
            "Structure",
            "Élément",
            "Montant",
            "Mise à facturer",
            "",
        ]
        for index, (col, label) in enumerate(zip(header, labels)):
            if label:
                _invoice_cell(
                    col,
                    label,
                    bold=True,
                    align="right" if index == 7 else "left",
                )

    for block_index, block in enumerate(_invoice_blocks(entries)):
        entry = block["parent"]
        details = block["details"]
        entity_token = entry.get("_entity_id") or "project"
        expand_key = (
            f"invoice_detail_open_{month_key}_{entry['_level']}_"
            f"{entry['_project_id']}_{entity_token}_{block_index}"
        )
        if expand_key not in st.session_state:
            st.session_state[expand_key] = False

        with ui_container(
            f"invoice_row_{month_key}_{block_index}_{entry['_level']}_{entry['_project_id']}",
            "invoicerow",
        ):
            cols = st.columns(widths, gap="small", vertical_alignment="center")

            if details:
                arrow = "▾" if st.session_state[expand_key] else "▸"
                if cols[0].button(
                    arrow,
                    key=f"toggle_{expand_key}",
                    help="Afficher / masquer le détail inclus",
                    use_container_width=True,
                ):
                    st.session_state[expand_key] = not st.session_state[expand_key]
                    st.rerun()
            else:
                _invoice_cell(cols[0], "", align="center")

            _invoice_cell(cols[1], entry["Niveau"], bold=True)
            _invoice_cell(cols[2], entry["N°"])
            _invoice_cell(cols[3], entry["Projet"])
            _invoice_cell(cols[4], entry["Client"])
            _invoice_cell(cols[5], entry["Structure"])
            _invoice_cell(cols[6], entry["Élément"])
            _invoice_cell(cols[7], display_amount(entry["Montant"]), align="right", bold=True)
            _invoice_cell(cols[8], entry["Date"].strftime("%d/%m/%Y %H:%M"))

            if cols[9].button(
                "↩",
                key=(
                    f"cancel_invoice_{month_key}_{entry['_level']}_"
                    f"{entry['_project_id']}_{entity_token}_{block_index}"
                ),
                help="Annuler la mise à facturer et remettre l'élément dans le Tableau.",
                use_container_width=True,
            ):
                _cancel_invoice(entry)
                st.rerun()

        if not details or not st.session_state[expand_key]:
            continue

        for detail_index, detail in enumerate(details):
            detail_depth = int(detail.get("_detail_depth", 0) or 0)
            with ui_container(
                f"invoice_detail_{month_key}_{block_index}_{detail_index}_{entry['_project_id']}",
                "invoicedetailrow",
            ):
                cols = st.columns(widths, gap="small", vertical_alignment="center")
                _invoice_cell(cols[0], "", muted=True)
                _invoice_cell(
                    cols[1],
                    "↳ " + detail["Niveau"],
                    muted=True,
                    detail_depth=max(detail_depth - 1, 0),
                )
                _invoice_cell(cols[2], "", muted=True)
                _invoice_cell(cols[3], "", muted=True)
                _invoice_cell(cols[4], "", muted=True)
                _invoice_cell(cols[5], "", muted=True)
                _invoice_cell(
                    cols[6],
                    detail["Élément"],
                    muted=True,
                    detail_depth=detail_depth,
                )
                _invoice_cell(
                    cols[7],
                    display_amount(detail["Montant"]),
                    align="right",
                    muted=True,
                )
                _invoice_cell(cols[8], "Inclus", muted=True)
                _invoice_cell(cols[9], "", muted=True)

def render_a_facturer(data: dict):
    invoice_header = css_scope("invoiceheader")
    invoice_row = css_scope("invoicerow")
    invoice_detail_row = css_scope("invoicedetailrow")
    st.markdown(
        f"""
        <style>
        .pbm-invoice-cell {{
            display: flex;
            align-items: center;
            width: 100%;
            min-height: 24px;
            padding: 0 0.18rem;
            margin: 0;
            box-sizing: border-box;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
            font-size: 0.78rem;
            line-height: 1;
            color: #1F2340;
        }}
        {invoice_header} {{
            min-height: 30px !important;
            padding: 0.08rem 0.12rem !important;
            margin: 0 0 0.10rem 0 !important;
            background: rgba(59,56,245,0.055);
            border: 1px solid rgba(59,56,245,0.12);
            border-radius: 8px;
            gap: 0 !important;
        }}
        {invoice_header} .pbm-invoice-cell {{
            min-height: 26px;
            font-size: 0.70rem;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            color: #70759A;
        }}
        {invoice_row},
        {invoice_detail_row} {{
            min-height: 28px !important;
            padding: 0.02rem 0.12rem !important;
            margin: 0 !important;
            gap: 0 !important;
        }}
        {invoice_row} {{
            border-bottom: 1px solid rgba(64,51,140,0.09);
            background: rgba(255,255,255,0.70);
        }}
        {invoice_detail_row} {{
            border-bottom: 1px solid rgba(64,51,140,0.035);
            background: rgba(64,51,140,0.018);
        }}
        {invoice_row} [data-testid="stHorizontalBlock"],
        {invoice_detail_row} [data-testid="stHorizontalBlock"] {{
            min-height: 28px !important;
            align-items: center !important;
            gap: 6px !important;
            margin: 0 !important;
            padding: 0 !important;
        }}
        {invoice_row} :is(.element-container, [data-testid="stElementContainer"]),
        {invoice_detail_row} :is(.element-container, [data-testid="stElementContainer"]),
        {invoice_header} :is(.element-container, [data-testid="stElementContainer"]) {{
            margin: 0 !important;
            padding: 0 !important;
        }}
        {invoice_detail_row} .pbm-invoice-cell {{
            min-height: 23px;
            font-size: 0.73rem;
        }}
        {invoice_row} [data-testid="stButton"] button {{
            min-height: 24px !important;
            height: 24px !important;
            padding: 0 !important;
            border-radius: 6px !important;
        }}
        {invoice_row} [data-testid="stButton"] button p {{
            margin: 0 !important;
            line-height: 1 !important;
            font-size: 0.86rem !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

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
        format_func=lambda value: "Tous les mois"
        if value is None
        else _month_label(value),
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

    billable_filtered = [entry for entry in filtered if not entry.get("_is_detail")]
    total = sum(entry["Montant"] for entry in billable_filtered)
    st.markdown(
        f"**{len(billable_filtered)} élément{'s' if len(billable_filtered) != 1 else ''} · {display_amount(total)}**"
    )

    grouped_months = sorted({entry["Mois"] for entry in filtered}, reverse=True)
    for month_key in grouped_months:
        month_entries = [entry for entry in filtered if entry["Mois"] == month_key]
        month_billable = [entry for entry in month_entries if not entry.get("_is_detail")]
        month_total = sum(entry["Montant"] for entry in month_billable)
        with st.expander(
            f"{_month_label(month_key)} · {len(month_billable)} élément{'s' if len(month_billable) != 1 else ''} · {display_amount(month_total)}",
            expanded=True,
        ):
            _render_invoice_table(month_entries, month_key)
