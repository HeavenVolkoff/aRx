from typing import TypeVar

from aioreactive.core import AsyncSingleStream
from aioreactive.core import AsyncDisposable, AsyncCompositeDisposable
from aioreactive.core import AsyncObserver, AsyncObservable, chain

T = TypeVar('T')


class Skip(AsyncObservable[T]):

    def __init__(self, count: int, source: AsyncObservable[T]) -> None:
        self._source = source
        self._count = count

    async def __asubscribe__(self, observer: AsyncObserver[T]) -> AsyncDisposable:
        sink = Skip.Sink(self)
        down = await chain(sink, observer)
        up = await chain(self._source, sink)

        return AsyncCompositeDisposable(up, down)

    class Sink(AsyncSingleStream[T]):

        def __init__(self, source: "Skip[T]") -> None:
            super().__init__()
            self._count = source._count

        async def asend_core(self, value: T):
            if self._count <= 0:
                await self._observer.asend(value)
            else:
                self._count -= 1


def skip(count: int, source: AsyncObservable[T]) -> AsyncObservable[T]:
    """Skip the specified number of values.

    Keyword arguments:
    count -- The number of elements to skip before returning the
        remaining values.

    Returns a source stream that contains the values that occur
    after the specified index in the input source stream.
    """

    return Skip(count, source)
