# Internal
import typing as T

# Project
from ....stream import SingleStream
from ....abstract import Observable, Observer, Disposable
from ....disposable import CompositeDisposable
from ....observable.operator import empty

K = T.TypeVar('T')


class Take(Observable):
    class Sink(SingleStream[K]):
        def __init__(self, count: int, **kwargs) -> None:
            super().__init__(**kwargs)

            self._count = count

        async def __asend__(self, value: K) -> None:
            if self._count > 0:
                self._count -= 1
                await super().__asend__(value)

                if self._count == 0:
                    await super().aclose()

    def __init__(self, count: int, source: Observable, **kwargs) -> None:
        super().__init__(**kwargs)

        self._source = source
        self._count = count

    async def __aobserve__(self, observer: Observer[K]) -> Disposable:
        sink = Take.Sink(self._count)  # type: SingleStream[K]
        down = await sink.__aobserve__(observer)
        up = await self.__aobserve__(sink)

        return CompositeDisposable(up, down)


def take(count: int, source: Observable) -> Observable:
    """Returns a specified number of contiguous elements from the start
    of the source stream.

    1 - take(5, source)
    2 - source | take(5)

    Keyword arguments:
    count -- The number of elements to return.

    Returns a source sequence that contains the specified number of
    elements from the start of the input sequence.
    """
    if count < 0:
        raise ValueError("Count must be bigger than 0")
    elif count == 0:
        return empty()

    return Take(count, source)
