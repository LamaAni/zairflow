import requests
import json
import logging
import time
from airflow.exceptions import AirflowException
from airflow.hooks.base_hook import BaseHook
from requests import exceptions as requests_exceptions
from airflow.models import BaseOperator
from airflow.hooks.postgres_hook import PostgresHook


DATABRICKS_WAREHOUSE_PATH = "s3://h1-databricks/oregon-prod/960084232686341/user/hive/warehouse"

JOB_SUBMIT_ENDPOINT = 'v1/jobs/submit'
JOB_CHECK_ENDPOINT = 'v1/jobs'

NON_TERMINAL_STATUSES = ['NEW', 'PROCESSING', 'QUEUED']

logging.basicConfig(format='%(module)s: %(message)s', level='INFO')
LOGGER = logging.getLogger(__name__)


class ValidatorHook(BaseHook):

    def __init__(
            self,
            validator_conn_id='validator_default',
            timeout_seconds=180,
            retry_limit=3,
            retry_delay=1.0,
            **kwargs
    ):
        """
        :param validator_conn_id: The name of the validator connection to use.
        :type validator_conn_id: str
        :param timeout_seconds: The amount of time in seconds the requests library
            will wait before timing-out.
        :type timeout_seconds: int
        :param retry_limit: The number of times to retry the connection in case of
            service outages.
        :type retry_limit: int
        :param retry_delay: The number of seconds to wait between retries (it
            might be a floating point number).
        :type retry_delay: float
        """
        self.validator_conn_id = validator_conn_id
        self.validator_conn = self.get_connection(validator_conn_id)
        self.base_url = f'{self.validator_conn.host}:{self.validator_conn.port}'
        self.timeout_seconds = timeout_seconds
        if retry_limit < 1:
            raise ValueError('Retry limit must be greater than equal to 1')
        self.retry_limit = retry_limit
        self.retry_delay = retry_delay
        self.auth_header = self._build_auth_header()

    def _build_auth_header(self):
        """
        Takes the token in the connection and returns the header
        the validator endpoint expects to authenticate with.
        :return: an authentication header
        """
        if 'token' not in self.validator_conn.extra_dejson:
            raise AirflowException(f'No token in {self.validator_conn_id} to authenticate with')
        token = self.validator_conn.extra_dejson['token']
        return {'X-Auth': token}

    def submit_job(self, query_string):
        """
        :param query_string: parameters for the job
        :return: the id of the job
        """
        url = f'http://{self.base_url}/{JOB_SUBMIT_ENDPOINT}?{query_string}'
        LOGGER.info(f'Submitting job to {url}')
        response = requests.get(url, headers=self.auth_header)
        try:
            response.raise_for_status()
            job_id = response.json()["jobId"]
            LOGGER.info(f'Job {job_id} submitted')
            return job_id
        except requests_exceptions.RequestException as e:
            raise AirflowException('Response: {0}, Status Code: {1}'.format(
                e.response.content, e.response.status_code))

    def check_job_status(self, job_id):
        url = f'http://{self.base_url}/{JOB_CHECK_ENDPOINT}/{job_id}'
        response = requests.head(url, headers=self.auth_header)
        try:
            response.raise_for_status()
        except requests_exceptions.RequestException as e:
            raise AirflowException('Response: {0}, Status Code: {1}'.format(
                e.response.content, e.response.status_code))
        job_status = response.headers['X-Job-Status']
        LOGGER.info(f'Job has status {job_status}')
        return job_status

    def get_job_summary(self, job_id):
        url = f'http://{self.base_url}/{JOB_CHECK_ENDPOINT}/{job_id}'
        response = requests.head(url, headers=self.auth_header)
        try:
            response.raise_for_status()
        except requests_exceptions.RequestException as e:
            raise AirflowException('Response: {0}, Status Code: {1}'.format(
                e.response.content, e.response.status_code))
        job_summary = json.loads(response.headers['X-Job-Summary'])
        LOGGER.info(f'Total Rows: {job_summary["total"]}')
        LOGGER.info(f'Valid Rows: {job_summary["valid-count"]}')
        LOGGER.info(f'Invalid Rows: {job_summary["invalid-count"]}')
        return job_summary


class ValidateParquetOperator(BaseOperator):

    template_fields = ('database', 'table')

    def __init__(
        self,
        database,
        table,
        field,
        id_field,
        rule_id,
        max_invalid_ratio=None,
        max_invalid_count=None,
        sleep_interval=5.0,
        db_logging_config=None,
        *args,
        **kwargs
    ):
        """
        :param database: The name of the databricks database the table was written to
        :type database: str
        :param table: The name of the databricks table
        :type table: str
        :param field: The column name of the field to validate
        :type field: str
        :param id_field: The name of the field to use as the ID for reporting
        :type id_field: str
        :param rule_id: The ID of the rule to validate the field against
        :type rule_id: str
        :param max_invalid_ratio: Raise an AirflowExeption if the invalid ratio exceeds this threshold
        :type max_invalid_ratio: float
        :param sleep_interval: Seconds to wait between checking job status
        :type sleep_interval: float
        :param db_logging_config: log result to a database. Needs conn_id, table, owner
        :type dict
        """
        self.database = database
        self.table = table
        self.field = field
        self.id_field = id_field
        self.rule_id = rule_id
        self.max_invalid_ratio = max_invalid_ratio
        self.max_invalid_count = max_invalid_count
        self.sleep_interval = sleep_interval

        self.check_passed = None

        if db_logging_config:
            if 'conn_id' in db_logging_config and 'table' in db_logging_config and 'owner' in db_logging_config:
                self.db_logging_config = db_logging_config
            else:
                raise AirflowException("db_logging_config requires a conn_id, table, and owner")
        else:
            self.db_logging_config = None
        super(ValidateParquetOperator, self).__init__(*args, **kwargs)

    def build_parquet_query(self):
        path = f"{DATABRICKS_WAREHOUSE_PATH}/{self.database}.db/{self.table}/*.parquet"
        return f"fields=[{self.field}]&validators=[{self.rule_id}]&parquet=[{path}]&ids=[{self.id_field}]"

    def check_max_invalid(self, total, invalid_count):
        if self.max_invalid_ratio is not None and invalid_count/total > self.max_invalid_ratio:
            return False
        elif self.max_invalid_count is not None and invalid_count > self.max_invalid_count:
            return False
        else:
            return True

    def log_summary_to_database(self, summary, job_id, job_success, context):
        hook = PostgresHook(postgres_conn_id=self.db_logging_config['conn_id'])
        metadata = {'rule_id': self.rule_id,
                    'job_id': job_id,
                    'total': summary['total'],
                    'invalid_count': summary['invalid-count'],
                    'valid_count': summary['valid-count']}
        sql = f"""
        INSERT INTO
        {self.db_logging_config['table']}
        (owner, workflow, task, execution_date, check_passed, metadata)
        VALUES
        (%s, %s, %s, %s, %s, %s);
        """
        hook.run(sql, parameters=(self.db_logging_config['owner'],
                                  context['dag'].dag_id,
                                  context['task'].task_id,
                                  context['ds'],
                                  job_success,
                                  json.dumps(metadata),))

    def execute(self, context):
        hook = ValidatorHook()
        query = self.build_parquet_query()
        job_id = hook.submit_job(query)
        status = 'NEW'

        while status in NON_TERMINAL_STATUSES:
            status = hook.check_job_status(job_id)
            time.sleep(self.sleep_interval)

        if status == 'COMPLETED':
            job_summary = hook.get_job_summary(job_id)
            job_success = None

            if self.max_invalid_ratio is not None or self.max_invalid_count is not None:
                job_success = self.check_max_invalid(job_summary['total'], job_summary['invalid-count'])
                print(f'job success: {job_success}')

            if self.db_logging_config:
                self.log_summary_to_database(job_summary, job_id, job_success, context)

            if not job_success and job_success is not None:
                raise AirflowException(f"invalid-count of {job_summary['invalid-count']} violates either " +
                                       f"max_invalid_count({self.max_invalid_count}) or " +
                                       f"max_invalid_ratio({self.max_invalid_ratio})")

            return job_summary
        else:
            raise AirflowException("Job did not complete properly")
