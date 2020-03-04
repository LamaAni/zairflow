import requests
import jsonschema
import logging
import os

from airflow import DAG
from airflow.exceptions import AirflowException
from airflow.hooks.base_hook import BaseHook
from airflow.models import BaseOperator, Variable
from airflow.operators.dummy_operator import DummyOperator
from airflow.operators.python_operator import PythonOperator


class schema:
    status_type = {
        "type": "string",
        "enum": [
            "operational",
            "under_maintenance",
            "degraded_performance",
            "partial_outage",
            "major_outage",
            "",
        ],
        "description": "Status of component",
    }

    component = {
        "type": "object",
        "properties": {
            "component": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "More detailed description for component",
                    },
                    "status": status_type,
                    "name": {"type": "string", "description": "Display name for component"},
                    "only_show_if_degraded": {
                        "type": "boolean",
                        "description": "Requires a special feature flag to be enabled",
                    },
                    "group_id": {
                        "type": "string",
                        "description": "Component Group identifier",
                    },
                    "showcase": {
                        "type": "boolean",
                        "description": "Should this component be showcased",
                    },
                },
                "additionalProperties": False,
            }
        },
        "additionalProperties": False,
        "required": ["component"],
    }

    # https://developer.statuspage.io/#operation/postPagesPageIdIncidents
    incident_request = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Incident Name"},
            "status": {"type": "string", "description": "Incident Status"},
            "body": {
                "type": "string",
                "description": "The initial message, created as the first incident update.",
            },
            "components": {
                "type": "object",
                "description": "Map of status changes to apply to affected components",
                # based on the example payloads in the API documentation
                "properties": {"component_id": status_type},
            },
        },
    }


class StatuspageClient:
    def __init__(self, api_key, page_name, group_name):
        """A Statuspage client for a page and group"""

        self.base_url = "https://api.statuspage.io/v1/"
        self.api_key = api_key

        self.page_id = self.get_page_id(page_name)
        self.group_id = self.get_component_group_id(group_name)

    def _request(self, method, path, data=None):
        headers = {"Authorization": "OAuth {}".format(self.api_key)}
        request_method = {
            "get": requests.get,
            "post": requests.post,
            "delete": requests.delete,
            "put": requests.put,
            "patch": requests.patch,
        }.get(method)

        if not request_method:
            raise ValueError("Method {} not supported".format(method))

        url = self.base_url + path
        resp = request_method(url, json=data, headers=headers)
        logging.info("status-code {} for {}".format(resp.status_code, url))
        if resp.status_code != 200:
            logging.error(resp.content)
        resp.raise_for_status()
        return resp

    def get_id(self, data, predicate):
        for row in data:
            if predicate(row):
                return row["id"]
        return None

    def get_page_id(self, name):
        resp = self._request("get", "pages")
        data = resp.json()
        return self.get_id(data, lambda r: r["name"] == name)

    def get_component_group_id(self, name):
        resp = self._request("get", "pages/{}/component-groups".format(self.page_id))
        data = resp.json()
        return self.get_id(data, lambda r: r["name"] == name)

    def get_component_id(self, name):
        resp = self._request("get", "pages/{}/components".format(self.page_id))
        data = resp.json()
        return self.get_id(data, lambda r: r["name"] == name)

    def create_component(self, component):
        jsonschema.validate(component, schema.component)
        resp = self._request(
            "post", "pages/{}/components".format(self.page_id), component
        )
        return resp.json().get("id")

    def update_component(self, component_id, component):
        jsonschema.validate(component, schema.component)
        route = "pages/{}/components/{}".format(self.page_id, component_id)
        resp = self._request("patch", route, component)
        return resp.json().get("id")

    def create_incident(
        self, name, incident_status, body, component_status, affected_component_ids
    ):
        """"
        Create an incident.

        See https://developer.statuspage.io/#operation/postPagesPageIdIncidents for more details.

        :param name:    The title name to give the incident.
        :param incident_status: The status of the incident e.g. investigating, identified, resolved
        :param body:    The initial message, created as the first incident update.
        :param component_status:    The status state to set the component.
        :param affected_component_ids:  A list of component id's that are affected by this incident.
        :returns: The id of the incident
        :raises jsonschema.exceptions.ValidationError:
        """
        if not isinstance(affected_component_ids, list):
            affected_component_ids = [affected_component_ids]

        data = {
            "name": name,
            "status": incident_status,
            "body": body,
            "components": {"component_id": component_status},
            "component_ids": affected_component_ids,
        }
        jsonschema.validate(data, schema.incident_request)
        resp = self._request(
            "post", "pages/{page_id}/incidents".format(page_id=self.page_id), data=data
        )
        return resp.json().get("id")


class DatasetStatus:
    """"A Statuspage client for setting the status of Data Engineering Datasets in Firefox Operations."""

    def __init__(self, api_key):
        self.client = StatuspageClient(
            api_key, "H1 Insights", "Data Engineering Dataset Pipeline"
        )

    def _create(self, name, description="", status="operational"):
        return self.client.create_component(
            {
                "component": {
                    "name": name,
                    "description": description,
                    "status": status,
                    "only_show_if_degraded": False,
                    "group_id": self.client.group_id,
                    "showcase": True,
                }
            }
        )

    def get_or_create(self, name, description=""):
        """Get or create the component id of a statuspage.

        :param name:        The name of the component
        :param description: The description associated with the component
        :returns:   A component id or None
        """
        cid = self.client.get_component_id(name)
        if not cid:
            cid = self._create(name, description)
        return cid

    def update(self, component_id, status):
        """Set the state of a component.

        :param component_id: The identifier of a component
        :param status: one of [operational, under_maintenance, degraded_performance, partial_outage, major_outage]
        :returns:   The component id if successful, None otherwise
        """
        patch = {"component": {"status": status}}
        return self.client.update_component(component_id, patch)

    def create_incident_investigation(
        self, name, component_id, body=None, component_status="partial_outage"
    ):
        """Create a new incident given a list of affected component ids.

        :param name:                The name of the dataset.
        :component_id:              The component id of the dataset
        :param body:                The initial message, created as the first incident update.
        :param component_status:    The status state to set the component.
        :returns:                   The id of the incident
        """
        templated_title = "Investigating Errors in {name}".format(name=name)

        default_body = (
            "Automated monitoring has determined that {name} is experiencing errors. "
            "Engineers have been notified to investigate the source of error. "
        ).format(name=name)

        return self.client.create_incident(
            name=templated_title,
            incident_status="Investigating",  # value derived from web-interface
            body=body or default_body,
            component_status=component_status,
            affected_component_ids=[component_id],
        )


class DatasetStatusHook(BaseHook):
    """Create and update the status of a dataset."""

    def __init__(self, api_key=None, statuspage_conn_id="statuspage_default"):
        """Initialize the client with an API key.

        :param api_key: Statuspage API key
        :param statuspage_conn_id: connection with the API token in the password field
        """

        self.api_key = (
            api_key
            or os.environ.get("STATUSPAGE_API_KEY")
            or self.get_connection(statuspage_conn_id).password
        )
        if not self.api_key:
            raise AirflowException("Missing an API key for Statuspage")

    def get_conn(self):
        return DatasetStatus(self.api_key)


class DatasetStatusOperator(BaseOperator):
    def __init__(
        self,
        name,
        description,
        status,
        statuspage_conn_id="statuspage_default",
        create_incident=False,
        incident_body=None,
        **kwargs
    ):
        """Create and update the status of a Data Engineering Dataset.

        :param name: Name of the Statuspage
        :param description: Description of the dataset
        :param status: one of [operational, under_maintenance, degraded_performance, partial_outage, major_outage]
        :param statuspage_conn_id: Airflow connection id for credentials
        :param create_incident: A flag to enable automated filing of Statuspage incidents
        :param incident_body:   Optional text for describing the incident
        """
        super(DatasetStatusOperator, self).__init__(**kwargs)
        self.statuspage_conn_id = statuspage_conn_id
        self.name = name
        self.description = description
        self.status = status
        self.create_incident = create_incident
        self.incident_body = incident_body

    def execute(self, context):
        conn = DatasetStatusHook(statuspage_conn_id=self.statuspage_conn_id).get_conn()
        comp_id = conn.get_or_create(self.name, self.description)

        self.log.info(
            "Setting status for {} ({}) to {}".format(self.name, comp_id, self.status)
        )

        if self.create_incident:
            incident_id = conn.create_incident_investigation(
                self.name, comp_id, self.incident_body, self.status
            )
            self.log.info("Created incident with id {}".format(incident_id))
        else:
            comp_id = conn.update(comp_id, self.status)


def register_status(operator, name, description, on_success=True):
    """Wrap an operator with an external status page.

    The default behavior will only set the state of a dataset to partial_outage.

    :param airflow.models.BaseOperator operator: An Airflow operator to set upstream
    :param str name:            The name of the dataset
    :param str description:     A short (1-2 sentence) description of the dataset.
    :param boolean on_success:  Indicator to set the dataset state to operational on success

    :returns: The original airflow operator with downstream dependencies
    """
    if Variable.get('env') != 'production':
        return operator

    kwargs = {"name": name, "description": description, "dag": operator.dag}

    def callable():
        conn = DatasetStatusHook().get_conn()
        comp_id = conn.get_or_create(name, description)
        logging.info(
            "Statuspage component {} is registered with {}".format(comp_id, name)
        )

    register = PythonOperator(
        task_id="{}_register".format(operator.task_id),
        python_callable=callable,
        dag=operator.dag,
    )
    operator >> register

    if on_success:
        # create and operator on the success case
        success = DatasetStatusOperator(
            trigger_rule="all_success",
            task_id="{}_success".format(operator.task_id),
            status="operational",
            **kwargs
        )
        operator >> success

    # create an operator on the failure case
    failure = DatasetStatusOperator(
        trigger_rule="one_failed",
        task_id="{}_failure".format(operator.task_id),
        status="partial_outage",
        **kwargs
    )

    operator >> failure

    return operator


class StatusPageDag(DAG):
    '''
    A DAG that registers all end_tasks as upstream from one dummy
    'end' task used for status page updates.
    '''
    def __exit__(self, _type, _value, _tb):
        dag_name = self.dag_id
        end_tasks = [task for task in self.tasks if not task.downstream_task_ids]
        dummy_end_task = DummyOperator(task_id=f'{dag_name}_end')
        register_status(dummy_end_task, dag_name, self.description)
        dummy_end_task << end_tasks
        super().__exit__(_type, _value, _tb)
