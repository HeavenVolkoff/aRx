__all__ = ("CompositeDisposable",)

from ..abstract.disposable import Disposable, adispose


class CompositeDisposable(Disposable):
    """A disposable that is a composition of various disposable."""

    @staticmethod
    def _validate_mapper(disposable):
        return isinstance(disposable, Disposable)

    def __init__(
        self, first: Disposable, second: Disposable, *rest: Disposable, **kwargs
    ) -> None:
        """CompositeDisposable constructor.

        Raises:
            TypeError: if any parameter is not a :class:`~.Disposable`.

        Arguments:
            first: First disposable to register.
            second: Second disposable to register.
            rest: Optional disposables to register.
            kwargs: Keyword parameters for super.

        """
        disposables = (first, second) + rest

        if not all(map(self._validate_mapper, disposables)):
            raise TypeError("Parameters must be disposable")

        super().__init__(**kwargs)

        self._disposables = disposables

    async def __adispose__(self) -> None:
        """Call all registered disposables on dispose."""
        await adispose(*self._disposables)
