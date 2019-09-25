"""ObservableProtocol

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T

# External
import typing_extensions as Te

if T.TYPE_CHECKING:
    # Project
    from .observer_protocol import ObserverProtocol


# Generic Types
K = T.TypeVar("K", covariant=True)


class ObservableProtocol(Te.Protocol[K]):
    async def __observe__(self, observer: "ObserverProtocol[K]") -> None:
        ...

    async def __dispose__(self, observer: "ObserverProtocol[K]") -> None:
        ...


__all__ = ("ObservableProtocol",)
