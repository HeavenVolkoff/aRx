__all__ = ("Filter", "filter")

import typing as T
from asyncio import iscoroutinefunction
from functools import partial

from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable, adispose
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

K = T.TypeVar("K")
FilterCallable = T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]]


class Filter(Observable):
    """Observable that output filtered data from another observable source."""

    class _FilterSink(SingleStream[K]):
        def __init__(self, predicate: FilterCallable, **kwargs) -> None:
            super().__init__(**kwargs)

            self._index = 0
            self._predicate = predicate

        async def __asend__(self, value: K) -> None:
            index = self._index
            self._index += 1

            is_accepted = self._predicate(value, index)

            if iscoroutinefunction(self._predicate):
                is_accepted = await is_accepted

            if is_accepted:
                res = super().__asend__(value)

                # Remove reference early to avoid keeping large objects in memory
                del value

                await res

    def __init__(self, predicate: FilterCallable, source: Observable, **kwargs) -> None:
        """Filter constructor.

        Arguments:
            predicate: Predicate to filter source.
            source: Observable source.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._source = source
        self._predicate = predicate

    def __observe__(self, observer: Observer) -> Disposable:
        sink = self._FilterSink(self._predicate)

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def filter(predicate: FilterCallable) -> T.Callable[[], Filter]:
    """Partial implementation of :class:`~.Filter` to be used with operator semantics.

    Returns:
        Return partial implementation of Filter

    """
    return partial(Filter, predicate)
