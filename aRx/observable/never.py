__all__ = ("Never",)

from ..disposable import AnonymousDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable
from ..abstract.observable import Observable


class Never(Observable[None]):
    """Observable that never outputs data, but stays open."""

    def __observe__(self, _: Observer) -> Disposable:
        """Do nothing."""
        return AnonymousDisposable()
