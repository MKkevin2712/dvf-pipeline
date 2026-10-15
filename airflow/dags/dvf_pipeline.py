"""DAG mensuel du pipeline DVF : ingestion → contrôle de volume → transformations et tests dbt."""
from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag, task

PROJECT = "/opt/airflow/project"
MIN_ROWS = 100_000   # en dessous, la source est probablement incomplète : on n'écrase pas les tables


@dag(
    schedule="@monthly",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,          # jamais deux chargements en même temps sur les mêmes tables
    tags=["dvf", "immobilier"],
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    doc_md=__doc__,
)
def dvf_pipeline():
    @task
    def ingestion() -> int:
        """Télécharge les fichiers DVF et les charge dans raw.dvf_mutations (PostgreSQL)."""
        from dvf_pipeline import ingest

        counts = ingest.run(target="postgres")
        return sum(counts.values())

    @task
    def controle_volume(nb_lignes: int) -> None:
        """Garde-fou : arrête le pipeline si l'ingestion a ramené trop peu de lignes."""
        if nb_lignes < MIN_ROWS:
            raise ValueError(f"Seulement {nb_lignes} lignes ingérées (minimum attendu : {MIN_ROWS})")

    dbt_build = BashOperator(
        task_id="dbt_build",
        doc_md="Construit les modèles staging, intermediate et marts, et lance les tests de qualité.",
        bash_command=f"cd {PROJECT}/dbt && /opt/airflow/dbt-venv/bin/dbt build --profiles-dir . --target postgres",
        append_env=True,
    )

    controle_volume(ingestion()) >> dbt_build


dvf_pipeline()
