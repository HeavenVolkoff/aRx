"""Work derived from async-timeout.

Reference: https://github.com/aio-libs/async-timeout
See original license in: ../licenses/LICENSE.async_timeout.txt
"""

import typing as T
import asyncio
from asyncio import AbstractEventLoop, get_event_loop
from weakref import ReferenceType

from .abstract.loopable import Loopable

current_task = getattr(asyncio, "current_task", asyncio.Task.current_task)


class expires(Loopable):
    """timeout context manager.

    Useful in cases when you want to apply timeout logic around block
    of code or in cases when asyncio.wait_for is not suitable. For example:

    >>> with expires(0.001):
    ...     async with aiohttp.get('https://github.com') as r:
    ...         await r.text()


    timeout - value in seconds or None to disable timeout logic
    loop - asyncio compatible event loop
    """

    def __init__(self, timeout: T.Optional[float], **kwargs) -> None:
        """expires Constructor."""
        super().__init__(**kwargs)

        # Internal
        self._expired = False
        self._timeout = timeout
        self._expire_at = 0.0
        self._cancel_handler = None  # type: T.Optional[asyncio.Handle]

    def start(self) -> "expires":
        self._expired = False

        if self._timeout is not None:
            # Get current task
            task = current_task(self.loop)
            if task is None:
                raise RuntimeError("Timeout context manager should be used inside a task")

            task_ref = ReferenceType(task)
            self._expire_at = self.loop.time()
            if self._timeout <= 0:
                self._cancel_handler = self.loop.call_soon(self._expire_task, task_ref)
            else:
                self._expire_at += self._timeout
                self._cancel_handler = self.loop.call_at(
                    self._expire_at, self._expire_task, task_ref
                )

        return self

    def __enter__(self) -> "expires":
        return self.start()

    def __exit__(self, exc_type: T.Type[BaseException], exc: BaseException, _) -> bool:
        if self._cancel_handler is not None:
            self._cancel_handler.cancel()
            self._cancel_handler = None

        if exc_type is asyncio.CancelledError and self._expired:
            raise asyncio.TimeoutError

        return False

    def _expire_task(self, task_ref: ReferenceType) -> None:
        task = task_ref()
        if task is not None:
            task.cancel()
            self._expired = True

    @property
    def remaining(self) -> float:
        """Time remaining for task to be cancelled."""
        return max(self._expire_at - self.loop.time(), 0.0)

    @property
    def expired(self) -> bool:
        """Whether task was cancelled or not."""
        return self._expired
