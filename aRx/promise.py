__all__ = ("Promise", )

# Internal
import typing as T

from asyncio import (
    shield, ensure_future, CancelledError, AbstractEventLoop, InvalidStateError
)

# Project
from .misc.flag import Flag
from .abstract.promise import Promise as AbstractPromise

K = T.TypeVar("K")
L = T.TypeVar("L")


async def _rejection_wrapper(
    promise: AbstractPromise[K], on_reject: T.Callable[[Exception], L],
    await_flag: Flag, loop: AbstractEventLoop
) -> L:
    """Coroutine that wraps a promise and manages a rejection callback.

    Arguments:
        promise: Promise to be wrapped.
        on_reject: Rejection callback.
        await_flag: Flag that indicates if promise is being awaited.
        loop: Asyncio loop reference.

    Returns:
        Callback result.

    """
    promise = shield(promise, loop=loop)

    try:
        result = await promise
    except CancelledError as ex:
        if await_flag:
            raise ex
        else:
            return
    except Exception as ex:
        result = on_reject(ex)

    try:
        result = ensure_future(result, loop=loop)
    except TypeError:
        pass  # Result isn't awaitable
    else:
        result = await result

    return result


async def _resolution_wrapper(
    promise: AbstractPromise[K], on_resolution: T.Callable[[], L],
    await_flag: Flag, loop: AbstractEventLoop
) -> L:
    """Coroutine that wraps a promise and manages a resolution callback.

    Arguments:
        promise: Promise to be wrapped.
        on_resolution: Resolution callback.
        await_flag: Flag that indicates if promise is being awaited.
        loop: Asyncio loop reference.

    Returns:
        Callback result.

    """
    promise = shield(promise, loop=loop)

    try:
        await promise
    except CancelledError as ex:
        if await_flag:
            raise ex
        else:
            return
    except Exception:
        pass

    result = on_resolution()

    try:
        result = ensure_future(result, loop=loop)
    except TypeError:
        pass  # Result isn't awaitable
    else:
        result = await result

    return result


async def _fulfillment_wrapper(
    promise: AbstractPromise[K], on_fulfilled: T.Callable[[K], L],
    await_flag: Flag, loop: AbstractEventLoop
) -> L:
    """Coroutine that wraps a promise and manages a fulfillment callback.

    Arguments:
        promise: Promise to be wrapped.
        on_fulfilled: Fulfillment callback.
        await_flag: Flag that indicates if promise is being awaited.
        loop: Asyncio loop reference.

    Returns:
        Callback result.

    """
    promise = shield(promise, loop=loop)

    try:
        result = await promise
    except CancelledError as ex:
        if await_flag:
            raise ex
        else:
            return

    result = on_fulfilled(result)

    try:
        result = ensure_future(result, loop=loop)
    except TypeError:
        pass  # Result isn't awaitable
    else:
        result = await result

    return result


class Promise(AbstractPromise[K]):
    """Concrete Promise implementation that maintains the callback queue using :class:`~typing.Coroutine`.
    
    See: :class:`~aRx.abstract.promise.Promise` for more information on the Promise abstract interface.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._await_flag = Flag()

    def __await__(self):
        self._await_flag.set_true()
        return super().__await__()

    def then(self, on_fulfilled: T.Callable[[K], L]) -> 'Promise[L]':
        """Concrete implementation that wraps the received callback on a :class:`~typing.Coroutine`.
        The :class:`~typing.Coroutine` will await the promise resolution and,
        if no exception is raised, it will call the callback with the promise 
        result.

        See: :meth:`~aRx.abstract.promise.Promise.then` for more information.

        """
        return ChainPromise(
            _fulfillment_wrapper(
                self, on_fulfilled, self._await_flag, self._loop
            ),
            loop=self._loop
        )

    def catch(self, on_reject: T.Callable[[Exception], L]) -> 'Promise[L]':
        """Concrete implementation that wraps the received callback on a :class:`~typing.Coroutine`.
        The :class:`~typing.Coroutine` will await the promise resolution and,
        if a exception is raised, it will call the callback with the promise 
        exception.

        See: :meth:`~aRx.abstract.promise.Promise.catch` for more information.
        
        """
        return ChainPromise(
            _rejection_wrapper(self, on_reject, self._await_flag, self._loop),
            loop=self._loop
        )

    def lastly(self, on_fulfilled: T.Callable[[], L]) -> 'Promise[L]':
        """Concrete implementation that wraps the received callback on a :class:`~typing.Coroutine`.
        The :class:`~typing.Coroutine` will await the promise resolution and 
        call the callback.

        See: :meth:`~aRx.abstract.promise.Promise.lastly` for more information.
        
        """
        return ChainPromise(
            _resolution_wrapper(
                self, on_fulfilled, self._await_flag, self._loop
            ),
            loop=self._loop
        )


class ChainPromise(Promise[K]):
    """A special promise implementation used by the chained callback Promises."""

    def resolve(self, _: K) -> None:
        """See: :meth:`~aRx.abstract.promise.Promise.resolve` for more information.
        
        Raises:
            InvalidStateError: Chained promises aren't allowed to be resolved externally.

        """
        raise InvalidStateError("Chain promise can't be resolve externally")

    def reject(self, _: Exception) -> None:
        """See: :meth:`~aRx.abstract.promise.Promise.reject` for more information.
        
        Raises:
            InvalidStateError: Chained promises aren't allowed to be resolved externally.

        """
        raise InvalidStateError("Chain promise can't be resolve externally")
