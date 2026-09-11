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

# Ligne principale : la structure et le statut sont portés uniquement par le projet.
PROJECT_ROW_WIDTHS = [0.46, 0.38, 0.82, 2.65, 1.45, 1.10, 1.12, 0.95, 0.90]
PROJECT_ROW_LABELS = ["Fact.", "", "N°", "Projet", "Client", "Structure", "Statut", "Budget", "Heures"]

# Sous-projet : Phase et Type étant le même concept, on ne garde que Type.
SUBPROJECT_ROW_WIDTHS = [0.46, 0.38, 1.35, 1.65, 1.05, 0.95, 0.90]
SUBPROJECT_ROW_LABELS = ["Fact.", "", "Type", "Collaborateur", "Échéance", "Budget", "Heures"]

# Tâche : pas de statut, celui-ci est porté par le projet parent.
TASK_ROW_WIDTHS = [0.46, 0.38, 2.85, 1.65, 1.05, 0.95, 0.90]
TASK_ROW_LABELS = ["Fact.", "", "Tâche", "Collaborateur", "Échéance", "Budget", "Heures"]

DATA_CACHE_TTL_SECONDS = 5
