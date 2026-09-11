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

ROW_WIDTHS = [0.38, 0.78, 2.85, 0.95, 1.55, 1.15, 1.0, 0.95, 0.95, 0.72]
ROW_LABELS = ["", "N°", "Projet", "Type", "Collaborateurs", "Statut", "Échéance", "Budget", "Heures", "Tâches"]
TOTAL_WIDTHS = [0.38, 0.78, 2.85, 0.95, 1.55, 1.15, 1.0, 0.95, 0.95, 0.72]

# Petit cache réseau : évite une requête Supabase à chaque clic purement visuel.
# Les écritures invalident immédiatement ce cache.
DATA_CACHE_TTL_SECONDS = 5
