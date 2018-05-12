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
L = T.TypeVar("M", Observable, BaseObservable)

FilterCallable = T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]]


class Filter(BaseObservable):
    class Sink(SingleStream):
        def __init__(
            self, is_coro: bool, predicate: FilterCallable, **kwargs
        ) -> None:
            super().__init__(**kwargs)

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
                    await super().__asend__(value)

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
        sink = Filter.Sink(self._is_coro, self._predicate, logger=self.logger)

        up = await observe(self._source, sink)
        down = await observe(sink, observer)

        return CompositeDisposable(up, down)


def filter(predicate: FilterCallable, source: Observable) -> BaseObservable:
    """Filters the source stream.

    Filters the items of the source stream based on a predicate
    function.
    """
    parent_logger = None
    if isinstance(source, BaseObservable):
        parent_logger = source.logger

    return Filter(predicate, source, parent_logger=parent_logger)
