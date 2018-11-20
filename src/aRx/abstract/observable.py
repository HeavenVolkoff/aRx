__all__ = ("Observable", "observe")

# Internal
import typing as T
from abc import ABCMeta, abstractmethod

# Project
from .base import Base
from .observer import Observer
from .disposable import Disposable

# Generic Types
J = T.TypeVar("J")
K = T.TypeVar("K")


class Observable(T.Generic[K], Base, metaclass=ABCMeta):
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

    def __or__(self, other: T.Callable[["Observable[K]"], "Observable[J]"]) -> "Observable[J]":
        return other(self)

    def __gt__(self, observer: Observer[K, T.Any]) -> Disposable:
        return observe(self, observer)

    def __add__(self, other: "Observable[J]") -> "Observable[T.Union[K, J]]":
        from ..operator import Concat

        return Concat(self, other)

    def __iadd__(self, other: "Observable[J]") -> "Observable[T.Union[K, J]]":
        return self.__add__(other)

    @abstractmethod
    def __observe__(self, observer: Observer[K, T.Any]) -> Disposable:
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


def observe(observable: Observable[K], observer: Observer[K, T.Any]) -> Disposable:
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
