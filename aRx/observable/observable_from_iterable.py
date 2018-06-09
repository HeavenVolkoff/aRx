# Internal
import typing as T

# Project
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable import AnonymousDisposable

K = T.TypeVar('K')


class ObservableFromIterable(Observable, T.Generic[K]):
    """Observable that uses an iterable as data source.

    Attributes:
        iterator: Iterator to be converted.
    """

    def __init__(self, iterable, **kwargs) -> None:
        """ObservableFromIterable constructor.

       Args:
           iterable: Iterable to be converted.
           kwargs: Keyword parameters for super.

       """
        super().__init__(**kwargs)
        self.iterator = iter(iterable)

    async def _worker(self, observer: Observer) -> None:
        for value in self.iterator:
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
