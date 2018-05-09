# Internal
import typing as T

from asyncio import iscoroutinefunction

# Project
from ...single_stream import SingleStream
from ....abstract import Observable, Observer, Disposable
from ....observable import observe
from ....disposable import CompositeDisposable
from ....observable.base import BaseObservable

K = T.TypeVar('K')
J = T.TypeVar('J')

MapCallable = T.Callable[[K, int], T.Union[T.Awaitable[J], J]]


class Map(BaseObservable):
    class Sink(SingleStream[J]):
        def __init__(
            self, mapper: MapCallable, is_coro: bool, **kwargs
        ) -> None:
            super().__init__(**kwargs)

            self._index = 0
            self._mapper = mapper
            self._is_coro = is_coro

        async def __asend__(self, value: K) -> None:
            try:
                if self._is_coro:
                    result = await self._mapper(value, self._index)
                else:
                    result = self._mapper(value, self._index)
            except Exception as err:
                await super().araise(err)
            else:
                await super().__asend__(result)
                self._index += 1

    def __init__(
        self, mapper: MapCallable, source: Observable, **kwargs
    ) -> None:

        super().__init__(**kwargs)

        self._mapper = mapper
        self._source = source
        self._is_coro = iscoroutinefunction(mapper)

    async def __aobserve__(self, observer: Observer[K]) -> Disposable:
        sink = Map.Sink(self._mapper, self._is_coro)

        up = await observe(self._source, sink)
        down = await observe(sink, observer)

        return CompositeDisposable(up, down)


def map(mapper: MapCallable, source: Observable) -> BaseObservable:
    """Project each item of the source observable.

    xs = map(lambda value: value * value, source)

    Keyword arguments:
    mapper: A transform function to apply to each source item.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of source.
    """
    parent_logger = None
    if isinstance(source, BaseObservable):
        parent_logger = source.logger

    return Map(mapper, source, parent_logger=parent_logger)
