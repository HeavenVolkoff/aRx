__all__ = ("AnonymousObserver",)


# Internal
import typing as T
from asyncio import AbstractEventLoop, InvalidStateError, iscoroutinefunction
from contextlib import suppress

# Project
from ..misc.namespace import Namespace
from ..abstract.observer import Observer

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


class AnonymousObserver(Observer[K, T.Optional[J]]):
    """An anonymous Observer.

    Creates as sink where the implementation is provided by three
    optional and anonymous functions, asend, araise and aclose. Used for
    listening to a source.
    """

    def __init__(
        self,
        asend: T.Optional[T.Callable[[K, Namespace], T.Any]] = None,
        araise: T.Optional[
            T.Callable[
                [Exception, Namespace],
                T.Union[T.Optional[bool], T.Coroutine[T.Any, T.Any, T.Optional[bool]]],
            ]
        ] = None,
        aclose: T.Optional[T.Callable[[], T.Union[J, T.Coroutine[T.Any, T.Any, J]]]] = None,
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

    async def __asend__(self, value: K, namespace: Namespace) -> None:
        res = self._send(value, namespace)

        if iscoroutinefunction(self._send):
            # Remove reference early to avoid keeping large objects in memory
            del value

            assert isinstance(res, T.Coroutine)

            await res

    async def __araise__(self, exc: Exception, namespace: Namespace) -> bool:
        res = self._raise(exc, namespace)

        if iscoroutinefunction(self._raise):
            assert isinstance(res, T.Coroutine)
            res = await res

        assert not isinstance(res, T.Coroutine)

        return bool(res)

    async def __aclose__(self) -> None:
        res = self._close()

        if iscoroutinefunction(self._close):
            assert isinstance(res, T.Coroutine)
            res = await res

        assert not isinstance(res, T.Coroutine)

        with suppress(InvalidStateError):
            self.resolve(res)
