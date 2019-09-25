"""Map

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T

# External
import typing_extensions as Te
from async_tools import attempt_await

# Project
from ..streams.single_stream import SingleStreamBase

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace


# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")
M = T.TypeVar("M", covariant=True)
N = T.TypeVar("N", contravariant=True)


@Te.runtime
class MapperCallable(Te.Protocol[M, N]):
    def __call__(self, __value: N) -> M:
        ...


@Te.runtime
class MapperErrorCallable(Te.Protocol):
    def __call__(self, __error: Exception) -> T.Union[T.Awaitable[Exception], Exception]:
        ...


@Te.runtime
class MapperCallableWithIndex(Te.Protocol[M, N]):
    def __call__(self, __value: N, __index: int) -> M:
        ...


@Te.runtime
class MapperAwaitableCallable(Te.Protocol[M, N]):
    def __call__(self, __value: N) -> T.Awaitable[M]:
        ...


@Te.runtime
class MapperAwaitableCallableWithIndex(Te.Protocol[M, N]):
    def __call__(self, __value: N, __index: int) -> T.Awaitable[M]:
        ...


class Map(SingleStreamBase[K, L]):
    @T.overload
    def __init__(
        self,
        asend_mapper: MapperAwaitableCallable[K, L],
        athrow_mapper: T.Optional[MapperErrorCallable] = None,
        *,
        with_index: Te.Literal[False] = False,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_mapper: MapperCallable[K, L],
        athrow_mapper: T.Optional[MapperErrorCallable] = None,
        *,
        with_index: Te.Literal[False] = False,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_mapper: Te.Literal[None],
        athrow_mapper: MapperErrorCallable,
        *,
        with_index: Te.Literal[False] = False,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_mapper: MapperAwaitableCallableWithIndex[K, L],
        athrow_mapper: T.Optional[MapperErrorCallable] = None,
        *,
        with_index: Te.Literal[True],
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_mapper: MapperCallableWithIndex[K, L],
        athrow_mapper: T.Optional[MapperErrorCallable] = None,
        *,
        with_index: Te.Literal[True],
        **kwargs: T.Any,
    ) -> None:
        ...

    def __init__(
        self,
        asend_mapper: T.Optional[
            T.Union[
                MapperCallable[K, L],
                MapperCallableWithIndex[K, L],
                MapperAwaitableCallable[K, L],
                MapperAwaitableCallableWithIndex[K, L],
            ]
        ],
        athrow_mapper: T.Optional[MapperErrorCallable] = None,
        *,
        with_index: bool = False,
        **kwargs: T.Any,
    ) -> None:
        super().__init__(**kwargs)

        # There must be passed at least one predicate as argument
        assert asend_mapper or athrow_mapper

        self._index = 0 if with_index else None
        self._asend_mapper = asend_mapper
        self._athrow_mapper = athrow_mapper

    async def _asend_impl(self, value: L) -> K:
        if self._asend_mapper is None:
            awaitable: T.Union[T.Awaitable[K], K] = T.cast(K, value)
        elif self._index is None:
            assert not (
                isinstance(self._asend_mapper, MapperCallableWithIndex)
                or isinstance(self._asend_mapper, MapperAwaitableCallableWithIndex)
            )
            awaitable = self._asend_mapper(value)
        else:
            assert not (
                isinstance(self._asend_mapper, MapperCallable)
                or isinstance(self._asend_mapper, MapperAwaitableCallable)
            )
            awaitable = self._asend_mapper(value, self._index)
            self._index += 1

        result = attempt_await(awaitable)

        # Remove reference early to avoid keeping large objects in memory
        del value

        return await result

    async def _athrow(self, exc: Exception, namespace: "Namespace") -> bool:
        if self._athrow_mapper:
            exc = await attempt_await(self._athrow_mapper(exc))

        return await super()._athrow(exc, namespace)


__all__ = ("Map",)
