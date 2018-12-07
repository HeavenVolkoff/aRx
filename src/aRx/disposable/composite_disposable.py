__all__ = ("CompositeDisposable",)


# Internal
import typing as T
from types import TracebackType

# External
from async_tools.operator import aexit
from async_tools.context_manager import AsyncContextManager


class CompositeDisposable(AsyncContextManager["CompositeDisposable"]):
    """A disposable that is a composition of various disposable."""

    @staticmethod
    def _validate_mapper(disposable: AsyncContextManager[T.Any]) -> bool:
        return isinstance(disposable, AsyncContextManager)

    def __init__(
        self,
        first: AsyncContextManager[T.Any],
        second: AsyncContextManager[T.Any],
        *rest: AsyncContextManager[T.Any],
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

    async def __aexit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional[TracebackType],
    ) -> T.Optional[bool]:
        """Call all registered disposables on dispose."""
        await aexit(*self._disposables)
        return False
