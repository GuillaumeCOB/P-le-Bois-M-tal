from pathlib import Path

PATH = None

PRIMARY = "#3B38F5"
PRIMARY_DARK = "#40338C"
SURFACE = "#F5F4F7"
SURFACE_ALT = "#FFFFFF"
TEXT = "#1F2340"
MUTED = "#70759A"
BORDER = "#D8D9E5"

LOGO_PATH = Path(__file__).parent / "assets" / "logo_builders_verticalsea.png"

DISCIPLINES = ["Bois / Métal", "Béton"]
DISCIPLINE_COLORS = {
    "Bois / Métal": "#005C4D",
    "Béton": "#3B38F5",
}

PROJECT_ROW_WIDTHS = [0.46, 0.38, 0.82, 3.1, 1.65, 1.02, 0.92]
PROJECT_ROW_LABELS = ["Fact.", "", "N°", "Projet", "Client", "Budget", "Heures"]

SUBPROJECT_ROW_WIDTHS = [0.46, 0.38, 1.05, 1.0, 1.55, 1.18, 1.0, 0.95, 0.92]
SUBPROJECT_ROW_LABELS = ["Fact.", "", "Phase", "Type", "Collaborateur", "Statut", "Échéance", "Budget", "Heures"]

TASK_ROW_WIDTHS = [0.46, 0.38, 2.95, 1.55, 1.18, 1.0, 0.95, 0.92]
TASK_ROW_LABELS = ["Fact.", "", "Tâche", "Collaborateur", "Statut", "Échéance", "Budget", "Heures"]

DATA_CACHE_TTL_SECONDS = 5
