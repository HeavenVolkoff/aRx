# Internal
from abc import ABCMeta, abstractmethod

# Project
from .observer import Observer
from .disposable import Disposable


class Observable(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    async def __aobserve__(self, observer: Observer) -> Disposable:
        raise NotImplemented()
