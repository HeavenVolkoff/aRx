__all__ = ("Stop", "stop_op")

import typing as T
from asyncio import iscoroutinefunction
from functools import partial

from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable, adispose
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

K = T.TypeVar("K")
StopCallable = T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]]


class Stop(Observable[K]):
    """Observable that stops according to a predicate."""

    class _StopSink(SingleStream[K]):
        def __init__(self, predicate: StopCallable, **kwargs) -> None:
            super().__init__(**kwargs)

            self._index = 0
            self._predicate = predicate

        async def __asend__(self, value: K):
            index = self._index
            self._index += 1

            must_stop = self._predicate(value, index)
            if iscoroutinefunction(self._predicate):
                must_stop = await T.cast(T.Awaitable[bool], must_stop)

            awaitable = self.aclose() if must_stop else super().__asend__(value)

            # Remove reference early to avoid keeping large objects in memory
            del value

            await awaitable

    def __init__(self, predicate: StopCallable, source: Observable, **kwargs) -> None:
        """Stop constructor.

        Arguments:
            predicate: Predicate to stop source.
            source: Observable source.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._source = source
        self._predicate = predicate

    def __observe__(self, observer: Observer[K, T.Any]) -> Disposable:
        sink = self._StopSink(self._predicate)  # type: Stop._StopSink[K]

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def stop_op(predicate: StopCallable) -> T.Callable[[], Stop]:
    """Partial implementation of :class:`~.Stop` to be used with operator semantics.

    Returns:
        Return partial implementation of Stop

    """
    return partial(Stop, predicate)
