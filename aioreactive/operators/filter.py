# Internal
import typing as T

from asyncio import iscoroutinefunction

# Project
from ..stream import SingleStream
from ..abstract import Observable, Observer, Disposable
from ..disposable import CompositeDisposable

K = T.TypeVar('K')

FilterCallable = T.Callable[[K], T.Union[T.Awaitable[bool], bool]]


class Filter(Observable):
    """Filters the elements of the source based on a predicate."""

    class Sink(SingleStream):
        """Stream that processes the source elements."""

        def __init__(self, predicate: FilterCallable) -> None:
            """Filter Sink constructor

            Args:
                predicate: Callable that will filter the received elements
            """
            super().__init__()

            self._is_coro = iscoroutinefunction(predicate)
            self._predicate = predicate

        async def __asend__(self, value: K) -> None:
            try:
                if self._is_coro:
                    is_accepted = await self._predicate(value)
                else:
                    is_accepted = self._predicate(value)
            except Exception as ex:
                await self.araise(ex)
            else:
                if is_accepted:
                    await self.__asend__(value)

    def __init__(self, predicate: FilterCallable, source: Observable) -> None:
        """ Filter constructor.

        :param predicate:
        :param source:
        """

        super().__init__()

        self._source = source
        self._predicate = predicate

    async def __aobserve__(self, observer: Observer) -> Disposable:
        sink = Filter.Sink(self._predicate)
        up = await self._source.__aobserve__(sink)
        down = await sink.__aobserve__(observer)

        return CompositeDisposable(up, down)


def filter(predicate: FilterCallable, source: Observable) -> Observable:
    """Filters the source stream.

    Filters the items of the source stream based on a predicate
    function.
    """
    return Filter(predicate, source)
