__all__ = ("Empty",)

from ..disposable import AnonymousDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable
from ..abstract.observable import Observable


class Empty(Observable):
    """Observable that doesn't output data and closes as soon as possible."""

    def __observe__(self, observer: Observer) -> Disposable:
        if not (observer.closed or observer.keep_alive):
            observer.loop.create_task(observer.aclose())

        return AnonymousDisposable()
