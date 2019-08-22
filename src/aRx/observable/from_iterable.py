__all__ = ("FromIterable",)


# Internal
import typing as T
from asyncio import Task, CancelledError
from weakref import ReferenceType
from contextlib import suppress

# External
from aRx.abstract.namespace import get_namespace

# Project
from ..disposable import AnonymousDisposable
from ..abstract.observer import Observer
from ..abstract.observable import Observable

# Generic Types
K = T.TypeVar("K")


class FromIterable(Observable[K]):
    """Observable that uses an iterable as data source."""

    def __init__(self, iterable: T.Iterable[K], **kwargs: T.Any) -> None:
        """FromIterable constructor.

       Arguments:
           iterable: Iterable to be converted.
           kwargs: Keyword parameters for super.

       """
        super().__init__(**kwargs)

        # Internal
        self._iterator: T.Optional[T.Iterator[K]] = iter(iterable)
        self._namespace = get_namespace(self, "next")

    # TODO: Make a base class to avoid code repetition
    def __observe__(self, observer: Observer[K], keep_alive: bool) -> AnonymousDisposable:
        """Schedule async iterator flush and register observer."""

        if not self._iterator:
            raise RuntimeError("Iterator is already closed")

        async def stop() -> None:
            task.cancel()

            # Close observer if necessary
            if observer and not (observer.closed or keep_alive):
                await observer.aclose()

        task = observer.loop.create_task(self._worker(self._iterator, observer))

        # Clear reference to prevent reiterations
        self._iterator = None

        return AnonymousDisposable(stop)

    async def _worker(self, iterator: T.Iterator[K], observer: Observer[K]) -> None:
        with suppress(CancelledError):
            try:
                for data in iterator:
                    if observer.closed:
                        break

                    await observer.asend(data, self._namespace)

            except CancelledError:
                raise
            except Exception as exc:
                if not observer.closed:
                    await observer.araise(exc, self._namespace)

            if not (observer.closed or observer.keep_alive):
                await observer.aclose()
