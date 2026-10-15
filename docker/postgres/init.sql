-- Base de métadonnées d'Airflow, séparée de l'entrepôt de données « dvf »
CREATE ROLE airflow WITH LOGIN PASSWORD 'airflow';
CREATE DATABASE airflow OWNER airflow;
