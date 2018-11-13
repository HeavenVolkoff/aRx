__all__ = ("Stop", "stop_op")

# Internal
import typing as T
from asyncio import iscoroutinefunction
from functools import partial

# Project
from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable, adispose
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

K = T.TypeVar("K")


class _StopSink(SingleStream[K, K]):
    def __init__(
        self, predicate: T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]], **kwargs
    ) -> None:
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


class Stop(Observable[K]):
    """Observable that stops according to a predicate."""

    def __init__(
        self,
        predicate: T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]],
        source: Observable[K],
        **kwargs,
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

    def __observe__(self, observer: Observer[K, T.Any]) -> Disposable:
        sink: _StopSink[K] = _StopSink(self._predicate, loop=observer.loop)

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down, loop=observer.loop)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink, loop=observer.loop))
            raise exc


def stop_op(
    predicate: T.Callable[[K, int], T.Union[T.Awaitable[bool], bool]]
) -> T.Callable[[Observable[K]], Stop]:
    """Partial implementation of :class:`~.Stop` to be used with operator semantics.

    Returns:
        Return partial implementation of Stop

    """
    return T.cast(T.Callable[[Observable[K]], Stop], partial(Stop, predicate))
