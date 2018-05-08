# Internal
import typing as T

# Project
from ....stream import SingleStream
from ....abstract import Observable, Observer, Disposable
from ....disposable import CompositeDisposable
from ....observable.base import BaseObservable

K = T.TypeVar('K')


class Skip(BaseObservable):
    class Sink(SingleStream[K]):
        def __init__(self, count: int, **kwargs) -> None:
            super().__init__(**kwargs)

            self._count = count

        async def __asend__(self, value: K):
            if self._count <= 0:
                await super().__asend__(value)
            else:
                self._count -= 1

    def __init__(self, count: int, source: Observable, **kwargs) -> None:
        super().__init__(**kwargs)

        self._count = count
        self._source = source

    async def __aobserve__(self, observer: Observer[K]) -> Disposable:
        sink = Skip.Sink(self._count)

        up = await self._source.__aobserve__(sink)
        down = await sink.__aobserve__(observer)

        return CompositeDisposable(up, down)


def skip(count: int, source: Observable) -> Skip[K]:
    """Skip the specified number of values.

    Keyword arguments:
    count -- The number of elements to skip before returning the
        remaining values.

    Returns a source stream that contains the values that occur
    after the specified index in the input source stream.
    """
    return Skip(count, source)
