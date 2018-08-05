__all__ = ("FromAsyncIterable", )

# Internal
import typing as T

# Project
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable import AnonymousDisposable

K = T.TypeVar('K')


class FromAsyncIterable(Observable, T.Generic[K]):
    """Observable that uses an async iterable as data source."""

    @staticmethod
    async def _worker(
        async_iterator: T.AsyncIterator, observer: Observer
    ) -> None:
        try:
            async for data in async_iterator:
                if observer.closed:
                    break

                await observer.asend(data)
        except Exception as ex:
            await observer.araise(ex)

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
        self._async_iterator = async_iterable.__aiter__()

    def __observe__(self, observer: Observer) -> Disposable:
        """Schedule async iterator flush and register observer."""
        task = None
        if getattr(self, "_async_iterator", None) is not None:
            task = observer.loop.create_task(
                FromAsyncIterable._worker(self._async_iterator, observer)
            )

            # Clear reference to prevent reiterations
            del self._async_iterator
        elif not (observer.closed or observer.keep_alive):
            observer.loop.create_task(observer.aclose())

        return AnonymousDisposable(None if task is None else task.cancel)
