# Internal
import typing as T
from collections import deque

# External
import typing_extensions as Te

# Project
from ..streams import SingleStream

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace

# Generic Types
K = T.TypeVar("K")


class Take(SingleStream[K]):
    def __init__(self, count: int, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)

        self._count = abs(count)
        self._reverse_queue: T.Optional[Te.Deque[T.Tuple[K, "Namespace"]]] = (
            deque(maxlen=self._count) if count < 0 else None
        )

    async def _asend(self, value: K, namespace: "Namespace") -> None:
        if self._reverse_queue is None:
            if self._count > 0:
                self._count -= 1
                awaitable: T.Awaitable[T.Any] = super()._asend(value, namespace)
            else:
                awaitable = self.aclose()

            # Remove reference early to avoid keeping large objects in memory
            del value

            await awaitable
        else:
            self._reverse_queue.append((value, namespace))

    async def _aclose(self) -> None:
        while self._reverse_queue:
            await super()._asend(*self._reverse_queue.popleft())

        return await super()._aclose()


__all__ = ("Take",)
