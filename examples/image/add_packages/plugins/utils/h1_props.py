from airflow.models import Variable
from airflow.hooks.postgres_hook import PostgresHook
from datetime import datetime, timedelta
import json

# Jar locations
DEVELOP_LATEST = 's3://h1-data-build-artifacts/develop/latest/h1-data_latest.jar'
ENVIRONMENT_LATEST_JAR = 's3://h1-data-build-artifacts/{{ var.value.jar_env }}/latest/h1-data_latest.jar'

CUSTOM_ASSET_MAPPING_PATH = 's3://disambiguation/airflow-sources/{{ var.value.env }}/custom-asset-mappings/*'

CLUSTER_TEMPLATE = {
    "new_cluster": {
        "spark_version": "6.2.x-scala2.11",
        "spark_conf": {},
        "aws_attributes": {
            "first_on_demand": 1,
            "availability": "SPOT_WITH_FALLBACK",
            "zone_id": "us-east-1e",
            "instance_profile_arn": "arn:aws:iam::247756923940:instance-profile/databricks-cluster",
            "spot_bid_price_percent": 100,
            "ebs_volume_type": "GENERAL_PURPOSE_SSD",
            "ebs_volume_count": 1,
            "ebs_volume_size": 100
        },
        "ssh_public_keys": [],
        "custom_tags": {
            "BusinessRegion": "NY"
        },
        "spark_env_vars": {
            "PYSPARK_PYTHON": "/databricks/python3/bin/python3"
        },
        "spark_conf": {
            "spark.hadoop.fs.s3a.impl": "com.databricks.s3a.S3AFileSystem",
            "spark.hadoop.fs.s3n.impl": "com.databricks.s3a.S3AFileSystem",
            "spark.hadoop.fs.s3a.acl.default": "BucketOwnerFullControl",
            "spark.hadoop.fs.s3a.canned.acl": "BucketOwnerFullControl",
            "spark.hadoop.fs.s3.impl": "com.databricks.s3a.S3AFileSystem"
        },
        "enable_elastic_disk": False,
        "init_scripts": []
    },
    "libraries": [{"jar": ENVIRONMENT_LATEST_JAR }],
    "timeout_seconds": 0
}

DEFAULT_CLUSTER = {
    "autoscale": {
        "min_workers": 2,
        "max_workers": 5
    },
    "spark_version": "6.2.x-scala2.11",
    "aws_attributes": {
        "zone_id": "us-east-1e",
        "first_on_demand": 1,
        "availability": "SPOT_WITH_FALLBACK",
        "instance_profile_arn": "arn:aws:iam::247756923940:instance-profile/databricks-cluster",
        "spot_bid_price_percent": 100,
        "ebs_volume_type": "GENERAL_PURPOSE_SSD",
        "ebs_volume_count": 1,
        "ebs_volume_size": 1000
    },
    "node_type_id": "r4.2xlarge",
    "driver_node_type_id": "r4.2xlarge",
    "custom_tags": {
        "BusinessRegion": "NY"
    },
    "spark_env_vars": {
        "PYSPARK_PYTHON": "/databricks/python3/bin/python3"
    },
    "enable_elastic_disk": False,
    "spark_conf": {
        "spark.hadoop.fs.s3a.impl": "com.databricks.s3a.S3AFileSystem",
        "spark.hadoop.fs.s3n.impl": "com.databricks.s3a.S3AFileSystem",
        "spark.hadoop.fs.s3a.acl.default": "BucketOwnerFullControl",
        "spark.hadoop.fs.s3a.canned.acl": "BucketOwnerFullControl",
        "spark.hadoop.fs.s3.impl": "com.databricks.s3a.S3AFileSystem"
    },
}


DATABRICKS_LIGHT_CLUSTER = {
    "num_workers": 2,
    "spark_version": "apache-spark-2.4.x-scala2.11",
    "aws_attributes": {
        "zone_id": "us-east-1e",
        "first_on_demand": 1,
        "availability": "SPOT_WITH_FALLBACK",
        "instance_profile_arn": "arn:aws:iam::247756923940:instance-profile/databricks-cluster",
        "spot_bid_price_percent": 100,
        "ebs_volume_type": "GENERAL_PURPOSE_SSD",
        "ebs_volume_count": 1,
        "ebs_volume_size": 1000
    },
    "node_type_id": "r4.xlarge",
    "custom_tags": {
        "BusinessRegion": "NY"
    },
    "spark_env_vars": {
        "PYSPARK_PYTHON": "/databricks/python3/bin/python3"
    },
    "enable_elastic_disk": False,
    "spark_conf": {
        "spark.hadoop.fs.s3a.impl": "com.databricks.s3a.S3AFileSystem",
        "spark.hadoop.fs.s3n.impl": "com.databricks.s3a.S3AFileSystem",
        "spark.hadoop.fs.s3a.acl.default": "BucketOwnerFullControl",
        "spark.hadoop.fs.s3a.canned.acl": "BucketOwnerFullControl",
        "spark.hadoop.fs.s3.impl": "com.databricks.s3a.S3AFileSystem"
    },
}

def get_database(name):
    env = Variable.get('env')
    return name if env == 'production' else f'{name}_{env}'


def get_metadb_owner():
    env = Variable.get('env')
    return 'airflow' if env == 'production' else f'airflow_{env}'


def get_table(dbname, tablename):
    full_dbname = get_database(dbname)
    return f'{full_dbname}.{tablename}'


def get_jar_config(path):
    return [{'jar': path}]


def get_pipeline_task(pipeline, job, **kwargs):

    parameters = ["{}={}".format(arg, kwargs[arg]) for arg in kwargs.keys()]
    main_class_name = 'com.h1insights.pipeline.{}.{}'.format(pipeline, job)

    return {'main_class_name': main_class_name, 'parameters':  parameters}


JOBS_META_LOGGING = {
    'conn_id': 'jobs_meta_postgres',
    'table': 'logs',
    'owner': get_metadb_owner()
}


def log_metadata(metadata, context):
    hook = PostgresHook(postgres_conn_id=JOBS_META_LOGGING['conn_id'])
    sql = f"""
    INSERT INTO
    {JOBS_META_LOGGING['table']}
    (owner, workflow, task, execution_date, check_passed, metadata)
    VALUES
    (%s, %s, %s, %s, %s, %s);
    """
    hook.run(sql, parameters=(JOBS_META_LOGGING['owner'],
                              context['dag'].dag_id,
                              context['task'].task_id,
                              context['ds'],
                              None,
                              json.dumps(metadata)))
