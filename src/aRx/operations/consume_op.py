# Internal
import typing as T

# Project
from ..operations.observe_op import observe
from ..protocols.observable_protocol import ObservableProtocol

# Generic Types
K = T.TypeVar("K")


@T.overload
async def consume(observable: ObservableProtocol[K]) -> K:
    ...


@T.overload
async def consume(observable: T.Awaitable[ObservableProtocol[K]]) -> K:
    ...


async def consume(observable: T.Any) -> K:
    """Consume an :class:`~.Observable` as a Promise.

    Arguments:
        observable: Observable to be consumed.

    Returns:
        Promise to be resolved with consumer initial outputted data.

    """
    consumer: Consumer[K] = Consumer()
    async with await observe(observable, consumer):
        return await consumer.result


__all__ = ("consume",)
