__all__ = ("FromIterable",)


# Internal
import typing as T
from uuid import UUID, uuid4
from asyncio import FIRST_COMPLETED, Future, CancelledError, wait

# Project
from ..disposable import AnonymousDisposable
from ..abstract.observer import Observer
from ..abstract.observable import Observable

# Generic Types
K = T.TypeVar("K")


class FromIterable(Observable[K]):
    """Observable that uses an iterable as data source."""

    @staticmethod
    async def _worker(
        iterator: T.Iterator[K], observer: Observer[K, T.Any], stop: "Future[None]", namespace: UUID
    ) -> None:
        pending = None

        try:
            for data in iterator:
                if observer.closed:
                    break

                pending = None
                (done,), (pending,) = await wait(
                    (observer.asend(data), stop), return_when=FIRST_COMPLETED
                )

                if observer.closed or done is stop:
                    break
        except CancelledError:
            raise
        except Exception as exc:
            if not observer.closed:
                await observer.araise(exc, namespace)

        if pending and pending is not stop:
            await pending

        if not (observer.closed or observer.keep_alive):
            await observer.aclose()

    def __init__(self, iterable: T.Iterable[K], **kwargs: T.Any) -> None:
        """FromIterable constructor.

       Arguments:
           iterable: Iterable to be converted.
           kwargs: Keyword parameters for super.

       """
        super().__init__(**kwargs)

        self.namespace = uuid4()

        # Internal
        self._iterator: T.Optional[T.Iterator[K]] = iter(iterable)

    def __observe__(self, observer: Observer[K, T.Any]) -> AnonymousDisposable:
        """Schedule iterator flush and register observer."""
        stop_future: "Future[None]" = observer.loop.create_future()

        def stop() -> None:
            stop_future.set_result(None)

        if self._iterator:
            observer.loop.create_task(
                FromIterable._worker(self._iterator, observer, stop_future, self.namespace)
            )

            # Cancel task when observer closes
            observer.lastly(stop)

            # Clear reference to prevent reiterations
            self._iterator = None
        elif not (observer.closed or observer.keep_alive):
            observer.loop.create_task(observer.aclose())

        return AnonymousDisposable(stop)
