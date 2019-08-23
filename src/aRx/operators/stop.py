# Internal
import typing as T

# External
import typing_extensions as Te
from async_tools import attempt_await

# Project
from ..streams import SingleStream
from ..namespace import Namespace

# Generic Types
K = T.TypeVar("K")


def noop(x: K) -> K:
    return x


class Stop(SingleStream[K]):
    @T.overload
    def __init__(
        self,
        asend_predicate: T.Callable[[K], T.Union[bool, T.Awaitable[bool]]],
        araise_predicate: T.Optional[
            T.Callable[[Exception], T.Union[bool, T.Awaitable[bool]]]
        ] = None,
        *,
        with_index: Te.Literal[False],
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_predicate: Te.Literal[None],
        araise_predicate: T.Callable[[Exception], T.Union[bool, T.Awaitable[bool]]],
        *,
        with_index: Te.Literal[False],
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_predicate: T.Callable[[K, int], T.Union[bool, T.Awaitable[bool]]],
        araise_predicate: T.Optional[
            T.Callable[[Exception], T.Union[bool, T.Awaitable[bool]]]
        ] = None,
        *,
        with_index: Te.Literal[True],
        **kwargs: T.Any,
    ) -> None:
        ...

    def __init__(
        self,
        asend_predicate: T.Any = None,
        araise_predicate: T.Any = None,
        *,
        with_index: bool = False,
        **kwargs: T.Any,
    ) -> None:
        super().__init__(**kwargs)

        assert asend_predicate or araise_predicate

        self._index = 0 if with_index else None
        self._close_guard = False
        self._asend_predicate = noop if asend_predicate is None else asend_predicate
        self._araise_predicate = noop if araise_predicate is None else araise_predicate

    async def __asend__(self, value: K, namespace: Namespace) -> None:
        if self._close_guard:
            return

        if self._index is None:
            stop_awaitable = self._asend_predicate(value)
        else:
            stop_awaitable = self._asend_predicate(value, self._index)
            self._index += 1

        if await attempt_await(stop_awaitable):
            self._close_guard = True
            self.loop.create_task(self.aclose())
        else:
            awaitable = super()._asend(value, namespace)

            # Remove reference early to avoid keeping large objects in memory
            del value

            await awaitable

    async def __araise__(self, exc: Exception, namespace: Namespace) -> bool:
        if not self._close_guard:
            if await attempt_await(self._araise_predicate(exc)):
                self._close_guard = True
                self.loop.create_task(self.aclose())
            else:
                return await super()._athrow(exc, namespace)

        return False


__all__ = ("Stop",)
