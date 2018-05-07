# Internal
import asyncio
import typing as T

# Project
from .base import BaseObserver
from ..misc import anoop

K = T.TypeVar("K")


class AnonymousObserver(BaseObserver[K]):
    """An anonymous AsyncObserver.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, araise and aclose. Used for
    listening to a source."""

    def __init__(
        self,
        asend_coro: T.Callable[BaseObserver[K].__asend__] = anoop,
        araise_coro: (T.Callable[BaseObserver[K].__araise__]) = anoop,
        aclose_coro: T.Callable[BaseObserver[K].__aclose__] = anoop,
        **kwargs
    ) -> None:
        super().__init__(**kwargs)

        if not asyncio.iscoroutinefunction(asend_coro):
            raise TypeError("asend must be a coroutine")

        if not asyncio.iscoroutinefunction(araise_coro):
            raise TypeError("araise must be a coroutine")

        if not asyncio.iscoroutinefunction(aclose_coro):
            raise TypeError("aclose must be a coroutine")

        self._send = asend_coro
        self._raise = araise_coro
        self._close = aclose_coro

    async def __asend__(self, value: K, **kwargs) -> None:
        await self._send(value, **kwargs)

    async def __araise__(self, ex: Exception, **kwargs) -> bool:
        return bool(await self._raise(ex, **kwargs))

    async def __aclose__(self, **kwargs) -> None:
        self.set_result(await self._close(**kwargs))
