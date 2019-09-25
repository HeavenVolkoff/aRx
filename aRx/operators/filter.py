"""Filter

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
from ..streams import SingleStream

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace


# Generic Types
K = T.TypeVar("K")
M = T.TypeVar("M", contravariant=True)


@Te.runtime
class FilterCallable(Te.Protocol[M]):
    def __call__(self, __value: M) -> T.Union[T.Awaitable[bool], bool]:
        ...


@Te.runtime
class FilterErrorCallable(Te.Protocol):
    def __call__(self, __error: Exception) -> T.Union[T.Awaitable[bool], bool]:
        ...


@Te.runtime
class FilterCallableWithIndex(Te.Protocol[M]):
    def __call__(self, __value: M, __index: int) -> T.Union[T.Awaitable[bool], bool]:
        ...


class Filter(SingleStream[K]):
    @T.overload
    def __init__(
        self,
        asend_predicate: FilterCallable[K],
        athrow_predicate: T.Optional[FilterErrorCallable] = None,
        *,
        with_index: Te.Literal[False] = False,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_predicate: Te.Literal[None],
        athrow_predicate: FilterErrorCallable,
        *,
        with_index: Te.Literal[False] = False,
        **kwargs: T.Any,
    ) -> None:
        ...

    @T.overload
    def __init__(
        self,
        asend_predicate: FilterCallableWithIndex[K],
        athrow_predicate: T.Optional[FilterErrorCallable] = None,
        *,
        with_index: Te.Literal[True],
        **kwargs: T.Any,
    ) -> None:
        ...

    def __init__(
        self,
        asend_predicate: T.Optional[T.Union[FilterCallable[K], FilterCallableWithIndex[K]]],
        athrow_predicate: T.Optional[FilterErrorCallable] = None,
        *,
        with_index: bool = False,
        **kwargs: T.Any,
    ) -> None:
        super().__init__(**kwargs)

        # There must be passed at least one predicate as argument
        assert asend_predicate or athrow_predicate

        self._index = 0 if with_index else None
        self._asend_predicate = asend_predicate
        self._athrow_predicate = athrow_predicate

    async def _asend(self, value: K, namespace: "Namespace") -> None:
        if self._asend_predicate is None:
            awaitable: T.Union[T.Awaitable[bool], bool] = True
        elif self._index is None:
            assert not (isinstance(self._asend_predicate, FilterCallableWithIndex))
            awaitable = self._asend_predicate(value)
        else:
            assert not (isinstance(self._asend_predicate, FilterCallable))
            awaitable = self._asend_predicate(value, self._index)
            self._index += 1

        if await attempt_await(awaitable):
            result = super()._asend(value, namespace)

            # Remove reference early to avoid keeping large objects in memory
            del value

            await result

    async def _athrow(self, exc: Exception, namespace: "Namespace") -> bool:
        if self._athrow_predicate is None or await attempt_await(self._athrow_predicate(exc)):
            return await super()._athrow(exc, namespace)

        return False


__all__ = ("Filter",)
