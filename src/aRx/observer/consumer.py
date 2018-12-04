__all__ = ("Consumer", "consume")


# Internal
import typing as T

# External
from prop import Promise

# Project
from ..misc.namespace import Namespace
from ..abstract.observer import Observer
from ..abstract.observable import Observable, observe

# Generic Types
K = T.TypeVar("K")


class Consumer(Observer[K, K]):
    async def __asend__(self, value: K, namespace: Namespace) -> None:
        self.resolve(value)

    async def __araise__(self, exc: Exception, namespace: Namespace) -> bool:
        return True

    async def __aclose__(self) -> None:
        pass


async def consume(observable: Observable[K]) -> K:
    """Consume an :class:`~.Observable` as a Promise.

    Arguments:
        observable: Observable to be consumed.

    Returns:
        Promise to be resolved with consumer initial outputted data.

    """
    consumer: Consumer[K] = Consumer()
    async with observe(observable, consumer):
        return await consumer
