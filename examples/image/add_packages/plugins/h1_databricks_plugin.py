import logging

from airflow import __version__
from airflow.models import BaseOperator, Variable
from airflow.hooks.base_hook import BaseHook
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults
from airflow.contrib.hooks.aws_hook import AwsHook
from airflow.contrib.hooks.databricks_hook import DatabricksHook
from airflow.contrib.operators.databricks_operator import DatabricksSubmitRunOperator
import tempfile, os, threading, json
import requests
from urllib import parse

from contextlib import closing

log = logging.getLogger(__name__)

def notebook_path(path):
    notebook_env = Variable.get("notebook_env")
    if "@" in notebook_env:
        return f"/Users/{notebook_env}/h1-data/" + path
    else:
        return f"/Shared/{notebook_env}/notebooks/" + path


class DatabricksRunResultHook(BaseHook):
    def __init__(
        self,
        databricks_conn_id = 'databricks_default'):
        self.databricks_conn = self.get_connection(databricks_conn_id)

    def get_run_result(self, run_id):
        host = parse.urlparse(self.databricks_conn.host).hostname
        url = 'https://{host}/api/2.0/jobs/runs/get-output'.format(
            host=host
        )

        result = requests.get(
            url,
            json={ 'run_id': run_id },
            headers={
                'user-agent': 'airflow-{v}'.format(v=__version__),
                'Authorization': 'Bearer ' + self.databricks_conn.extra_dejson['token']
            },
            timeout=180
        )

        json_result = result.json()
        notebook_output = json_result['notebook_output']['result']

        return json.loads(notebook_output)

class DatabricksRunResultOperator(BaseOperator):

    template_fields = ('databricks_run_id',)

    @apply_defaults
    def __init__(
            self,
            databricks_run_id,
            databricks_conn_id='databricks_default',
            aws_conn_id='aws_default',
            custom_handler=None,
            *args,
            **kwargs):
        self.databricks_run_id = databricks_run_id
        self.databricks_conn_id = databricks_conn_id
        self.aws_conn_id = aws_conn_id
        self.response_handler = self.default_handler if custom_handler is None else custom_handler
        super(DatabricksRunResultOperator, self).__init__(*args, **kwargs)

    def execute(self, context):
        db_result_hook = DatabricksRunResultHook(databricks_conn_id=self.databricks_conn_id)
        result = db_result_hook.get_run_result(self.databricks_run_id)
        self.response_handler(result, context)

    @staticmethod
    def default_handler(result, context):
        if 'failed' in result and result['failed'] == True:
            db_hook = DatabricksHook(databricks_conn_id=self.databricks_conn_id)
            run_page = db_hook.get_run_page_url(self.databricks_run_id)
            aws_hook = AwsHook(aws_conn_id=self.aws_conn_id)
            sns_client = aws_hook.get_client_type('sns')

            resp = sns_client.publish(
                TargetArn='arn:aws:sns:us-east-1:247756923940:airflow-development',
                Message='Data Validation Failed',
                MessageStructure='string',
                Subject="DATA VALIDATION FAILED",
                MessageAttributes={
                    'execution_date': {
                        'DataType': 'String',
                        'StringValue': str(context['execution_date'])
                    },
                    'databricks_run_id': {
                        'DataType': 'String',
                        'StringValue': self.databricks_run_id
                    },
                    'databricks_run_url': {
                        'DataType': 'String',
                        'StringValue': run_page
                    },
                }
            )
            print(resp)


class DatabricksRunResultPlugin(AirflowPlugin):
    name = "pg_table_to_s3_plugin"
    operators = [DatabricksRunResultOperator]
    hooks = [DatabricksRunResultHook]


def build_databricks_task(
  source,
  name,
  min_workers=1,
  max_workers=2,
  extra_params={}):

    notebook_name = notebook_path(f"{source}/{name}")

    libraries = [{'jar': 's3://h1-data-build-artifacts/{{ var.value.env }}/latest/h1-data_latest.jar'}]

    cluster_config = {
        "notebook_task": {
            "notebook_path": notebook_name,
            "base_parameters": {
                "execution_date": "{{ ds }}",
                "env": "{{ var.value.env }}",
                **extra_params
            }
        },
        "name": source + "_" + name,
        "libraries": libraries,
        "new_cluster": {
            "autoscale": {
                "min_workers": min_workers,
                "max_workers": max_workers
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
            "node_type_id": "c4.4xlarge",
            "driver_node_type_id": "c4.4xlarge",
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
    }

    return DatabricksSubmitRunOperator(
        task_id=source + '_' + name,
        json=cluster_config,
        do_xcom_push=True
    )
