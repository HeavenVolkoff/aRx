__all__ = ("Empty", )

# Internal
from asyncio import Task

# Project
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable import AnonymousDisposable


class Empty(Observable):
    """Observable that doesn't output data and closes as soon as possible."""

    __slots__ = ()

    def __observe__(self, observer: Observer) -> Disposable:
        """Register a call to observable `close`_ on loop."""
        task = observer.loop.create_task(observer.aclose())  # type: Task

        async def dispose():
            task.cancel()

        return AnonymousDisposable(dispose)
