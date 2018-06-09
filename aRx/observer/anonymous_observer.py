# Internal
import typing as T

from asyncio import iscoroutinefunction

# Project
from ..misc.noop import anoop
from ..abstract.observer import Observer

K = T.TypeVar("K")


class AnonymousObserver(Observer[K]):
    """An anonymous Observer.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, araise and aclose. Used for
    listening to a source.
    """

    def __init__(
        self,
        asend: T.Callable[[K], T.Any] = anoop,
        araise: T.Callable[[Exception], T.Any] = anoop,
        aclose: T.Callable[[], T.Any] = anoop,
        **kwargs
    ) -> None:
        """AnonymousObserver Constructor.

        Args:
            asend: Implementation of send logic.
            araise: Implementation of raise logic.
            aclose: Implementation of close logic.
            kwargs: Keyword parameters for super.
        """
        super().__init__(**kwargs)

        self._send = asend
        self._raise = araise
        self._close = aclose

    async def __asend__(self, value: K) -> None:
        """:meth:`Observer.__asend__`"""
        res = self._send(value)

        if iscoroutinefunction(self._send):
            await res

    async def __araise__(self, ex: Exception) -> bool:
        """:meth:`Observer.__araise__`"""
        res = self._raise(ex)

        if iscoroutinefunction(self._raise):
            res = await res

        return bool(res)

    async def __aclose__(self) -> None:
        """:meth:`Observer.__aclose__`"""
        res = self._close()

        if iscoroutinefunction(self._close):
            await res
