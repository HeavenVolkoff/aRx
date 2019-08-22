# Internal
import typing as T
from abc import abstractmethod

# External
import typing_extensions as Te

# Project
from .observer import Observer

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


@Te.runtime
class Observable(Te.Protocol[K]):
    """Observable abstract class.

    Base class for defining an object through which data flows and can be observed.

    The data can be observed by :class:`~.Observer`.

    The logic that defines how the data is observed is specific for each Observable type,
    and must be implemented in the magic method :meth:`~.Observable.__observe__`.
    """

    def __init__(self, **kwargs: T.Any) -> None:
        """Observable constructor.

        Arguments:
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)  # type: ignore

    @abstractmethod
    def __observe__(
        self, observer: Observer[K], *, keep_alive: bool
    ) -> T.AsyncContextManager[T.Any]:
        """Interface through which observers are registered to observe the data flow.

        Define how each observers is registered into this observable and the
        mechanisms necessary for data flow and propagation.

        Arguments:
            observer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """
        raise NotImplementedError()

    def __add__(self, other: "Observable[L]") -> "Observable[T.Union[K, L]]":
        from ..operation.concat import concat

        return concat(self, other)

    def __iadd__(self, other: "Observable[L]") -> "Observable[T.Union[K, L]]":
        return self + other

    def __rshift__(self, observer: Observer[K]) -> T.AsyncContextManager[T.Any]:
        """Shortcut for :meth:`~.Observable.__observe__` magic method.

        Args:
            observer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """
        return self.__observe__(observer, keep_alive=observer.keep_alive)


__all__ = ("Observable",)
