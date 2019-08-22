# Internal
import typing as T

# External
from async_tools import attempt_await

__all__ = ("AnonymousDisposable",)


def default_dispose() -> None:
    return


class AnonymousDisposable(T.AsyncContextManager[None]):
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

    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, _: T.Any, __: T.Any, ___: T.Any) -> T.Optional[bool]:
        """Call anonymous function on dispose."""

        await attempt_await(self._adispose())

        return False

    def clear(self) -> None:
        self._adispose = default_dispose
