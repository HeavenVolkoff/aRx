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
        ex = None
        while ex is None:
            try:
                # TODO: FIX in Python 3.7
                data = await async_iterator.__anext__()
            except Exception as _ex:
                ex = _ex
            else:
                await observer.asend(data)

        if isinstance(ex, StopAsyncIteration) or not await observer.araise(ex):
            await observer.aclose()

    def __init__(self, async_iterable: T.AsyncIterable[K], **kwargs) -> None:
        """FromAsyncIterable constructor.

        Arguments:
            async_iterable: AsyncIterable to be iterated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # TODO: FIX in Python 3.7
        self._async_iterator = async_iterable.__aiter__()

    def __observe__(self, observer: Observer) -> Disposable:
        """Schedule async iterator flush and register observer."""
        if self._async_iterator is not None:
            task = observer.loop.create_task(
                FromAsyncIterable._worker(self._async_iterator, observer)
            )

            # Clear reference to prevent reiterations
            self._async_iterator = None

        async def cancel():
            task.cancel()

        return AnonymousDisposable(cancel)
