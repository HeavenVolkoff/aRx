from asyncio import Task

from aioreactive.abstract import Observable, Observer, Disposable
from aioreactive.disposable import AnonymousDisposable


class Empty(Observable):
    async def __aobserve__(self, observer: Observer) -> Disposable:
        """Start streaming."""

        task = observer.loop.create_task(observer.aclose())  # type: Task

        async def dispose():
            task.cancel()

        return AnonymousDisposable(dispose)


def empty() -> Observable:
    """Returns an empty source sequence.

    1 - xs = empty()

    Returns a source sequence with no items."""

    return Empty()
