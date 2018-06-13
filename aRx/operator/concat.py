# Internal
import typing as T

from functools import partial

# Project
from ..stream.single_stream import SingleStream
from ..abstract.observer import Observer
from ..abstract.observable import Observable, observe
from ..abstract.disposable import Disposable, adispose
from ..disposable import CompositeDisposable

K = T.TypeVar("K")


class Concat(Observable):
    """Observable that is the concatenation of multiple observables sources"""

    def __init__(
        self, first: Observable, second: Observable, *rest: Observable, **kwargs
    ) -> None:
        """Concat constructor.

        Arguments:
            first: First observable to be concatenated.
            second: Second observable to be concatenated.
            rest: Optional observables to be concatenated.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)

        self._sources = (first, second) + rest

    def __observe__(self, observer: Observer[K]) -> Disposable:
        sink = SingleStream()

        try:
            return CompositeDisposable(
                *map(lambda s: observe(s, sink), self._sources),
                observe(sink, observer)
            )
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def concat(first: Observable) -> T.Callable[[], Concat]:
    """Partial implementation of :class:`~.Concat` to be used with operator semantics.

    Returns:
        Partial implementation of Concat

    """
    return partial(Concat, first)
