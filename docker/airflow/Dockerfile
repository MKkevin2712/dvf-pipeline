# Image Airflow du projet : Airflow 3 + dbt (dans un environnement séparé pour éviter les conflits de versions)
FROM apache/airflow:3.1.0-python3.12

# Ingestion : client PostgreSQL pour le chargement en COPY
RUN pip install --no-cache-dir "psycopg[binary]==3.2.*"

# dbt dans son propre environnement virtuel, appelé par le DAG
RUN python -m venv /opt/airflow/dbt-venv \
    && /opt/airflow/dbt-venv/bin/pip install --no-cache-dir "dbt-core==1.10.*" "dbt-postgres==1.9.*"
