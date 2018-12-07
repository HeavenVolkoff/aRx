__all__ = ("FromIterable",)


# Internal
import typing as T
from asyncio import Task, CancelledError
from weakref import ReferenceType
from contextlib import suppress

# External
from prop import AbstractPromise

# Project
from ..disposable import AnonymousDisposable
from ..misc.namespace import get_namespace
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

    def __observe__(self, observer: Observer[K, T.Any]) -> AnonymousDisposable:
        """Schedule iterator flush and register observer."""

        task_ref: T.Optional["ReferenceType[Task[None]]"] = None
        observer_lastly: T.Optional[AbstractPromise[None]] = None

        def stop() -> None:
            task: T.Optional[Task[None]] = None if task_ref is None else task_ref()
            if task:
                task.cancel()
            if observer_lastly:
                observer_lastly.cancel()

        if self._iterator:
            task_ref = ReferenceType(
                observer.loop.create_task(self._worker(self._iterator, observer))
            )

            # Cancel task when observer closes
            observer_lastly = observer.lastly(stop)

            # Clear reference to prevent reiterations
            self._iterator = None
        elif not (observer.closed or observer.keep_alive):
            observer.loop.create_task(observer.aclose())

        return AnonymousDisposable(stop)

    async def _worker(self, iterator: T.Iterator[K], observer: Observer[K, T.Any]) -> None:
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
