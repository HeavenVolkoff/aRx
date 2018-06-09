__all__ = ("Observable", "aobserve")

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

    def __init__(self, **kwargs):
        """Observable constructor.

        Args
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

    def __or__(
        self,
        other: T.Callable[['Observable'], 'Observable'],
    ) -> 'Observable':
        return other(self)

    def __gt__(self, observer: Observer) -> Disposable:
        from ..subscription import subscribe
        return subscribe(observer, self)

    def __add__(self, other: 'Observable') -> 'Observable':
        from ..stream.operator.interface import concat as concat_op
        return concat_op(self, other)

    def __iadd__(self, other: 'Observable') -> 'Observable':
        return self.__add__(other)

    @abstractmethod
    async def __aobserve__(self, observer: Observer[K]) -> Disposable:
        """Implementation of the Observable-like magic method.
        Enables observers to be subscribed into this observable to receive new
        data.

        Args:
            observer: Observer to be subscribed.

        Returns:
            Disposable that undoes this subscription.
        """
        raise NotImplemented()


async def aobserve(observable: Observable, observer: Observer) -> Disposable:
    """Subscribe observer into observable.

    Args:
        observable: Observable to be subscribed.
        observer: Observer to be subscribed.

    Returns:
        Disposable that undoes this subscription.
    """
    return await observable.__aobserve__(observer)
