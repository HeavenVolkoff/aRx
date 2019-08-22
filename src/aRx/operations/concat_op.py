# Internal
import typing as T
from asyncio import AbstractEventLoop

# External
from async_tools.abstract import Loopable

# Project
from ..streams import SingleStream
from ..protocols import ObservableProtocol
from .dispose_op import dispose
from .observe_op import observe
from ..observables import Observable

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")
M = T.TypeVar("M")


async def concat(
    a: ObservableProtocol[K],
    b: ObservableProtocol[L],
    *,
    loop: T.Optional[AbstractEventLoop] = None,
) -> Observable[T.Union[K, L]]:
    if loop is None:
        if isinstance(a, Loopable):
            loop = a.loop
        elif isinstance(b, Loopable):
            loop = b.loop

    sink: SingleStream[T.Any] = SingleStream(loop=loop)

    try:
        await observe(a, sink)
        await observe(b, sink)
    except Exception:
        await dispose(a, sink)
        await dispose(b, sink)

        raise

    return sink


__all__ = ("concat",)
