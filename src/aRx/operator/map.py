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

__all__ = ("Map", "map_op")


# Generic Types
J = T.TypeVar("J")
K = T.TypeVar("K")
L = T.TypeVar("L", bound=T.AsyncContextManager[T.Any])


class _MapSink(T.Generic[J, K], SingleStream[K]):
    @T.overload
    def __init__(self, mapper: T.Callable[[J, int], T.Awaitable[K]], **kwargs: T.Any) -> None:
        ...

    @T.overload
    def __init__(self, mapper: T.Callable[[J, int], K], **kwargs: T.Any) -> None:
        ...

    def __init__(self, mapper: T.Callable[[J, int], T.Any], **kwargs: T.Any) -> None:
        super().__init__(**kwargs)

        self._index = 0
        self._mapper = mapper

    async def __asend__(self, value: J, namespace: Namespace) -> None:
        index = self._index
        self._index += 1

        result = attempt_await(self._mapper(value, index), self.loop)

        # Remove reference early to avoid keeping large objects in memory
        del value

        awaitable = super().__asend__(await result, namespace)

        del result

        await awaitable


class Map(T.Generic[J, K], Observable[K, CompositeDisposable]):
    """Observable that outputs transmuted data from an observable source."""

    @T.overload
    def __init__(
        self,
        mapper: T.Callable[[J, int], T.Awaitable[K]],
        source: Observable[J, L],
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self, mapper: T.Callable[[J, int], K], source: Observable[J, L], **kwargs: T.Any
    ) -> None:
        ...

    def __init__(
        self, mapper: T.Callable[[J, int], T.Any], source: Observable[J, L], **kwargs: T.Any
    ) -> None:
        """Map constructor.

        Arguments:
            mapper: Transmutation function.
            source: Observable source.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._mapper = mapper
        self._source = source

    def __observe__(self, observer: Observer[K, T.Any]) -> CompositeDisposable:
        sink: _MapSink[J, K] = _MapSink(self._mapper, loop=observer.loop)
        with dispose_sink(sink):
            return CompositeDisposable(
                observe(self._source, T.cast(SingleStream[J], sink)), observe(sink, observer)
            )


@T.overload
def map_op(
    mapper: T.Callable[[J, int], T.Awaitable[K]]
) -> T.Callable[[Observable[J, L]], Map[J, K]]:
    ...


@T.overload
def map_op(mapper: T.Callable[[J, int], K]) -> T.Callable[[Observable[J, L]], Map[J, K]]:
    ...


def map_op(mapper: T.Callable[[J, int], T.Any]) -> T.Callable[[Observable[J, L]], Map[J, T.Any]]:
    """Partial implementation of :class:`~.Map` to be used with operator semantics.

    Returns:
        Partial implementation of Map

    """
    return T.cast(T.Callable[[Observable[J, L]], Map[J, K]], partial(Map, mapper))
