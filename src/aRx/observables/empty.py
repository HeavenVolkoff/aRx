# Internal
import typing as T

# Project
from ..protocols import ObserverProtocol, ObservableProtocol


class Empty(ObservableProtocol[T.Any]):
    """Observable that doesn't output data and closes any observers as soon as possible."""

    async def __observe__(self, observer: ObserverProtocol[T.Any]) -> None:
        from ..operations import dispose

        await dispose(self, observer)

    async def __dispose__(self, observer: ObserverProtocol[T.Any]) -> None:
        return


__all__ = ("Empty",)
