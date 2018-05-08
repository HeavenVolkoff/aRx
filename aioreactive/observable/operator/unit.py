# Internal
from asyncio import (
    Task, isfuture, iscoroutine, CancelledError, InvalidStateError
)

# Project
from ..base import BaseObservable
from aioreactive.abstract import Observer, Disposable


class Unit(BaseObservable, Disposable):
    def __init__(self, value, **kwargs) -> None:
        super().__init__(**kwargs)

        self.value = value
        self._task = None  # type: Task

    def _clear_task(self, fut=None):
        if fut is not None:
            # Treat task callback response
            try:
                fut.result()
            except (CancelledError, InvalidStateError):
                # In case future was cancelled or not resolved,
                # just ignore and clear it
                pass

        if self._task is not None:
            self._task.cancel()
            self._task = None

    async def __adispose__(self):
        self._clear_task()

    async def _worker(self, observer: Observer) -> None:
        """Task for sending value."""

        if iscoroutine(self.value) or isfuture(self.value):
            try:
                value = await self.value
            except CancelledError:
                pass
            except Exception as ex:
                await observer.araise(ex)
            else:
                await observer.asend(value)
        else:
            await observer.asend(self.value)

        await observer.aclose()

    async def __aobserve__(self, observer: Observer) -> Disposable:
        # Add worker execution to loop queue
        self._task = observer.loop.create_task(self._worker(observer))
        # Add callback to clear task after it's completion
        self._task.add_done_callback(self._clear_task)

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
