__all__ = ("CompositeDisposable",)


# Internal
import typing as T

# External
from async_tools import is_coroutine_function
from async_tools.operator import aexit


class CompositeDisposable(T.AsyncContextManager["CompositeDisposable"]):
    """A disposable that is a composition of various disposable."""

    @staticmethod
    def _validate_mapper(disposable: object) -> bool:
        return is_coroutine_function(getattr(disposable, "__aexit__", None))

    def __init__(self, first: object, second: object, *rest: object, **kwargs: T.Any) -> None:
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
