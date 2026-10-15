"""Tests de l'ingestion sur un petit fichier DVF fictif (sans téléchargement)."""
import gzip

import duckdb
import pytest

from dvf_pipeline import ingest

HEADER = ("id_mutation,date_mutation,nature_mutation,valeur_fonciere,code_commune,nom_commune,"
          "code_departement,type_local,surface_reelle_bati")
ROWS = [
    "2024-1,2024-01-03,Vente,250000,34172,Montpellier,34,Appartement,50",
    "2024-1,2024-01-03,Vente,250000,34172,Montpellier,34,Dépendance,",
    "2024-2,2024-02-10,Vente,400000,34172,Montpellier,34,Maison,100",
]


@pytest.fixture
def csv_gz(tmp_path):
    path = tmp_path / "dvf_2024_34.csv.gz"
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write("\n".join([HEADER, *ROWS]) + "\n")
    return path


def test_load_duckdb_keeps_raw_text_and_lineage(csv_gz, tmp_path):
    db = tmp_path / "test.duckdb"
    counts = ingest.load_duckdb([csv_gz], db)
    assert counts == {"dvf_2024_34.csv.gz": 3}
    with duckdb.connect(str(db)) as con:
        types = {name: typ for name, typ, *_ in con.execute("DESCRIBE raw.dvf_mutations").fetchall()
                 if not name.startswith("_")}
        assert set(types.values()) == {"VARCHAR"}          # couche brute : tout en texte
        assert con.execute("SELECT DISTINCT _source_file FROM raw.dvf_mutations").fetchall() == [
            ("dvf_2024_34.csv.gz",)
        ]


def test_reloading_a_file_does_not_duplicate_rows(csv_gz, tmp_path):
    db = tmp_path / "test.duckdb"
    ingest.load_duckdb([csv_gz], db)
    ingest.load_duckdb([csv_gz], db)
    with duckdb.connect(str(db)) as con:
        assert con.execute("SELECT count(*) FROM raw.dvf_mutations").fetchone()[0] == 3


def test_header_reader(csv_gz):
    assert ingest.read_header(csv_gz)[:3] == ["id_mutation", "date_mutation", "nature_mutation"]
