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
        try:
            for data in iterator:
                if observer.closed:
                    break

                await observer.asend(data)
        except Exception as ex:
            await observer.araise(ex)

        if not (observer.closed or observer.keep_alive):
            await observer.aclose()

    def __init__(self, iterable: T.Iterable[K], **kwargs) -> None:
        """FromIterable constructor.

       Arguments:
           iterable: Iterable to be converted.
           kwargs: Keyword parameters for super.

       """
        super().__init__(**kwargs)

        # Internal
        self._iterator = iter(iterable)

    def __observe__(self, observer: Observer) -> Disposable:
        """Schedule iterator flush and register observer."""
        task = None
        if hasattr(self, "_iterator"):
            task = observer.loop.create_task(
                FromIterable._worker(self._iterator, observer)
            )

            # Clear reference to prevent reiterations
            del self._iterator
        elif not (observer.closed or observer.keep_alive):
            observer.loop.create_task(observer.aclose())

        return AnonymousDisposable(None if task is None else task.cancel)
