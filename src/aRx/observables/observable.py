# Internal
import typing as T
from abc import ABCMeta

# External
import typing_extensions as Te

# Project
from ._Pipe import Pipe
from ..protocols import ObserverProtocol, ObservableProtocol, TransformerProtocol
from ..operations.observe_op import observe

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


class Observable(ObservableProtocol[K], metaclass=ABCMeta):
    """Observable abstract class.

    Base class for defining an object through which data flows and can be observed.

    The data can be observed by :class:`~.Observer`.

    The logic that defines how the data is observed is specific for each Observable type,
    and must be implemented in the magic method :meth:`~.Observable.__observe__`.
    """

    def __gt__(self, observer: ObserverProtocol[K]) -> T.Awaitable[Te.AsyncContextManager[T.Any]]:
        """Shortcut for :meth:`~.Observable.__observe__` magic method.

        Args:
            observer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """
        return observe(self, observer)

    def __or__(self, transformer: TransformerProtocol[K, L]) -> Pipe[K, L]:
        """Shortcut for :meth:`~.Observable.__observe__` magic method.

        Args:
            transformer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """
        if not isinstance(transformer, TransformerProtocol):
            raise ValueError("Argument must be a Transformer")

        p: Pipe[K, L] = Pipe()

        p.__append__(self)
        p.__append__(transformer)

        return p


__all__ = ("Observable",)
