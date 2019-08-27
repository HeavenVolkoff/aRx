# Internal
import typing as T

# External
import typing_extensions as Te

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace


# Generic Types
K = T.TypeVar("K", contravariant=True)


class ObserverProtocol(Te.Protocol[K]):
    """Observer protocols class.

    An observers represents a data sink, where data can flow into and be
    transformed by it.
    """

    keep_alive: bool
    """Flag that indicates the default behaviour on whether or not the observers should be closed on
        observation disposition.
    """

    @property
    def closed(self) -> bool:
        ...

    async def asend(self, data: K, namespace: T.Optional["Namespace"] = None) -> None:
        ...

    async def athrow(self, main_exc: Exception, namespace: T.Optional["Namespace"] = None) -> None:
        ...

    async def aclose(self) -> bool:
        ...


__all__ = ("ObserverProtocol",)
