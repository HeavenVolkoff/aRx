# Internal
import typing as T
from collections import deque

# Project
from ..stream import SingleStream
from ..abstract import Namespace

# Generic Types
K = T.TypeVar("K")


class Skip(SingleStream[K]):
    def __init__(self, count: int, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)

        self._count = abs(count)
        self._reverse_queue: T.Optional[T.Deque[K]] = (
            deque(maxlen=self._count) if count < 0 else None
        )

    async def __asend__(self, value: K, namespace: Namespace) -> None:
        if self._reverse_queue is not None:
            # Skip values from end
            value = self._reverse_queue[0]
            self._reverse_queue.append(value)
        elif self._count > 0:
            # Skip values from start
            self._count -= 1
            return

        awaitable = super().__asend__(value, namespace)

        # Remove reference early to avoid keeping large objects in memory
        del value

        await awaitable

    async def __aclose__(self) -> None:
        if self._reverse_queue is not None:
            self._reverse_queue.clear()

        await super().__aclose__()


__all__ = ("Skip",)
