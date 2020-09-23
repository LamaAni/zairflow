
FROM python:3.7.4-slim
ENV TERM linux

#########################################
# Prepare envrioment

USER root
WORKDIR /image_install

# prepare ubuntu version.
RUN apt-get update -yqq &&\
   apt-get upgrade -yqq &&\
   apt-get install -yqq --no-install-recommends\
   apt-utils \
   # prepare enviroment (utf-8, english)
   && apt-get install -yqq --no-install-recommends locales\
   && sed -i 's/^# en_US.UTF-8 UTF-8$/en_US.UTF-8 UTF-8/g' /etc/locale.gen \
   && locale-gen \
   && update-locale LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 \
   # Install core packages
   && apt-get install -yqq --no-install-recommends\
   # Core tools (for use in image)
   curl\
   git\
   openssh-client\
   apt-utils\
   build-essential\
   gnupg2\
   # utils
   htop\
   sudo\
   netcat\
   libssl-dev\
   redis-tools\
   postgresql-client\
   default-libmysqlclient-dev\
   # changes in airflow 1.10.12
   libsasl2-dev

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
RUN yes | pip install --no-cache-dir -U\
   # airflow install requirements
   setuptools\
   wheel\
   pytz\
   pyOpenSSL\
   ndg-httpsclient\
   pyasn1\
   argcomplete\
   redis\
   psycopg2-binary\
   crypto\
   postgres\
   kubernetes\
   google-cloud-storage\
   google-cloud-bigquery

################################################
# Configure
ENV SCRIPTS_PATH=/scripts
RUN useradd -m airflow

# set python to use unicode.
ENV SLUGIFY_USES_TEXT_UNIDECODE=yes
ENV PATH="/scripts:${PATH}:/home/airflow/.local/bin"

##########################
# Main version

ARG AIRFLOW_VERSION=1.10.12
ARG AIRFLOW_DEPS=""
ARG PYTHON_DEPS=""

##########################
# Copy dependencies
COPY db_logger /db_logger

##########################
# Install airflow 
WORKDIR /airflow
RUN yes | pip install --no-cache-dir --upgrade \
   apache-airflow[crypto,celery,postgres,hive,jdbc,mysql,ssh,kubernets${AIRFLOW_DEPS:+,}${AIRFLOW_DEPS}]==${AIRFLOW_VERSION}\
   airflow-kubernetes-job-operator==1.0.1 \
   # Falsk sometimes comes in the wrong version.
   # Flask \
   # Specialized db logger.
   /db_logger

##########################
# Scripts
WORKDIR /scripts

# Copy all the scripts.
COPY ./scripts /scripts

# copy bash scripts.
RUN git clone https://github.com/LamaAni/git_autosync.git --branch 1.1.0 /scripts/git_autosync && \
   ln -sf /scripts/git_autosync/git_autosync /usr/bin/git_autosync && \
   mv /usr/local/bin/airflow /usr/local/bin/call_airflow && \
   ln -sf /scripts/image/invoke_airflow /usr/local/bin/airflow && \
   chmod +x -R /scripts && chmod +x /usr/bin/git_autosync

# ##########################
# # Cleanup

WORKDIR /
RUN apt-get autoremove -yqq --purge &&\
   apt-get clean && \
   rm -R /db_logger

################################################
# Airflow directories
WORKDIR /airflow
USER airflow

# copy the config.
COPY ./docker/airflow.cfg ./airflow.cfg

# airflow envs
ARG ZAIRFLOW_VERSION="debug"
ENV AIRFLOW_HOME /airflow
ENV FERNET_KEY "abcd"
ENV PGHOST localhost
ENV PGUSER airflow
ENV AIRFLOW_CONFIG /airflow/airflow.cfg
ENV ZAIRFLOW_VERSION=${ZAIRFLOW_VERSION}

# create the empty logs folder.
WORKDIR /airflow/logs

######################################
# setup permissions
USER root
WORKDIR /app
RUN chown -R airflow /airflow /app && chmod -R 0777 /airflow

######################################
# Image entry config.
USER airflow
WORKDIR /app
EXPOSE 8080 5555 8793
ENTRYPOINT ["/scripts/image/entrypoint.sh"]