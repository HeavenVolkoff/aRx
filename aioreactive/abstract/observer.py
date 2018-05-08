# Internal
import typing as T

from abc import ABCMeta, abstractmethod
from asyncio import Future, AbstractEventLoop

K = T.TypeVar("K")


class Observer(Future, T.Generic[K], metaclass=ABCMeta):
    """An async observer abstract base class.

    Both a future and async observer.
    The future resolves with the value passed to close.
    """

    __slots__ = ("keep_alive", )

    def __init__(self, *, keep_alive: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.keep_alive = keep_alive

    @property
    def loop(self) -> AbstractEventLoop:
        return self._loop

    @abstractmethod
    async def asend(self, value: K) -> None:
        raise NotImplemented()

    @abstractmethod
    async def araise(self, ex: Exception) -> bool:
        raise NotImplemented()

    @abstractmethod
    async def aclose(self) -> None:
        raise NotImplemented()

    @abstractmethod
    async def __asend__(self, value: K) -> None:
        raise NotImplemented()

    @abstractmethod
    async def __araise__(self, ex: Exception) -> bool:
        raise NotImplemented()

    @abstractmethod
    async def __aclose__(self) -> None:
        raise NotImplemented()
