# Internal
from abc import ABCMeta, abstractmethod

# Project
from .observer import Observer
from .disposable import Disposable


class Observable(object, metaclass=ABCMeta):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    async def __aobserve__(self, observer: Observer) -> Disposable:
        raise NotImplemented()
