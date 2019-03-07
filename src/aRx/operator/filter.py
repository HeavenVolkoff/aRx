__all__ = ("Filter", "filter_op")

# Internal
import typing as T
from functools import partial

# External
from async_tools import attempt_await

# Project
from ..disposable import CompositeDisposable
from ..misc.namespace import Namespace
from ..abstract.observer import Observer
from ..misc.dispose_sink import dispose_sink
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L", bound=T.AsyncContextManager[T.Any])


class _FilterSink(SingleStream[K]):
    @T.overload
    def __init__(
        self, predicate: T.Callable[[K, int], T.Awaitable[bool]], **kwargs: T.Any
    ) -> None:
        ...

    @T.overload
    def __init__(self, predicate: T.Callable[[K, int], bool], **kwargs: T.Any) -> None:
        ...

    def __init__(self, predicate: T.Callable[[K, int], T.Any], **kwargs: T.Any) -> None:
        super().__init__(**kwargs)

        self._index = 0
        self._predicate = predicate

    async def __asend__(self, value: K, namespace: Namespace) -> None:
        index = self._index
        self._index += 1

        if await attempt_await(self._predicate(value, index), self.loop):
            res = super().__asend__(value, namespace)

            # Remove reference early to avoid keeping large objects in memory
            del value

            await res


class Filter(Observable[K, CompositeDisposable]):
    """Observable that output filtered data from another observable source."""

    @T.overload
    def __init__(
        self,
        predicate: T.Callable[[K, int], T.Awaitable[bool]],
        source: Observable[K, L],
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self, predicate: T.Callable[[K, int], bool], source: Observable[K, L], **kwargs: T.Any
    ) -> None:
        ...

    def __init__(
        self, predicate: T.Callable[[K, int], T.Any], source: Observable[K, L], **kwargs: T.Any
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
            return CompositeDisposable(observe(self._source, sink), observe(sink, observer))


@T.overload
def filter_op(
    predicate: T.Callable[[K, int], T.Awaitable[bool]]
) -> T.Callable[[Observable[K, L]], Filter[K]]:
    ...


@T.overload
def filter_op(predicate: T.Callable[[K, int], bool]) -> T.Callable[[Observable[K, L]], Filter[K]]:
    ...


def filter_op(predicate: T.Callable[[K, int], T.Any]) -> T.Callable[[Observable[K, L]], Filter[K]]:
    """Partial implementation of :class:`~.Filter` to be used with operator semantics.

    Returns:
        Return partial implementation of Filter

    """
    return T.cast(T.Callable[[Observable[K, L]], Filter[K]], partial(Filter, predicate))
