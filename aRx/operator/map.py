# Internal
import typing as T

from asyncio import iscoroutinefunction
from functools import partial

# Project
from ..stream.single_stream import SingleStream
from ..abstract.observer import Observer
from ..abstract.observable import Observable, observe
from ..abstract.disposable import Disposable, adispose
from ..disposable import CompositeDisposable

K = T.TypeVar('K')
J = T.TypeVar('J')
MapCallable = T.Callable[[K, int], T.Union[T.Awaitable[J], J]]


class Map(Observable):
    """Observable that outputs transmuted data from an observable source."""

    class _Sink(SingleStream[J]):
        def __init__(self, mapper: MapCallable, **kwargs) -> None:
            super().__init__(**kwargs)

            self._index = 0
            self._mapper = mapper

        async def __asend__(self, value: K) -> None:
            index = self._index
            self._index += 1

            value = self._mapper(value, index)

            if iscoroutinefunction(self._mapper):
                value = await value

            awaitable = super().__asend__(value)

            # Remove reference early to avoid keeping large objects in memory
            del value

            await awaitable

    def __init__(
        self, mapper: MapCallable, source: Observable, **kwargs
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

    def __observe__(self, observer: Observer[K]) -> Disposable:
        sink = self._Sink(self._mapper)

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def map(mapper: MapCallable) -> T.Callable[[], Map]:
    """Partial implementation of :class:`~.Map` to be used with operator semantics.

    Returns:
        Partial implementation of Map

    """
    return partial(Map, mapper)
