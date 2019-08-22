__all__ = ("FromAsyncIterable",)


# Internal
import typing as T
from asyncio import Task, CancelledError
from weakref import ReferenceType
from contextlib import suppress
from collections.abc import AsyncGenerator

# External
from aRx.abstract.namespace import get_namespace

# Project
from ..disposable import AnonymousDisposable
from ..abstract.observer import Observer
from ..abstract.observable import Observable

# Generic Types
K = T.TypeVar("K")


class FromAsyncIterable(Observable[K]):
    """Observable that uses an async iterable as data source."""

    def __init__(self, async_iterable: T.AsyncIterable[K], **kwargs: T.Any) -> None:
        """FromAsyncIterable constructor.

        Arguments:
            async_iterable: AsyncIterable to be iterated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # Internal
        self._namespace = get_namespace(self, "anext")
        self._async_iterator: T.Optional[T.AsyncIterator[K]] = async_iterable.__aiter__()

    # TODO: Make a base class to avoid code repetition
    def __observe__(self, observer: Observer[K], keep_alive: bool) -> AnonymousDisposable:
        """Schedule async iterator flush and register observer."""

        if not self._async_iterator:
            raise RuntimeError("Iterator is already closed")

        async def stop() -> None:
            task.cancel()

            # Close observer if necessary
            if observer and not (observer.closed or keep_alive):
                await observer.aclose()

        task = observer.loop.create_task(self._worker(self._async_iterator, observer))

        # Clear reference to prevent reiterations
        self._async_iterator = None

        return AnonymousDisposable(stop)

    async def _worker(self, async_iterator: T.AsyncIterator[K], observer: Observer[K]) -> None:

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
                    await observer.araise(exc, self._namespace)

            if isinstance(async_iterator, AsyncGenerator):
                # Ensure async_generator gets closed
                await async_iterator.aclose()

            if not (observer.closed or observer.keep_alive):
                await observer.aclose()
