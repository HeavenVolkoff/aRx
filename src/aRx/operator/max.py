__all__ = ("Max", "max_op")

# Internal
import typing as T

# Project
from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..misc.dispose_sink import dispose_sink
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

K = T.TypeVar("K")


class _MaxSink(SingleStream[K]):
    def __init__(self, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)

    async def __asend__(self, value: K) -> None:
        try:
            is_greater = value > getattr(self, "_max")
        except AttributeError:
            is_greater = True

        if is_greater:
            setattr(self, "_max", value)

    async def __aclose__(self) -> None:
        try:
            awaitable = super().__asend__(getattr(self, "_max"))
            # Remove reference early to avoid keeping large objects in memory
            delattr(self, "_max")
        except AttributeError:
            pass
        else:
            await awaitable

        await super().__aclose__()


class Max(Observable[K]):
    """Observable that outputs the largest data read from an observable source.

    .. Note::

        Data comparison is made using the ``>`` (grater than) operation.

    .. Warning::

        This observable only outputs data after source observable has closed.
    """

    def __init__(self, source: Observable[K], **kwargs: T.Any) -> None:
        """Max constructor.

        Arguments:
            source: Observable source.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)
        self._source = source

    def __observe__(self, observer: Observer[K, T.Any]) -> CompositeDisposable:
        sink: _MaxSink[K] = _MaxSink(loop=observer.loop)
        with dispose_sink(sink):
            return CompositeDisposable(
                observe(self._source, sink), observe(sink, observer), loop=observer.loop
            )


def max_op() -> T.Type[Max[K]]:
    """Implementation of :class:`~.Max` to be used with operator semantics.

    Returns:
        Implementation of Max.

    """
    return Max
