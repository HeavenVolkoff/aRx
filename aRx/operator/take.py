__all__ = ("Take", "take_op")

import typing as T
from functools import partial
from collections import deque

from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable, adispose
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

K = T.TypeVar("K")


class _TakeSink(SingleStream[K, K]):
    def __init__(self, count: int, **kwargs) -> None:
        super().__init__(**kwargs)

        self._count = abs(count)
        self._reverse_queue: T.Optional[T.Deque[K]] = (
            deque(maxlen=self._count) if count < 0 else None
        )

    async def __aclose__(self):
        if self._reverse_queue is not None:
            # TODO: Don't hold values in memory more than necessary
            for value in self._reverse_queue:
                await super().asend(value)

            self._reverse_queue.clear()

        return await super().__aclose__()

    async def __asend__(self, value: K):
        if self._reverse_queue is None:
            if self._count > 0:
                self._count -= 1
                awaitable = super().__asend__(value)
            else:
                awaitable = self.aclose()

            # Remove reference early to avoid keeping large objects in memory
            del value

            await awaitable
        else:
            self._reverse_queue.append(value)


class Take(Observable[K]):
    def __init__(self, count: int, source: Observable[K], **kwargs) -> None:
        """Take constructor.

        .. Note::

            If count is positive values are taken from the first elements
            outputted by source.
            If count is negative values are taken from the last elements
            outputted by source.

        .. Warning::

            If in reverse mode, this observable only outputs data after source
            observable has closed.

        Arguments:
            count: Quantity of data to skip.
            source: Observable source.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)

        self._count = count
        self._source = source

    def __observe__(self, observer: Observer[K, T.Any]) -> Disposable:
        sink: _TakeSink[K] = _TakeSink(self._count, loop=observer.loop)

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down, loop=observer.loop)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink, loop=observer.loop))
            raise exc


def take_op(count: int) -> T.Callable[[Observable[K]], Take]:
    """Partial implementation of :class:`~.Take` to be used with operator semantics.

    Returns:
        Partial implementation of Take.

    """
    return T.cast(T.Callable[[Observable[K]], Take], partial(Take, count))
