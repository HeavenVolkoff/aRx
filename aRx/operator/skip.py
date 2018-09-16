__all__ = ("Skip", "skip_op")

import typing as T
from functools import partial
from collections import deque

from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable, adispose
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

K = T.TypeVar("K")


class _SkipSink(SingleStream[K, K]):
    def __init__(self, count: int, **kwargs) -> None:
        super().__init__(**kwargs)

        self._count = abs(count)
        self._reverse_queue: T.Optional[T.Deque[K]] = (
            deque(maxlen=self._count) if count < 0 else None
        )

    async def __aclose__(self):
        if self._reverse_queue is not None:
            self._reverse_queue.clear()

        return await super().__aclose__()

    async def __asend__(self, value: K):
        if self._reverse_queue is not None:
            value = self._reverse_queue[0]
            self._reverse_queue.append(value)
        elif self._count > 0:
            self._count -= 1
            return

        awaitable = super().__asend__(value)

        # Remove reference early to avoid keeping large objects in memory
        del value

        await awaitable


class Skip(Observable[K]):
    """Observable that outputs data from source skipping some."""

    def __init__(self, count: int, source: Observable[K], **kwargs) -> None:
        """Skip constructor.

        .. Note::

            If count is positive values are skipped from the first elements
            outputted by source.
            If count is negative values are skipped from the last elements
            outputted by source.

        Arguments:
            count: Quantity of data to skip.
            source: Observable source.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)

        self._count = count
        self._source = source

    def __observe__(self, observer: Observer[K, T.Any]) -> Disposable:
        sink: _SkipSink[K] = _SkipSink(self._count)

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down, loop=observer.loop)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink, loop=observer.loop))
            raise exc


def skip_op(count: int) -> T.Callable[[Observable[K]], Skip]:
    """Partial implementation of :class:`~.Skip` to be used with operator semantics.

    Returns:
        Partial implementation of Skip.

    """
    return T.cast(T.Callable[[Observable[K]], Skip], partial(Skip, count))
