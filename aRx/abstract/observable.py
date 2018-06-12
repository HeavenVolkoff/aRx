__all__ = ("Observable", "observe")

# Internal
import typing as T

from abc import ABCMeta, abstractmethod

# Project
from .observer import Observer
from .disposable import Disposable

K = T.TypeVar('K')


class Observable(object, metaclass=ABCMeta):
    """Observable abstract class.

    An observable is a data generator to which observers can subscribe.
    """

    __slots__ = ()

    def __or__(
        self,
        other: T.Callable[['Observable'], 'Observable'],
    ) -> 'Observable':
        return other(self)

    def __gt__(self, observer: Observer) -> Disposable:
        from ..subscription import subscribe
        return subscribe(observer, self)

    def __add__(self, other: 'Observable') -> 'Observable':
        from ..operator import Concat
        return Concat(self, other)

    def __iadd__(self, other: 'Observable') -> 'Observable':
        return self.__add__(other)

    @abstractmethod
    def __observe__(self, observer: Observer[K]) -> Disposable:
        """Interface by which observers are subscribed.
        Define how each observers is subscribed into this observable.
        Also describe the necessary mechanisms necessary for data flow and
        propagation.

        Args:
            observer: Observer to be subscribed.

        Returns:
            Disposable that undoes this subscription.
        """
        raise NotImplemented()


def observe(observable: Observable, observer: Observer) -> Disposable:
    """External access to observable magic method.

     .. Hint::

        `super`_.

    Args:
        observable: Observable to be subscribed.
        observer: Observer which will subscribe.

    Returns:
        Disposable that undoes this subscription.

    .. _super::

        :meth:`AbstractPromise.__observe__`.
    """
    return observable.__observe__(observer)
