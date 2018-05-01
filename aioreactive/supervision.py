# Internal
import typing as T

from collections.abc import Awaitable

# Project
from . import abstract

K = T.TypeVar("K")


class Supervision(Awaitable, abstract.Disposable):
    """Async stream factory.

    A helper class that makes it possible to subscribe both
    using await and async-with. You will most likely not use this class
    directly, but it will created when using subscribe()."""

    def __init__(
        self, observable: abstract.Observable, observer: abstract.Observer[K]
    ):
        self._observer = observer
        self._observable = observable
        self._subscription = None  # type: T.Optional[abstract.Disposable]

    def __await__(self):
        """Await stream creation."""
        return self.create().__await__()

    async def create(self):
        """Awaits stream creation.

        Awaits until stream has been created, and returns the new
        stream.

        """
        if self._subscription is None:
            self._subscription = await self._observable.__aobserve__(
                self._observer
            )

        return self._subscription

    async def __aenter__(self) -> abstract.Disposable:
        """Awaits subscription creation."""
        return await self.create()

    async def __adispose__(self) -> None:
        """Closes stream."""
        if self._subscription is not None:
            await self._subscription.__adispose__()

        self._subscription = None


def observe(observable: abstract.Observable,
            observer: abstract.Observer[K]) -> Supervision:
    """Start streaming source into observer.

    Returns an AsyncStreamFactory that is lazy in the sense that it will
    not start the source before it's either awaited or entered using
    async-with.

    Examples:

    1. Awaiting stream with explicit cancel:

    stream = await subscribe(source, observer)
    async for x in stream:
        print(x)

    stream.cancel()

    2. Start streaming with a context manager:

    async with subscribe(source, observer) as stream:
        async for x in stream:
            print(x)

    3. Start streaming without a specific observer

    async with subscribe(source) as stream:
        async for x in stream:
            print(x)

    Keyword arguments:
    observer -- Optional AsyncObserver that will receive all events sent through
        the stream.

    Returns AsyncStreamFactory that may either be awaited or entered
    using async-for.
    """
    return Supervision(observable, observer)


async def inquire(
    observer: abstract.Observer[K], observable: abstract.Observable
) -> K:
    async with Supervision(observable, observer):
        return await observer
