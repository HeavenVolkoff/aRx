"""Unit

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T

# External
from async_tools import attempt_await

# Project
from ._internal.from_source import FromSource

# Generic Types
K = T.TypeVar("K")


class Unit(FromSource[K, K]):
    """Observable that outputs a single value then closes."""

    @T.overload
    def __init__(self, value: T.Awaitable[K], **kwargs: T.Any) -> None:
        ...

    @T.overload
    def __init__(self, value: K, **kwargs: T.Any) -> None:
        ...

    def __init__(self, value: T.Any, **kwargs: T.Any) -> None:
        """Unit constructor

        Arguments:
            value: Value to be outputted by observables.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

    async def _worker(self) -> None:
        assert self._observer is not None

        try:
            value = await attempt_await(self._source)
        except Exception as ex:
            await self._observer.athrow(ex, self._namespace)
        else:
            await self._observer.asend(value, self._namespace)


__all__ = ("Unit",)
