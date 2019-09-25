"""Max

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T

# External
import typing_extensions as Te

# Project
from ..streams import SingleStream

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace


class Comparable(Te.Protocol):
    def __gt__(self, other: T.Any) -> bool:
        ...


# Generic Types
K = T.TypeVar("K", bound=Comparable)
_NOT_PROVIDED = object()


class Max(SingleStream[K]):
    def __init__(self, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)
        self._max: K = _NOT_PROVIDED  # type: ignore
        self._namespace: T.Optional["Namespace"] = None

    async def _asend(self, value: K, namespace: "Namespace") -> None:
        if self._max == _NOT_PROVIDED or value > self._max:
            self._max = value
            self._namespace = namespace

    async def _aclose(self) -> None:
        if self._max != _NOT_PROVIDED:
            assert self._namespace is not None

            awaitable = super()._asend(self._max, self._namespace)

            self._max = _NOT_PROVIDED  # type: ignore
            self._namespace = None

            await awaitable

        await super()._aclose()


__all__ = ("Max",)
