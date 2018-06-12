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
    class _Sink(SingleStream[K]):
        def __init__(self, count: int, **kwargs) -> None:
            super().__init__(**kwargs)

            self._count = abs(count)
            self._reverse_queue = deque() \
                if count <= 0 else None  # type: T.Optional[T.Deque[K]]

        async def __aclose__(self) -> None:
            if self._reverse_queue:
                # Send take values on close
                for value in self._reverse_queue:
                    await super().__asend__(value)

                self._reverse_queue = None

            return await super().__aclose__()

        async def __asend__(self, value: K) -> None:
            if self._count > 0:
                self._count -= 1

                if self._reverse_queue:
                    self._reverse_queue.append(value)
                else:
                    await super().__asend__(value)
            else:
                if self._reverse_queue:
                    self._reverse_queue.append(value)
                    self._reverse_queue.popleft()
                else:
                    await super().aclose()

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

        Args:
            count: Quantity of data to skip.
            source: Observable source.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)

        self._count = count
        self._source = source

    def __observe__(self, observer: Observer[K]) -> Disposable:
        sink = self._Sink(self._count)

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def take(count: int) -> partial[Take]:
    """Partial implementation of `Take`_ to be used with operator semantics.

    Returns:
        Partial implementation of Take.

    .. _Take::

        :class:`Take`.
    """
    return partial(Take, count)
