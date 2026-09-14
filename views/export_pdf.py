from __future__ import annotations

from datetime import datetime
from html import escape
from io import BytesIO
from zoneinfo import ZoneInfo

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import LOGO_PATH, PRIMARY, PRIMARY_DARK
from ui.components import project_totals, projects_totals
from views.tableau import get_filtered_projects


PARIS_TZ = ZoneInfo("Europe/Paris")


def current_tableau_filters() -> dict:
    """Lit les filtres déjà appliqués dans la page Tableau."""
    return {
        "query": st.session_state.get("pbm_search", ""),
        "person_filter": st.session_state.get("pbm_person"),
        "type_filter": st.session_state.get("pbm_type"),
        "discipline_filter": st.session_state.get("pbm_summary_discipline"),
        "status_filter": st.session_state.get("pbm_summary_status"),
    }


def tableau_export_filename() -> str:
    now = datetime.now(PARIS_TZ)
    return f"recap_tableau_{now.strftime('%Y-%m-%d_%H-%M')}.pdf"


def _amount(value) -> str:
    return f"{float(value or 0):,.0f} €".replace(",", " ")


def _hours(value) -> str:
    return f"{float(value or 0):.1f} h".replace(".", ",")


def _text(value, fallback="-") -> str:
    if value in (None, ""):
        return fallback
    return str(value).replace("\n", " ").strip() or fallback


def _safe_hex(value: str | None, fallback: str) -> colors.Color:
    try:
        return HexColor(str(value or fallback))
    except Exception:
        return HexColor(fallback)


def _paragraph(value, style) -> Paragraph:
    return Paragraph(escape(_text(value)), style)


def _filter_summary(filters: dict) -> list[tuple[str, str]]:
    rows = []
    query = str(filters.get("query") or "").strip()
    if query:
        rows.append(("Recherche", query))
    if filters.get("person_filter"):
        rows.append(("Collaborateur", str(filters["person_filter"])))
    if filters.get("type_filter"):
        rows.append(("Type", str(filters["type_filter"])))
    if filters.get("discipline_filter"):
        rows.append(("Structure", str(filters["discipline_filter"])))
    if filters.get("status_filter"):
        rows.append(("Statut", str(filters["status_filter"])))
    return rows


def _sorted_projects(projects: list[dict]) -> list[dict]:
    return sorted(
        projects,
        key=lambda p: (
            str(p.get("project_number") or "999999999").casefold(),
            str(p.get("name") or "").casefold(),
        ),
    )


def _status_projects(data: dict, projects: list[dict], status_filter: str | None):
    for status in data.get("statuses", []):
        if status_filter is not None and status != status_filter:
            continue
        rows = _sorted_projects([p for p in projects if p.get("status") == status])
        if rows:
            yield status, rows


def _page_header_footer(canvas, doc):
    canvas.saveState()
    width, height = landscape(A4)
    canvas.setStrokeColor(colors.HexColor("#E6E6F2"))
    canvas.setLineWidth(0.5)
    canvas.line(14 * mm, 11 * mm, width - 14 * mm, 11 * mm)
    canvas.setFillColor(colors.HexColor("#70759A"))
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(14 * mm, 7 * mm, "Builders - verticalsea | Suivi de projets Structures")
    canvas.drawRightString(width - 14 * mm, 7 * mm, f"Page {doc.page}")
    canvas.restoreState()


@st.cache_data(show_spinner=False)
def build_tableau_pdf(data: dict, filters: dict) -> bytes:
    """Crée le récapitulatif PDF du Tableau pour les filtres courants."""
    projects = get_filtered_projects(data, **filters)
    now = datetime.now(PARIS_TZ)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=16 * mm,
        title="Récapitulatif du tableau de projets",
        author="Builders - verticalsea",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PbmTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=19,
        textColor=_safe_hex(PRIMARY_DARK, "#40338C"),
        alignment=TA_LEFT,
        spaceAfter=2 * mm,
    )
    meta_style = ParagraphStyle(
        "PbmMeta",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#70759A"),
    )
    filter_label_style = ParagraphStyle(
        "PbmFilterLabel",
        parent=meta_style,
        fontName="Helvetica-Bold",
        textColor=_safe_hex(PRIMARY_DARK, "#40338C"),
    )
    status_style = ParagraphStyle(
        "PbmStatus",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=_safe_hex(PRIMARY_DARK, "#40338C"),
        spaceBefore=3.5 * mm,
        spaceAfter=1.5 * mm,
    )
    cell_style = ParagraphStyle(
        "PbmCell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor("#1F2340"),
    )
    cell_bold_style = ParagraphStyle(
        "PbmCellBold",
        parent=cell_style,
        fontName="Helvetica-Bold",
    )
    cell_right_style = ParagraphStyle(
        "PbmCellRight",
        parent=cell_style,
        alignment=TA_RIGHT,
    )
    cell_right_bold_style = ParagraphStyle(
        "PbmCellRightBold",
        parent=cell_right_style,
        fontName="Helvetica-Bold",
    )
    header_style = ParagraphStyle(
        "PbmHeaderCell",
        parent=cell_style,
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        textColor=colors.HexColor("#5D6288"),
    )
    header_right_style = ParagraphStyle(
        "PbmHeaderRight",
        parent=header_style,
        alignment=TA_RIGHT,
    )

    story = []

    top_data = []
    if LOGO_PATH.exists():
        logo = Image(str(LOGO_PATH))
        logo.drawHeight = 13 * mm
        logo.drawWidth = 36 * mm
        top_data.append(logo)
    else:
        top_data.append("")

    title_block = [
        Paragraph("Récapitulatif des projets", title_style),
        Paragraph(f"Export du {now.strftime('%d/%m/%Y à %H:%M')}", meta_style),
    ]
    top_data.append(title_block)
    top = Table([top_data], colWidths=[42 * mm, doc.width - 42 * mm], hAlign="LEFT")
    top.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(top)
    story.append(Spacer(1, 3 * mm))

    active_filters = _filter_summary(filters)
    if active_filters:
        filter_cells = []
        for label, value in active_filters:
            filter_cells.append(
                [
                    Paragraph(escape(label), filter_label_style),
                    Paragraph(escape(value), meta_style),
                ]
            )
        filters_table = Table(filter_cells, colWidths=[28 * mm, 78 * mm], hAlign="LEFT")
        filters_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F7FC")),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E3E3F2")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#ECECF6")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(filters_table)
        story.append(Spacer(1, 3 * mm))
    else:
        story.append(Paragraph("Filtres : aucun", meta_style))
        story.append(Spacer(1, 2 * mm))

    total_budget, total_hours = projects_totals(projects)
    summary = Table(
        [
            [
                Paragraph("PROJETS AFFICHÉS", header_style),
                Paragraph("BUDGET TOTAL", header_style),
                Paragraph("HEURES TOTALES", header_style),
            ],
            [
                Paragraph(str(len(projects)), cell_bold_style),
                Paragraph(_amount(total_budget), cell_bold_style),
                Paragraph(_hours(total_hours), cell_bold_style),
            ],
        ],
        colWidths=[45 * mm, 45 * mm, 45 * mm],
        hAlign="LEFT",
    )
    summary.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F1F0FE")),
                ("BACKGROUND", (0, 1), (-1, 1), colors.white),
                ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#DAD8F7")),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#E8E7F7")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(summary)
    story.append(Spacer(1, 2 * mm))

    if not projects:
        story.append(
            Paragraph(
                "Aucun projet ne correspond aux filtres actuellement appliqués au Tableau.",
                cell_style,
            )
        )
    else:
        header = [
            Paragraph("N°", header_style),
            Paragraph("Projet", header_style),
            Paragraph("Client", header_style),
            Paragraph("Structure", header_style),
            Paragraph("Statut", header_style),
            Paragraph("Budget", header_right_style),
            Paragraph("Heures", header_right_style),
        ]
        col_widths = [22 * mm, 63 * mm, 43 * mm, 31 * mm, 36 * mm, 30 * mm, 24 * mm]

        for status, status_projects in _status_projects(
            data, projects, filters.get("status_filter")
        ):
            status_budget, status_hours = projects_totals(status_projects)
            status_color = _safe_hex(
                data.get("status_colors", {}).get(status),
                PRIMARY,
            )
            story.append(
                Paragraph(
                    f"{escape(_text(status))} - {len(status_projects)} projet"
                    f"{'s' if len(status_projects) != 1 else ''} - "
                    f"{escape(_amount(status_budget))} - {escape(_hours(status_hours))}",
                    status_style,
                )
            )

            table_rows = [header]
            for project in status_projects:
                budget, hours = project_totals(project)
                table_rows.append(
                    [
                        _paragraph(project.get("project_number"), cell_bold_style),
                        _paragraph(project.get("name"), cell_bold_style),
                        _paragraph(project.get("client"), cell_style),
                        _paragraph(project.get("discipline"), cell_style),
                        _paragraph(project.get("status"), cell_style),
                        Paragraph(escape(_amount(budget)), cell_right_style),
                        Paragraph(escape(_hours(hours)), cell_right_style),
                    ]
                )

            table_rows.append(
                [
                    "",
                    Paragraph("TOTAL", cell_bold_style),
                    Paragraph(
                        f"{len(status_projects)} projet{'s' if len(status_projects) != 1 else ''}",
                        cell_style,
                    ),
                    "",
                    "",
                    Paragraph(escape(_amount(status_budget)), cell_right_bold_style),
                    Paragraph(escape(_hours(status_hours)), cell_right_bold_style),
                ]
            )

            table = LongTable(
                table_rows,
                colWidths=col_widths,
                repeatRows=1,
                hAlign="LEFT",
            )
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F4F3FD")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#5D6288")),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.8, status_color),
                        ("GRID", (0, 1), (-1, -2), 0.25, colors.HexColor("#EAEAF3")),
                        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#FAFAFD")),
                        ("LINEABOVE", (0, -1), (-1, -1), 0.6, colors.HexColor("#D9D8E9")),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 3.2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3.2),
                    ]
                )
            )
            story.append(table)

    doc.build(story, onFirstPage=_page_header_footer, onLaterPages=_page_header_footer)
    return buffer.getvalue()
