
FROM python:3.7.4-slim
USER root
WORKDIR /image_install

# set the terminal type.
ENV TERM linux
ARG DEBIAN_FRONTEND=noninteractive

# prepare ubuntu version.
RUN apt-get update -yqq &&\
   apt-get upgrade -yqq &&\
   apt-get install -yqq --no-install-recommends\
   apt-utils

# prepare enviroment (utf-8, english)
RUN apt-get install -yqq --no-install-recommends locales\
   && sed -i 's/^# en_US.UTF-8 UTF-8$/en_US.UTF-8 UTF-8/g' /etc/locale.gen \
   && locale-gen \
   && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8

# Install core packages
RUN apt-get install -yqq --no-install-recommends\
   # Core tools (for use in image)
   curl\
   git\
   apt-utils\
   build-essential\
   gnupg2\
   # utils
   htop\
   sudo\
   netcat\
   # airflow dependencies. 
   libssl-dev\
   # redis cli tools
   redis-tools\
   # postgres cli tools
   postgresql-client

##########################
# google keyring & kubectl

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" |\
   tee -a /etc/apt/sources.list.d/google-cloud-sdk.list &&\
   curl https://packages.cloud.google.com/apt/doc/apt-key.gpg |\
   apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - &&\
   apt-get update -y &&\
   apt-get install --no-install-recommends -yqq\
   kubectl

##########################
# Python enviroment
RUN yes | pip install -U\
   # communication between main pod, scheduler and workers
   redis\
   # postgres python binaries
   psycopg2-binary\
   # airflow dependencies.
   crypto\
   # postgres package
   postgres\
   # kubernets package
   kubernetes\
   # gcloud libs
   google-cloud-storage\
   google-cloud-bigquery

################################################
# Configure
ENV SCRIPTS_PATH=/scripts
RUN useradd -m airflow

# set python to use unicode.
ENV SLUGIFY_USES_TEXT_UNIDECODE=yes
ENV AIRFLOW_GPL_UNIDECODE yes

ENV C_FORCE_ROOT=true

ENV PATH="/scripts:${PATH}:/home/airflow/.local/bin"

##########################
# Main version

ENV ZAIRFLOW_VERSION=0.1.2

##########################
# Install airflow 
USER airflow

RUN yes | pip install --user\
   apache-airflow==1.10.9\
   git+https://github.com/LamaAni/KubernetesJobOperator.git@master

# this update is required since the airflow is installing the 
# wrong versions. Should be : Werkzeug>=0.15.0,Jinja2>=2.10.0]
RUN yes | pip install --user --upgrade Flask

##########################
# Scripts
USER root
WORKDIR /scripts

# copy bash scripts.
COPY ./scripts /scripts
COPY ./git_autosync/git_autosync /usr/bin/git_autosync
RUN chmod +x -R /scripts && chmod +x /usr/bin/git_autosync

# override the airflow command to allow hooks.
RUN ln -sf /scripts/invoke_airflow /usr/bin/airflow

##########################
# Cleanup

WORKDIR /
RUN apt-get autoremove -yqq --purge &&\
   apt-get clean

################################################
# Airflow directories
WORKDIR /airflow
USER airflow

# expose appropriate ports to the outside world.
EXPOSE 8080 5555 8793

# copy the config.
COPY airflow.cfg ./airflow.cfg

# airflow envs
ENV AIRFLOW_HOME /airflow
ENV PGHOST localhost
ENV PGUSER airflow
ENV AIRFLOW_CONFIG /airflow/airflow.cfg

# create the empty logs folder.
WORKDIR /airflow/logs

######################################
# change permissions to allow everything...
USER root
WORKDIR /app
RUN chown -R airflow /airflow /app && chmod -R 0777 /airflow

########### set entrypoint and start values.
USER airflow
WORKDIR /app

# set the entry point.
ENTRYPOINT ["/scripts/entrypoint.sh"]