from typing import TypeVar, AsyncIterable, AsyncIterator, Generic

from ...observable import observe
from ...observable.base import Observable
from ..iterator_observer import IteratorObserver

T = TypeVar('T')


class ToAsyncIterable(Generic[T], AsyncIterable[T]):
    def __init__(self, source: Observable) -> None:
        self._source = source

    async def __aiter__(self) -> AsyncIterator:
        """Iterate asynchronously.

        Transforms the async source to an async iterable. The source
        will await for the iterator to pick up the value before
        continuing to avoid queuing values.
        """

        obv = IteratorObserver()
        await observe(self._source, obv)
        return obv


def to_async_iterable(source: Observable) -> AsyncIterable:
    """Skip the specified number of values.

    Keyword arguments:
    count -- The number of elements to skip before returning the
        remaining values.

    Returns a source stream that contains the values that occur
    after the specified index in the input source stream.
    """

    return ToAsyncIterable(source)
