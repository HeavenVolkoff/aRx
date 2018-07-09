__all__ = ("FromIterable", )

# Internal
import typing as T

# Project
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable import AnonymousDisposable

K = T.TypeVar('K')


class FromIterable(Observable, T.Generic[K]):
    """Observable that uses an iterable as data source."""

    @staticmethod
    async def _worker(iterator: T.Iterator, observer: Observer) -> None:
        ex = None
        while ex is None:
            try:
                data = next(iterator)
            except Exception as _ex:
                ex = _ex
            else:
                await observer.asend(data)

        if isinstance(ex, StopIteration) or not await observer.araise(ex):
            await observer.aclose()

    def __init__(self, iterable: T.Iterable[K], **kwargs) -> None:
        """FromIterable constructor.

       Arguments:
           iterable: Iterable to be converted.
           kwargs: Keyword parameters for super.

       """
        super().__init__(**kwargs)
        self._iterator = iter(iterable)

    def __observe__(self, observer: Observer) -> Disposable:
        """Schedule iterator flush and register observer."""
        if self._iterator is not None:
            task = observer.loop.create_task(
                FromIterable._worker(self._iterator, observer)
            )

            # Clear reference to prevent reiterations
            self._iterator = None

        async def cancel():
            task.cancel()

        return AnonymousDisposable(cancel)
