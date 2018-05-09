import typing as T

from logging import Logger, getLogger
from asyncio import Future, get_event_loop, AbstractEventLoop

K = T.TypeVar("K")


def coro_done_callback(
    unresolved_fut: Future,
    coro: T.Optional[T.Awaitable[K]] = None,
    *,
    loop: T.Optional[AbstractEventLoop] = None,
    logger: T.Optional[Logger] = None
) -> T.Callable[[Future], None]:
    loop = loop if loop else get_event_loop()
    logger = logger if logger else getLogger()

    def cb(fut: Future) -> None:
        try:
            fut.result()
        except Exception as ex:
            logger.error("Future <%s> resulted in error:", fut)
            logger.exception(ex)

        if coro:
            loop.create_task(coro).add_done_callback(cb)
            coro = None

    unresolved_fut.add_done_callback(cb)

    return cb
