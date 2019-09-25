"""sink

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T

# Project
from .observe_op import observe

if T.TYPE_CHECKING:
    # Internal
    from types import TracebackType

    # Project
    from .pipe_op import pipe
    from ..protocols import ObserverProtocol, ObservableProtocol


# Generic Types
K = T.TypeVar("K")


class sink(observe[K]):
    def __init__(
        self,
        observable: "ObservableProtocol[K]",
        observer: "ObserverProtocol[K]",
        *,
        previous_pipe: T.Optional["pipe[T.Any, K]"] = None,
        **kwargs: T.Any,
    ) -> None:
        super().__init__(observable, observer, **kwargs)

        # Internal
        self._previous = previous_pipe

    async def __aenter__(self) -> "ObserverProtocol[K]":
        await super().__aenter__()

        if self._previous:
            await self._previous.__aenter__()

        return self._observer

    async def __aexit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional["TracebackType"],
    ) -> None:
        if self._previous is not None:
            await self._previous.__aexit__(exc_type, exc_value, traceback)

        await super().__aexit__(exc_type, exc_value, traceback)
