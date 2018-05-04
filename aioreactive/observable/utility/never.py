from aioreactive.abstract import Observer, Observable, Disposable
from aioreactive.disposable import AnonymousDisposable


class Never(Observable):
    async def __aobserve__(self, _: Observer) -> Disposable:
        return AnonymousDisposable()


def never() -> Observable:
    """Returns an asynchronous source where nothing happens.

    Example:
    xs = never()

    Returns a source stream where nothing happens.
    """

    return Never()
