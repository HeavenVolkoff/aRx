__all__ = ("Take", "take_op")

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


class _TakeSink(SingleStream[K]):
    def __init__(self, count: int, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)

        self._count = abs(count)
        self._reverse_queue: T.Optional[T.Deque[K]] = (
            deque(maxlen=self._count) if count < 0 else None
        )

    async def __asend__(self, value: K) -> None:
        if self._reverse_queue is None:
            if self._count > 0:
                self._count -= 1
                awaitable: T.Awaitable[T.Any] = super().__asend__(value)
            else:
                awaitable = self.aclose()

            # Remove reference early to avoid keeping large objects in memory
            del value

            await awaitable
        else:
            self._reverse_queue.append(value)

    async def __aclose__(self) -> None:
        while self._reverse_queue:
            await super().__asend__(self._reverse_queue.popleft())

        return await super().__aclose__()


class Take(Observable[K]):
    def __init__(self, count: int, source: Observable[K], **kwargs: T.Any) -> None:
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

    def __observe__(self, observer: Observer[K, T.Any]) -> CompositeDisposable:
        sink: _TakeSink[K] = _TakeSink(self._count, loop=observer.loop)
        with dispose_sink(sink):
            return CompositeDisposable(
                observe(self._source, sink), observe(sink, observer), loop=observer.loop
            )


def take_op(count: int) -> T.Callable[[Observable[K]], Take[K]]:
    """Partial implementation of :class:`~.Take` to be used with operator semantics.

    Returns:
        Partial implementation of Take.

    """
    return T.cast(T.Callable[[Observable[K]], Take[K]], partial(Take, count))
