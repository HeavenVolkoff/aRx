# Internal
import typing as T

# External
import typing_extensions as Te

# External
from aRx.namespace import Namespace

# Project
from .observer_protocol import ObserverProtocol
from .observable_protocol import ObservableProtocol

# Generic Types
K = T.TypeVar("K", contravariant=True)
L = T.TypeVar("L", covariant=True)


@Te.runtime
class TransformerProtocol(ObservableProtocol[L], ObserverProtocol[K], Te.Protocol[K, L]):
    """Transformer abstract class.

    Base class for defining an object that is an Observer and Observable at the same time,
    in other words something through which data is inputted, transformed and outputted.

               ▄▄▄▄▄▄▄▄▄
            ▄█████████████▄
    █████  █████████████████  █████
    ▐████▌ ▀███▄       ▄███▀ ▐████▌
     █████▄  ▀███▄   ▄███▀  ▄█████
     ▐██▀███▄  ▀███▄███▀  ▄███▀██▌
      ███▄▀███▄  ▀███▀  ▄███▀▄███
      ▐█▄▀█▄▀███ ▄ ▀ ▄ ███▀▄█▀▄█▌
       ███▄▀█▄██ ██▄██ ██▄█▀▄███
        ▀███▄▀██ █████ ██▀▄███▀
       █▄ ▀█████ █████ █████▀ ▄█
       ███        ███        ███
       ███▄    ▄█ ███ █▄    ▄███
       █████ ▄███ ███ ███▄ █████
       █████ ████ ███ ████ █████
       █████ ████ ███ ████ █████
       █████ ████ ███ ████ █████
       █████ ████▄▄▄▄▄████ █████
        ▀███ █████████████ ███▀
          ▀█ ███ ▄▄▄▄▄ ███ █▀
             ▀█▌▐█████▌▐█▀
                ███████
    """

    keep_alive: bool
    """Flag that indicates the default behaviour on whether or not the observers should be closed on
        observation disposition.
    """

    @property
    def closed(self) -> bool:
        ...

    async def asend(self, data: K, namespace: T.Optional[Namespace] = None) -> None:
        ...

    async def athrow(self, main_exc: Exception, namespace: T.Optional[Namespace] = None) -> None:
        ...

    async def aclose(self) -> bool:
        ...

    async def __observe__(self, observer: ObserverProtocol[L]) -> None:
        ...

    async def __dispose__(self, observer: ObserverProtocol[L]) -> None:
        ...
