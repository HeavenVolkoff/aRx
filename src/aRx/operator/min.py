__all__ = ("Min", "min_op")

# Internal
import typing as T
from abc import ABCMeta, abstractmethod

# Project
from ..disposable import CompositeDisposable
from ..misc.namespace import Namespace
from ..abstract.observer import Observer
from ..misc.dispose_sink import dispose_sink
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream
from ..misc.async_context_manager import AsyncContextManager


class Comparable(metaclass=ABCMeta):
    @abstractmethod
    def __lt__(self, other: T.Any) -> bool:
        ...


# Generic Types
K = T.TypeVar("K", bound=Comparable)

_NOT_PROVIDED = object()


class _MinSink(SingleStream[K]):
    def __init__(self, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)
        self._min: K = T.cast(K, _NOT_PROVIDED)
        self._namespace: T.Optional[Namespace] = None

    async def __asend__(self, value: K, namespace: Namespace) -> None:
        if self._min == _NOT_PROVIDED or value < self._min:
            self._min = value
            self._namespace = namespace

    async def __aclose__(self) -> None:
        if self._min != _NOT_PROVIDED:
            assert self._namespace is not None

            awaitable = super().__asend__(self._min, self._namespace)

            self._min = T.cast(K, _NOT_PROVIDED)
            self._namespace = None

            await awaitable

        await super().__aclose__()


class Min(Observable[K, CompositeDisposable]):
    """Observable that outputs the largest data read from an observable source.

    .. Note::

        Data comparison is made using the ``\<`` (lesser than) operation.

    .. Warning::

        This observable only outputs data after source observable has closed.
    """

    def __init__(self, source: Observable[K, AsyncContextManager], **kwargs: T.Any) -> None:
        """Min constructor.

        Arguments:
            source: Observable source.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)
        self._source = source

    def __observe__(self, observer: Observer[K, AsyncContextManager]) -> CompositeDisposable:
        sink: _MinSink[K] = _MinSink(loop=observer.loop)
        with dispose_sink(sink):
            return CompositeDisposable(observe(self._source, sink), observe(sink, observer))


def min_op() -> T.Type[Min[K]]:
    """Implementation of :class:`~.Min` to be used with operator semantics.

    Returns:
        Implementation of Min.

    """
    return Min
