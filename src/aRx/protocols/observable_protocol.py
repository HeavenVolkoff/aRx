# Internal
import typing as T

# External
import typing_extensions as Te

if T.TYPE_CHECKING:
    # Project
    from .observer_protocol import ObserverProtocol


# Generic Types
K = T.TypeVar("K", covariant=True)


class ObservableProtocol(Te.Protocol[K]):
    async def __observe__(self, observer: "ObserverProtocol[K]") -> None:
        ...

    async def __dispose__(self, observer: "ObserverProtocol[K]") -> None:
        ...


__all__ = ("ObservableProtocol",)
