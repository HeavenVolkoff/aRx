__all__ = ("Never", )

# Project
from ..abstract.observer import Observer
from ..abstract.observable import Observable
from ..abstract.disposable import Disposable
from ..disposable import AnonymousDisposable


class Never(Observable):
    """Observable that never outputs data, but stays open."""

    def __observe__(self, _: Observer) -> Disposable:
        """Do nothing."""
        return AnonymousDisposable()
