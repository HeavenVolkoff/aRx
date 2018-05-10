# Internal
import typing as T

from logging import Logger, getLogger
from asyncio import Future, get_event_loop, AbstractEventLoop
from functools import partial

K = T.TypeVar("K")


def cb(
    fut: Future,
    *,
    loop: AbstractEventLoop,
    coro: T.Optional[T.Awaitable[K]] = None,
    logger: Logger
) -> None:
    try:
        fut.result()
    except Exception as ex:
        logger.error("Future <%s> resulted in error:", fut)
        logger.exception(ex)

    if coro:
        loop.create_task(coro).add_done_callback(
            partial(cb, loop=loop, logger=logger)
        )


def coro_done_callback(
    unresolved_fut: Future,
    coro: T.Optional[T.Awaitable[K]] = None,
    *,
    loop: T.Optional[AbstractEventLoop] = None,
    logger: T.Optional[Logger] = None
) -> T.Callable[[Future], None]:
    partial_cb = partial(
        cb,
        loop=loop if loop else get_event_loop(),
        coro=coro,
        logger=logger if logger else getLogger()
    )

    unresolved_fut.add_done_callback(partial_cb)

    return partial_cb
