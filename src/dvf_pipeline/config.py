"""Paramètres du pipeline (modifiables par variables d'environnement)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DUCKDB_PATH = Path(os.environ.get("DVF_DUCKDB_PATH", ROOT / "data" / "warehouse" / "dvf.duckdb"))

# Source : « Demandes de valeurs foncières géolocalisées » (Etalab), un fichier par année et département
DVF_URL = "https://files.data.gouv.fr/geo-dvf/latest/csv/{year}/departements/{departement}.csv.gz"
YEARS = [int(y) for y in os.environ.get("DVF_YEARS", "2021,2022,2023,2024,2025").split(",")]
# Par défaut : Hérault (Montpellier), Paris, Rhône (Lyon), Gironde (Bordeaux), Bouches-du-Rhône (Marseille)
DEPARTEMENTS = os.environ.get("DVF_DEPARTEMENTS", "34,75,69,33,13").split(",")

# Entrepôt cible : « duckdb » (local, sans installation) ou « postgres » (Docker)
TARGET = os.environ.get("DVF_TARGET", "duckdb")
POSTGRES_DSN = os.environ.get(
    "DVF_POSTGRES_DSN", "postgresql://dvf:dvf@localhost:5432/dvf"
)

RAW_SCHEMA = "raw"
RAW_TABLE = "dvf_mutations"
