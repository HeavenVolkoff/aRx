__all__ = ("Max", "max_op")

import typing as T

from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable, adispose
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

K = T.TypeVar("K")


class Max(Observable[K]):
    """Observable that outputs the largest data read from an observable source.

    .. Note::

        Data comparison is made using the ``>`` (grater than) operation.

    .. Warning::

        This observable only outputs data after source observable has closed.
    """

    class _MaxSink(SingleStream[K, K]):
        def __init__(self, **kwargs) -> None:
            super().__init__(**kwargs)

        async def __asend__(self, value: K):
            try:
                is_greater = value > getattr(self, "_max")
            except AttributeError:
                is_greater = True

            if is_greater:
                setattr(self, "_max", value)

        async def __aclose__(self):
            try:
                awaitable = super().asend(getattr(self, "_max"))
                # Remove reference early to avoid keeping large objects in memory
                delattr(self, "_max")
            except AttributeError:
                pass
            else:
                await awaitable

            await super().__aclose__()

    def __init__(self, source: Observable[K], **kwargs) -> None:
        """Max constructor.

        Arguments:
            source: Observable source.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)
        self._source = source

    def __observe__(self, observer: Observer[K, T.Any]) -> Disposable:
        sink = self._MaxSink()  # type: Max._MaxSink[K]

        try:
            up = observe(self._source, sink)
            down = observe(sink, observer)

            return CompositeDisposable(up, down, loop=observer.loop)
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink, loop=observer.loop))
            raise exc


def max_op() -> T.Type[Max]:
    """Implementation of :class:`~.Max` to be used with operator semantics.

    Returns:
        Implementation of Max.

    """
    return Max
