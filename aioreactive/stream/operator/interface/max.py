# Internal
import typing as T

# Project
from ....stream import SingleStream
from ....abstract import Observable, Observer, Disposable
from ....disposable import CompositeDisposable
from ....observable.base import BaseObservable

K = T.TypeVar('K')


class Max(BaseObservable):
    class Stream(SingleStream[K]):
        def __init__(self, *, close_observer: bool, **kwargs) -> None:
            super().__init__(**kwargs)

            self._max = None  # type: K
            self._close_observer = close_observer

        async def __asend__(self, value: K) -> None:
            if value > self._max:
                self._max = value

        async def __aclose__(self, *, close_observer: bool = True) -> None:
            await super().__asend__(self._max)
            await super().__aclose__(
                close_observer=(close_observer and self._close_observer)
            )

    def __init__(
        self, source: Observable, *, close_observer: bool = True, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self._source = source
        self._close_observer = close_observer

    async def __aobserve__(self, observer: Observer) -> Disposable:
        sink = Max.Stream(close_observer=self._close_observer)

        up = await self._source.__aobserve__(sink)
        down = await sink.__aobserve__(observer)

        return CompositeDisposable(up, down)


def max(source: Observable, *, close_observer: bool = True) -> Max:
    """Project each item of the source stream.

    xs = max(source)

    Keyword arguments:
    source: Source to find max value from.

    Returns a stream with a single item that is the item with the
    maximum value from the source stream.
    """
    return Max(source, close_observer=close_observer)
