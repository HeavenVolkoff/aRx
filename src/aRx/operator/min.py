__all__ = ("Min", "min_op")

# Internal
import typing as T

# Project
from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..misc.dispose_sink import dispose_sink
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

K = T.TypeVar("K")


class _MinSink(SingleStream[K]):
    def __init__(self, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)

    async def __asend__(self, value: K) -> None:
        try:
            is_greater = value < getattr(self, "_min")
        except AttributeError:
            is_greater = True

        if is_greater:
            setattr(self, "_min", value)

    async def __aclose__(self) -> None:
        try:
            awaitable = super().__asend__(getattr(self, "_min"))
            # Remove reference early to avoid keeping large objects in memory
            delattr(self, "_min")
        except AttributeError:
            pass
        else:
            await awaitable

        await super().__aclose__()


class Min(Observable[K]):
    """Observable that outputs the largest data read from an observable source.

    .. Note::

        Data comparison is made using the ``\<`` (lesser than) operation.

    .. Warning::

        This observable only outputs data after source observable has closed.
    """

    def __init__(self, source: Observable[K], **kwargs: T.Any) -> None:
        """Min constructor.

        Arguments:
            source: Observable source.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)
        self._source = source

    def __observe__(self, observer: Observer[K, T.Any]) -> CompositeDisposable:
        sink: _MinSink[K] = _MinSink(loop=observer.loop)
        with dispose_sink(sink):
            return CompositeDisposable(
                observe(self._source, sink), observe(sink, observer), loop=observer.loop
            )


def min_op() -> T.Type[Min[K]]:
    """Implementation of :class:`~.Min` to be used with operator semantics.

    Returns:
        Implementation of Min.

    """
    return Min
