__all__ = ("CompositeDisposable",)

# Internal
import typing as T

# Project
from ..abstract.disposable import Disposable, adispose


class CompositeDisposable(Disposable):
    """A disposable that is a composition of various disposable."""

    @staticmethod
    def _validate_mapper(disposable: Disposable) -> bool:
        return isinstance(disposable, Disposable)

    def __init__(
        self, first: Disposable, second: Disposable, *rest: Disposable, **kwargs: T.Any
    ) -> None:
        """CompositeDisposable constructor.

        Arguments:
            first: First disposable to register.
            second: Second disposable to register.
            rest: Optional disposables to register.
            kwargs: Keyword parameters for super.

        Raises:
            TypeError: if any parameter is not a :class:`~.Disposable`.

        """
        disposables = (first, second) + rest

        if not all(map(self._validate_mapper, disposables)):
            raise TypeError("Arguments must be disposable")

        super().__init__(**kwargs)

        self._disposables = disposables

    async def __adispose__(self) -> None:
        """Call all registered disposables on dispose."""
        await adispose(*self._disposables)
