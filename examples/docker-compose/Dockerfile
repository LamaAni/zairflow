
# Starting from the zairflow image.
FROM lamaani/zairflow:latest

USER root

# You can install other stuff here.

################
# Back to airflow
# Application will be in dags.

USER airflow

COPY ./dags /app/dags
COPY ./plugins /app/plugins
COPY ./scripts/init_connections /scripts/init_connections

# Defining airflow folders
ENV AIRFLOW__CORE__DAGS_FOLDER=/app/dags
ENV AIRFLOW__CORE__PLUGINS_FOLDER=/app/plugins
