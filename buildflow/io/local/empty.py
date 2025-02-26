import dataclasses

from buildflow.config.cloud_provider_config import LocalOptions
from buildflow.core.credentials.empty_credentials import EmptyCredentials
from buildflow.core.utils import uuid
from buildflow.io.local.strategies.empty_strategies import EmptySink
from buildflow.io.primitive import LocalPrimtive


@dataclasses.dataclass
class Empty(LocalPrimtive):
    def primitive_id(self):
        return uuid()

    @classmethod
    def from_local_options(
        cls,
        local_options: LocalOptions,
    ) -> "Empty":
        return cls()

    def sink(self, credentials: EmptyCredentials) -> EmptySink:
        return EmptySink(credentials)
