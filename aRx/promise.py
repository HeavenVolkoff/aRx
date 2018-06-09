__all__ = ("Promise", )

# Internal
import typing as T

from asyncio import shield, ensure_future, AbstractEventLoop

# Project
from .abstract import Promise as AbstractPromise

K = T.TypeVar("K")
L = T.TypeVar("L")


class Promise(AbstractPromise):
    """Promise that uses coroutines to maintain the callback queue."""

    @staticmethod
    async def rejection_wrapper(
        promise: T.Awaitable[K], on_reject: T.Callable[[Exception], T.Any],
        loop: AbstractEventLoop
    ) -> L:
        """Coroutine that wraps a promise and manages a rejection callback.

        Args:
            promise: Promise to be wrapped.
            on_reject: Rejection callback.
            loop: Asyncio loop reference.

        Returns:
            Callback result.

        """
        try:
            result = await shield(promise, loop=loop)
        except Exception as ex:
            result = on_reject(ex)

        try:
            result = await ensure_future(result, loop=loop)
        except TypeError:
            pass

        return result

    @staticmethod
    async def resolution_wrapper(
        promise: T.Awaitable[K], on_resolution: T.Callable[[], T.Any],
        loop: AbstractEventLoop
    ) -> L:
        """Coroutine that wraps a promise and manages a resolution callback.

        Args:
            promise: Promise to be wrapped.
            on_resolution: Resolution callback.
            loop: Asyncio loop reference.

        Returns:
            Callback result.

        """
        try:
            await shield(promise, loop=loop)
        except Exception:
            pass

        result = on_resolution()

        try:
            result = await ensure_future(result, loop=loop)
        except TypeError:
            pass

        return result

    @staticmethod
    async def fulfillment_wrapper(
        promise: T.Awaitable[K], on_fulfilled: T.Callable[[Exception], T.Any],
        loop: AbstractEventLoop
    ) -> L:
        """Coroutine that wraps a promise and manages a fulfillment callback.

        Args:
            promise: Promise to be wrapped.
            on_fulfilled: Fulfillment callback.
            loop: Asyncio loop reference.

        Returns:
            Callback result.

        """
        result = on_fulfilled(await shield(promise, loop=loop))

        try:
            result = await ensure_future(result, loop=loop)
        except TypeError:
            pass

        return result

    def then(self, on_fulfilled: T.Callable[[L], T.Any]) -> 'Promise':
        """:meth:`AbstractPromise.then`"""
        return Promise(
            Promise.fulfillment_wrapper(self, on_fulfilled, self._loop),
            loop=self._loop
        )

    def catch(self, on_reject: T.Callable[[Exception], T.Any]) -> 'Promise':
        """:meth:`AbstractPromise.catch`"""
        return Promise(
            Promise.rejection_wrapper(self, on_reject, self._loop),
            loop=self._loop
        )

    def lastly(self, on_fulfilled: T.Callable[[L], T.Any]) -> 'Promise':
        """:meth:`AbstractPromise.lastly`"""
        pass
