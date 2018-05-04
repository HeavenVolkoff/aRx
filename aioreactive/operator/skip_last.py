from typing import TypeVar, List

from aioreactive.core import AsyncObserver, AsyncObservable, AsyncSingleStream
from aioreactive.core import AsyncDisposable, AsyncCompositeDisposable, chain

T = TypeVar('T')


class SkipLast(AsyncObservable):

    def __init__(self, count: int, source: AsyncObservable) -> None:
        self._source = source
        self._count = count

    async def __asubscribe__(self, observer: AsyncObserver) -> AsyncDisposable:
        sink = SkipLast.Sink(self)
        down = await chain(sink, observer)
        up = await chain(self._source, sink)

        return AsyncCompositeDisposable(up, down)

    class Sink(AsyncSingleStream):

        def __init__(self, source: "SkipLast") -> None:
            super().__init__()
            self._count = source._count
            self._q = []  # type: List[T]

        async def asend_core(self, value: T) -> None:
            front = None  # type: T
            self._q.append(value)
            if len(self._q) > self._count:
                front = self._q.pop(0)

            if front is not None:
                await self._observer.asend(front)


def skip_last(count: int, source: AsyncObservable) -> AsyncObservable:
    """Bypasses a specified number of elements at the end of a source
    sequence.

    Description:
    This operator accumulates a queue with a length enough to store the
    first `count` elements. As more elements are received, elements are
    taken from the front of the queue and produced on the result
    sequence. This causes elements to be delayed.

    Keyword arguments:
    count -- Number of elements to bypass at the end of the source
        sequence.

    Returns a source sequence containing the source
    sequence elements except for the bypassed ones at the end.
    """
    return SkipLast(count, source)
