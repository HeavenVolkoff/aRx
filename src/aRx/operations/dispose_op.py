# Internal
import typing as T
from asyncio import CancelledError

# Project
from ..protocols import ObserverProtocol, ObservableProtocol

K = T.TypeVar("K")


async def dispose(
    observable: ObservableProtocol[K],
    observer: ObserverProtocol[K],
    *,
    keep_alive: T.Optional[bool] = None,
) -> None:
    cancelled = False

    try:
        await observable.__dispose__(observer)
    except CancelledError:
        cancelled = True
        raise
    except Exception:
        keep_alive = False
        raise
    except BaseException:
        cancelled = True
        raise
    finally:
        if not cancelled:
            if keep_alive is None:
                keep_alive = observer.keep_alive

            if not (observer.closed or keep_alive):
                await observer.aclose()


__all__ = ("dispose",)
