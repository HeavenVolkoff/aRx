# Internal
import typing as T
from contextlib import contextmanager

# External
from async_tools.adispose import adispose

# Project
from ..abstract.observer import Observer


@contextmanager
def dispose_sink(sink: Observer[T.Any, T.Any]) -> T.Generator[None, None, None]:
    try:
        yield
    except Exception:
        sink.loop.create_task(adispose(sink))
        raise
