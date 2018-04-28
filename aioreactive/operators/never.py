from ..core import AsyncObserver, AsyncDisposable
from ..abstract import AsyncObservable


class Never(AsyncObservable):
    async def __aobserve__(self, _: AsyncObserver) -> AsyncDisposable:
        return AsyncDisposable()


def never() -> AsyncObservable:
    """Returns an asynchronous source where nothing happens.

    Example:
    xs = never()

    Returns a source stream where nothing happens.
    """

    return Never()
