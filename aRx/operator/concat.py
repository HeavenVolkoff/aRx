__all__ = ("Concat", "concat_op")

import typing as T
from functools import partial

from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable, adispose
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

J = T.TypeVar("J")
K = T.TypeVar("K")
L = T.TypeVar("L")


class Concat(Observable[J]):
    """Observable that is the concatenation of multiple observables sources"""

    def __init__(self, *observables: Observable[J], **kwargs) -> None:
        """Concat constructor.

        Arguments:
            observables: Observables to be concatenated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # Must have at least two observables
        assert len(observables) > 1

        self._sources = observables

    def __observe__(self, observer: Observer[J, T.Any]) -> Disposable:
        sink: SingleStream[J, J] = SingleStream()

        try:
            return CompositeDisposable(
                *map(lambda s: observe(s, sink), self._sources),
                observe(sink, observer),
                loop=observer.loop,
            )
        finally:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink, loop=observer.loop))


def concat_op(first: Observable[K]) -> T.Callable[[Observable[L]], Concat]:
    """Partial implementation of :class:`~.Concat` to be used with operator semantics.

    Returns:
        Partial implementation of Concat

    """
    return T.cast(T.Callable[[Observable], Concat], partial(Concat, first))
