__all__ = ("Empty",)

# Internal
import typing as T

# Project
from ..disposable import AnonymousDisposable
from ..abstract.observer import Observer
from ..abstract.observable import Observable


class Empty(Observable[None]):
    """Observable that doesn't output data and closes any observer as soon as possible."""

    def __observe__(self, observer: Observer[T.Any], keep_alive: bool) -> AnonymousDisposable:
        if not (observer.closed or keep_alive):
            observer.loop.create_task(observer.aclose())

        return AnonymousDisposable()
