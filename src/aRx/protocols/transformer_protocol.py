# Internal
import typing as T

# External
import typing_extensions as Te

# Project
from .observer_protocol import ObserverProtocol
from .observable_protocol import ObservableProtocol

# Generic Types
L = T.TypeVar("L", covariant=True)
K = T.TypeVar("K", contravariant=True)


@Te.runtime
class TransformerProtocol(ObserverProtocol[K], ObservableProtocol[L], Te.Protocol):
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
