# Internal
import typing as T

# Project
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable import AnonymousDisposable

K = T.TypeVar('K')


class ObservableFromAsyncIterable(Observable, T.Generic[K]):
    """Observable that uses an async iterable as data source.

    Attributes:
        async_iterator: AsyncIterator to be converted.
    """

    def __init__(self, async_iterable: T.AsyncIterable, **kwargs) -> None:
        """ObservableFromAsyncIterable constructor.

        Args:
            async_iterable: AsyncIterable to be converted.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # TODO: FIX in Python 3.7
        self.async_iterator = async_iterable.__aiter__()

    async def _worker(self, observer: Observer) -> None:
        async for value in self.async_iterator:
            try:
                await observer.asend(value)
            except Exception as ex:
                if await observer.araise(ex):
                    break

        await observer.aclose()

    async def __aobserve__(self, observer: Observer) -> Disposable:
        task = observer.loop.create_task(self._worker(observer))

        async def cancel():
            task.cancel()

        return AnonymousDisposable(cancel)
