__all__ = ("FromAsyncIterable",)

import typing as T
from asyncio import CancelledError
from contextlib import suppress

from ..disposable import AnonymousDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable
from ..abstract.observable import Observable
from ..misc.async_exit_stack import AsyncExitStack

K = T.TypeVar("K")


class FromAsyncIterable(Observable, T.Generic[K]):
    """Observable that uses an async iterable as data source."""

    @staticmethod
    async def _worker(async_iterator: T.AsyncIterator, observer: Observer) -> None:
        async with AsyncExitStack() as stack:
            if isinstance(async_iterator, T.AsyncGenerator):
                # Ensure async_generator gets closed
                stack.push_async_callback(async_iterator.aclose)

            # Redirect any error to observer
            stack.push_async_exit(
                lambda _, exc, __: (
                    None if observer.closed else (observer.loop.create_task(observer.araise(exc)))
                )
            )

            stack.push(suppress(CancelledError))
            async for data in async_iterator:
                if not observer.closed:
                    observer.loop.create_task(observer.asend(data))

        if not (observer.closed or observer.keep_alive):
            observer.loop.create_task(observer.aclose())

    def __init__(self, async_iterable: T.AsyncIterable[K], **kwargs) -> None:
        """FromAsyncIterable constructor.

        Arguments:
            async_iterable: AsyncIterable to be iterated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # Internal
        self._async_iterator = async_iterable.__aiter__()

    def __observe__(self, observer: Observer) -> Disposable:
        """Schedule async iterator flush and register observer."""
        task = None
        if hasattr(self, "_async_iterator"):
            task = observer.loop.create_task(
                FromAsyncIterable._worker(self._async_iterator, observer)
            )

            # Cancel task when observer closes
            observer.lastly(task.cancel)

            # Clear reference to prevent reiterations
            del self._async_iterator
        elif not (observer.closed or observer.keep_alive):
            observer.loop.create_task(observer.aclose())

        return AnonymousDisposable(None if task is None else task.cancel)
