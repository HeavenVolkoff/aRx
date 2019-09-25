"""FromIterable

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T
from asyncio import CancelledError

# Project
from ._internal.from_source import FromSource

# Generic Types
K = T.TypeVar("K")


class FromIterable(FromSource[K, T.Iterator[K]]):
    """Observable that uses an iterable as data source."""

    def __init__(self, iterable: T.Iterable[K], **kwargs: T.Any) -> None:
        """FromIterable constructor.

       Arguments:
           iterable: Iterable to be converted.
           kwargs: Keyword parameters for super.

       """
        super().__init__(iter(iterable), **kwargs)

    async def _worker(self) -> None:
        assert self._observer is not None

        try:
            for data in self._source:
                if self._observer.closed:
                    break

                await self._observer.asend(data, self._namespace)

        except CancelledError:
            raise
        except Exception as exc:
            if not self._observer.closed:
                await self._observer.athrow(exc, self._namespace)


__all__ = ("FromIterable",)
