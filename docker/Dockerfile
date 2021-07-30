
FROM ubuntu:20.10
ENV DEBIAN_FRONTEND="noninteractive"
#########################################
# Prepare environment

USER root
WORKDIR /image_install

# core install command
ARG APT_GET_INSTALL="apt-get install -yq --no-install-recommends"
ARG APT_GET_DEPS=""

# prepare ubuntu version.
RUN apt-get update -yqq && apt-get upgrade -yqq \
   # Prepare environment and core tools
   &&\
   ${APT_GET_INSTALL}\
   bash\
   apt-utils\
   locales\
   apt-transport-https\
   gnupg2\
   curl\
   ca-certificates\
   &&\
   curl -fsSL "https://download.docker.com/linux/ubuntu/gpg" | apt-key add - &&\
   curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - &&\
   echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | tee -a /etc/apt/sources.list.d/kubernetes.list &&\
   apt-get update\
   # set the local
   &&\
   sed -i 's/^# en_US.UTF-8 UTF-8$/en_US.UTF-8 UTF-8/g' /etc/locale.gen &&\
   locale-gen && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
   # Install packages
   &&\
   ${APT_GET_INSTALL}\
   ${APT_GET_DEPS}\
   # tools
   git\
   sudo\
   netcat\
   libssl-dev\
   redis-tools\
   openssh-client\
   build-essential\
   libmysqlclient-dev\
   libsasl2-dev\
   kubectl\
   # python + binary packages
   python3.8 python3.8-dev python3-pip\
   python3-setuptools\
   postgresql-client\
   python3-psycopg2\
   python3-pandas\
   python3-nacl\
   libffi-dev\
   libpq-dev\
   # Cleanup
   &&\
   apt-get clean

# Configure for airflow installation.
ARG AIRFLOW_CORE_DEPS="crypto,celery,postgres,ssh,kubernetes"
ARG AIRFLOW_DEPS="crypto,celery,postgres,ssh,kubernetes"
ARG PYTHON_DEPS=""
ARG AIRFLOW_VERSION="2.1.2"
ARG KUBE_JOB_OPERATOR_VERSION='2.0.0'
ARG AIRFLOW_DB_LOGGER_VERSION='2.0.1'

# Copy install dependencies
COPY ./docker/requirements.txt .

# Install python requirements and airflow.
ENV SLUGIFY_USES_TEXT_UNIDECODE="yes"
ARG PIP_INSTALL_COMMAND="pip3 install --no-cache-dir"
RUN \
   curl -fsSL https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-3.8.txt > ./constraints.txt\
   &&\
   ${PIP_INSTALL_COMMAND} \
   -r ./requirements.txt \
   -c ./constraints.txt \
   ${PYTHON_DEPS}\
   airflow-db-logger==${AIRFLOW_DB_LOGGER_VERSION}\
   airflow-kubernetes-job-operator==${KUBE_JOB_OPERATOR_VERSION}\
   apache-airflow[${AIRFLOW_CORE_DEPS},${AIRFLOW_DEPS}]==${AIRFLOW_VERSION}

ARG GIT_AUTOSYNC_VERSION="1.2.6"
ARG GIT_AUTOSYNC_REPO_BRANCH="master"
ARG ZBASH_COMMONS_VERSION="0.1.11"

# Global scripts and paths.
ENV\
   SCRIPTS_PATH=/scripts \
   PATH="/scripts:${PATH}:/home/airflow/.local/bin"\
   GIT_AUTOSYNC_REPO_BRANCH=${GIT_AUTOSYNC_REPO_BRANCH}\
   ZBASH_COMMONS_VERSION=${ZBASH_COMMONS_VERSION}\
   GIT_AUTOSYNC_VERSION="${GIT_AUTOSYNC_VERSION}"\
   ZAIRFLOW_AIRFLOW_COMMAND_PATH="/usr/local/bin/airflow"

COPY ./scripts /scripts
RUN chmod -R +x /scripts && \
   bash /scripts/image/install.sh

###################################
# Work environment
WORKDIR /airflow
WORKDIR /app
ARG FERNET_KEY="not_a_key"

# Create the empty core folders.
WORKDIR /airflow/logs
WORKDIR /app/dags
WORKDIR /app/plugins
WORKDIR /app

ARG ZAIRFLOW_AIRFLOW_IS_ROOT="false"

# airflow user
RUN groupadd airflow &&\
   useradd -s /bin/bash -m -g airflow airflow &&\
   bash -c "if [ "${ZAIRFLOW_AIRFLOW_IS_ROOT}" == "true" ]; then usermod -a -G sudo airflow; fi" \
   &&\
   # set permissions
   chown -R airflow /airflow /app && chmod -R 0777 /airflow

# switch
USER airflow

# copy the config.
COPY --chown=airflow:airflow ./docker/default_webserver_config.py /airflow/webserver_config.py

# Control args
ARG AIRFLOW_STANDALONE_EXECUTOR="SequentialExecutor"
ARG LOG_LEVEL="INFO"

# Environment setup
ENV\
   LOG_LEVEL="${LOG_LEVEL}"\
   FERNET_KEY="${FERNET_KEY}"\
   PGHOST=localhost\
   PGUSER=airflow\
   AIRFLOW_HOME=/airflow \
   AIRFLOW_CONFIG=/airflow/airflow.cfg \
   AIRFLOW__CORE__DAGS_FOLDER=/app/dags \
   AIRFLOW__CORE__PLUGINS_FOLDER=/app/plugins \
   AIRFLOW__LOGGING__LOGGING_CONFIG_CLASS=airflow_db_logger.LOGGING_CONFIG \
   AIRFLOW__WEBSERVER__INSTANCE_NAME=ZAirflow\
   AIRFLOW_STANDALONE_EXECUTOR="${AIRFLOW_STANDALONE_EXECUTOR}"

EXPOSE 8080 5555 8793
CMD ["/scripts/image/entrypoint.sh"]

ARG ZAIRFLOW_VERSION="debug"
ENV\
   PATH="${SCRIPTS_PATH}/image/bin:${PATH}" \ 
   ZAIRFLOW_VERSION=${ZAIRFLOW_VERSION}
