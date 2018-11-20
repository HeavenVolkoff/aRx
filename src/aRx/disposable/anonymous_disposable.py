__all__ = ("AnonymousDisposable",)

# Internal
import typing as T
from asyncio import iscoroutine

# Project
from ..abstract.disposable import Disposable


def default_dispose() -> None:
    return


class AnonymousDisposable(Disposable):
    """An anonymous Disposable.

    Disposable where the custom close logic implementation is provided by a
    optional and anonymous function.
    """

    def __init__(self, dispose: T.Optional[T.Callable[[], T.Any]] = None, **kwargs: T.Any) -> None:
        """AnonymousDisposable constructor.

        Arguments:
            dispose: Callback to be used as the custom close logic
                implementation.
            kwargs: Keyword parameters for super.

        Raises:
            TypeError: When dispose parameter is not a :class:`~typing.Coroutine`.

        """
        super().__init__(**kwargs)

        if dispose is None:
            dispose = default_dispose

        if not callable(dispose):
            raise TypeError("Argument must be Callable")

        self._adispose = dispose

    async def __adispose__(self) -> None:
        """Call anonymous function on dispose."""
        dispose = self._adispose()

        if iscoroutine(dispose):
            await T.cast(T.Coroutine[T.Any, T.Any, T.Any], dispose)
