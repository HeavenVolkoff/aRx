# Project
from ..abstract.disposable import Disposable, adispose


class CompositeDisposable(Disposable):
    """A disposable that is a composition of various disposable."""

    @staticmethod
    def _validate_mapper(disposable):
        return isinstance(disposable, Disposable)

    def __init__(
        self, a: Disposable, b: Disposable, *rest: Disposable, **kwargs
    ) -> None:
        """CompositeDisposable constructor.

        Args:
            a: First disposable to register.
            b: Second disposable to register.
            rest: Optional disposables to register.
            kwargs: Keyword parameters for super.

        """
        disposables = (a, b) + rest

        if not all(map(self._validate_mapper, disposables)):
            raise TypeError("Parameters must be disposable")

        super().__init__(**kwargs)

        self._disposables = disposables

    async def __adispose__(self) -> None:
        """Call all registered disposables on dispose."""
        for disposable in self._disposables:
            await adispose(disposable)
