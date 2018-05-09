# Internal
import typing as T

# Project
from ...single_stream import SingleStream
from ....abstract import Observable, Observer, Disposable
from ....observable import observe
from ....disposable import CompositeDisposable
from ....observable.base import BaseObservable
from ....observable.operator.empty import Empty

K = T.TypeVar('T')


class Take(BaseObservable):
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
        down = await observe(sink, observer)
        up = await observe(self, sink)

        return CompositeDisposable(up, down)


def take(count: int, source: Observable) -> BaseObservable:
    """Returns a specified number of contiguous elements from the start
    of the source stream.

    1 - take(5, source)
    2 - source | take(5)

    Keyword arguments:
    count -- The number of elements to return.

    Returns a source sequence that contains the specified number of
    elements from the start of the input sequence.
    """
    parent_logger = None
    if isinstance(source, BaseObservable):
        parent_logger = source.logger

    if count < 0:
        raise ValueError("Count must be bigger than 0")
    elif count == 0:
        return Empty(parent_logger=parent_logger)

    return Take(count, source, parent_logger=parent_logger)
