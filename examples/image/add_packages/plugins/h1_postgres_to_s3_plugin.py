import logging

from airflow.models import BaseOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults
import tempfile, os, threading

from airflow.hooks.postgres_hook import PostgresHook
from airflow.hooks.S3_hook import S3Hook
from contextlib import closing

log = logging.getLogger(__name__)

class PGTableToS3Operator(BaseOperator):

    template_fields = ('dest_key', 'source_table', 'dest_bucket')

    @apply_defaults
    def __init__(
        self,
        source_table, 
        dest_key, 
        aws_conn_id,
        postgres_conn_id,
        dest_bucket = 'disambiguation', 
        *args, 
        **kwargs):
        self.source_table = source_table
        self.postgres_conn_id = postgres_conn_id
        self.aws_conn_id = aws_conn_id
        self.dest_key = dest_key
        self.dest_bucket = dest_bucket
        super(PGTableToS3Operator, self).__init__(*args, **kwargs)

    def execute(self, context):
        r, w = os.pipe()
        hook = S3Hook(aws_conn_id = self.aws_conn_id)
        
        t1 = threading.Thread(target=self.fetch, args=(w,))
        t2 = threading.Thread(target=self.upload, args=(r,))

        t1.start()
        t2.start()

        t1.join()
        t2.join()

        return {
            'bucket': self.dest_bucket,
            'key': self.dest_key,
            'table': self.source_table
        }

        

    def fetch(self, outfile):
        hook = PostgresHook(postgres_conn_id = self.postgres_conn_id)

        with closing(hook.get_conn()) as conn:
            with closing(conn.cursor()) as cur:
                cur.copy_expert("COPY {table} TO STDOUT WITH (FORMAT csv, HEADER)".format(table=self.source_table), os.fdopen(outfile, 'wb'))
                conn.commit()

    def upload(self, infile):
        hook = S3Hook(aws_conn_id = self.aws_conn_id)

        hook.load_file_obj(os.fdopen(infile, 'rb'), self.dest_key, bucket_name=self.dest_bucket, replace=True, encrypt=True)



class PGTableToS3Plugin(AirflowPlugin):
    name = "pg_table_to_s3_plugin"
    operators = [PGTableToS3Operator]