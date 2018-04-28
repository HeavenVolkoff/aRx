# Internal
from abc import ABCMeta, abstractmethod

# Project
from .disposable import Disposable, AsyncDisposable


class Observable(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def __observe__(self, observer) -> Disposable:
        raise NotImplemented()


class AsyncObservable(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    async def __aobserve__(self, observer) -> AsyncDisposable:
        raise NotImplemented()
