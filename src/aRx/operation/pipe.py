# Internal
import typing as T

# External
from async_tools import wait_with_care
from aRx.abstract import Observer, Observable, Transformer
from aRx.disposable import CompositeDisposable
from async_tools.operator import aexit

# Project
from .observe import observe

K = T.TypeVar("K")
L = T.TypeVar("L")


def pipe(
    source: Observable[K], transformer: Transformer[K, L], sink: Observer[L]
) -> T.AsyncContextManager[None]:
    """Pipe data from a source through a transformer to a sink.

    A simple data flow chart would be:
    data ‐→ source ‐‐(data)‐→ transformer ‐‐(data')‐→ sink

    For more info see: :func:`~.observe.observe`

    Arguments:
        source: Data source.
        transformer: Data transformation.
        sink: Data sink

    Returns:
        Async context manager that dispel the piping.
    """
    in_disposable = None
    out_disposable = None
    try:
        in_disposable = observe(source, transformer)
        out_disposable = observe(transformer, sink)

        return CompositeDisposable(in_disposable, out_disposable)
    except Exception:
        # This dispose the observations if any exception occurs
        disposables = []
        if in_disposable:
            disposables.append(in_disposable)
        if out_disposable:
            disposables.append(out_disposable)

        transformer.loop.create_task(
            wait_with_care(*(aexit(disposable) for disposable in disposables))
        )

        raise
