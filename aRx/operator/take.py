__all__ = ("Take", "take")

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

K = T.TypeVar('T')


class Take(Observable):
    class _TakeSink(SingleStream[K]):

        __slots__ = ("_count", "_reverse_queue")

        def __init__(self, count: int, **kwargs) -> None:
            super().__init__(**kwargs)

            self._count = abs(count)
            self._reverse_queue = (
                deque(maxlen=self._count) if count < 0 else None
            )  # type: T.Optional[T.Deque[K]]

        async def __aclose__(self) -> None:
            if self._reverse_queue is not None:
                # TODO: Don't hold values in memory more than necessary
                for value in self._reverse_queue:
                    await super().asend(value)

                self._reverse_queue.clear()

            return await super().__aclose__()

        async def __asend__(self, value: K) -> None:
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

    __slots__ = ("_count", "_source")

    def __init__(self, count: int, source: Observable, **kwargs) -> None:
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

    def __observe__(self, observer: Observer[K]) -> Disposable:
        sink = self._TakeSink(self._count)

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def take(count: int) -> T.Callable[[], Take]:
    """Partial implementation of :class:`~.Take` to be used with operator semantics.

    Returns:
        Partial implementation of Take.

    """
    return partial(Take, count)
