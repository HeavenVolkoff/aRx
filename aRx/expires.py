import typing as T
import asyncio
from asyncio import AbstractEventLoop, get_event_loop
from weakref import ReferenceType

current_task = getattr(asyncio, "current_task", asyncio.Task.current_task)


class expires:
    """timeout context manager.

    Useful in cases when you want to apply timeout logic around block
    of code or in cases when asyncio.wait_for is not suitable. For example:

    >>> with expires(0.001):
    ...     async with aiohttp.get('https://github.com') as r:
    ...         await r.text()


    timeout - value in seconds or None to disable timeout logic
    loop - asyncio compatible event loop
    """

    def __init__(self, timeout: T.Optional[float], *, loop: AbstractEventLoop = None) -> None:
        """expires Constructor."""
        # Internal
        self._loop = get_event_loop() if loop is None else loop
        self._timeout = timeout
        self._cancel_at = 0.0
        self._cancelled = False
        self._cancel_handler = None  # type: T.Optional[asyncio.Handle]

    def __enter__(self) -> "expires":
        self._cancelled = False

        if self._timeout is not None:
            # Get current task
            task = current_task(self._loop)
            if task is None:
                raise RuntimeError("Timeout context manager should be used inside a task")

            task_ref = ReferenceType(task)
            self._cancel_at = self._loop.time()
            if self._timeout <= 0:
                self._cancel_handler = self._loop.call_soon(self._cancel_task, task_ref)
            else:
                self._cancel_at += self._timeout
                self._cancel_handler = self._loop.call_at(
                    self._cancel_at, self._cancel_task, task_ref
                )

        return self

    def __exit__(self, exc_type: T.Type[BaseException], exc: BaseException, _) -> bool:
        self._cancel_handler.cancel()
        self._cancel_handler = None

        if exc_type is asyncio.CancelledError and self._cancelled:
            raise asyncio.TimeoutError

        return False

    def _cancel_task(self, task_ref: ReferenceType) -> None:
        task = task_ref()
        if task is not None:
            task.cancel()
            self._cancelled = True

    @property
    def remaining(self) -> float:
        """Time remaining for task to be cancelled."""
        return max(self._cancel_at - self._loop.time(), 0.0)

    @property
    def cancelled(self) -> bool:
        """Whether task was cancelled or not."""
        return self._cancelled
