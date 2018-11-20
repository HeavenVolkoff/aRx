"""Work derived from async-timeout written by Andrew Svetlov.

Reference:
    https://github.com/aio-libs/async-timeout
See original license in:
    https://raw.githubusercontent.com/aio-libs/async-timeout/3b295845d830357fbcf99b0acd55708e44a0e3ac/LICENSE
"""

__all__ = ("auto_timeout", "expires")

# Internal
import typing as T
from types import TracebackType
from asyncio import Task, Handle, TimeoutError, CancelledError
from weakref import ReferenceType
from contextlib import AbstractContextManager

# Project
from .abstract.loopable import Loopable
from .misc.current_task import current_task

# Typing helper
Number = T.Union[int, float]


# noinspection PyPep8Naming
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

    def __eq__(self, other: object) -> bool:
        if isinstance(other, auto_timeout):
            return (
                self.timeout == self.timeout
                and self.min == self.min
                and self.max == self.max
                and self.step == self.step
            )

        return self.timeout == other

    def __lt__(self, other: Number) -> bool:
        return self.timeout < other

    def __le__(self, other: Number) -> bool:
        return self.timeout <= other

    def __gt__(self, other: Number) -> bool:
        return self.timeout > other

    def __ge__(self, other: Number) -> bool:
        return self.timeout >= other

    def __int__(self) -> int:
        return int(self.timeout)

    def __float__(self) -> float:
        return self.timeout

    def __bool__(self) -> bool:
        return bool(self.timeout)

    def __add__(self, other: Number) -> float:
        return self.timeout + other

    def __radd__(self, other: Number) -> float:
        return other + self.timeout

    def __sub__(self, other: Number) -> float:
        return self.timeout - other

    def __rsub__(self, other: Number) -> float:
        return other - self.timeout

    def __mul__(self, other: Number) -> float:
        return self.timeout * other

    def __rmul__(self, other: Number) -> float:
        return other * self.timeout

    def __truediv__(self, other: Number) -> float:
        return self.timeout / other

    def __rtruediv__(self, other: Number) -> float:
        return other / self.timeout

    def __floordiv__(self, other: int) -> int:
        return int(self) // other

    def __rfloordiv__(self, other: int) -> int:
        return other // int(self)

    def update(self, remaining: T.Union[int, float]) -> None:
        if remaining == 0:
            self.timeout = min(self.timeout + self.step, self.max)
        elif remaining > self.threshold:
            self.timeout = max(self.timeout - self.step, self.min)


# noinspection PyPep8Naming
class expires(AbstractContextManager["expires"], Loopable):
    """timeout context manager.

    Useful in cases when you want to apply timeout logic around block
    of code or in cases when asyncio.wait_for is not suitable. For example:

    >>> with expires(0.001):
    ...     async with aiohttp.get('https://github.com') as r:
    ...         await r.text()
    """

    def __init__(
        self,
        timeout: T.Optional[T.Union[float, auto_timeout]],
        suppress: bool = False,
        **kwargs: T.Any,
    ) -> None:
        """expires Constructor."""
        super().__init__(**kwargs)

        # Internal
        self._task: T.Optional[ReferenceType[Task[T.Any]]] = None
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
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional[TracebackType],
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

    def _expire_task(self) -> None:
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

    def reset(self) -> None:
        task = self._task() if self._task else None
        if task is None:
            raise ReferenceError("Task reference is not available anymore")

        self.__exit__(None, None, None)
        self._task = ReferenceType(task)
        self.__enter__()
