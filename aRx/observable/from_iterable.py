__all__ = ("FromIterable",)

import typing as T

from ..disposable import AnonymousDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable
from ..abstract.observable import Observable

K = T.TypeVar("K")


class FromIterable(Observable[K]):
    """Observable that uses an iterable as data source."""

    @staticmethod
    async def _worker(iterator: T.Iterator, observer: Observer):
        try:
            for data in iterator:
                if observer.closed:
                    return

                await observer.asend(data)
        except Exception as ex:
            if observer.closed:
                return

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
            task = observer.loop.create_task(FromIterable._worker(self._iterator, observer))

            # Clear reference to prevent reiterations
            del self._iterator
        elif not (observer.closed or observer.keep_alive):
            observer.loop.create_task(observer.aclose())

        return AnonymousDisposable(None if task is None else task.cancel)
