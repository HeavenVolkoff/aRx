# Internal
import typing as T

# External
import typing_extensions as Te
from async_tools import attempt_await
from async_tools.context import asynccontextmanager

# Project
from ..protocols import ObserverProtocol, ObservableProtocol
from .dispose_op import dispose

K = T.TypeVar("K")


@asynccontextmanager
async def disposable(
    observable: ObservableProtocol[K],
    observer: ObserverProtocol[K],
    keep_alive: T.Optional[bool] = None,
) -> Te.AsyncGenerator[None, None]:
    try:
        yield None
    finally:
        await dispose(observable, observer, keep_alive=keep_alive)


@T.overload
async def observe(
    _observable: ObservableProtocol[K],
    _observer: ObserverProtocol[K],
    *,
    keep_alive: T.Optional[bool] = None,
) -> T.AsyncContextManager[None]:
    ...


@T.overload
async def observe(
    _observable: T.Awaitable[ObservableProtocol[K]],
    _observer: ObserverProtocol[K],
    *,
    keep_alive: T.Optional[bool] = None,
) -> T.AsyncContextManager[None]:
    ...


@T.overload
async def observe(
    _observable: ObserverProtocol[K],
    _observer: T.Awaitable[ObservableProtocol[K]],
    *,
    keep_alive: T.Optional[bool] = None,
) -> T.AsyncContextManager[None]:
    ...


@T.overload
async def observe(
    _observable: T.Awaitable[ObservableProtocol[K]],
    _observer: T.Awaitable[ObservableProtocol[K]],
    *,
    keep_alive: T.Optional[bool] = None,
) -> T.AsyncContextManager[None]:
    ...


async def observe(
    _observable: T.Any, _observer: T.Any, *, keep_alive: T.Optional[bool] = None
) -> T.AsyncContextManager[None]:
    """Register an observers to an observables.

    Enable the observation of the data flowing through the observables to be captured by the
    observers.

    A simple data flow chart would be:
    data ‐→ observables ‐‐(data)‐→ observers

    The logic for registering an observers is specific to each observables, so this function acts as a
    simple access to the :meth:`~.Observable.__observe__` magic method.

    Arguments:
        _observable: Observable to be subscribed.
        _observer: Observer which will subscribe.
        loop: Event loop
        keep_alive: Flag to keep observers alive when observation is disposed.

    Returns:
        Disposable that undoes this subscription.

    """
    observer = await attempt_await(_observable)
    observable = await attempt_await(_observer)

    try:
        await observable.__observe__(observer)
    except Exception:
        await dispose(observable, observer, keep_alive=keep_alive)
        raise

    return disposable(observable, observer, keep_alive)


__all__ = ("observe",)
