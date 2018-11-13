"""Work derived from async-timeout.

Reference: https://github.com/aio-libs/async-timeout
See original license in: ../licenses/LICENSE.async_timeout.txt
"""

# Internal
import typing as T
from asyncio import Task, Handle, TimeoutError, CancelledError
from weakref import ReferenceType
from functools import total_ordering
from contextlib import AbstractContextManager

# Project
from .abstract.loopable import Loopable
from .misc.current_task import current_task


# noinspection PyPep8Naming
@total_ordering
class auto_timeout:
    def __init__(
        self,
        min: float,
        step: float = 1.0,
        *,
        max: T.Optional[float] = None,
        initial: T.Optional[float] = None,
        threshold: T.Optional[float] = None,
    ) -> None:
        assert min > 0 and (max is None or (max > 0 and max > min))

        self.min = float(min)
        self.max = float("Inf") if max is None else float(max)
        self.step = float(step)
        self.timeout = self.min if initial is None else float(initial)
        self.threshold = float(threshold) if threshold else self.step

    def __eq__(self, other):
        if isinstance(other, auto_timeout):
            return (
                self.timeout == self.timeout
                and self.min == self.min
                and self.max == self.max
                and self.step == self.step
            )

        return self.timeout == other

    def __lt__(self, other):
        return self.timeout < other

    def __int__(self):
        return int(self.timeout)

    def __float__(self):
        return self.timeout

    def __bool__(self):
        return bool(self.timeout)

    def __add__(self, other):
        return self.timeout + other

    def __radd__(self, other):
        return other + self.timeout

    def __sub__(self, other):
        return self.timeout - other

    def __rsub__(self, other):
        return other - self.timeout

    def __mul__(self, other):
        return self.timeout * other

    def __rmul__(self, other):
        return other * self.timeout

    def __truediv__(self, other):
        return self.timeout / other

    def __rtruediv__(self, other):
        return other / self.timeout

    def __floordiv__(self, other):
        return self.timeout // other

    def __rfloordiv__(self, other):
        return other // self.timeout

    def update(self, remaining: T.Union[int, float]):
        if remaining == 0:
            self.timeout = min(self.timeout + self.step, self.max)
        elif remaining > self.threshold:
            self.timeout = max(self.timeout - self.step, self.min)


# noinspection PyPep8Naming
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

    def __init__(
        self, timeout: T.Optional[T.Union[float, auto_timeout]], suppress=False, **kwargs
    ) -> None:
        """expires Constructor."""
        super().__init__(**kwargs)

        # Internal
        self._task: T.Optional[ReferenceType[Task]] = None
        self._expired = False
        self._timeout = timeout
        self._suppress = suppress
        self._expire_at = 0.0
        self._cancel_handler: T.Optional[Handle] = None

    def __enter__(self) -> "expires":
        self._expired = False

        if self._timeout is not None:
            # Get current task
            if self._task is None:
                task = current_task(self.loop)
                if task is None:
                    raise RuntimeError("Timeout context manager should be used inside a task")

                self._task = ReferenceType(task)

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

        # Clear some references
        self._task = None
        self._cancel_handler = None

        if isinstance(self._timeout, auto_timeout):
            self._timeout.update(self.remaining)

        if exc_type is CancelledError and self._expired:
            if self._suppress:
                return True

            raise TimeoutError

        return False

    def _expire_task(self):
        task = self._task() if self._task else None
        if task:
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

    def reset(self):
        task = self._task() if self._task else None
        if task is None:
            raise ReferenceError("Task reference is not available anymore")

        self.__exit__(None, None, None)
        self._task = ReferenceType(task)
        self.__enter__()
