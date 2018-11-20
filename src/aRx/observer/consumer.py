__all__ = ("Consumer", "consume")


# Internal
import typing as T
from uuid import UUID

# External
from prop import Promise

# Project
from ..abstract.observer import Observer
from ..abstract.observable import Observable, observe

# Generic Types
K = T.TypeVar("K")


class Consumer(Observer[K, K]):
    async def __asend__(self, value: K) -> None:
        self.resolve(value)

    async def __araise__(self, exc: Exception, namespace: UUID) -> bool:
        return True

    async def __aclose__(self) -> None:
        pass


def consume(observable: Observable[K]) -> Promise[K]:
    """Consume an :class:`~.Observable` as a Promise.

    Arguments:
        observable: Observable to be consumed.

    Returns:
        Promise to be resolved with consumer initial outputted data.

    """
    consumer: Consumer[K] = Consumer()
    observe(observable, consumer)
    return consumer
