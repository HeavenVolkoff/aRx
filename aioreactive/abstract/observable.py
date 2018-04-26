from abc import ABCMeta, abstractmethod


class Observable(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def __observe__(self, observer):
        raise NotImplemented()


class AsyncObservable(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    async def __aobserve__(self, observer):
        raise NotImplemented()
