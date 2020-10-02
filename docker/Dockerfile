
FROM ubuntu:20.10
ENV DEBIAN_FRONTEND="noninteractive"
#########################################
# Prepare environment

USER root
WORKDIR /image_install

# core install command
ARG APT_GET_INSTALL="apt-get install -yqq --no-install-recommends "
ARG APT_GET_DEPS=""

# prepare ubuntu version.
RUN apt-get update -yqq && apt-get upgrade -yqq 
# Prepare environment and core tools
# &&\
RUN ${APT_GET_INSTALL}\
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
# &&\
# pip3 install --upgrade pip

# Configure for airflow installation.
ENV SLUGIFY_USES_TEXT_UNIDECODE="yes"
ARG AIRFLOW_CORE_DEPS="crypto,celery,postgres,ssh,kubernetes"
ARG AIRFLOW_DEPS="crypto,celery,postgres,ssh,kubernetes"
ARG PYTHON_DEPS=""

ARG AIRFLOW_VERSION="1.10.12"
ARG KUBE_JOB_OPERATOR_VERSION='1.0.9'

# Copy install dependencies
COPY ./db_logger ./db_logger
COPY ./docker/requirements_pip.txt .

# Install python requirements and airflow.
ARG PIP_INSTALL_COMMAND="pip3 install --no-cache-dir"
RUN ${PIP_INSTALL_COMMAND} \
   -r ./requirements_pip.txt \
   ./db_logger\
   ${PYTHON_DEPS}\
   airflow-kubernetes-job-operator==${KUBE_JOB_OPERATOR_VERSION}\
   apache-airflow[${AIRFLOW_CORE_DEPS},${AIRFLOW_DEPS}]==${AIRFLOW_VERSION}

# Set this parameter to not "true" so it would create a non sudo user and cleanup more stuff.
ARG DEBUG_MODE="true"
ARG GIT_AUTOSYNC_BRANCH="master"

# Global scripts and paths.
ENV\
   SCRIPTS_PATH=/scripts \
   PATH="/scripts:${PATH}:/home/airflow/.local/bin"\
   GIT_AUTOSYNC_BRANCH=${GIT_AUTOSYNC_BRANCH}

COPY ./scripts /scripts
RUN chmod -R +x /scripts && bash /scripts/image/install.sh


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

# airflow user
RUN groupadd airflow &&\
   useradd -s /bin/bash -m -g airflow airflow &&\
   bash -c "if [ "$DEBUG_MODE" == "true" ]; then usermod -a -G sudo airflow; fi" &&\
   # set permissions
   chown -R airflow /airflow /app && chmod -R 0777 /airflow

# switch
USER airflow

# copy the config.
COPY ./docker/airflow.cfg /airflow/airflow.cfg

# airflow core config envs.
ENV FERNET_KEY="${FERNET_KEY}"

ENV PGHOST=localhost
ENV PGUSER=airflow

ENV AIRFLOW_HOME=/airflow
ENV AIRFLOW_CONFIG=/airflow/airflow.cfg
ENV AIRFLOW__CORE__DAGS_FOLDER=/app/dags
ENV AIRFLOW__CORE__PLUGINS_FOLDER=/app/plugins

EXPOSE 8080 5555 8793
CMD ["/scripts/image/entrypoint.sh"]

ARG ZAIRFLOW_VERSION="debug"
ENV ZAIRFLOW_VERSION=${ZAIRFLOW_VERSION}
