__all__ = ("Promise", )

# Internal
import typing as T

from asyncio import (shield, ensure_future, CancelledError, InvalidStateError)
from contextlib import AbstractContextManager

# Project
from .abstract.promise import Promise as AbstractPromise

K = T.TypeVar("K")
L = T.TypeVar("L")


def contains_cancelled_error(ex: T.Optional[Exception]):
    return isinstance(ex, Exception) and (
        isinstance(ex, CancelledError)
        or contains_cancelled_error(ex.__cause__)
        or contains_cancelled_error(ex.__context__)
    )


class Promise(AbstractPromise[K]):
    """Concrete Promise implementation that maintains the callback queue using :class:`~typing.Coroutine`.
    
    See: :class:`~aRx.abstract.promise.Promise` for more information on the Promise abstract interface.
    """

    def then(self, on_fulfilled: T.Callable[[K], L]) -> 'Promise[L]':
        """Concrete implementation that wraps the received callback on a :class:`~typing.Coroutine`.
        The :class:`~typing.Coroutine` will await the promise resolution and,
        if no exception is raised, it will call the callback with the promise 
        result.

        See: :meth:`~aRx.abstract.promise.Promise.then` for more information.

        """
        return FulfillmentPromise(self, on_fulfilled, loop=self._loop)

    def catch(self, on_reject: T.Callable[[Exception], L]) -> 'Promise[L]':
        """Concrete implementation that wraps the received callback on a :class:`~typing.Coroutine`.
        The :class:`~typing.Coroutine` will await the promise resolution and,
        if a exception is raised, it will call the callback with the promise 
        exception.

        See: :meth:`~aRx.abstract.promise.Promise.catch` for more information.
        
        """
        return RejectionPromise(self, on_reject, loop=self._loop)

    def lastly(self, on_resolved: T.Callable[[], L]) -> 'Promise[K]':
        """Concrete implementation that wraps the received callback on a :class:`~typing.Coroutine`.
        The :class:`~typing.Coroutine` will await the promise resolution and
        call the callback.

        See: :meth:`~aRx.abstract.promise.Promise.lastly` for more information.

        """
        return ResolutionPromise(self, on_resolved, loop=self._loop)


class ChainPromise(Promise[K], AbstractContextManager):
    """A special promise implementation used by the chained callback Promises."""

    def __exit__(self, exc_type, exc_value, traceback):
        if contains_cancelled_error(exc_value) and not self._awaited:
            return True

    def resolve(self, _: K) -> None:
        """See: :meth:`~aRx.abstract.promise.Promise.resolve` for more information.
        
        Raises:
            InvalidStateError: Chained promises aren't allowed to be resolved externally.

        """
        raise InvalidStateError("Chain promise can't be resolved externally")

    def reject(self, _: Exception) -> None:
        """See: :meth:`~aRx.abstract.promise.Promise.reject` for more information.
        
        Raises:
            InvalidStateError: Chained promises aren't allowed to be resolved externally.

        """
        raise InvalidStateError("Chain promise can't be rejected externally")


class FulfillmentPromise(ChainPromise[L]):
    def __init__(
        self, promise: AbstractPromise, on_fulfilled: T.Callable[[K], L],
        **kwargs
    ):
        super().__init__(
            awaitable=self._wrapper(promise, on_fulfilled), **kwargs
        )

    async def _wrapper(
        self, promise: AbstractPromise, on_fulfilled: T.Callable[[K], L]
    ) -> L:
        """Coroutine that wraps a promise and manages a fulfillment callback.

        Arguments:
            promise: Promise to be awaited for chain action
            on_fulfilled: Fulfillment callback.

        Returns:
            Callback result.

        """
        with self:
            result = on_fulfilled(await shield(promise, loop=self.loop))

            try:
                result = ensure_future(result, loop=self.loop)
            except TypeError:
                pass
            else:
                result = await result

            return result


class RejectionPromise(ChainPromise[L]):
    def __init__(
        self, promise: AbstractPromise, on_reject: T.Callable[[Exception], L],
        **kwargs
    ):
        super().__init__(awaitable=self._wrapper(promise, on_reject), **kwargs)

    async def _wrapper(
        self, promise: AbstractPromise, on_reject: T.Callable[[Exception], L]
    ) -> L:
        """Coroutine that wraps a promise and manages a rejection callback.

        Arguments:
            promise: Promise to be awaited for chain action
            on_reject: Rejection callback.

        Returns:
            Callback result.

        """
        with self:
            try:
                return await shield(promise, loop=self.loop)
            except Exception as ex:
                try:
                    if self._cancelled:
                        return

                    result = on_reject(ex)

                    try:
                        result = ensure_future(result, loop=self.loop)
                    except TypeError:
                        pass
                    else:
                        if contains_cancelled_error(ex):
                            # Defer cancel to give task time to begin execution
                            self.loop.call_soon(result.cancel)

                        result = await result

                    return result
                except Exception as _ex:
                    # Fix error chain context
                    _ex.__context__ = ex
                    raise _ex


class ResolutionPromise(ChainPromise[K]):
    def __init__(
        self, promise: AbstractPromise, on_resolution: T.Callable[[], L],
        **kwargs
    ):
        super().__init__(
            awaitable=self._wrapper(promise, on_resolution), **kwargs
        )

    async def _wrapper(
        self, promise: AbstractPromise, on_resolution: T.Callable[[], L]
    ) -> K:
        """Coroutine that wraps a promise and manages a resolution callback.

        Arguments:
            promise: Promise to be awaited for chain action
            on_resolution: Resolution callback.

        Returns:
            Callback result.

        """
        try:
            from contextlib import AsyncExitStack
        except ImportError:
            from async_exit_stack import AsyncExitStack

        async with AsyncExitStack() as stack:
            stack.push(self)

            @stack.push_async_callback
            async def resolution():
                if self._cancelled:
                    return

                result = on_resolution()

                try:
                    result = ensure_future(result, loop=self.loop)
                except TypeError:
                    pass  # Result isn't awaitable
                else:
                    await result

            return await shield(promise, loop=self.loop)
