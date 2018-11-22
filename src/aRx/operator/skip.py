__all__ = ("Skip", "skip_op")

# Internal
import typing as T
from functools import partial
from collections import deque

# Project
from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..misc.dispose_sink import dispose_sink
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

# Generic Types
K = T.TypeVar("K")


class _SkipSink(SingleStream[K]):
    def __init__(self, count: int, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)

        self._count = abs(count)
        self._reverse_queue: T.Optional[T.Deque[K]] = (
            deque(maxlen=self._count) if count < 0 else None
        )

    async def __asend__(self, value: K) -> None:
        if self._reverse_queue is not None:
            # Skip values from end
            value = self._reverse_queue[0]
            self._reverse_queue.append(value)
        elif self._count > 0:
            # Skip values from start
            self._count -= 1
            return

        awaitable = super().__asend__(value)

        # Remove reference early to avoid keeping large objects in memory
        del value

        await awaitable

    async def __aclose__(self) -> None:
        if self._reverse_queue is not None:
            self._reverse_queue.clear()

        await super().__aclose__()


class Skip(Observable[K]):
    """Observable that outputs data from source skipping some."""

    def __init__(self, count: int, source: Observable[K], **kwargs: T.Any) -> None:
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

    def __observe__(self, observer: Observer[K, T.Any]) -> CompositeDisposable:
        sink: _SkipSink[K] = _SkipSink(self._count, loop=observer.loop)
        with dispose_sink(sink):
            return CompositeDisposable(
                observe(self._source, sink), observe(sink, observer)
            )


def skip_op(count: int) -> T.Callable[[Observable[K]], Skip[K]]:
    """Partial implementation of :class:`~.Skip` to be used with operator semantics.

    Returns:
        Partial implementation of Skip.

    """
    return T.cast(T.Callable[[Observable[K]], Skip[K]], partial(Skip, count))
