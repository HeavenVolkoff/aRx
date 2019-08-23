# Internal
import typing as T
from asyncio import CancelledError
from contextlib import suppress
from collections.abc import AsyncGenerator

# Project
from ..protocols import ObserverProtocol
from ._internal.from_iterable_base import FromIterableBase

# Generic Types
K = T.TypeVar("K")


class FromIterableIterable(FromIterableBase[K, T.AsyncIterator[K]]):
    """Observable that uses an async iterable as data source."""

    def __init__(self, async_iterable: T.AsyncIterable[K], **kwargs: T.Any) -> None:
        """FromAsyncIterable constructor.

        Arguments:
            async_iterable: AsyncIterable to be iterated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # Internal
        self._iterator = async_iterable.__aiter__()

    async def _worker(
        self, async_iterator: T.AsyncIterator[K], observer: ObserverProtocol[K]
    ) -> None:
        with suppress(CancelledError):
            try:
                async for data in async_iterator:
                    if observer.closed:
                        break

                    await observer.asend(data, self._namespace)
            except CancelledError:
                raise
            except Exception as exc:
                if not observer.closed:
                    await observer.athrow(exc, self._namespace)

            if isinstance(async_iterator, AsyncGenerator):
                # Ensure async_generator gets closed
                await async_iterator.aclose()

            if not (observer.closed or observer.keep_alive):
                await observer.aclose()


__all__ = ("FromIterableIterable",)
