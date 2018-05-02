# Internal
import typing as T

from asyncio import iscoroutinefunction

# Project
from ..stream import SingleStream
from ..abstract import Observable, Observer, Disposable
from ..disposable import CompositeDisposable

K = T.TypeVar('K')
J = T.TypeVar('J')


class Map(Observable):
    class Sink(SingleStream[J]):
        def __init__(self, mapper: T.Callable[[K], J]) -> None:
            super().__init__()
            self._mapper = mapper

        async def __asend__(self, value: K) -> None:
            try:
                result = self._mapper(value)
            except Exception as err:
                await super().__araise__(err)
            else:
                await super().__asend__(result)

    def __init__(self, mapper: T.Callable[[K], J], source: Observable) -> None:
        if not iscoroutinefunction(mapper):
            raise TypeError("mapper must be a coroutine")

        self._source = source
        self._mapper = mapper

    async def __aobserve__(self, observer: Observer) -> Disposable:
        sink = Map.Sink(self._mapper)  # type: SingleStream[J]

        up = await self._source.__aobserve__(sink)
        down = await sink.__aobserve__(observer)

        return CompositeDisposable(up, down)


def map(mapper: T.Callable[[K], J], source: Observable) -> Observable:
    """Project each item of the source observable.

    xs = map(lambda value: value * value, source)

    Keyword arguments:
    mapper: A transform function to apply to each source item.

    Returns an observable sequence whose elements are the result of
    invoking the mapper function on each element of source.
    """
    return Map(mapper, source)
