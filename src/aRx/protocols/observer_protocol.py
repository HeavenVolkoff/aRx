# Internal
import typing as T

# External
import typing_extensions as Te

# Project
from ..namespace import Namespace

# Generic Types
K = T.TypeVar("K", contravariant=True)


class ObserverProtocol(Te.Protocol[K]):
    """Observer protocols class.

    An observers represents a data sink, where data can flow into and be
    transformed by it.
    """

    closed: bool
    """Flag that indicates whether observers is closed or not"""

    keep_alive: bool
    """Flag that indicates the default behaviour on whether or not the observers should be closed on
        observation disposition.
    """

    async def asend(self, data: K, namespace: T.Optional[Namespace] = None) -> None:
        """Interface through which data is inputted.

        Arguments:
            data: Data to be inputted.
            namespace: Namespace to identify propagation origin.

        Raises:
            ObserverClosedError: If observers is closed.

        """
        raise NotImplementedError()

    async def athrow(self, main_exc: Exception, namespace: T.Optional[Namespace] = None) -> None:
        """Interface through which exceptions are inputted.

        Arguments:
            main_exc: Exception to be inputted.
            namespace: Namespace to identify propagation origin.

        Raises:
            ObserverClosedError: If observers is closed.

        """
        raise NotImplementedError()

    async def aclose(self) -> bool:
        """Close observers.

        Returns:
            Boolean indicating if close executed or if it wasn't necessary.

        """
        raise NotImplementedError()


__all__ = ("ObserverProtocol",)
