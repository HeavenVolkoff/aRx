# Internal
import typing as T
from asyncio import AbstractEventLoop

# External
from async_tools import wait_with_care
from async_tools.abstract import Loopable
from async_tools.operator import aexit

# Project
from ..stream import SingleStream
from .observe import observe
from ..abstract import Observable
from ..disposable import CompositeDisposable

__all__ = ("concat",)


# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")
M = T.TypeVar("M")


def concat(
    a: Observable[K], b: Observable[L], *, loop: T.Optional[AbstractEventLoop] = None
) -> Observable[T.Union[K, L]]:
    if loop is None:
        if isinstance(a, Loopable):
            loop = a.loop
        elif isinstance(b, Loopable):
            loop = b.loop

    sink: SingleStream[T.Any] = SingleStream(loop=loop)

    a_dispose = None
    b_dispose = None
    try:
        a_dispose = observe(a, sink)
        b_dispose = observe(b, sink)
    except Exception:
        # This dispose the observations if any exception occurs
        disposables = []
        if a_dispose:
            disposables.append(a_dispose)
        if b_dispose:
            disposables.append(b_dispose)

        sink.loop.create_task(wait_with_care(*(aexit(disposable) for disposable in disposables)))

        raise

    return sink
