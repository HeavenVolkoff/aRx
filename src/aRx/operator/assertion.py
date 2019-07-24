__all__ = ("Assert", "assert_op")


# Internal
import typing as T
from async_tools import is_coroutine_function
from functools import partial

# Project
from ..disposable import CompositeDisposable
from ..misc.namespace import Namespace
from ..abstract.observer import Observer
from ..misc.dispose_sink import dispose_sink
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L", bound=T.AsyncContextManager[T.Any])


class _AssertSink(SingleStream[K]):
    def __init__(
        self,
        predicate: T.Callable[[K], T.Union[T.Awaitable[bool], bool]],
        exc: Exception,
        **kwargs: T.Any,
    ) -> None:
        super().__init__(**kwargs)

        self._exc = exc
        self._predicate = predicate

    async def __asend__(self, value: K, namespace: Namespace) -> None:
        is_valid = self._predicate(value)

        if is_coroutine_function(self._predicate):
            is_valid = await T.cast(T.Awaitable[bool], is_valid)

        if not is_valid:
            raise self._exc

        res = super().__asend__(value, namespace)

        # Remove reference early to avoid keeping large objects in memory
        del value

        await res


class Assert(Observable[K, CompositeDisposable]):
    """Observable that raises exception if predicate is false."""

    def __init__(
        self,
        predicate: T.Callable[[K], T.Union[T.Awaitable[bool], bool]],
        exc: Exception,
        source: Observable[K, L],
        **kwargs: T.Any,
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

    def __observe__(self, observer: Observer[K, T.Any]) -> CompositeDisposable:
        sink: _AssertSink[K] = _AssertSink(self._predicate, self._exc, loop=observer.loop)
        with dispose_sink(sink):
            return CompositeDisposable(observe(self._source, sink), observe(sink, observer))


@T.overload
def assert_op(
    predicate: T.Callable[[K], T.Awaitable[bool]], exc: Exception
) -> T.Callable[[Observable[K, L]], Assert[K]]:
    ...


@T.overload
def assert_op(
    predicate: T.Callable[[K], bool], exc: Exception
) -> T.Callable[[Observable[K, L]], Assert[K]]:
    ...


def assert_op(
    predicate: T.Callable[[K], T.Any], exc: Exception
) -> T.Callable[[Observable[K, L]], Assert[K]]:
    """Partial implementation of :class:`~.Filter` to be used with operator semantics.

    Returns:
        Return partial implementation of Filter

    """
    return T.cast(T.Callable[[Observable[K, L]], Assert[K]], partial(Assert, predicate, exc))
