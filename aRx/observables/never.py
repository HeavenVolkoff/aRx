"""Never

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T

# Project
from .observable import Observable

if T.TYPE_CHECKING:
    # Project
    from ..protocols import ObserverProtocol


class Never(Observable[None]):
    """Observable that never outputs data, but stays open."""

    async def __observe__(self, _: "ObserverProtocol[T.Any]") -> None:
        """Do nothing."""
        return

    async def __dispose__(self, _: "ObserverProtocol[T.Any]") -> None:
        """Do nothing."""
        return


__all__ = ("Never",)
