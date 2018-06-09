# Project
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable import AnonymousDisposable


class Never(Observable):
    """Observable that never outputs data."""

    async def __aobserve__(self, _: Observer) -> Disposable:
        return AnonymousDisposable()
