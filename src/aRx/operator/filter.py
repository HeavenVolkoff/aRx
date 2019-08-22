# Internal
import typing as T

# External
import typing_extensions as Te

# External
from async_tools import attempt_await
from aRx.abstract.namespace import Namespace

# Project
from ..stream import SingleStream

# Generic Types
K = T.TypeVar("K")


class Filter(SingleStream[K]):
    @T.overload
    def __init__(
        self,
        asend_predicate: T.Callable[[K], T.Union[bool, T.Awaitable[bool]]],
        araise_predicate: T.Optional[T.Callable[[Exception], T.Union[bool, T.Awaitable[bool]]]],
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
        araise_predicate: T.Optional[T.Callable[[Exception], T.Union[bool, T.Awaitable[bool]]]],
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
        self._asend_predicate = asend_predicate
        self._araise_predicate = araise_predicate

    async def __asend__(self, value: K, namespace: Namespace) -> None:
        if self._index is None:
            awaitable = self._asend_predicate(value)
        else:
            awaitable = self._asend_predicate(value, self._index)
            self._index += 1

        if await attempt_await(awaitable):
            result = super().__asend__(value, namespace)

            # Remove reference early to avoid keeping large objects in memory
            del value

            await result

    async def __araise__(self, exc: Exception, namespace: Namespace) -> bool:
        if await attempt_await(self._araise_predicate(exc)):
            return await super().__araise__(exc, namespace)

        return False


__all__ = ("Filter",)
