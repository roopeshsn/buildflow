import asyncio
from typing import Any, Callable, Iterable, Type

from buildflow.core.options.runtime_options import RuntimeOptions
from buildflow.core.io.utils.schemas import converters
from buildflow.core.strategies.source import AckInfo, PullResponse, SourceStrategy


class PulseSource(SourceStrategy):
    def __init__(
        self,
        *,
        runtime_options: RuntimeOptions,
        items: Iterable[Any],
        pulse_interval_seconds: float,
        backlog_size: int = 0,
    ):
        super().__init__(
            runtime_options=runtime_options, strategy_id="local-pulse-source"
        )
        self.items = items
        self.pulse_interval_seconds = pulse_interval_seconds
        self._to_emit = 0
        self.backlog_size = backlog_size

    def max_batch_size(self) -> int:
        return 1

    async def pull(self) -> PullResponse:
        await asyncio.sleep(self.pulse_interval_seconds)
        item = self.items[self._to_emit]
        self._to_emit += 1
        if self._to_emit == len(self.items):
            self._to_emit = 0
        return PullResponse([item], None)

    def pull_converter(self, user_defined_type: Type) -> Callable[[Any], Any]:
        return converters.identity()

    async def ack(self, to_ack: AckInfo, success: bool):
        pass

    async def backlog(self) -> int:
        return self.backlog_size
