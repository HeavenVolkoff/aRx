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
J = T.TypeVar("J")
K = T.TypeVar("K")
L = T.TypeVar("L")


class Concat(Observable[J]):
    """Observable that is the concatenation of multiple observables sources"""

    def __init__(self, *observables: Observable[T.Any], **kwargs: T.Any) -> None:
        """Concat constructor.

        Arguments:
            observables: Observables to be concatenated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # Must have at least two observables
        assert len(observables) > 1

        self._sources = observables

    def __observe__(self, observer: Observer[J, T.Any]) -> CompositeDisposable:
        sink: SingleStream[J] = SingleStream(loop=observer.loop)
        with dispose_sink(sink):
            return CompositeDisposable(
                *(observe(source, sink) for source in self._sources), observe(sink, observer)
            )


def concat_op(first: Observable[K]) -> T.Callable[[Observable[L]], Concat[T.Union[K, L]]]:
    """Partial implementation of :class:`~.Concat` to be used with operator semantics.

    Returns:
        Partial implementation of Concat

    """
    return T.cast(T.Callable[[Observable[L]], Concat[T.Union[K, L]]], partial(Concat, first))
