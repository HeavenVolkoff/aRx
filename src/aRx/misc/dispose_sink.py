# Internal
import typing as T
from contextlib import contextmanager

# Project
from ..abstract.observer import Observer
from ..abstract.disposable import adispose


@contextmanager
def dispose_sink(sink: Observer[T.Any, T.Any]) -> T.Generator[None, None, None]:
    try:
        yield
    except Exception:
        sink.loop.create_task(adispose(sink))
        raise
