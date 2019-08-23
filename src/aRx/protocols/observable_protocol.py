# Internal
import typing as T
from abc import abstractmethod

# External
import typing_extensions as Te

# Project
from .observer_protocol import ObserverProtocol

K = T.TypeVar("K", covariant=True)


class ObservableProtocol(Te.Protocol[K]):
    async def __observe__(self, observer: ObserverProtocol[K]) -> None:
        ...

    async def __dispose__(self, observer: ObserverProtocol[K]) -> None:
        ...
