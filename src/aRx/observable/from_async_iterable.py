__all__ = ("FromAsyncIterable",)


# Internal
import typing as T
from uuid import UUID, uuid4
from asyncio import FIRST_COMPLETED, Future, CancelledError, wait
from collections.abc import AsyncGenerator

# Project
from ..disposable import AnonymousDisposable
from ..abstract.observer import Observer
from ..abstract.observable import Observable

# Generic Types
K = T.TypeVar("K")


class FromAsyncIterable(Observable[K]):
    """Observable that uses an async iterable as data source."""

    @staticmethod
    async def _worker(
        async_iterator: T.AsyncIterator[K],
        observer: Observer[K, T.Any],
        stop: Future[None],
        namespace: UUID,
    ) -> None:
        pending = None

        try:
            async for data in async_iterator:
                if observer.closed:
                    break

                pending = None
                (done,), (pending,) = await wait(
                    (observer.asend(data), stop), return_when=FIRST_COMPLETED
                )

                if observer.closed or done is stop:
                    break
        except CancelledError:
            raise
        except Exception as exc:
            if not observer.closed:
                await observer.araise(exc, namespace)

        if pending and pending is not stop:
            await pending

        if isinstance(async_iterator, AsyncGenerator):
            # Ensure async_generator gets closed
            await async_iterator.aclose()

        if not (observer.closed or observer.keep_alive):
            await observer.aclose()

    def __init__(self, async_iterable: T.AsyncIterable[K], **kwargs: T.Any) -> None:
        """FromAsyncIterable constructor.

        Arguments:
            async_iterable: AsyncIterable to be iterated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self.namespace = uuid4()

        # Internal
        self._async_iterator: T.Optional[T.AsyncIterator[K]] = async_iterable.__aiter__()

    def __observe__(self, observer: Observer[K, T.Any]) -> AnonymousDisposable:
        """Schedule async iterator flush and register observer."""
        stop_future: "Future[None]" = observer.loop.create_future()

        def stop() -> None:
            stop_future.set_result(None)

        if self._async_iterator:
            observer.loop.create_task(
                FromAsyncIterable._worker(
                    self._async_iterator, observer, stop_future, self.namespace
                )
            )

            # Cancel task when observer closes
            observer.lastly(stop)

            # Clear reference to prevent reiterations
            self._async_iterator = None
        elif not (observer.closed or observer.keep_alive):
            observer.loop.create_task(observer.aclose())

        return AnonymousDisposable(stop)
