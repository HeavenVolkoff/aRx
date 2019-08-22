# Internal
import typing as T
from asyncio import CancelledError
from contextlib import suppress

# Project
from ..protocols import ObserverProtocol
from ._from_iterable_base import _FromAsyncBase

# Generic Types
K = T.TypeVar("K")


class FromIterable(_FromAsyncBase[K, T.Iterable[K]]):
    """Observable that uses an iterable as data source."""

    def __init__(self, iterable: T.Iterable[K], **kwargs: T.Any) -> None:
        """FromIterable constructor.

       Arguments:
           iterable: Iterable to be converted.
           kwargs: Keyword parameters for super.

       """
        super().__init__(**kwargs)

        # Internal
        self._iterator = iter(iterable)

    async def _worker(self, iterator: T.Iterable[K], observer: ObserverProtocol[K]) -> None:
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
                    await observer.athrow(exc, self._namespace)

            if not (observer.closed or observer.keep_alive):
                await observer.aclose()


__all__ = ("FromIterable",)
