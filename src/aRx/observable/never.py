__all__ = ("Never",)

# Internal
import typing as T

# Project
from ..disposable import AnonymousDisposable
from ..abstract.observer import Observer
from ..abstract.observable import Observable


class Never(Observable[None, AnonymousDisposable]):
    """Observable that never outputs data, but stays open."""

    def __observe__(self, _: Observer[T.Any, T.Any]) -> AnonymousDisposable:
        """Do nothing."""
        return AnonymousDisposable()
