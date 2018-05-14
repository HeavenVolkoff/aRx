# Internal
import typing as T

from asyncio import iscoroutinefunction

# Project
from .base import BaseObserver
from ..misc import anoop

K = T.TypeVar("K")
L = T.TypeVar("L")


class AnonymousObserver(BaseObserver[K]):
    """An anonymous AsyncObserver.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, araise and aclose. Used for
    listening to a source."""

    def __init__(
        self,
        asend_coro: T.Callable[[K], T.Union[T.Awaitable[L], L]] = anoop,
        araise_coro: T.Callable[[Exception], T.Union[T.Awaitable[L], L]
                                ] = anoop,
        aclose_coro: T.Callable[[], T.Union[T.Awaitable[L], L]] = anoop,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

        self._send = asend_coro
        self._raise = araise_coro
        self._close = aclose_coro

        self._send_is_coro = iscoroutinefunction(asend_coro)
        self._raise_is_coro = iscoroutinefunction(araise_coro)
        self._close_is_coro = iscoroutinefunction(aclose_coro)

    async def __asend__(self, value: K) -> None:
        if self._send_is_coro:
            await self._send(value)
        else:
            self._send(value)

    async def __araise__(self, ex: Exception) -> bool:
        if self._raise_is_coro:
            return bool(await self._raise(ex))
        else:
            return bool(self._raise(ex))

    async def __aclose__(self) -> None:
        if self._close_is_coro:
            self.set_result(await self._close())
        else:
            self.set_result(self._close())
