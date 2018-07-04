# Internal
import typing as T

from asyncio import InvalidStateError, iscoroutinefunction
from warnings import warn
from contextlib import suppress

# Project
from ..misc.noop import noop
from ..error import ARxWarning
from ..abstract.observer import Observer

K = T.TypeVar("K")


def default_araise(ex):
    warn(ARxWarning("Error propagated through AnonymousObserver", ex))
    return False


class AnonymousObserver(Observer[K]):
    """An anonymous Observer.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, araise and aclose. Used for
    listening to a source.
    """

    def __init__(
        self,
        asend: T.Callable[[K], T.Any] = noop,
        araise: T.Callable[[Exception], T.Any] = default_araise,
        aclose: T.Callable[[], T.Any] = noop,
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
            # Remove reference early to avoid keeping large objects in memory
            del value

            await res

    async def __araise__(self, ex: Exception) -> bool:
        res = self._raise(ex)

        if iscoroutinefunction(self._raise):
            res = await res

        return bool(res)

    async def __aclose__(self) -> None:
        res = self._close()

        if iscoroutinefunction(self._close):
            res = await res

        with suppress(InvalidStateError):
            self.future.set_result(res)
