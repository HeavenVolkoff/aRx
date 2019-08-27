# Internal
import typing as T

# External
import typing_extensions as Te
from async_tools import attempt_await

# Project
from ..error import ObserverClosedError
from ..streams import SingleStream

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace


# Generic Types
K = T.TypeVar("K")


def noop(_: T.Any) -> bool:
    return False


class _StopMark(ObserverClosedError):
    pass


class Stop(SingleStream[K]):
    @T.overload
    def __init__(
        self,
        asend_predicate: T.Callable[[K], T.Union[bool, T.Awaitable[bool]]],
        athrow_predicate: T.Optional[
            T.Callable[[Exception], T.Union[bool, T.Awaitable[bool]]]
        ] = None,
        *,
        with_index: Te.Literal[False] = False,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_predicate: Te.Literal[None],
        athrow_predicate: T.Callable[[Exception], T.Union[bool, T.Awaitable[bool]]],
        *,
        with_index: Te.Literal[False] = False,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_predicate: T.Callable[[K, int], T.Union[bool, T.Awaitable[bool]]],
        athrow_predicate: T.Optional[
            T.Callable[[Exception], T.Union[bool, T.Awaitable[bool]]]
        ] = None,
        *,
        with_index: Te.Literal[True] = True,
        **kwargs: T.Any,
    ) -> None:
        ...

    def __init__(
        self,
        asend_predicate: T.Any = None,
        athrow_predicate: T.Any = None,
        *,
        with_index: bool = False,
        **kwargs: T.Any,
    ) -> None:
        super().__init__(**kwargs)

        assert asend_predicate or athrow_predicate

        self._index = 0 if with_index else None
        self._asend_predicate = noop if asend_predicate is None else asend_predicate
        self._athrow_predicate = noop if athrow_predicate is None else athrow_predicate

    async def _asend(self, value: K, namespace: "Namespace") -> None:
        if self._index is None:
            stop_awaitable = self._asend_predicate(value)
        else:
            stop_awaitable = self._asend_predicate(value, self._index)
            self._index += 1

        if await attempt_await(stop_awaitable):
            raise _StopMark(self)

        awaitable = super()._asend(value, namespace)

        # Remove reference early to avoid keeping large objects in memory
        del value

        await awaitable

    async def _athrow(self, exc: Exception, namespace: "Namespace") -> bool:
        if isinstance(exc, _StopMark) or await attempt_await(self._athrow_predicate(exc)):
            return True
        return await super()._athrow(exc, namespace)


__all__ = ("Stop",)
