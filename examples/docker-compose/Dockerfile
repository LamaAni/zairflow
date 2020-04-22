
# Starting from the zairflow image.
FROM lamaani/zairflow:latest

# USER root

# You can install other stuff here.

################
# Back to airflow
# Application will be in dags.
USER airflow

COPY --chown=airflow ./dags /app/dags
COPY --chown=airflow ./plugins /app/plugins
COPY --chown=airflow ./scripts/init_connections /app/scripts/init_connections
RUN chmod +x -R /app/scripts

# Defining airflow folders
ENV AIRFLOW__CORE__DAGS_FOLDER=/app/dags
ENV AIRFLOW__CORE__PLUGINS_FOLDER=/app/plugins
