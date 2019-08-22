# Internal
import typing as T

# External
import typing_extensions as Te

# External
from async_tools import attempt_await
from aRx.abstract.namespace import Namespace

# Project
from ..stream.single_stream import SingleStreamBase

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


class Map(SingleStreamBase[K, L]):
    @T.overload
    def __init__(
        self,
        asend_mapper: T.Callable[[K], T.Union[L, T.Awaitable[L]]],
        araise_mapper: T.Optional[
            T.Callable[[Exception], T.Union[Exception, T.Awaitable[Exception]]]
        ],
        *,
        with_index: Te.Literal[False],
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_mapper: Te.Literal[None],
        araise_mapper: T.Callable[[Exception], T.Union[Exception, T.Awaitable[Exception]]],
        *,
        with_index: Te.Literal[False],
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_mapper: T.Callable[[K, int], T.Union[L, T.Awaitable[L]]],
        araise_mapper: T.Optional[
            T.Callable[[Exception], T.Union[Exception, T.Awaitable[Exception]]]
        ],
        *,
        with_index: Te.Literal[True],
        **kwargs: T.Any,
    ) -> None:
        ...

    def __init__(
        self,
        asend_mapper: T.Any = None,
        araise_mapper: T.Any = None,
        *,
        with_index: bool = False,
        **kwargs: T.Any,
    ) -> None:
        super().__init__(**kwargs)

        assert asend_mapper or araise_mapper

        self._index = 0 if with_index else None
        self._asend_mapper = asend_mapper
        self._araise_mapper = araise_mapper

    async def __asend__(self, value: K, namespace: Namespace) -> None:
        if self._index is None:
            awaitable = self._asend_mapper(value)
        else:
            awaitable = self._asend_mapper(value, self._index)
            self._index += 1

        result = attempt_await(awaitable)

        # Remove reference early to avoid keeping large objects in memory
        del value

        awaitable = super().__asend_impl__(await result, namespace)

        # Remove reference early to avoid keeping large objects in memory
        del result

        await awaitable

    async def __araise__(self, exc: Exception, namespace: Namespace) -> bool:
        return await super().__araise_impl__(
            await attempt_await(self._araise_mapper(exc)), namespace
        )


__all__ = ("Map",)
