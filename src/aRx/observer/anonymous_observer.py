__all__ = ("AnonymousObserver",)


# Internal
import typing as T
from uuid import UUID
from asyncio import AbstractEventLoop, InvalidStateError, iscoroutinefunction
from functools import partial
from contextlib import suppress

# Project
from ..abstract.observer import Observer

# Generic Types
K = T.TypeVar("K")
J = T.TypeVar("J")


def default_asend(_: T.Any) -> None:
    return


def default_araise(exc: Exception, namespace: UUID, *, loop: AbstractEventLoop) -> bool:
    loop.call_exception_handler(
        {
            "message": f"Unhandled error propagated through {AnonymousObserver.__qualname__}",
            "exception": exc,
        }
    )

    return False


def default_aclose() -> None:
    return


class AnonymousObserver(Observer[K, J]):
    """An anonymous Observer.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, araise and aclose. Used for
    listening to a source.
    """

    def __init__(
        self,
        asend: T.Optional[T.Callable[[K], T.Any]] = None,
        araise: T.Optional[T.Callable[[Exception, UUID], T.Optional[bool]]] = None,
        aclose: T.Optional[T.Callable[[], J]] = None,
        **kwargs: T.Any,
    ) -> None:
        """AnonymousObserver Constructor.

        Arguments:
            asend: Implementation of asend logic.
            araise: Implementation of araise logic.
            aclose: Implementation of aclose logic.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        if asend is None:
            asend = default_asend

        if araise is None:
            araise = partial(default_araise, loop=self.loop)

        if aclose is None:
            aclose = T.cast(T.Callable[[], J], default_aclose)

        self._send = asend
        self._raise = araise
        self._close = aclose

    async def __asend__(self, value: K) -> None:
        res = self._send(value)

        if iscoroutinefunction(self._send):
            # Remove reference early to avoid keeping large objects in memory
            del value

            await T.cast(T.Awaitable[T.Any], res)

    async def __araise__(self, exc: Exception, namespace: UUID) -> bool:
        res = self._raise(exc, namespace)

        if iscoroutinefunction(self._raise):
            res = await T.cast(T.Awaitable[T.Optional[bool]], res)

        return bool(res)

    async def __aclose__(self) -> None:
        res = self._close()

        if iscoroutinefunction(self._close):
            res = await T.cast(T.Awaitable[J], res)

        with suppress(InvalidStateError):
            self.resolve(res)
