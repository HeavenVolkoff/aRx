# Project
from ..base import BaseObservable
from ...abstract import Observer, Disposable
from ...disposable import AnonymousDisposable


class Never(BaseObservable):
    async def __aobserve__(self, _: Observer) -> Disposable:
        return AnonymousDisposable()


def never() -> Never:
    """Returns an asynchronous source where nothing happens.

    Example:
    xs = never()

    Returns a source stream where nothing happens.
    """

    return Never()
