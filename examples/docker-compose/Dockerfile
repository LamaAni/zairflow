
# Starting from the zairflow image.
FROM lamaani/zairflow:latest

USER root

# installing some more root packges
RUN apt-get install -yqq\
    jq

USER airflow
# We are currently using the airflow user. So pip should install to user.
RUN yes | pip install --user \
    apache-airflow[slack] \
    bcrypt\
    flask-bcrypt\
    boto3\
    awscli\
    ec2instanceconnectcli


COPY ./dags /app/dags
COPY ./plugins /app/plugins
COPY ./scripts/init_connections /scripts/init_connections

# ENV ZAIRFLOW_DAGS_SUBFOLDER="dags" # The same as the line below
ENV AIRFLOW__CORE__DAGS_FOLDER=/app/dags
# Adding a plugins folder
ENV AIRFLOW__CORE__PLUGINS_FOLDER=/app/plugins
