__all__ = ("Skip", "skip")

# Internal
import typing as T

from functools import partial
from collections import deque

# Project
from ..stream.single_stream import SingleStream
from ..abstract.observer import Observer
from ..abstract.observable import Observable, observe
from ..abstract.disposable import Disposable, adispose
from ..disposable import CompositeDisposable

K = T.TypeVar('K')


class Skip(Observable):
    """Observable that outputs data from source skipping some."""

    class _SkipSink(SingleStream[K]):
        def __init__(self, count: int, **kwargs) -> None:
            super().__init__(**kwargs)

            self._count = abs(count)
            self._reverse_queue = (
                deque(maxlen=self._count) if count < 0 else None
            )  # type: T.Optional[T.Deque[K]]

        async def __aclose__(self) -> None:
            if self._reverse_queue is not None:
                self._reverse_queue.clear()

            return await super().__aclose__()

        async def __asend__(self, value: K) -> None:
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

    def __init__(self, count: int, source: Observable, **kwargs) -> None:
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

    def __observe__(self, observer: Observer[K]) -> Disposable:
        sink = self._SkipSink(self._count)

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def skip(count: int) -> T.Callable[[], Skip]:
    """Partial implementation of :class:`~.Skip` to be used with operator semantics.

    Returns:
        Partial implementation of Skip.

    """
    return partial(Skip, count)
