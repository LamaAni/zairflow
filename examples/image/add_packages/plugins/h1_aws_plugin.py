from airflow.contrib.hooks.aws_hook import AwsHook
from airflow.hooks.S3_hook import S3Hook
from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults
from botocore.waiter import WaiterModel, create_waiter_with_client


import ast
import time


class AwsCommandOperator(BaseOperator):

    template_fields = ('service', 'command_name', 'command_params')

    @apply_defaults
    def __init__(self,
                 service=None,
                 command_name=None,
                 command_params=None,
                 aws_conn_id='aws_default',
                 verify=None,
                 handler=None,
                 *args,
                 **kwargs):
        super(AwsCommandOperator, self).__init__(*args, **kwargs)

        if not isinstance(service, str):
            raise ValueError("'service' must be a string")
        if not isinstance(command_name, str):
            raise ValueError("'command_name' must be a string")
        if not isinstance(command_params, dict):
            raise ValueError("'command_params' must be a dict")
        if not isinstance(aws_conn_id, str):
            raise ValueError("'aws_conn_id' must be string")
        if verify is not None and not isinstance(verify, bool):
            raise ValueError("'verify' must be None or bool")

        self.service = service
        self.command_name = command_name
        self.command_params = command_params
        self.aws_conn_id = aws_conn_id
        self.verify = verify
        self.handler = handler

    def execute(self, context):
        hook = AwsHook(aws_conn_id=self.aws_conn_id, verify=self.verify)
        client = hook.get_client_type(self.service)
        command = getattr(client, self.command_name)
        try:
            res = command(**self.command_params)
            if self.handler is not None:
                self.handler(res, context)
            return res
        except Exception as e:
            self.log.info(self.command_params)
            raise e


class AwsWaiterOperator(BaseOperator):

    template_fields = ('service', 'waiter_name', 'waiter_params', 'delayed_polling')

    @apply_defaults
    def __init__(self,
                 service=None,
                 waiter_name=None,
                 waiter_params=None,
                 delayed_polling=False,
                 aws_conn_id='aws_default',
                 verify=None,
                 *args,
                 **kwargs):
        super(AwsWaiterOperator, self).__init__(*args, **kwargs)

        if not isinstance(service, str):
            raise ValueError("'service' must be a string")
        if not isinstance(waiter_name, str):
            raise ValueError("'waiter_name' must be a string")
        if not isinstance(waiter_params, dict):
            raise ValueError("'waiter_params' must be a dict")
        if not isinstance(aws_conn_id, str):
            raise ValueError("'aws_conn_id' must be string")
        if verify is not None and not isinstance(verify, bool):
            raise ValueError("'verify' must be None or bool")
        if not isinstance(delayed_polling, bool):
            raise ValueError("'delayed_polling' must be a bool")

        self.service = service
        self.waiter_name = waiter_name
        self.waiter_params = waiter_params
        self.delayed_polling = delayed_polling
        self.aws_conn_id = aws_conn_id
        self.verify = verify

    def execute(self, context):
        hook = AwsHook(aws_conn_id=self.aws_conn_id, verify=self.verify)
        client = hook.get_client_type(self.service)
        waiter = client.get_waiter(self.waiter_name)
        if self.delayed_polling:
            time.sleep(waiter.config.delay)
        try:
            waiter.wait(**self.waiter_params)
        except Exception as e:
            self.log.info(self.waiter_params)
            raise e


class AwsCustomWaiterOperator(BaseOperator):

    template_fields = ('service', 'waiter_name', 'waiter_params', 'delayed_polling', 'waiter_config')

    @apply_defaults
    def __init__(self,
                 service=None,
                 waiter_name=None,
                 waiter_params=None,
                 waiter_config=None,
                 delayed_polling=False,
                 verify=None,
                 aws_conn_id='aws_default',
                 *args,
                 **kwargs):
        super(AwsCustomWaiterOperator, self).__init__(*args, **kwargs)

        if not isinstance(service, str):
            raise ValueError("'service' must be a string")
        if not isinstance(waiter_name, str):
            raise ValueError("'waiter_name' must be a string")
        if not isinstance(waiter_params, dict):
            raise ValueError("'waiter_params' must be a dict")
        if not isinstance(aws_conn_id, str):
            raise ValueError("'aws_conn_id' must be string")
        if not isinstance(delayed_polling, bool):
            raise ValueError("'delayed_polling' must be a bool")
        if verify is not None and not isinstance(verify, bool):
            raise ValueError("'verify' must be None or bool")
        if not isinstance(waiter_config, dict):
            raise ValueError("'waiter_config' must be a dict")

        self.service = service
        self.waiter_name = waiter_name
        self.waiter_params = waiter_params
        self.delayed_polling = delayed_polling
        self.aws_conn_id = aws_conn_id
        self.waiter_config = waiter_config
        self.verify = verify


    def execute(self, context):
            hook = AwsHook(aws_conn_id=self.aws_conn_id, verify=self.verify)
            client = hook.get_client_type(self.service)
            waiter_model = WaiterModel(self.waiter_config)
            waiter = create_waiter_with_client(self.waiter_name, waiter_model, client)
            if self.delayed_polling:
                time.sleep(waiter.config.delay)
            try:
                waiter.wait(**self.waiter_params)
            except Exception as e:
                self.log.info(self.waiter_params)
                raise e



class S3ListPrefixesOperator(BaseOperator):

    template_fields = ('bucket', 'prefix', 'delimiter')

    @apply_defaults
    def __init__(self,
                 bucket,
                 prefix='',
                 delimiter='',
                 aws_conn_id='aws_default',
                 verify=None,
                 *args,
                 **kwargs):
        super(S3ListPrefixesOperator, self).__init__(*args, **kwargs)
        self.bucket = bucket
        self.prefix = prefix
        self.delimiter = delimiter
        self.aws_conn_id = aws_conn_id
        self.verify = verify

    def execute(self, context):
        hook = S3Hook(aws_conn_id=self.aws_conn_id, verify=self.verify)

        self.log.info(
            'Getting the list of files from bucket: {0} with wildcard: {1} (Delimiter {2})'.
            format(self.bucket, self.prefix, self.delimiter))

        return hook.list_prefixes(
            bucket_name=self.bucket,
            delimiter=self.delimiter,
            prefix=self.prefix
        )


class S3CopySuccessfulReport(BaseOperator):

    template_fields = ('job_output_dir', 'report_dir', 'report_files', 'bucket_name')

    @apply_defaults
    def __init__(self,
                 job_output_dir,
                 report_dir,
                 report_files,
                 bucket_name,
                 aws_conn_id,
                 verify=None,
                 *args,
                 **kwargs):
        super(S3CopySuccessfulReport, self).__init__(*args, **kwargs)
        self.job_output_dir = job_output_dir
        self.report_dir = report_dir
        self.report_files = report_files
        self.bucket_name = bucket_name
        self.aws_conn_id = aws_conn_id
        self.verify = verify
        self.hook = S3Hook(aws_conn_id=self.aws_conn_id, verify=self.verify)

    def parse_unvalidated_files(self, report_files):
        if report_files and len(report_files) > 2:
            return ast.literal_eval(report_files)

    def get_csv_to_copy(self, prefix, file):
        full_prefix = prefix + file
        self.log.info(full_prefix)
        files_and_prefixes = self.hook.list_keys(
            prefix=full_prefix,
            bucket_name=self.bucket_name)
        files = [file_and_prefix.split("/")[-1] for file_and_prefix in files_and_prefixes]
        success_file = "_SUCCESS"
        self.log.info(files)
        if success_file in files:
            csv_files = [file for file in files if ".csv" in file]

            if len(csv_files) == 1:
                return csv_files[0]

            elif len(csv_files) == 0:
                self.log.warn("No CSV files found in {}".format(prefix))

            else:
                self.log.warn("Multiple CSV files found in {}".format(prefix))

    def execute(self, context):
        report_files = self.parse_unvalidated_files(self.report_files)
        for file in report_files:
            self.log.info(file)
            job_output_file = self.get_csv_to_copy(self.job_output_dir, file)
            if job_output_file:
                object_path_source = "{base_dir}{file}/{job_output_file}".format(base_dir=self.job_output_dir, file=file, job_output_file=job_output_file)
                object_path_dest = "{base_dir}REPORT_{file}".format(base_dir=self.report_dir, file=file)
                self.hook.copy_object(
                    source_bucket_key=object_path_source,
                    dest_bucket_key=object_path_dest,
                    source_bucket_name=self.bucket_name,
                    dest_bucket_name=self.bucket_name
                )


class S3OperatorsPlugin(AirflowPlugin):
    name = "s3_operators"
    operators = [S3ListPrefixesOperator, S3CopySuccessfulReport]
