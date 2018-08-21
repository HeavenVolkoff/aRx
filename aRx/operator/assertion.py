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
AssertCallable = T.Callable[[K], T.Union[T.Awaitable[bool], bool]]


class Assert(Observable[K]):
    """Observable that raises exception if predicate is false."""

    class _AssertSink(SingleStream[K]):
        def __init__(self, predicate: AssertCallable, exc: Exception, **kwargs) -> None:
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

    def __init__(
        self, predicate: AssertCallable, exc: Exception, source: Observable, **kwargs
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

    def __observe__(self, observer: Observer) -> Disposable:
        sink = self._AssertSink(
            self._predicate, self._exc, loop=observer.loop
        )  # type: Assert._AssertSink[K]

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def assert_op(predicate: AssertCallable, exc: Exception) -> T.Callable[[], Assert]:
    """Partial implementation of :class:`~.Filter` to be used with operator semantics.

    Returns:
        Return partial implementation of Filter

    """
    return partial(Assert, predicate, exc)
