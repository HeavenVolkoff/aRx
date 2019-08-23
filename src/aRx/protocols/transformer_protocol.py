# Internal
import typing as T

# External
import typing_extensions as Te

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

    pass
