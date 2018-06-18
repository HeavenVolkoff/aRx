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

        Arguments:
            asend: Implementation of asend logic.
            araise: Implementation of araise logic.
            aclose: Implementation of aclose logic.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._send = asend
        self._raise = araise
        self._close = aclose

    async def __asend__(self, value: K) -> None:
        res = self._send(value)

        if iscoroutinefunction(self._send):
            await res

    async def __araise__(self, ex: Exception) -> bool:
        res = self._raise(ex)

        if iscoroutinefunction(self._raise):
            res = await res

        return bool(res)

    async def __aclose__(self) -> None:
        res = self._close()

        if iscoroutinefunction(self._close):
            await res