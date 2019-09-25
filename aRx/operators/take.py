"""Take

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T
from collections import deque

# External
import typing_extensions as Te

# Project
from ..errors import ObserverClosedError
from ..streams import SingleStream

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace


# Generic Types
K = T.TypeVar("K")


class _TakeMark(ObserverClosedError):
    pass


class Take(SingleStream[K]):
    def __init__(self, count: int, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)

        self._count = abs(count)
        self._reverse_queue: T.Optional[Te.Deque[T.Tuple[K, "Namespace"]]] = (
            deque(maxlen=self._count) if count < 0 else None
        )

    async def _asend(self, value: K, namespace: "Namespace") -> None:
        if self._reverse_queue is None:
            if self._count <= 0:
                raise _TakeMark(self)

            self._count -= 1
            awaitable: T.Awaitable[T.Any] = super()._asend(value, namespace)

            # Remove reference early to avoid keeping large objects in memory
            del value

            await awaitable
        else:
            self._reverse_queue.append((value, namespace))

    async def _athrow(self, exc: Exception, namespace: "Namespace") -> bool:
        if isinstance(exc, _TakeMark):
            return True
        return await super()._athrow(exc, namespace)

    async def _aclose(self) -> None:
        while self._reverse_queue:
            await super()._asend(*self._reverse_queue.popleft())

        return await super()._aclose()


__all__ = ("Take",)
