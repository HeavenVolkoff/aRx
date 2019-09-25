"""Empty

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T

# Project
from .observable import Observable
from ..operations import observe

if T.TYPE_CHECKING:
    # Project
    from ..protocols import ObserverProtocol


class Empty(Observable[T.Any]):
    """Observable that doesn't output data and closes any observers as soon as possible."""

    async def __observe__(self, observer: "ObserverProtocol[T.Any]") -> None:
        await observe(self, observer).dispose()

    async def __dispose__(self, observer: "ObserverProtocol[T.Any]") -> None:
        return


__all__ = ("Empty",)
