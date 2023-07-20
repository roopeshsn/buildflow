from typing import Optional, Type

import pulumi
import pulumi_gcp

from buildflow.core.credentials import GCPCredentials
from buildflow.core.providers.provider import (
    PulumiProvider,
    SinkProvider,
)
from buildflow.core.types.gcp_types import GCPProjectID, GCSBucketName, GCPRegion
from buildflow.core.resources.pulumi import PulumiResource

from buildflow.core.io.gcp.strategies.storage_strategies import GCSBucketSink


class GCSBucketProvider(SinkProvider, PulumiProvider):
    def __init__(
        self,
        *,
        project_id: GCPProjectID,
        bucket_name: GCSBucketName,
        bucket_region: GCPRegion,
        # sink-only options
        # pulumi-only options
    ):
        self.project_id = project_id
        self.bucket_name = bucket_name
        self.bucket_region = bucket_region
        # sink-only options
        # pulumi-only options

    def sink(self, credentials: GCPCredentials):
        return GCSBucketSink(
            credentials=credentials,
            project_id=self.project_id,
            bucket_name=self.bucket_name,
        )

    def pulumi_resources(self, type_: Optional[Type]):
        del type_
        bucket_resource_id = f"{self.project_id}-{self.bucket_name}"
        bucket_resource = pulumi_gcp.storage.Bucket(
            resource_name=bucket_resource_id,
            name=self.bucket_name,
            location=self.bucket_region,
            project=self.project_id,
        )
        pulumi.export("gcp.storage.bucket_id", bucket_resource_id)
        return [
            PulumiResource(
                resource_id=bucket_resource_id,
                resource=bucket_resource,
                exports={
                    "gcp.storage.bucket_id": bucket_resource_id,
                },
            )
        ]
