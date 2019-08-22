__all__ = ("Never",)

# Internal
import typing as T

# Project
from ..protocols import ObserverProtocol, ObservableProtocol


class Never(ObservableProtocol[None]):
    """Observable that never outputs data, but stays open."""

    async def __observe__(self, _: ObserverProtocol[T.Any]) -> None:
        """Do nothing."""
        return

    async def __dispose__(self, _: ObserverProtocol[T.Any]) -> None:
        """Do nothing."""
        return
