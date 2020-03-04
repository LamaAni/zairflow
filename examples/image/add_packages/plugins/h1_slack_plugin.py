from airflow.contrib.hooks.slack_webhook_hook import SlackWebhookHook
from airflow.hooks.base_hook import BaseHook
from airflow.operators.http_operator import SimpleHttpOperator
from airflow.plugins_manager import AirflowPlugin
from airflow.utils.decorators import apply_defaults


SLACK_CONN_ID = 'slack'
SLACK_WEBHOOK_TOKEN = BaseHook.get_connection(SLACK_CONN_ID).password


class H1SlackWebhookOperator(SimpleHttpOperator):

    template_fields = ('message',)

    @apply_defaults
    def __init__(self,
                 http_conn_id=None,
                 webhook_token=None,
                 message="",
                 channel=None,
                 username=None,
                 icon_emoji=None,
                 link_names=False,
                 proxy=None,
                 *args,
                 **kwargs):
        super(H1SlackWebhookOperator, self).__init__(endpoint=webhook_token,
                                                     *args,
                                                     **kwargs)
        self.http_conn_id = http_conn_id
        self.webhook_token = webhook_token
        self.message = message
        self.channel = channel
        self.username = username
        self.icon_emoji = icon_emoji
        self.link_names = link_names
        self.proxy = proxy
        self.hook = None

    def execute(self, context):
        """
        Call the SlackWebhookHook to post the provided Slack message
        """
        self.hook = SlackWebhookHook(
            self.http_conn_id,
            self.webhook_token,
            self.message,
            self.channel,
            self.username,
            self.icon_emoji,
            self.link_names,
            self.proxy
        )
        self.hook.execute()


def get_slack_operator(task_id, message, **context):

    return H1SlackWebhookOperator(
        task_id=task_id,
        http_conn_id=SLACK_CONN_ID,
        webhook_token=SLACK_WEBHOOK_TOKEN,
        message=message,
        username='airflow',
        **context)
