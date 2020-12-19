"""FromAsyncIterable

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T
from asyncio import get_running_loop

# Project
from ._internal.from_source import FromSource

# Generic Types
K = T.TypeVar("K")


class FromIterableIterable(FromSource[K, T.AsyncIterator[K]]):
    """Observable that uses an async iterable as data source."""

    def __init__(self, async_iterable: T.AsyncIterable[K], **kwargs: T.Any) -> None:
        """FromAsyncIterable constructor.

        Arguments:
            async_iterable: AsyncIterable to be iterated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(async_iterable.__aiter__(), **kwargs)

    async def _worker(self) -> None:
        assert self._observer is not None

        loop = get_running_loop()
        try:
            async for data in self._source:
                if self._observer.closed:
                    break

                await self._observer.asend(data, self._namespace)
        except Exception as exc:
            await self._observer.athrow(exc, self._namespace)
        finally:
            if isinstance(self._source, T.AsyncGenerator):
                # Ensure async_generator gets closed
                loop.create_task(self._source.aclose())


__all__ = ("FromIterableIterable",)
