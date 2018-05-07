# Internal
import typing as T

# Project
from ...abstract import Observer, Observable, Disposable
from ...disposable import AnonymousDisposable

K = T.TypeVar('K')


class FromAsyncIterable(Observable, T.Generic[K]):
    def __init__(self, iterable, **kwargs) -> None:
        super().__init__(**kwargs)

        # TODO: FIX in Python 3.7
        self.async_iterator = iterable.__aiter__()

    async def __aobserve__(self, observer: Observer) -> Disposable:
        async def worker() -> None:
            async for value in self.async_iterator:
                try:
                    await observer.asend(value)
                except Exception as ex:
                    if await observer.araise(ex):
                        break

            await observer.aclose()

        task = observer.loop.create_task(worker())

        async def cancel():
            task.cancel()

        return AnonymousDisposable(cancel)


def from_async_iterable(iterable: T.AsyncIterable[K]) -> Observable:
    """Convert an async iterable to a source stream.

    2 - xs = from_async_iterable(async_iterable)

    Returns the source stream whose elements are pulled from the
    given (async) iterable sequence."""
    return FromAsyncIterable(iterable)
