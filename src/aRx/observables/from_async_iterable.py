# Internal
import typing as T
from asyncio import CancelledError

# External
import typing_extensions as Te

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

        cancelled = False

        try:
            async for data in self._source:
                if self._observer.closed:
                    break

                await self._observer.asend(data, self._namespace)
        except CancelledError:
            cancelled = True
            raise
        except Exception as exc:
            if not self._observer.closed:
                await self._observer.athrow(exc, self._namespace)
        except BaseException:
            cancelled = True
            raise
        finally:
            if not cancelled and isinstance(self._source, Te.AsyncGenerator):
                # Ensure async_generator gets closed
                await self._source.aclose()


__all__ = ("FromIterableIterable",)
