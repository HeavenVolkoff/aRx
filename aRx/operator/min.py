__all__ = ("Min", "min")

# Internal
import typing as T

# Project
from ..stream.single_stream import SingleStream
from ..abstract.observer import Observer
from ..abstract.observable import Observable, observe
from ..abstract.disposable import Disposable, adispose
from ..disposable import CompositeDisposable

K = T.TypeVar('K')


class Min(Observable):
    """Observable that outputs the largest data read from an observable source.

    .. Note::

        Data comparison is made using the ``\<`` (lesser than) operation.

    .. Warning::

        This observable only outputs data after source observable has closed.
    """

    class _MinSink(SingleStream[K]):
        def __init__(self, **kwargs) -> None:
            super().__init__(**kwargs)

            self._min = None  # type: T.Optional[K]

        async def __asend__(self, value: K) -> None:
            if value < self._min:
                self._min = value

        async def __aclose__(self) -> None:
            min_value = self._min
            self._min = None

            awaitable = super().asend(min_value)

            # Remove reference early to avoid keeping large objects in memory
            del min_value

            await awaitable

            await super().__aclose__()

    def __init__(self, source: Observable, **kwargs) -> None:
        """Min constructor.

        Arguments:
            source: Observable source.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)
        self._source = source

    def __observe__(self, observer: Observer) -> Disposable:
        sink = self._MinSink()

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def min() -> T.Type[Min]:
    """Implementation of :class:`~.Min` to be used with operator semantics.

    Returns:
        Implementation of Min.

    """
    return Min
