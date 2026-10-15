"""Tests de l'API sur un petit entrepôt DuckDB fictif (mêmes tables que les marts dbt)."""
import duckdb
import pytest
from fastapi.testclient import TestClient

from dvf_pipeline import api, config


@pytest.fixture
def client(tmp_path, monkeypatch):
    db = tmp_path / "entrepot.duckdb"   # pas « marts.duckdb » : le nom du fichier entrerait en conflit avec le schéma
    with duckdb.connect(str(db)) as con:
        con.execute("CREATE SCHEMA marts")
        con.execute("""
            CREATE TABLE marts.fct_ventes_logements AS SELECT * FROM (VALUES
                ('m1', 2024, '34', '34172', 'Appartement', 200000.0, 50.0, 4000.0),
                ('m2', 2024, '34', '34172', 'Appartement', 120000.0, 40.0, 3000.0),
                ('m3', 2025, '34', '34172', 'Appartement', 220000.0, 50.0, 4400.0),
                ('m4', 2025, '34', '34172', 'Appartement', 132000.0, 40.0, 3300.0)
            ) t(id_mutation, annee, code_departement, code_commune, type_local, prix, surface, prix_m2)
        """)
        con.execute("""
            CREATE TABLE marts.agg_prix_m2_commune_annee AS SELECT * FROM (VALUES
                (2024, '34', '34172', 'Montpellier', 'Appartement', 20, 3500.0, 3000.0, 4000.0, 160000.0, 45.0),
                (2025, '34', '34172', 'Montpellier', 'Appartement', 20, 3850.0, 3300.0, 4400.0, 176000.0, 45.0),
                (2025, '34', '34301', 'Sète',        'Appartement',  3, 3000.0, 2800.0, 3200.0, 150000.0, 50.0)
            ) t(annee, code_departement, code_commune, nom_commune, type_local, nb_ventes,
                prix_m2_median, prix_m2_q1, prix_m2_q3, prix_median, surface_mediane)
        """)
        con.execute("""
            CREATE TABLE marts.dim_communes AS SELECT * FROM (VALUES
                ('34172', 'Montpellier', '34', 3.87, 43.61, 40),
                ('34301', 'Sète', '34', 3.69, 43.40, 3)
            ) t(code_commune, nom_commune, code_departement, longitude, latitude, nb_ventes_total)
        """)
        con.execute("""
            CREATE TABLE marts.agg_prix_m2_departement_mois AS SELECT * FROM (VALUES
                (DATE '2025-01-01', '34', 'Appartement', 10, 3800.0),
                (DATE '2025-02-01', '34', 'Appartement', 12, 3900.0)
            ) t(mois, code_departement, type_local, nb_ventes, prix_m2_median)
        """)
    monkeypatch.setattr(config, "TARGET", "duckdb")
    monkeypatch.setattr(config, "DUCKDB_PATH", db)
    return TestClient(api.app)


PARAMS = {"departement": "34", "type_local": "Appartement", "annee": 2025}


def test_health(client):
    assert client.get("/api/health").json() == {"statut": "ok", "entrepot": "duckdb", "ventes": 4}


def test_meta_lists_filters(client):
    meta = client.get("/api/meta").json()
    assert meta["annees"] == [2024, 2025]
    assert meta["departements"] == [{"code": "34", "nom": "Hérault"}]


def test_kpis_compute_median_and_yearly_change(client):
    k = client.get("/api/kpis", params=PARAMS).json()
    assert k["nb_ventes"] == 2
    assert k["prix_m2_median"] == pytest.approx(3850)
    assert k["evolution_prix_m2_1an"] == pytest.approx(3850 / 3500 - 1)


def test_communes_filter_small_samples_and_join_coordinates(client):
    rows = client.get("/api/communes", params=PARAMS).json()
    assert [r["nom_commune"] for r in rows] == ["Montpellier"]        # Sète : 3 ventes < 10
    assert rows[0]["latitude"] == pytest.approx(43.61)
    assert rows[0]["evolution_1an"] == pytest.approx(0.10)
    assert len(client.get("/api/communes", params={**PARAMS, "min_ventes": 1}).json()) == 2


def test_evolution_is_sorted_by_month(client):
    series = client.get("/api/evolution", params={"departement": "34", "type_local": "Appartement"}).json()
    assert [s["mois"] for s in series] == ["2025-01-01", "2025-02-01"]


def test_commune_detail_and_errors(client):
    detail = client.get("/api/communes/34172").json()
    assert detail["nom_commune"] == "Montpellier" and len(detail["historique"]) == 2
    assert client.get("/api/communes/99999").status_code == 404
    assert client.get("/api/kpis", params={**PARAMS, "annee": 2010}).status_code == 404
    assert client.get("/api/kpis", params={**PARAMS, "type_local": "Château"}).status_code == 422
