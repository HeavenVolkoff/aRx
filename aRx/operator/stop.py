__all__ = ("Stop", "stop")

# Internal
import typing as T

from asyncio import iscoroutinefunction
from functools import partial

# Project
from ..stream.single_stream import SingleStream
from ..abstract.observer import Observer
from ..abstract.observable import Observable, observe
from ..abstract.disposable import Disposable, adispose
from ..disposable import CompositeDisposable

K = T.TypeVar('K')
StopCallable = T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]]


class Stop(Observable):
    """Observable that stop observable source according to a predicate."""

    class _StopSink(SingleStream[K]):

        __slots__ = ("_index", "_predicate")

        def __init__(self, predicate: StopCallable, **kwargs) -> None:
            super().__init__(**kwargs)

            self._index = 0
            self._predicate = predicate

        async def __asend__(self, value: K) -> None:
            index = self._index
            self._index += 1

            must_stop = self._predicate(value, index)
            if iscoroutinefunction(self._predicate):
                must_stop = await must_stop

            # Remove reference early to avoid keeping large objects in memory
            awaitable = self.aclose() if must_stop else super().__asend__(value)

            del value

            await awaitable

    __slots__ = ("_source", "_predicate")

    def __init__(
        self, predicate: StopCallable, source: Observable, **kwargs
    ) -> None:
        """Stop constructor.

        Arguments:
            predicate: Predicate to stop source.
            source: Observable source.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._source = source
        self._predicate = predicate

    def __observe__(self, observer: Observer) -> Disposable:
        sink = self._StopSink(self._predicate)

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def stop(predicate: StopCallable) -> T.Callable[[], Stop]:
    """Partial implementation of :class:`~.Stop` to be used with operator semantics.

    Returns:
        Return partial implementation of Stop

    """
    return partial(Stop, predicate)
