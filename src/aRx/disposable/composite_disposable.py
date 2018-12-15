__all__ = ("CompositeDisposable",)


# Internal
import typing as T

# External
from async_tools.operator import aexit

# Project
from ..misc.async_context_manager import AsyncContextManager


class CompositeDisposable(AsyncContextManager):
    """A disposable that is a composition of various disposable."""

    @staticmethod
    def _validate_mapper(disposable: AsyncContextManager) -> bool:
        return isinstance(disposable, AsyncContextManager)

    def __init__(
        self,
        first: AsyncContextManager,
        second: AsyncContextManager,
        *rest: AsyncContextManager,
        **kwargs: T.Any,
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

        super().__init__(**kwargs)  # type: ignore

        self._disposables = disposables

    async def __aexit__(self, _: T.Any, __: T.Any, ___: T.Any) -> bool:
        """Call all registered disposables on dispose."""
        await aexit(*self._disposables)
        return False
