# Internal
import typing as T
from abc import abstractmethod

# External
from async_tools.abstract import AsyncABCMeta

# Project
from ..protocols import TransformerProtocol
from ..operations import pipe, sink

if T.TYPE_CHECKING:
    # Project
    from ..protocols import ObserverProtocol

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


class Observable(T.Generic[K], metaclass=AsyncABCMeta):
    """Observable abstract class.

    Base class for defining an object through which data flows and can be observed.

    The data can be observed by :class:`~.Observer`.

    The logic that defines how the data is observed is specific for each Observable type,
    and must be implemented in the magic method :meth:`~.Observable.__observe__`.
    """

    def __gt__(self, observer: "ObserverProtocol[K]") -> sink[K]:
        return sink(self, observer)

    def __or__(self, transformer: TransformerProtocol[K, L]) -> pipe[K, L]:
        if not isinstance(transformer, TransformerProtocol):
            raise TypeError("Argument must be an object that implements the TransformerProtocol")

        return pipe(self, transformer)

    @abstractmethod
    async def __observe__(self, observer: "ObserverProtocol[K]") -> None:
        """Interface through which observers are registered to observe the data flow.

        Define how each observers is registered into this observable and the mechanisms necessary
        for data flow and propagation.

        Arguments:
            observer: Observer which will be registered.

        """
        raise NotImplementedError

    @abstractmethod
    async def __dispose__(self, observer: "ObserverProtocol[K]") -> None:
        """Interface through which observers are unregistered from observation of the data flow.

        Define how each observers is unregistered from this observable and the mechanisms necessary
        to stop data flow and propagation.

        Arguments:
            observer: Observer which will be registered.

        """
        raise NotImplementedError


__all__ = ("Observable",)
