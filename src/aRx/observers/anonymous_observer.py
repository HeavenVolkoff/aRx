# Internal
import typing as T

# External
from async_tools import attempt_await

# Project
from .observer import Observer

if T.TYPE_CHECKING:
    # Internal
    from asyncio import AbstractEventLoop

    # Project
    from ..namespace import Namespace


# Generic Types
K = T.TypeVar("K")


def default_asend(_: T.Any, __: T.Any) -> None:
    return


def setup_default_athrow(loop: "AbstractEventLoop") -> T.Callable[[Exception, "Namespace"], bool]:
    def default_athrow(exc: Exception, namespace: "Namespace") -> bool:
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

    return default_athrow


def default_aclose() -> None:
    return


class AnonymousObserver(Observer[K]):
    """An anonymous Observer.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, athrow and aclose. Used for
    listening to a source.
    """

    @T.overload
    def __init__(
        self,
        asend: T.Optional[T.Callable[[K, "Namespace"], T.Any]] = None,
        athrow: T.Optional[
            T.Callable[[Exception, "Namespace"], T.Awaitable[T.Optional[bool]]]
        ] = None,
        aclose: T.Optional[T.Callable[[], T.Any]] = None,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend: T.Optional[T.Callable[[K, "Namespace"], T.Any]] = None,
        athrow: T.Optional[T.Callable[[Exception, "Namespace"], T.Optional[bool]]] = None,
        aclose: T.Optional[T.Callable[[], T.Any]] = None,
        **kwargs: T.Any,
    ) -> None:
        ...

    def __init__(
        self, asend: T.Any = None, athrow: T.Any = None, aclose: T.Any = None, **kwargs: T.Any
    ) -> None:
        """AnonymousObserver Constructor.

        Arguments:
            asend: Implementation of asend logic.
            athrow: Implementation of athrow logic.
            aclose: Implementation of aclose logic.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._asend_impl = default_asend if asend is None else asend
        self._athrow_impl = setup_default_athrow(self.loop) if athrow is None else athrow
        self._aclose_impl = default_aclose if aclose is None else aclose

    async def _asend(self, value: K, namespace: "Namespace") -> None:
        awaitable = self._asend_impl(value, namespace)

        # Remove reference early to avoid keeping large objects in memory
        del value

        await attempt_await(awaitable)

    async def _athrow(self, exc: Exception, namespace: "Namespace") -> bool:
        return await attempt_await(self._athrow_impl(exc, namespace))

    async def _aclose(self) -> None:
        await attempt_await(self._aclose_impl())


__all__ = ("AnonymousObserver",)
