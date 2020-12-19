"""ObserverProtocol

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""


# Internal
import typing as T

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace


# Generic Types
K = T.TypeVar("K", contravariant=True)


class ObserverProtocol(T.Protocol[K]):
    """Observer protocols class.

    An observers represents a data sink, where data can flow into and be
    transformed by it.
    """

    keep_alive: bool
    """Flag that indicates the default behaviour on whether or not the observers should be closed on
        observation disposition.
    """

    @property
    def closed(self) -> bool:
        ...

    async def asend(self, data: K, namespace: T.Optional["Namespace"] = None) -> None:
        ...

    async def athrow(self, main_exc: Exception, namespace: T.Optional["Namespace"] = None) -> None:
        ...

    async def aclose(self) -> bool:
        ...


__all__ = ("ObserverProtocol",)
