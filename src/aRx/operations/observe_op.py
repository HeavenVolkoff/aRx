# Internal
import typing as T
from asyncio import CancelledError

# External
import typing_extensions as Te

if T.TYPE_CHECKING:
    # Internal
    from types import TracebackType

    # Project
    from ..protocols import ObserverProtocol, ObservableProtocol

# Generic Types
K = T.TypeVar("K")


class observe(T.Generic[K], T.Awaitable["observe[K]"], Te.AsyncContextManager[None]):
    def __init__(
        self,
        observable: "ObservableProtocol[K]",
        observer: "ObserverProtocol[K]",
        *,
        keep_alive: T.Optional[bool] = None,
        **kwargs: T.Any,
    ):
        super().__init__(**kwargs)  # type: ignore

        # Internal
        self._observer = observer
        self._observable = observable
        self._keep_alive = keep_alive

    def __await__(self) -> T.Generator[None, None, "observe[K]"]:
        yield from self.__aenter__().__await__()
        return self

    __iter__ = __await__  # make compatible with 'yield from'.

    async def __aenter__(self) -> None:
        try:
            await self._observable.__observe__(self._observer)
        except CancelledError:
            raise
        except Exception as exc:
            if not await self.__aexit__(type(exc), exc, exc.__traceback__):
                raise

    async def __aexit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional["TracebackType"],
    ) -> None:
        cancelled = False

        keep_alive = self._keep_alive

        try:
            await self._observable.__dispose__(self._observer)
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
                    keep_alive = self._observer.keep_alive

                if not (self._observer.closed or keep_alive):
                    await self._observer.aclose()

    async def dispose(self) -> None:
        return await self.__aexit__(None, None, None)


__all__ = ("observe",)
