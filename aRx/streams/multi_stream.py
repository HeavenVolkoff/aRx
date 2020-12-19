"""MultiStream

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

# Internal
import typing as T
from asyncio import ALL_COMPLETED, Future, AbstractEventLoop, wait, get_running_loop
from contextlib import suppress

# External
from async_tools import wait_with_care

# Project
from ..errors import ObserverClosedError
from ..observers import Observer
from ..operations import observe
from ..observables import Observable

if T.TYPE_CHECKING:
    # Project
    from ..namespace import Namespace
    from ..protocols import ObserverProtocol


# Generic Types
K = T.TypeVar("K")


class MultiStream(Observer[K], Observable[K]):
    """Hot streams that can be observed by multiple observers.

    .. Note::

        The AsyncMultiStream is hot in the sense that it will drop events if there are currently no
        observers running, and all redirection only enqueue the observers action, not waiting for
        it's execution.
    """

    def __init__(self, **kwargs: T.Any) -> None:
        """MultiStream constructor.

        Arguments:
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        # Internal
        self._observers: T.Set["ObserverProtocol[K]"] = set()
        self._disposables: T.Optional[T.Awaitable[T.Any]] = None

    async def _clear_closed_observers(self) -> None:
        await wait_with_care(
            *set(observe(self, obv).dispose() for obv in self._observers if obv.closed)
        )
        self._disposables = None

    def _process_done(self, loop: AbstractEventLoop, done: T.Set["Future[T.Any]"]) -> None:
        for fut in done:
            exc = fut.exception()
            # Ignore ObserverClosedError in multi-stream as it's occurrence is natural due to the
            # lazy way observers closure is handled
            if isinstance(exc, Exception) and not isinstance(exc, ObserverClosedError):
                loop.call_exception_handler(
                    {
                        "future": fut,
                        "message": (
                            f"{self}: Unhandled exception while attempting to propagate data "
                            "through observers"
                        ),
                        "exception": exc,
                    }
                )
            elif exc is not None:
                # BaseException
                raise exc

        if not self._disposables:
            # Enqueue clearing
            self._disposables = loop.create_task(self._clear_closed_observers())

    async def _asend(self, value: K, namespace: "Namespace") -> None:
        if not self._observers:
            return

        loop = get_running_loop()

        awaitable = wait(
            tuple(
                loop.create_task(obv.asend(value, namespace))
                for obv in self._observers
                if not obv.closed
            ),
            return_when=ALL_COMPLETED,
        )

        # Remove reference early to avoid keeping large objects in memory
        del value

        done, pending = await awaitable

        assert not pending

        self._process_done(get_running_loop(), done)

    async def _athrow(self, main_exc: Exception, namespace: "Namespace") -> bool:
        if self._observers:
            loop = get_running_loop()
            done, pending = await wait(
                tuple(
                    loop.create_task(obv.athrow(main_exc, namespace))
                    for obv in self._observers
                    if not obv.closed
                ),
                return_when=ALL_COMPLETED,
            )

            assert not pending

            self._process_done(get_running_loop(), done)

        # A MultiStream never closes on athrow
        return False

    async def _aclose(self) -> None:
        if self._disposables:
            await self._disposables

        await wait_with_care(*(observe(self, observer).dispose() for observer in self._observers))

    async def __observe__(self, observer: "ObserverProtocol[K]") -> None:
        # Add observers to internal observation set
        self._observers.add(observer)

    async def __dispose__(self, observer: "ObserverProtocol[K]") -> None:
        with suppress(KeyError):
            self._observers.remove(observer)


__all__ = ("MultiStream",)
