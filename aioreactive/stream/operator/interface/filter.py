# Internal
import typing as T

from asyncio import iscoroutinefunction

# Project
from ....stream import SingleStream
from ....abstract import Observable, Observer, Disposable
from ....disposable import CompositeDisposable
from ....observable.base import BaseObservable

K = T.TypeVar('K')
L = T.TypeVar("M", Observable, BaseObservable)

FilterCallable = T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]]


class Filter(BaseObservable):
    class Sink(SingleStream):
        def __init__(self, is_coro: bool, predicate: FilterCallable) -> None:
            super().__init__()

            self._index = 0
            self._is_coro = is_coro
            self._predicate = predicate

        async def __asend__(self, value: K) -> None:
            try:
                if self._is_coro:
                    is_accepted = await self._predicate(value, self._index)
                else:
                    is_accepted = self._predicate(value, self._index)
            except Exception as ex:
                await self.araise(ex)
            else:
                if is_accepted:
                    await self.__asend__(value)

                self._index += 1

    def __init__(
        self, predicate: FilterCallable, source: Observable, **kwargs
    ) -> None:
        """Filters the elements of the source based on a predicate."""

        super().__init__(**kwargs)

        self._source = source
        self._is_coro = iscoroutinefunction(predicate)
        self._predicate = predicate

    async def __aobserve__(self, observer: Observer) -> Disposable:
        sink = Filter.Sink(self._is_coro, self._predicate)

        up = await self._source.__aobserve__(sink)
        down = await sink.__aobserve__(observer)

        return CompositeDisposable(up, down)


def filter(predicate: FilterCallable, source: Observable) -> Filter:
    """Filters the source stream.

    Filters the items of the source stream based on a predicate
    function.
    """
    return Filter(predicate, source)
