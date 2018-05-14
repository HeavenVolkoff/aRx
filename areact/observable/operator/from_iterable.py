# Internal
import typing as T

# Project
from ..base import BaseObservable
from aioreactive.abstract import Observer, Disposable
from aioreactive.disposable import AnonymousDisposable

K = T.TypeVar('K')


class FromIterable(BaseObservable, T.Generic[K]):
    def __init__(self, iterable, **kwargs) -> None:
        super().__init__(**kwargs)
        self.iterator = iter(iterable)

    async def __aobserve__(self, observer: Observer) -> Disposable:
        async def worker() -> None:
            for value in self.iterator:
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


def from_iterable(iterable: T.Iterable[K]) -> FromIterable:
    """Convert an iterable to a source stream.

    1 - xs = from_iterable([1,2,3])

    Returns the source stream whose elements are pulled from the
    given (async) iterable sequence."""

    return FromIterable(iterable)
