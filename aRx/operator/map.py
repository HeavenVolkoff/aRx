__all__ = ("Map", "map_op")

import typing as T
from asyncio import iscoroutinefunction
from functools import partial

from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable, adispose
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

J = T.TypeVar("J")
K = T.TypeVar("K")


class _MapSink(SingleStream[J, K]):
    def __init__(self, mapper: T.Callable[[J, int], K], **kwargs) -> None:
        super().__init__(**kwargs)

        self._index = 0
        self._mapper = mapper

    async def __asend__(self, value: J):
        index = self._index
        self._index += 1

        result = self._mapper(value, index)

        # Remove reference early to avoid keeping large objects in memory
        del value

        if iscoroutinefunction(self._mapper):
            result = await T.cast(T.Awaitable[K], result)

        awaitable = super().__asend__(result)

        # Remove reference early to avoid keeping large objects in memory
        del result

        await awaitable


class Map(T.Generic[J, K], Observable[K]):
    """Observable that outputs transmuted data from an observable source."""

    def __init__(self, mapper: T.Callable[[J, int], K], source: Observable[J], **kwargs) -> None:
        """Map constructor.

        Arguments:
            mapper: Transmutation function.
            source: Observable source.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._mapper = mapper
        self._source = source

    def __observe__(self, observer: Observer[K, T.Any]) -> Disposable:
        sink: _MapSink[J, K] = _MapSink(self._mapper, loop=observer.loop)

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down, loop=observer.loop)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink, loop=observer.loop))
            raise exc


def map_op(mapper: T.Callable[[J, int], K]) -> T.Callable[[Observable[J]], Map]:
    """Partial implementation of :class:`~.Map` to be used with operator semantics.

    Returns:
        Partial implementation of Map

    """
    return T.cast(T.Callable[[Observable[J]], Map], partial(Map, mapper))
