# Internal
import typing as T
from abc import abstractmethod

# External
import typing_extensions as Te

# Generic Types
K = T.TypeVar("K")


@Te.runtime
class Observable(Te.Protocol[K]):
    """Observable abstract class.

    Base class for defining an object through which data flows and can be observed.

    The data can be observed by :class:`~.Observer`.

    The logic that defines how the data is observed is specific for each Observable type,
    and must be implemented in the magic method :meth:`~.Observable.__observe__`.
    """

    def __init__(self, **kwargs):
        """Observable constructor.

        Arguments:
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)  # type: ignore

    @abstractmethod
    def __observe__(self, observer, *, keep_alive: bool):
        """Interface through which observers are registered to observe the data flow.

        Define how each observers is registered into this observable and the
        mechanisms necessary for data flow and propagation.

        Arguments:
            observer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """
        raise NotImplementedError()

    def __gt__(self, observer):
        """Shortcut for :meth:`~.Observable.__observe__` magic method.

        Args:
            observer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """
        return self.__observe__(observer, keep_alive=observer.keep_alive)

    def __or__(self, transformer):
        """Shortcut for :meth:`~.Observable.__observe__` magic method.

        Args:
            transformer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """

        from .transformer import Transformer

        if not isinstance(transformer, Transformer):
            raise ValueError("Argument must be a Transformer")

        self.__observe__(transformer, keep_alive=transformer.keep_alive)

        return transformer

    def __add__(self, other):
        from ..operation.concat import concat

        return concat(self, other)

    def __iadd__(self, other):
        return self + other


__all__ = ("Observable",)
