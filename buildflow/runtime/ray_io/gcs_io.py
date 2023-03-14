import dataclasses
import logging
from typing import Any, Dict, List, Optional

from google.api_core import exceptions
from google.cloud import storage

from buildflow.api import io
from buildflow.runtime.ray_io import pubsub_io
from buildflow.runtime.ray_io import pubsub_utils


@dataclasses.dataclass
class GCSFileEvent:
    # Metadata about that action taken.
    metadata: Dict[str, Any]

    @property
    def blob(self) -> bytes:
        if self.metadata['eventType'] == 'OBJECT_DELETE':
            raise ValueError('Can\'t fetch blob for `OBJECT_DELETE` event.')
        client = storage.Client()
        bucket = client.bucket(bucket_name=self.metadata['bucketId'])
        blob = bucket.get_blob(self.metadata['objectId'])
        return blob.download_as_bytes()


@dataclasses.dataclass
class GCSFileNotifications(io.Source):
    bucket_name: str
    project_id: str
    # The pubsub topic that is configured to point at the bucket. If not set
    # we will create one.
    pubsub_topic: str = ''
    # The pubsub subscription that is configure to point at the bucket. If not
    # set we will create one.
    pubsub_subscription: str = ''
    # The event types that should trigger the stream. This is only used if we
    # are attaching a new notification listener to your bucket. Defaults to
    # only new uploads. If set to None will listen to all uploads.
    event_types: Optional[List[str]] = ('OBJECT_FINALIZE', )

    # Internal values to track if the user provide the topics or we are
    # creating them. If the user is providing them we will assume things are
    # configured correctly.
    _managed_subscriber = True
    _managed_publisher = True

    def __post_init__(self):
        if not self.pubsub_topic:
            self.pubsub_topic = f'projects/{self.project_id}/topics/{self.bucket_name}_notifications'  # noqa: E501
            logging.info(
                f'No pubsub topic provided. Defaulting to {self.pubsub_topic}.'
            )
        else:
            self._managed_publisher = False
        if not self.pubsub_subscription:
            self.pubsub_subscription = f'projects/{self.project_id}/subscriptions/{self.bucket_name}_subscriber'  # noqa: E501
            logging.info('No pubsub subscription provided. Defaulting to '
                         f'{self.pubsub_subscription}.')
        else:
            self._managed_subscriber = False

    def setup(self):

        storage_client = storage.Client()
        bucket = None
        try:
            bucket = storage_client.get_bucket(self.bucket_name)
        except exceptions.NotFound:
            print(f'bucket {self.bucket_name} not found attempting to create')
            try:
                print(f'Creating bucket: {self.bucket_name}')
                bucket = storage_client.create_bucket(self.bucket_name,
                                                      project=self.project_id)
            except exceptions.PermissionDenied:
                raise ValueError(
                    f'Failed to create bucket: {self.bucket_name}. Please '
                    'ensure you have permission to read the existing bucket '
                    'or permission to create a new bucket if needed.')

        if self._managed_subscriber:
            gcs_notify_sa = (
                f'serviceAccount:service-{bucket.project_number}@gs-project-accounts.iam.gserviceaccount.com'  # noqa: E501
            )
            pubsub_utils.maybe_create_subscription(
                self.pubsub_subscription,
                self.pubsub_topic,
                publisher_members=[gcs_notify_sa])
        if self._managed_publisher:
            notification_found = False
            try:
                _, _, _, topic_name = self.pubsub_topic.split('/')
                # gotcha 1: have to list through notifications to get the topic
                notifications = bucket.list_notifications()
                for notification in notifications:
                    if (notification.topic_name == topic_name
                            and notification.bucket.name == self.bucket_name):
                        notification_found = True
                        break

            except exceptions.PermissionDenied:
                raise ValueError(
                    'Failed to create bucket notification for bucket: '
                    f'{self.bucket_name}. Please ensure you have permission '
                    'to modify the bucket.')
            if not notification_found:
                print(f'bucket notification for bucket {self.bucket_name} not '
                      'found attempting to create')
                try:
                    print(
                        f'Creating notification for bucket {self.bucket_name}')
                    _, project, _, topic = self.pubsub_topic.split('/')
                    # gotcha 2: you cant pass the full topic path
                    bucket.notification(topic_name=topic,
                                        topic_project=project,
                                        event_types=self.event_types).create()
                except exceptions.PermissionDenied:
                    raise ValueError(
                        'Failed to create bucket notification for bucket: '
                        f'{self.bucket_name}. Please ensure you have '
                        'permission to modify the bucket.')

    def preprocess(self, message: pubsub_io.PubsubMessage) -> GCSFileEvent:
        return GCSFileEvent(metadata=message.attributes)

    def actor(self, ray_sinks):
        return pubsub_io.PubSubSourceActor.remote(
            ray_sinks,
            pubsub_io.PubSubSource(self.pubsub_subscription,
                                   self.pubsub_topic,
                                   include_attributes=True))

    @classmethod
    def is_streaming(cls) -> bool:
        return True
