"""Work derived from async-timeout.

Reference: https://github.com/aio-libs/async-timeout
See original license in: ../licenses/LICENSE.async_timeout.txt
"""

import typing as T
from asyncio import Task, Handle, TimeoutError, CancelledError
from contextlib import AbstractContextManager

from .abstract.loopable import Loopable
from .misc.current_task import current_task


class expires(AbstractContextManager, Loopable):
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
        self._task = None  # type: T.Optional[Task]
        self._expired = False
        self._timeout = timeout
        self._expire_at = 0.0
        self._cancel_handler = None  # type: T.Optional[Handle]

    def __enter__(self) -> "expires":
        self._expired = False

        if self._timeout is not None:
            # Get current task
            if self._task is None:
                task = current_task(self.loop)
                if task is None:
                    raise RuntimeError("Timeout context manager should be used inside a task")

                self._task = task

            self._expire_at = self.loop.time()
            if self._timeout <= 0:
                self._cancel_handler = self.loop.call_soon(self._expire_task)
            else:
                self._expire_at += self._timeout
                self._cancel_handler = self.loop.call_at(self._expire_at, self._expire_task)

        return self

    def __exit__(
        self, exc_type: T.Optional[T.Type[BaseException]], exc: T.Optional[BaseException], _
    ) -> bool:
        if self._cancel_handler:
            self._cancel_handler.cancel()
            self._cancel_handler = None

        if self._task:
            self._task = None

        if exc_type is CancelledError and self._expired:
            raise TimeoutError

        return False

    def _expire_task(self):
        if self._task is not None:
            self._task.cancel()
            self._expired = True

    @property
    def remaining(self) -> float:
        """Time remaining for task to be cancelled."""
        return max(self._expire_at - self.loop.time(), 0.0)

    @property
    def expired(self) -> bool:
        """Whether task was cancelled or not."""
        return self._expired

    def reset(self):
        task = self._task
        if task:
            self.__exit__(None, None, None)
            self._task = task
            self.__enter__()
