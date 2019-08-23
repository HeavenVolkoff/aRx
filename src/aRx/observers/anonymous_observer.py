__all__ = ("AnonymousObserver",)


# Internal
import typing as T
from asyncio import AbstractEventLoop

# External
from async_tools import attempt_await

# Project
from ..namespace import Namespace
from ..observers.observer import Observer

# Generic Types
K = T.TypeVar("K")
J = T.TypeVar("J")


def default_asend(_: T.Any, __: T.Any) -> None:
    return


def setup_default_araise(loop: AbstractEventLoop) -> T.Callable[[Exception, Namespace], bool]:
    def default_araise(exc: Exception, namespace: Namespace) -> bool:
        ref = namespace.ref
        loop.call_exception_handler(
            {
                "message": (
                    f"Unhandled error propagated through {AnonymousObserver.__qualname__}"
                    f" from {ref if ref else namespace.type} at {namespace.action}"
                ),
                "exception": exc,
            }
        )

        return False

    return default_araise


def default_aclose() -> None:
    return


class AnonymousObserver(Observer[K]):
    """An anonymous Observer.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, araise and aclose. Used for
    listening to a source.
    """

    @T.overload
    def __init__(
        self,
        asend: T.Optional[T.Callable[[K, Namespace], T.Any]] = None,
        araise: T.Optional[
            T.Callable[[Exception, Namespace], T.Awaitable[T.Optional[bool]]]
        ] = None,
        aclose: T.Optional[T.Callable[[], T.Awaitable[J]]] = None,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend: T.Optional[T.Callable[[K, Namespace], T.Any]] = None,
        araise: T.Optional[
            T.Callable[[Exception, Namespace], T.Awaitable[T.Optional[bool]]]
        ] = None,
        aclose: T.Optional[T.Callable[[], J]] = None,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend: T.Optional[T.Callable[[K, Namespace], T.Any]] = None,
        araise: T.Optional[T.Callable[[Exception, Namespace], T.Optional[bool]]] = None,
        aclose: T.Optional[T.Callable[[], T.Awaitable[J]]] = None,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend: T.Optional[T.Callable[[K, Namespace], T.Any]] = None,
        araise: T.Optional[T.Callable[[Exception, Namespace], T.Optional[bool]]] = None,
        aclose: T.Optional[T.Callable[[], J]] = None,
        **kwargs: T.Any,
    ) -> None:
        ...

    def __init__(
        self,
        asend: T.Optional[T.Callable[[K, Namespace], T.Any]] = None,
        araise: T.Optional[T.Callable[[Exception, Namespace], T.Any]] = None,
        aclose: T.Optional[T.Callable[[], T.Any]] = None,
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

        self._send = default_asend if asend is None else asend
        self._raise = setup_default_araise(self.loop) if araise is None else araise
        self._close = default_aclose if aclose is None else aclose

    async def _asend(self, value: K, namespace: Namespace) -> None:
        res = self._send(value, namespace)

        # Remove reference early to avoid keeping large objects in memory
        del value

        await attempt_await(res, loop=self.loop)

    async def _athrow(self, exc: Exception, namespace: Namespace) -> bool:
        return bool(await attempt_await(self._raise(exc, namespace), loop=self.loop))

    async def _aclose(self) -> None:
        await attempt_await(self._close(), loop=self.loop)