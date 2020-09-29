from airflow import DAG
from airflow_kubernetes_job_operator.kubernetes_job_operator import KubernetesJobOperator
from airflow.utils.dates import days_ago

default_args = {"owner": "tester", "start_date": days_ago(2), "retries": 0}
dag = DAG(
    "job-operator-example", default_args=default_args, description="Test base job operator", schedule_interval=None
)

job_file = __file__ + ".yaml"
tick_count = 2

KubernetesJobOperator(
    dag=dag,
    task_id="test-job-success",
    body_filepath=job_file,
    envs={
        "EXIT_ERROR": "0",
        "TICKS": tick_count,
    },
)
KubernetesJobOperator(
    dag=dag,
    task_id="test-job-fail",
    body_filepath=job_file,
    envs={
        "EXIT_ERROR": "22",
        "TICKS": tick_count,
    },
)
KubernetesJobOperator(
    task_id="test-job-overrides",
    dag=dag,
    image="ubuntu",
    command=["bash", "-c", "echo start; sleep 10; echo end"],
)
