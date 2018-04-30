# Internal
import typing as T

from abc import ABCMeta, abstractmethod

K = T.TypeVar("K")


class Observer(T.Generic[K], metaclass=ABCMeta):
    """An async observer abstract base class.

    Both a future and async observer.
    The future resolves with the value passed to close.
    """

    __slots__ = ()

    @abstractmethod
    async def __asend__(self, value: K) -> None:
        raise NotImplemented()

    @abstractmethod
    async def __araise__(self, error: Exception) -> None:
        raise NotImplemented()

    @abstractmethod
    async def __aclose__(self) -> None:
        raise NotImplemented()
