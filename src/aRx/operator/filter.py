__all__ = ("Filter", "filter_op")

# Internal
import typing as T
from asyncio import iscoroutinefunction
from functools import partial

# Project
from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..misc.dispose_sink import dispose_sink
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

# Generic Types
K = T.TypeVar("K")


class _FilterSink(SingleStream[K]):
    def __init__(
        self, predicate: T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]], **kwargs: T.Any
    ) -> None:
        super().__init__(**kwargs)

        self._index = 0
        self._predicate = predicate

    async def __asend__(self, value: K) -> None:
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


class Filter(Observable[K]):
    """Observable that output filtered data from another observable source."""

    def __init__(
        self,
        predicate: T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]],
        source: Observable[K],
        **kwargs: T.Any,
    ) -> None:
        """Filter constructor.

        Arguments:
            predicate: Predicate to filter source.
            source: Observable source.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # Internal
        self._source = source
        self._predicate = predicate

    def __observe__(self, observer: Observer[K, T.Any]) -> CompositeDisposable:
        sink: _FilterSink[K] = _FilterSink(self._predicate, loop=observer.loop)
        with dispose_sink(sink):
            return CompositeDisposable(
                observe(self._source, sink), observe(sink, observer)
            )


def filter_op(
    predicate: T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]]
) -> T.Callable[[Observable[K]], Filter[K]]:
    """Partial implementation of :class:`~.Filter` to be used with operator semantics.

    Returns:
        Return partial implementation of Filter

    """
    return T.cast(T.Callable[[Observable[K]], Filter[K]], partial(Filter, predicate))
