__all__ = ("FromAsyncIterable",)


# Internal
import typing as T
from asyncio import Task, CancelledError
from weakref import ReferenceType
from contextlib import suppress
from collections.abc import AsyncGenerator

# External
from prop import AbstractPromise

# Project
from ..disposable import AnonymousDisposable
from ..misc.namespace import get_namespace
from ..abstract.observer import Observer
from ..abstract.observable import Observable

# Generic Types
K = T.TypeVar("K")


class FromAsyncIterable(Observable[K, AnonymousDisposable]):
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

    def __observe__(self, observer: Observer[K, T.Any]) -> AnonymousDisposable:
        """Schedule async iterator flush and register observer."""

        task_ref: T.Optional["ReferenceType[Task[None]]"] = None
        observer_lastly: T.Optional[AbstractPromise[None]] = None

        def stop() -> None:
            task: T.Optional[Task[None]] = None if task_ref is None else task_ref()
            if task:
                task.cancel()
            if observer_lastly:
                observer_lastly.cancel()

        if self._async_iterator:
            task_ref = ReferenceType(
                observer.loop.create_task(self._worker(self._async_iterator, observer))
            )

            # Cancel task when observer closes
            observer_lastly = observer.lastly(stop)

            # Clear reference to prevent reiterations
            self._async_iterator = None
        elif not (observer.closed or observer.keep_alive):
            observer.loop.create_task(observer.aclose())

        return AnonymousDisposable(stop)

    async def _worker(
        self, async_iterator: T.AsyncIterator[K], observer: Observer[K, T.Any]
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
                    await observer.araise(exc, self._namespace)

            if isinstance(async_iterator, AsyncGenerator):
                # Ensure async_generator gets closed
                await async_iterator.aclose()

            if not (observer.closed or observer.keep_alive):
                await observer.aclose()
