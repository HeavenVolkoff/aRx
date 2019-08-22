# Internal
import typing as T
from asyncio import Future

# External
from aRx.abstract.namespace import Namespace

# Project
from ..abstract.observer import Observer
from ..operation.observe import observe
from ..abstract.observable import Observable

# Generic Types
K = T.TypeVar("K")


class ConsumerExit(Exception):
    pass


class Consumer(Observer[K]):
    def __init__(self, **kwargs: T.Any) -> None:
        super().__init__(keep_alive=False, **kwargs)

        self.result: "Future[K]" = self.loop.create_future()

    async def __asend__(self, value: K, _: Namespace) -> None:
        if self.result.done():
            return

        self.result.set_result(value)

        # Use exception as shorthand for closing consumer
        raise ConsumerExit

    async def __araise__(self, exc: Exception, __: Namespace) -> bool:
        if not self.result.done():
            self.result.set_exception(exc)
        return True

    async def __aclose__(self) -> None:
        self.result.cancel()


async def consume(observable: Observable[K]) -> K:
    """Consume an :class:`~.Observable` as a Promise.

    Arguments:
        observable: Observable to be consumed.

    Returns:
        Promise to be resolved with consumer initial outputted data.

    """
    consumer: Consumer[K] = Consumer()
    async with observe(observable, consumer):
        return await consumer.result


__all__ = ("consume",)
