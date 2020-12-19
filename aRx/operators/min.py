"""Min

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T

# Project
from ..streams import SingleStream

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace


# Generic Types
K = T.TypeVar("K")


class Comparable(T.Protocol):
    def __lt__(self: K, other: K) -> bool:
        ...


M = T.TypeVar("M", bound=Comparable)
_NOT_PROVIDED: T.Final = object()


class Min(SingleStream[M]):
    def __init__(self, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)
        self._min: M = _NOT_PROVIDED  # type: ignore
        self._namespace: T.Optional["Namespace"] = None

    async def _asend(self, value: M, namespace: "Namespace") -> None:
        if self._min == _NOT_PROVIDED or value < self._min:
            self._min = value
            self._namespace = namespace

    async def _aclose(self) -> None:
        if self._min != _NOT_PROVIDED:
            assert self._namespace is not None

            awaitable = super()._asend(self._min, self._namespace)

            self._min = _NOT_PROVIDED  # type: ignore
            self._namespace = None

            await awaitable

        await super()._aclose()


__all__ = ("Min",)
