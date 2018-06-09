# Internal
import typing as T

from asyncio import iscoroutinefunction

# Project
from ..misc.noop import anoop
from ..abstract.disposable import Disposable


class AnonymousDisposable(Disposable):
    """An anonymous Disposable.

    Creates as disposable where the custom close logic implementation is
    provided by a optional and anonymous function.
    """

    __slots__ = ("_adispose", )

    def __init__(
        self, dispose: T.Callable[[], T.Awaitable[None]] = anoop, **kwargs
    ) -> None:
        """AnonymousDisposable constructor.

        Args:
            dispose: Callback to be used as the custom close logic
                implementation.
            kwargs: Keyword parameters for super.
        """
        if not iscoroutinefunction(dispose):
            raise TypeError("Parameter dispose must be a coroutine")

        super().__init__(**kwargs)

        self._adispose = dispose

    async def __adispose__(self) -> None:
        """:meth:`Disposable.__adispose__`"""
        await self._adispose()
