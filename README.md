# Pipeline de données immobilières (DVF)

> 🚧 Projet en cours (octobre 2026)

Pipeline de data engineering sur les **Demandes de valeurs foncières** (DVF) : toutes les ventes immobilières
publiées par l'État. Objectif : produire des indicateurs fiables de **prix au m²** par commune et par mois.

## Architecture

```
data.gouv.fr ──► ingestion Python ──► raw (texte brut) ──► dbt : staging ► intermediate ► marts ──► dashboard
                  (idempotente)        DuckDB ou PostgreSQL       (tests de qualité)
                                           orchestré par Airflow (Docker)
```

Le même projet dbt tourne sur **DuckDB** (local, CI) et **PostgreSQL** (Docker).

## Les pièges des données DVF, et leur traitement

| Piège | Conséquence si on l'ignore | Traitement (dbt) |
|---|---|---|
| Une vente = plusieurs lignes (logement, caves, parkings, parcelles), **prix répété sur chaque ligne** | prix multipliés | regroupement par mutation, prix pris une seule fois |
| 7 % des ventes portent sur **plusieurs logements** | prix au m² faux | exclusion de ces ventes |
| Parcelles situées dans **deux communes** | vente attribuée à la mauvaise commune | localisation prise sur la ligne du logement |
| Prix au m² aberrants (vente à 1 €, lots de parkings…) | moyennes faussées | bornes de plausibilité (500–30 000 €/m²) et médiane |

Le troisième piège a été détecté par un **test dbt** (unicité commune × année × type).

## Lancer le projet

```bash
uv sync
uv run python -m dvf_pipeline.ingest          # télécharge et charge 5 ans × 5 départements (≈ 2,3 M lignes)
cd dbt && uv run dbt build --profiles-dir .   # transformations + 25 tests
uv run pytest                                 # tests de l'ingestion
```

## Plan

- [x] Ingestion idempotente (DuckDB et PostgreSQL)
- [x] Modèles dbt staging / intermediate / marts et tests de qualité
- [ ] Docker Compose : PostgreSQL + Airflow
- [ ] DAG Airflow : ingestion → dbt build
- [ ] Dashboard (carte et évolution des prix)
- [ ] CI GitHub Actions (dbt build sur DuckDB)

## Auteur

Kevin Moukam Nkameni — [github.com/MKkevin2712](https://github.com/MKkevin2712)
