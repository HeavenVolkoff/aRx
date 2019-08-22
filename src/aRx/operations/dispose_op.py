# Internal
import typing as T

# Project
from ..protocols import ObserverProtocol, ObservableProtocol

K = T.TypeVar("K")


async def dispose(
    observable: ObservableProtocol[K],
    observer: ObserverProtocol[K],
    *,
    keep_alive: T.Optional[bool] = None,
) -> None:
    await observable.__dispose__(observer)

    if keep_alive is None:
        keep_alive = observer.keep_alive

    if not (observer.closed or keep_alive):
        await observer.aclose()


__all__ = ("dispose",)
