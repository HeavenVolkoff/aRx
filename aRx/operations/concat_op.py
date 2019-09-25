"""concat

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T
from asyncio import CancelledError

# Project
from .observe_op import observe

if T.TYPE_CHECKING:
    # Project
    from ..protocols import ObservableProtocol
    from ..observables import Observable


# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")
M = T.TypeVar("M")


async def concat(
    a: "ObservableProtocol[K]", b: "ObservableProtocol[L]"
) -> "Observable[T.Union[K, L]]":
    # Project
    from ..streams import SingleStream

    sink: SingleStream[T.Any] = SingleStream()

    await observe(a, sink)

    try:
        await observe(b, sink)
    except CancelledError:
        raise
    except Exception:
        await observe(a, sink).dispose()
        raise

    return sink


__all__ = ("concat",)
