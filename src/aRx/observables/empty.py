# Internal
import typing as T

# Project
from .observable import Observable
from ..operations import observe

if T.TYPE_CHECKING:
    # Project
    from ..protocols import ObserverProtocol


class Empty(Observable[T.Any]):
    """Observable that doesn't output data and closes any observers as soon as possible."""

    async def __observe__(self, observer: "ObserverProtocol"[T.Any]) -> None:
        await observe(self, observer).dispose()

    async def __dispose__(self, observer: "ObserverProtocol"[T.Any]) -> None:
        return


__all__ = ("Empty",)
