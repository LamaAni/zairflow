from airflow import DAG
import airflow.models
from airflow.operators.subdag_operator import SubDagOperator

class SubDag(DAG):
    def __init__(self, name, parent=None, **kwargs):
        if parent is None:
            parent_dag = airflow.settings.CONTEXT_MANAGER_DAG
        else:
            parent_dag = parent
        super().__init__(
            f'{parent_dag.dag_id}.{name}',
            schedule_interval=parent_dag.schedule_interval,
            default_args=parent_dag.default_args
        )
        self.task = SubDagOperator(subdag=self, task_id=name)
