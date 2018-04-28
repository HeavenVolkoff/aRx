import asyncio

from .. import abstract
from ..core import AsyncObserver


class Unit(abstract.AsyncObservable, abstract.AsyncDisposable):
    def __init__(
        self, value, *, loop: asyncio.AbstractEventLoop = None
    ) -> None:
        self.loop = loop if loop else asyncio.get_event_loop()
        self.value = value

        self._task = None  # type: asyncio.Task

    async def worker(self, sink: AsyncObserver) -> None:
        """Task for sending value."""

        if asyncio.iscoroutine(self.value) or asyncio.isfuture(self.value):
            try:
                value = await self.value
            except asyncio.CancelledError:
                pass
            except Exception as ex:
                await sink.araise(ex)
            else:
                await sink.asend(value)
        else:
            await sink.asend(self.value)

        await sink.aclose()

    def clear_task(self, fut=None):
        if fut is not None:
            # Treat task callback response
            try:
                fut.result()
            except (asyncio.CancelledError, asyncio.InvalidStateError):
                # In case future was cancelled or not resolved,
                # just ignore and clear it
                pass

        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def __adispose__(self):
        self.clear_task()

    async def __aobserve__(
        self, observer: AsyncObserver
    ) -> abstract.AsyncDisposable:
        # Add worker execution to loop queue
        self._task = self.loop.create_task(self.worker(observer))
        # Add callback to clear task after it's completion
        self._task.add_done_callback(self.clear_task)

        return self


def unit(value) -> Unit:
    """Returns a source stream that sends a single value.

    Example:
    1. xs = unit(42)
    2. xs = unit(future)

    Keyword arguments:
    value -- Single value to send into the source stream.

    Returns a source stream that is sent the single specified value.
    """

    return Unit(value)
