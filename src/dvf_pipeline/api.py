"""API des indicateurs immobiliers, lue par l'interface React.

Elle lit les tables « marts » produites par dbt, dans DuckDB (local) ou PostgreSQL (Docker).

Lancer en local :
    uv run uvicorn dvf_pipeline.api:app --reload        # documentation : http://127.0.0.1:8000/docs
"""
import re
from decimal import Decimal
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from dvf_pipeline import config

DEPARTEMENTS = {
    "13": "Bouches-du-Rhône",
    "33": "Gironde",
    "34": "Hérault",
    "69": "Rhône",
    "75": "Paris",
}
TypeLocal = Literal["Appartement", "Maison"]


def _clean(row: dict) -> dict:
    # Les décimaux (type NUMERIC) seraient sérialisés en texte dans le JSON : on les convertit en nombres
    return {k: float(v) if isinstance(v, Decimal) else v for k, v in row.items()}


def query(sql: str, params: dict | None = None) -> list[dict]:
    """Exécute une requête paramétrée (« :nom ») sur l'entrepôt configuré et renvoie des dictionnaires."""
    params = params or {}
    if config.TARGET == "postgres":
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(config.POSTGRES_DSN, row_factory=dict_row) as con:
            rows = con.execute(re.sub(r":(\w+)", r"%(\1)s", sql), params).fetchall()
    else:
        import duckdb

        with duckdb.connect(str(config.DUCKDB_PATH), read_only=True) as con:
            cur = con.execute(re.sub(r":(\w+)", r"$\1", sql), params)
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    return [_clean(r) for r in rows]


app = FastAPI(
    title="API immobilier DVF",
    description="Prix au m² des logements par commune et par mois, calculés par le pipeline DVF.",
    version="1.0.0",
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])


@app.get("/api/health")
def health() -> dict:
    n = query("select count(*) as n from marts.fct_ventes_logements")[0]["n"]
    return {"statut": "ok", "entrepot": config.TARGET, "ventes": n}


@app.get("/api/meta")
def meta() -> dict:
    """Valeurs disponibles pour les filtres de l'interface."""
    annees = [r["annee"] for r in query("select distinct annee from marts.agg_prix_m2_commune_annee order by annee")]
    deps = [r["code_departement"] for r in query(
        "select distinct code_departement from marts.agg_prix_m2_commune_annee order by 1")]
    return {
        "annees": annees,
        "departements": [{"code": d, "nom": DEPARTEMENTS.get(d, d)} for d in deps],
        "types_local": ["Appartement", "Maison"],
    }


@app.get("/api/kpis")
def kpis(departement: str, type_local: TypeLocal, annee: int) -> dict:
    """Chiffres clés d'un département pour une année, et évolution par rapport à l'année précédente."""
    rows = query(
        """
        select annee,
               count(*)                                                as nb_ventes,
               percentile_cont(0.5) within group (order by prix_m2)    as prix_m2_median,
               percentile_cont(0.5) within group (order by prix)       as prix_median,
               percentile_cont(0.5) within group (order by surface)    as surface_mediane
        from marts.fct_ventes_logements
        where code_departement = :dep and type_local = :type and annee in (:annee, :annee - 1)
        group by annee
        """,
        {"dep": departement, "type": type_local, "annee": annee},
    )
    by_year = {r["annee"]: r for r in rows}
    if annee not in by_year:
        raise HTTPException(404, "Aucune vente pour ces filtres")
    current, previous = by_year[annee], by_year.get(annee - 1)
    evolution = None
    if previous:
        evolution = current["prix_m2_median"] / previous["prix_m2_median"] - 1
    return {**current, "evolution_prix_m2_1an": evolution}


@app.get("/api/communes")
def communes(
    departement: str,
    type_local: TypeLocal,
    annee: int,
    min_ventes: int = Query(10, ge=1, description="nombre minimal de ventes pour qu'un prix soit affiché"),
) -> list[dict]:
    """Prix au m² médian de chaque commune (avec sa position), et son évolution sur un an."""
    return query(
        """
        select c.code_commune, c.nom_commune, d.latitude, d.longitude,
               c.nb_ventes, c.prix_m2_median, c.prix_m2_q1, c.prix_m2_q3, c.prix_median, c.surface_mediane,
               c.prix_m2_median / nullif(p.prix_m2_median, 0) - 1 as evolution_1an
        from marts.agg_prix_m2_commune_annee c
        join marts.dim_communes d using (code_commune)
        left join marts.agg_prix_m2_commune_annee p
               on p.code_commune = c.code_commune and p.type_local = c.type_local
              and p.annee = c.annee - 1 and p.nb_ventes >= :min_ventes
        where c.code_departement = :dep and c.type_local = :type and c.annee = :annee
          and c.nb_ventes >= :min_ventes
        order by c.prix_m2_median desc
        """,
        {"dep": departement, "type": type_local, "annee": annee, "min_ventes": min_ventes},
    )


@app.get("/api/evolution")
def evolution(departement: str, type_local: TypeLocal) -> list[dict]:
    """Prix au m² médian mois par mois pour un département."""
    return query(
        """
        select mois, nb_ventes, prix_m2_median
        from marts.agg_prix_m2_departement_mois
        where code_departement = :dep and type_local = :type
        order by mois
        """,
        {"dep": departement, "type": type_local},
    )


@app.get("/api/communes/{code_commune}")
def commune(code_commune: str) -> dict:
    """Historique annuel d'une commune, par type de logement."""
    rows = query(
        """
        select annee, type_local, nb_ventes, prix_m2_median, prix_median, surface_mediane
        from marts.agg_prix_m2_commune_annee
        where code_commune = :code
        order by type_local, annee
        """,
        {"code": code_commune},
    )
    info = query("select * from marts.dim_communes where code_commune = :code", {"code": code_commune})
    if not info:
        raise HTTPException(404, "Commune inconnue")
    return {**info[0], "historique": rows}
