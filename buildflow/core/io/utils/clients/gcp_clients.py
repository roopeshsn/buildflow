from typing import Optional

from google.cloud import (
    bigquery,
    bigquery_storage_v1,
    monitoring_v3,
    pubsub,
    storage,
)
from google.pubsub_v1.services.publisher import PublisherAsyncClient
from google.pubsub_v1.services.subscriber import SubscriberAsyncClient
from google.cloud.bigquery_storage_v1.services.big_query_write.async_client import (
    BigQueryWriteAsyncClient,
)
from google.api_core import client_options

from buildflow.core.credentials import GCPCredentials


class GCPClients:
    __shared_state = {}

    def __init__(
        self,
        *,
        credentials: GCPCredentials = None,
        quota_project_id: Optional[str] = None,
    ):
        # We use the "borg" design pattern here to share state between instances
        # See: https://code.activestate.com/recipes/66531/
        self.__dict__ = self.__shared_state
        if "creds" in self.__shared_state:
            return
        self.creds = credentials.get_creds()

    def get_storage_client(self, project: str = None) -> storage.Client:
        return storage.Client(credentials=self.creds, project=project)

    def get_bigquery_client(self, project: str = None) -> bigquery.Client:
        return bigquery.Client(credentials=self.creds, project=project)

    def get_bigquery_write_async_client(
        self,
        project: str = None,
    ) -> bigquery_storage_v1.BigQueryWriteClient:
        return BigQueryWriteAsyncClient(
            credentials=self.creds,
            client_options=client_options.ClientOptions(quota_project_id=project),
        )

    def get_bigquery_storage_client(self) -> bigquery_storage_v1.BigQueryReadClient:
        return bigquery_storage_v1.BigQueryReadClient(credentials=self.creds)

    def get_metrics_client(self):
        return monitoring_v3.MetricServiceClient(credentials=self.creds)

    def get_async_subscriber_client(self):
        return SubscriberAsyncClient(credentials=self.creds)

    def get_async_publisher_client(self):
        return PublisherAsyncClient(credentials=self.creds)

    def get_publisher_client(self):
        return pubsub.PublisherClient(credentials=self.creds)

    def get_subscriber_client(self):
        return pubsub.SubscriberClient(credentials=self.creds)
