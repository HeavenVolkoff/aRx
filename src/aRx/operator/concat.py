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

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L", bound=T.AsyncContextManager[T.Any])
M = T.TypeVar("M")
N = T.TypeVar("N", bound=T.AsyncContextManager[T.Any])


class Concat(T.Generic[K, M], Observable[T.Union[K, M], CompositeDisposable]):
    """Observable that is the concatenation of multiple observables sources"""

    def __init__(self, a: Observable[K, L], b: Observable[M, N], **kwargs: T.Any) -> None:
        """Concat constructor.

        Arguments:
            observables: Observables to be concatenated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._a = a
        self._b = b

    def __observe__(self, observer: Observer[T.Union[K, M], T.Any]) -> CompositeDisposable:
        sink: SingleStream[T.Union[K, M]] = SingleStream(loop=observer.loop)
        with dispose_sink(sink):
            return CompositeDisposable(
                # The cast is necessary due to https://github.com/python/mypy/issues/5871
                observe(self._a, T.cast(SingleStream[K], sink)),
                observe(self._b, T.cast(SingleStream[M], sink)),
                observe(sink, observer),
            )


def concat_op(first: Observable[K, L]) -> T.Callable[[Observable[M, N]], Concat[K, M]]:
    """Partial implementation of :class:`~.Concat` to be used with operator semantics.

    Returns:
        Partial implementation of Concat

    """
    return T.cast(T.Callable[[Observable[M, N]], Concat[K, M]], partial(Concat, first))
