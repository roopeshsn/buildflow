import json
import unittest
from dataclasses import asdict, dataclass

from buildflow.core.options.runtime_options import RuntimeOptions
from buildflow.core.io.gcp.pubsub import GCPPubSubSubscription, GCPPubSubTopic


# TODO: Add tests for PulumiResources. Can reference bigquery_test.py for an example.
class GCPPubsubTest(unittest.TestCase):
    def test_gcp_pubsub_pull_converter_bytes(self):
        pubsub_subscription = GCPPubSubSubscription(
            project_id="project",
            subscription_name="pubsub-sub",
            topic_id="projects/project/topics/pubsub-topic",
        )
        pubsub_source = pubsub_subscription.source_provider().source(
            RuntimeOptions.default()
        )

        input_data = "test".encode("utf-8")
        converter = pubsub_source.pull_converter(type(input_data))
        self.assertEqual(input_data, converter(input_data))

    def test_gcp_pubsub_pull_converter_dataclass(self):
        @dataclass
        class Test:
            a: int

        pubsub_subscription = GCPPubSubSubscription(
            project_id="project",
            subscription_name="pubsub-sub",
            topic_id="projects/project/topics/pubsub-topic",
        )
        pubsub_source = pubsub_subscription.source_provider().source(
            RuntimeOptions.default()
        )

        input_data = Test(a=1)
        bytes_data = json.dumps(asdict(input_data)).encode("utf-8")
        converter = pubsub_source.pull_converter(type(input_data))
        self.assertEqual(input_data, converter(bytes_data))

    def test_gcp_pubsub_pull_converter_none(self):
        pubsub_subscription = GCPPubSubSubscription(
            project_id="project",
            subscription_name="pubsub-sub",
            topic_id="projects/project/topics/pubsub-topic",
        )
        pubsub_source = pubsub_subscription.source_provider().source(
            RuntimeOptions.default()
        )

        input_data = "test".encode("utf-8")
        converter = pubsub_source.pull_converter(None)
        self.assertEqual(input_data, converter(input_data))

    def test_gcp_pubsub_push_converter_bytes(self):
        pubsub_topic = GCPPubSubTopic(project_id="project", topic_name="pubsub-topic")
        pubsub_sink = pubsub_topic.sink_provider().sink(RuntimeOptions.default())

        input_data = "test".encode("utf-8")
        converter = pubsub_sink.push_converter(type(input_data))
        self.assertEqual(input_data, converter(input_data))

    def test_gcp_pubsub_push_converter_dataclass(self):
        @dataclass
        class Test:
            a: int

        pubsub_topic = GCPPubSubTopic(project_id="project", topic_name="pubsub-topic")
        pubsub_sink = pubsub_topic.sink_provider().sink(RuntimeOptions.default())

        input_data = Test(a=1)
        bytes_data = json.dumps(asdict(input_data)).encode("utf-8")
        converter = pubsub_sink.push_converter(type(input_data))
        self.assertEqual(bytes_data, converter(input_data))

    def test_gcp_pubsub_push_converter_none(self):
        pubsub_topic = GCPPubSubTopic(project_id="project", topic_name="pubsub-topic")
        pubsub_sink = pubsub_topic.sink_provider().sink(RuntimeOptions.default())
        input_data = "test".encode("utf-8")
        converter = pubsub_sink.push_converter(None)
        self.assertEqual(input_data, converter(input_data))


if __name__ == "__main__":
    unittest.main()
