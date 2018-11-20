__all__ = ("AnonymousDisposable",)

# Internal
import typing as T
from types import TracebackType
from asyncio import iscoroutine

# External
from async_tools.abstract.abstract_async_context_manager import AbstractAsyncContextManager

def default_dispose() -> None:
    return

class AnonymousDisposable(AbstractAsyncContextManager["AnonymousDisposable"]):
    """An anonymous Disposable.

    Disposable where the custom close logic implementation is provided by a
    optional and anonymous function.
    """

    def __init__(self, dispose: T.Optional[T.Callable[[], T.Any]] = None, **kwargs: T.Any) -> None:
        """AnonymousDisposable constructor.

        Arguments:
            dispose: Callback to be used as the custom close logic implementation.
            kwargs: Keyword parameters for super.

        Raises:
            TypeError: When dispose parameter is not a :class:`~typing.Coroutine`.

        """
        super().__init__(**kwargs)  # type: ignore

        if dispose is None:
            dispose = default_dispose

        if not callable(dispose):
            raise TypeError("Argument must be Callable")

        self._adispose = dispose

    async def __aexit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional[TracebackType],
    ) -> T.Optional[bool]:
        """Call anonymous function on dispose."""
        dispose = self._adispose()

        if iscoroutine(dispose):
            await T.cast(T.Coroutine[T.Any, T.Any, T.Any], dispose)

        return False
