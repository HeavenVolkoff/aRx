# Internal
import typing as T
from abc import ABCMeta, abstractmethod

# Project
from .observer import Observer

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L", bound=T.AsyncContextManager[T.Any])
M = T.TypeVar("M")
N = T.TypeVar("N", bound=T.AsyncContextManager[T.Any])
O = T.TypeVar("O", bound=T.AsyncContextManager[T.Any])


class Observable(T.Generic[K, L], metaclass=ABCMeta):
    """Observable abstract class.

    An observable is a data generator to which observers can subscribe.
    """

    __slots__ = ()

    def __init__(self, **kwargs: T.Any) -> None:
        """Observable constructor.

        Arguments:
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)  # type: ignore

    def __or__(
        self, other: T.Callable[["Observable[K, L]"], "Observable[M, N]"]
    ) -> "Observable[M, N]":
        return other(self)

    def __gt__(self, observer: Observer[K, T.Any]) -> L:
        return observe(self, observer)

    def __add__(self, other: "Observable[M, N]") -> "Observable[T.Union[K, M], O]":
        from ..operator import Concat

        return Concat(self, other)

    def __iadd__(self, other: "Observable[M, N]") -> "Observable[T.Union[K, M], O]":
        from ..operator import Concat

        return Concat(self, other)

    @abstractmethod
    def __observe__(self, observer: Observer[K, T.Any]) -> L:
        """Interface through which observers are subscribed.

        Define how each observers is subscribed into this observable and the
        mechanisms necessary for data flow and propagation.

        Arguments:
            observer: Observer which will subscribe.

        Raises:
            NotImplemented

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.
        """
        raise NotImplemented()


def observe(observable: Observable[K, L], observer: Observer[K, T.Any]) -> L:
    """External access to observable magic method.

    See also: :meth:`~.Observable.__observe__`

    Arguments:
        observable: Observable to be subscribed.
        observer: Observer which will subscribe.

    Returns:
        Disposable that undoes this subscription.
    """
    from ..error import ObserverClosedError

    if observer.closed:
        raise ObserverClosedError(observer)

    return observable.__observe__(observer)


__all__ = ("Observable", "observe")
