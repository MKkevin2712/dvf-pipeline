"""Construit le dataset Kaggle (colonnes en anglais) à partir des tables « marts » du pipeline.

Usage (depuis la racine du projet, après ingestion et dbt build) :
    uv run python kaggle/build_dataset.py
    uv run kaggle datasets create -p kaggle/dataset          # première publication
    uv run kaggle datasets version -p kaggle/dataset -m "…"  # mises à jour
"""
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE = ROOT / "data" / "warehouse" / "dvf.duckdb"
OUT = Path(__file__).parent / "dataset"

PROPERTY_TYPE = "CASE type_local WHEN 'Appartement' THEN 'Apartment' ELSE 'House' END"

EXPORTS = {
    "home_sales.parquet": f"""
        SELECT id_mutation AS sale_id, date_mutation AS sale_date, annee AS year, mois AS month,
               est_neuf AS is_new_build, code_departement AS department_code, code_commune AS commune_code,
               nom_commune AS commune_name, code_postal AS postal_code, {PROPERTY_TYPE} AS property_type,
               surface AS living_area_m2, nombre_pieces AS rooms, nb_dependances AS outbuildings,
               surface_terrain AS land_area_m2, prix AS price_eur, prix_m2 AS price_per_m2_eur,
               longitude, latitude
        FROM marts.fct_ventes_logements
        ORDER BY sale_date, sale_id
    """,
    "price_per_m2_by_commune_year.csv": f"""
        SELECT annee AS year, code_departement AS department_code, code_commune AS commune_code,
               nom_commune AS commune_name, {PROPERTY_TYPE} AS property_type, nb_ventes AS sales,
               round(prix_m2_median) AS median_price_per_m2, round(prix_m2_q1) AS q1_price_per_m2,
               round(prix_m2_q3) AS q3_price_per_m2, round(prix_median) AS median_price,
               surface_mediane AS median_living_area_m2
        FROM marts.agg_prix_m2_commune_annee
        ORDER BY year, commune_code, property_type
    """,
    "price_per_m2_by_department_month.csv": f"""
        SELECT mois AS month, code_departement AS department_code, {PROPERTY_TYPE} AS property_type,
               nb_ventes AS sales, round(prix_m2_median) AS median_price_per_m2
        FROM marts.agg_prix_m2_departement_mois
        ORDER BY month, department_code, property_type
    """,
    "communes.csv": """
        SELECT code_commune AS commune_code, nom_commune AS commune_name, code_departement AS department_code,
               round(longitude, 5) AS longitude, round(latitude, 5) AS latitude, nb_ventes_total AS total_sales
        FROM marts.dim_communes
        ORDER BY commune_code
    """,
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(WAREHOUSE), read_only=True) as con:
        for name, query in EXPORTS.items():
            path = (OUT / name).as_posix()
            fmt = "(FORMAT parquet, COMPRESSION zstd)" if name.endswith(".parquet") else "(HEADER, DELIMITER ',')"
            con.execute(f"COPY ({query}) TO '{path}' {fmt}")
            rows = con.execute(f"SELECT count(*) FROM ({query})").fetchone()[0]
            print(f"{name:<40} {rows:>9,} lignes  {(OUT / name).stat().st_size / 1e6:6.1f} Mo")


if __name__ == "__main__":
    main()
