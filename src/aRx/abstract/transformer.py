# Internal
import typing as T

# External
from async_tools.abstract import AsyncABCMeta

# Project
from .observer import Observer
from .observable import Observable

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


class Transformer(Observer[K], Observable[L], metaclass=AsyncABCMeta):
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
