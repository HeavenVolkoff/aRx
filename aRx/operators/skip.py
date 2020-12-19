"""Skip

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T
from collections import deque

# Project
from ..streams import SingleStream

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace


# Generic Types
K = T.TypeVar("K")


class Skip(SingleStream[K]):
    # TODO: Implement Skip athrow
    def __init__(self, count: int, **kwargs: T.Any) -> None:
        super().__init__(**kwargs)

        self._count = abs(count)
        self._reverse_queue: T.Optional[T.Deque[K]] = (
            deque(maxlen=self._count) if count < 0 else None
        )

    async def _asend(self, value: K, namespace: "Namespace") -> None:
        if self._reverse_queue is not None:
            # Skip values from end
            _value = self._reverse_queue[0]
            self._reverse_queue.append(value)
            value = _value
        elif self._count > 0:
            # Skip values from start
            self._count -= 1
            return

        awaitable = super()._asend(value, namespace)

        # Remove reference early to avoid keeping large objects in memory
        del value

        await awaitable

    async def _aclose(self) -> None:
        if self._reverse_queue is not None:
            self._reverse_queue.clear()

        await super()._aclose()


__all__ = ("Skip",)
