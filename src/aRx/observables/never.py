# Internal
import typing as T

# Project
from .observable import Observable

if T.TYPE_CHECKING:
    # Project
    from ..protocols import ObserverProtocol


class Never(Observable[None]):
    """Observable that never outputs data, but stays open."""

    async def __observe__(self, _: "ObserverProtocol"[T.Any]) -> None:
        """Do nothing."""
        return

    async def __dispose__(self, _: "ObserverProtocol"[T.Any]) -> None:
        """Do nothing."""
        return


__all__ = ("Never",)
