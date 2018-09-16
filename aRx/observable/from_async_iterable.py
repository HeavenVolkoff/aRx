__all__ = ("FromAsyncIterable",)

import typing as T
from asyncio import FIRST_COMPLETED, Future, CancelledError, wait

from ..disposable import AnonymousDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable
from ..abstract.observable import Observable

K = T.TypeVar("K")


class FromAsyncIterable(Observable[K]):
    """Observable that uses an async iterable as data source."""

    @staticmethod
    async def _worker(async_iterator: T.AsyncIterator, observer: Observer, stop: Future):
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
                await observer.araise(exc)

        if pending and pending is not stop:
            await pending

        if isinstance(async_iterator, T.AsyncGenerator):
            # Ensure async_generator gets closed
            await async_iterator.aclose()

        if not (observer.closed or observer.keep_alive):
            await observer.aclose()

    def __init__(self, async_iterable: T.AsyncIterable[K], **kwargs) -> None:
        """FromAsyncIterable constructor.

        Arguments:
            async_iterable: AsyncIterable to be iterated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # Internal
        self._async_iterator: T.Optional[T.AsyncIterator] = async_iterable.__aiter__()

    def __observe__(self, observer: Observer) -> Disposable:
        """Schedule async iterator flush and register observer."""
        stop_future: T.Optional[Future] = None

        def stop():
            if stop_future:
                stop_future.set_result(None)

        if self._async_iterator:
            stop_future = T.cast(Future, observer.loop.create_future())

            observer.loop.create_task(
                FromAsyncIterable._worker(self._async_iterator, observer, stop_future)
            )

            # Cancel task when observer closes
            observer.lastly(stop)

            # Clear reference to prevent reiterations
            self._async_iterator = None
        elif not (observer.closed or observer.keep_alive):
            observer.loop.create_task(observer.aclose())

        return AnonymousDisposable(stop)
