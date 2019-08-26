# Internal
import typing as T
from asyncio import CancelledError

# External
from async_tools.abstract import Loopable

# Project
from .observe_op import observe

if T.TYPE_CHECKING:
    # Internal
    from asyncio import AbstractEventLoop

    # Project
    from ..protocols import ObservableProtocol
    from ..observables import Observable

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")
M = T.TypeVar("M")


async def concat(
    a: "ObservableProtocol"[K],
    b: "ObservableProtocol"[L],
    *,
    loop: T.Optional["AbstractEventLoop"] = None,
) -> "Observable"[T.Union[K, L]]:
    # Project
    from ..streams import SingleStream

    if loop is None:
        if isinstance(a, Loopable):
            loop = a.loop
        elif isinstance(b, Loopable):
            loop = b.loop

    sink: SingleStream[T.Any] = SingleStream(loop=loop)

    observation = await observe(a, sink)

    try:
        await observe(b, sink)
    except CancelledError:
        raise
    except Exception:
        await observation.dispose()
        raise

    return sink


__all__ = ("concat",)
