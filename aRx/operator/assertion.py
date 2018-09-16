__all__ = ("Assert", "assert_op")

import typing as T
from asyncio import iscoroutinefunction
from functools import partial

from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable, adispose
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

K = T.TypeVar("K")


class _AssertSink(SingleStream[K, K]):
    def __init__(
        self,
        predicate: T.Callable[[K], T.Union[T.Awaitable[bool], bool]],
        exc: Exception,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self._exc = exc
        self._predicate = predicate

    async def __asend__(self, value: K) -> None:
        is_valid = self._predicate(value)

        if iscoroutinefunction(self._predicate):
            is_valid = await T.cast(T.Awaitable[bool], is_valid)

        if not is_valid:
            raise self._exc

        res = super().__asend__(value)

        # Remove reference early to avoid keeping large objects in memory
        del value

        await res


class Assert(Observable[K]):
    """Observable that raises exception if predicate is false."""

    def __init__(
        self,
        predicate: T.Callable[[K], T.Union[T.Awaitable[bool], bool]],
        exc: Exception,
        source: Observable[K],
        **kwargs,
    ) -> None:
        """Filter constructor.

        Arguments:
            predicate: Predicate to filter source.
            source: Observable source.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._exc = exc
        self._source = source
        self._predicate = predicate

    def __observe__(self, observer: Observer[K, T.Any]) -> Disposable:
        sink: _AssertSink[K] = _AssertSink(self._predicate, self._exc, loop=observer.loop)

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down, loop=observer.loop)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink, loop=observer.loop))
            raise exc


def assert_op(
    predicate: T.Callable[[K], T.Union[T.Awaitable[bool], bool]], exc: Exception
) -> T.Callable[[Observable[K]], Assert]:
    """Partial implementation of :class:`~.Filter` to be used with operator semantics.

    Returns:
        Return partial implementation of Filter

    """
    return T.cast(T.Callable[[Observable[K]], Assert], partial(Assert, predicate, exc))
