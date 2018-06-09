# Internal
from asyncio import Task

# Project
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable import AnonymousDisposable


class Empty(Observable):
    """Observable that is empty and will close as soon as possible."""

    async def __aobserve__(self, observer: Observer) -> Disposable:
        task = observer.loop.create_task(observer.aclose())  # type: Task

        async def dispose():
            task.cancel()

        return AnonymousDisposable(dispose)
