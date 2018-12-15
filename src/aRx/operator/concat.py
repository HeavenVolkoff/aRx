__all__ = ("Concat", "concat_op")

# Internal
import typing as T
from functools import partial

# Project
from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..misc.dispose_sink import dispose_sink
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream
from ..misc.async_context_manager import AsyncContextManager

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


class Concat(T.Generic[K, L], Observable[T.Union[K, L], CompositeDisposable]):
    """Observable that is the concatenation of multiple observables sources"""

    def __init__(
        self,
        a: Observable[K, AsyncContextManager],
        b: Observable[L, AsyncContextManager],
        **kwargs: T.Any,
    ) -> None:
        """Concat constructor.

        Arguments:
            observables: Observables to be concatenated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._a = a
        self._b = b

    def __observe__(self, observer: Observer[T.Union[K, L], T.Any]) -> CompositeDisposable:
        sink: SingleStream[T.Union[K, L]] = SingleStream(loop=observer.loop)
        with dispose_sink(sink):
            return CompositeDisposable(
                observe(self._a, sink), observe(self._b, sink), observe(sink, observer)
            )


def concat_op(
    first: Observable[K, AsyncContextManager]
) -> T.Callable[[Observable[L, AsyncContextManager]], Concat[K, L]]:
    """Partial implementation of :class:`~.Concat` to be used with operator semantics.

    Returns:
        Partial implementation of Concat

    """
    return T.cast(
        T.Callable[[Observable[L, AsyncContextManager]], Concat[K, L]], partial(Concat, first)
    )
