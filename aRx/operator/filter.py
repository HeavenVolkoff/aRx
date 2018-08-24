__all__ = ("Filter", "filter_op")

import typing as T
from asyncio import iscoroutinefunction
from functools import partial

from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable, adispose
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

K = T.TypeVar("K")


class Filter(Observable[K]):
    """Observable that output filtered data from another observable source."""

    class _FilterSink(SingleStream[K]):
        def __init__(
            self, predicate: T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]], **kwargs
        ) -> None:
            super().__init__(**kwargs)

            self._index = 0
            self._predicate = predicate

        async def __asend__(self, value: K):
            index = self._index
            self._index += 1

            is_accepted = self._predicate(value, index)

            if iscoroutinefunction(self._predicate):
                is_accepted = await T.cast(T.Awaitable[bool], is_accepted)

            if is_accepted:
                res = super().__asend__(value)

                # Remove reference early to avoid keeping large objects in memory
                del value

                await res

    def __init__(
        self,
        predicate: T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]],
        source: Observable[K],
        **kwargs,
    ) -> None:
        """Filter constructor.

        Arguments:
            predicate: Predicate to filter source.
            source: Observable source.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._source = source
        self._predicate = predicate

    def __observe__(self, observer: Observer[K, T.Any]) -> Disposable:
        sink = self._FilterSink(self._predicate)  # type: Filter._FilterSink[K]

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def filter_op(
    predicate: T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]]
) -> T.Callable[[Observable[K]], Filter]:
    """Partial implementation of :class:`~.Filter` to be used with operator semantics.

    Returns:
        Return partial implementation of Filter

    """
    return T.cast(T.Callable[[Observable[K]], Filter], partial(Filter, predicate))
