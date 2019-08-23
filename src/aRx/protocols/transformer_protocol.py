# Internal
import typing as T

# External
import typing_extensions as Te
from async_tools.abstract import AsyncABCMeta

# External
from aRx.namespace import Namespace

# Project
from .observer_protocol import ObserverProtocol
from .observable_protocol import ObservableProtocol

# Generic Types
K = T.TypeVar("K", covariant=True)
L = T.TypeVar("L", contravariant=True)


@Te.runtime
class TransformerProtocol(ObservableProtocol[K], ObserverProtocol[L], Te.Protocol[K, L]):
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

    pass
