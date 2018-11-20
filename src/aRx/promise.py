__all__ = ("Promise",)

# Internal
import typing as T
from abc import ABCMeta, abstractmethod
from asyncio import CancelledError, AbstractEventLoop, InvalidStateError, shield, ensure_future

# Project
from .abstract.promise import Promise as AbstractPromise

# Generic types
K = T.TypeVar("K")
L = T.TypeVar("L")


async def resolve_awaitable(awaitable: T.Union[K, T.Awaitable[K]], loop: AbstractEventLoop) -> K:
    try:
        result_fut = ensure_future(T.cast(T.Awaitable[K], awaitable), loop=loop)
    except TypeError:
        return T.cast(K, awaitable)  # Not an awaitable
    else:
        return await result_fut


class Promise(AbstractPromise[K]):
    """Promise implementation that maintains the callback queue using :class:`~typing.Coroutine`.
    
    See: :class:`~.abstract.promise.Promise` for more information on the Promise abstract interface.
    """

    def then(
        self, on_fulfilled: T.Callable[[K], T.Union[L, T.Awaitable[L]]]
    ) -> "ChainPromise[K, L]":
        """Concrete implementation that wraps the received callback on a :class:`~typing.Coroutine`.
        The :class:`~typing.Coroutine` will await the promise resolution and,
        if no exception is raised, it will call the callback with the promise 
        result.

        See: :meth:`~.abstract.promise.Promise.then` for more information.

        """
        return FulfillmentPromise(self, on_fulfilled, loop=self._loop)

    def catch(
        self, on_reject: T.Callable[[Exception], T.Union[L, T.Awaitable[L]]]
    ) -> "ChainPromise[K, L]":
        """Concrete implementation that wraps the received callback on a :class:`~typing.Coroutine`.
        The :class:`~typing.Coroutine` will await the promise resolution and,
        if a exception is raised, it will call the callback with the promise 
        exception.

        See: :meth:`~.abstract.promise.Promise.catch` for more information.
        
        """
        return RejectionPromise(self, on_reject, loop=self._loop)

    def lastly(self, on_resolved: T.Callable[[], T.Any]) -> "ChainPromise[K, K]":
        """Concrete implementation that wraps the received callback on a :class:`~typing.Coroutine`.
        The :class:`~typing.Coroutine` will await the promise resolution and
        call the callback.

        See: :meth:`~.abstract.promise.Promise.lastly` for more information.

        """
        return ResolutionPromise(self, on_resolved, loop=self._loop)


class ChainPromise(T.Generic[K, L], Promise[K], metaclass=ABCMeta):
    """A special promise implementation used by the chained callback Promises."""

    def __init__(
        self, promise: AbstractPromise[K], callback: T.Callable[..., T.Any], **kwargs: T.Any
    ) -> None:
        super().__init__(self._wrapper(shield(promise, loop=promise.loop), callback), **kwargs)

        # Disable the "destroy pending task" warning
        self._fut._log_destroy_pending = False  # type: ignore

    @abstractmethod
    def _wrapper(self, promise: T.Awaitable[K], callback: T.Callable[..., T.Any]) -> T.Any:
        raise NotImplementedError

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


class FulfillmentPromise(ChainPromise[K, L]):
    def __init__(
        self,
        promise: AbstractPromise[K],
        on_fulfilled: T.Callable[[K], T.Union[L, T.Awaitable[L]]],
        **kwargs: T.Any,
    ) -> None:
        super().__init__(promise, on_fulfilled, **kwargs)

    async def _wrapper(
        self, promise: T.Awaitable[K], on_fulfilled: T.Callable[[K], T.Union[L, T.Awaitable[L]]]
    ) -> L:
        """Coroutine that wraps a promise and manages a fulfillment callback.

        Arguments:
            promise: Promise to be awaited for chain action
            on_fulfilled: Fulfillment callback.

        Returns:
            Callback result.

        """
        return await resolve_awaitable(on_fulfilled(await promise), self.loop)


class RejectionPromise(ChainPromise[K, L]):
    def __init__(
        self,
        promise: AbstractPromise[K],
        on_reject: T.Callable[[Exception], T.Union[L, T.Awaitable[L]]],
        **kwargs: T.Any,
    ) -> None:
        super().__init__(promise, on_reject, **kwargs)

    async def _wrapper(
        self,
        promise: T.Awaitable[K],
        on_reject: T.Callable[[Exception], T.Union[L, T.Awaitable[L]]],
    ) -> T.Union[L, K]:
        """Coroutine that wraps a promise and manages a rejection callback.

        Arguments:
            promise: Promise to be awaited for chain action
            on_reject: Rejection callback.

        Returns:
            Callback result.

        """
        try:
            return await promise
        except CancelledError:
            raise  # CancelledError must be propagated
        except Exception as exc:
            return await resolve_awaitable(on_reject(exc), self.loop)


class ResolutionPromise(ChainPromise[K, K]):
    def __init__(
        self, promise: AbstractPromise[K], on_resolution: T.Callable[[], T.Any], **kwargs: T.Any
    ) -> None:
        super().__init__(promise, on_resolution, **kwargs)

        self._direct_cancellation = False

    def cancel(self) -> bool:
        self._direct_cancellation = True
        return super().cancel()

    async def _wrapper(self, promise: T.Awaitable[K], on_resolution: T.Callable[[], T.Any]) -> K:
        """Coroutine that wraps a promise and manages a resolution callback.
        Arguments:
            promise: Promise to be awaited for chain action
            on_resolution: Resolution callback.
        Returns:
            Callback result.
        """
        try:
            return await promise
        finally:
            # Finally executes always, except in the case itself was stopped.
            if not self._direct_cancellation:
                await resolve_awaitable(on_resolution(), self.loop)
