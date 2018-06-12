# Internal
import typing as T

# Project
from ..stream.single_stream import SingleStream
from ..abstract.observer import Observer
from ..abstract.observable import Observable, observe
from ..abstract.disposable import Disposable, adispose
from ..disposable import CompositeDisposable

K = T.TypeVar('K')


class Max(Observable):
    """Observable that outputs the largest data read from an observable source.

    .. Note::

        Data comparison is made using the `>` (grater than) operation.

    .. Warning::

        This observable only outputs data after source observable has closed.
    """

    class _Stream(SingleStream[K]):
        def __init__(self, **kwargs) -> None:
            super().__init__(**kwargs)

            self._max = None  # type: K

        async def __asend__(self, value: K) -> None:
            if value > self._max:
                self._max = value

        async def __aclose__(self) -> None:
            await super().__asend__(self._max)
            await super().__aclose__()

    def __init__(self, source: Observable, **kwargs) -> None:
        """Max constructor.

        Args:
            source: Observable source.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)
        self._source = source

    def __observe__(self, observer: Observer) -> Disposable:
        sink = self._Stream()

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def max() -> T.Type[Max]:
    """Implementation of `Max`_ to be used with operator semantics.

    Returns:
        Implementation of Max.

    .. _Max::

        :class:`Max`.
    """
    return Max
