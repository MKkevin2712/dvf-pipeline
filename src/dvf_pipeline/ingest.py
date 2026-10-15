"""Ingestion : téléchargement des fichiers DVF et chargement brut dans l'entrepôt.

La couche « raw » garde les données telles quelles (toutes les colonnes en texte) : le typage,
le nettoyage et les règles métier sont faits ensuite par dbt. Le chargement est idempotent :
recharger un fichier remplace ses lignes au lieu de les dupliquer.

Usage :
    uv run python -m dvf_pipeline.ingest                       # années et départements par défaut
    uv run python -m dvf_pipeline.ingest --years 2024 --departements 34 75
    uv run python -m dvf_pipeline.ingest --target postgres     # vers PostgreSQL (Docker)
"""
import argparse
import gzip
import io
from datetime import UTC, datetime
from pathlib import Path

import httpx

from dvf_pipeline import config

TECH_COLUMNS = ["_source_file", "_loaded_at"]


def download(year: int, departement: str, force: bool = False) -> Path:
    """Télécharge un fichier (mis en cache dans data/raw) et renvoie son chemin."""
    path = config.DATA_RAW / f"dvf_{year}_{departement}.csv.gz"
    if path.exists() and not force:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    url = config.DVF_URL.format(year=year, departement=departement)
    tmp = path.with_suffix(".part")
    with httpx.stream("GET", url, follow_redirects=True, timeout=120) as r:
        r.raise_for_status()
        with tmp.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    tmp.replace(path)
    return path


def read_header(path: Path) -> list[str]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return f.readline().strip().split(",")


# ---------------------------------------------------------------- DuckDB

def load_duckdb(paths: list[Path], db_path: Path = config.DUCKDB_PATH) -> dict[str, int]:
    import duckdb

    db_path.parent.mkdir(parents=True, exist_ok=True)
    table = f"{config.RAW_SCHEMA}.{config.RAW_TABLE}"
    counts = {}
    with duckdb.connect(str(db_path)) as con:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {config.RAW_SCHEMA}")
        for path in paths:
            select = f"""
                SELECT *, '{path.name}' AS _source_file, now() AS _loaded_at
                FROM read_csv('{path.as_posix()}', header = true, all_varchar = true)
            """
            if not con.execute(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema = ? AND table_name = ?",
                [config.RAW_SCHEMA, config.RAW_TABLE],
            ).fetchone()[0]:
                con.execute(f"CREATE TABLE {table} AS {select} LIMIT 0")
            con.execute(f"DELETE FROM {table} WHERE _source_file = ?", [path.name])
            con.execute(f"INSERT INTO {table} BY NAME {select}")
            counts[path.name] = con.execute(
                f"SELECT count(*) FROM {table} WHERE _source_file = ?", [path.name]
            ).fetchone()[0]
    return counts


# ---------------------------------------------------------------- PostgreSQL

def load_postgres(paths: list[Path], dsn: str = config.POSTGRES_DSN) -> dict[str, int]:
    import psycopg

    table = f"{config.RAW_SCHEMA}.{config.RAW_TABLE}"
    counts = {}
    with psycopg.connect(dsn) as con:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {config.RAW_SCHEMA}")
        columns = read_header(paths[0])
        ddl = ", ".join(f'"{c}" text' for c in columns)
        con.execute(f"CREATE TABLE IF NOT EXISTS {table} ({ddl}, _source_file text, _loaded_at timestamptz)")
        for path in paths:
            con.execute(f"DELETE FROM {table} WHERE _source_file = %s", [path.name])
            cols = ", ".join(f'"{c}"' for c in read_header(path))
            with gzip.open(path, "rb") as raw:
                data = io.BytesIO(raw.read())
            with con.cursor().copy(f"COPY {table} ({cols}) FROM STDIN WITH (FORMAT csv, HEADER true)") as copy:
                while chunk := data.read(1 << 20):
                    copy.write(chunk)
            con.execute(
                f"UPDATE {table} SET _source_file = %s, _loaded_at = %s WHERE _source_file IS NULL",
                [path.name, datetime.now(UTC)],
            )
            counts[path.name] = con.execute(
                f"SELECT count(*) FROM {table} WHERE _source_file = %s", [path.name]
            ).fetchone()[0]
        con.commit()
    return counts


def run(years=None, departements=None, target=None, force=False) -> dict[str, int]:
    years = years or config.YEARS
    departements = departements or config.DEPARTEMENTS
    target = target or config.TARGET
    paths = [download(y, d, force) for y in years for d in departements]
    counts = load_duckdb(paths) if target == "duckdb" else load_postgres(paths)
    for name, n in counts.items():
        print(f"{name:<24} {n:>9,} lignes")
    print(f"Total : {sum(counts.values()):,} lignes chargées dans {target}")
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--years", nargs="+", type=int)
    parser.add_argument("--departements", nargs="+")
    parser.add_argument("--target", choices=["duckdb", "postgres"])
    parser.add_argument("--force", action="store_true", help="retélécharger les fichiers déjà présents")
    args = parser.parse_args()
    run(args.years, args.departements, args.target, args.force)


if __name__ == "__main__":
    main()
