__all__ = ("Disposable", "adispose")

# Internal
import typing as T
from abc import ABCMeta, abstractmethod
from types import TracebackType
from asyncio import ALL_COMPLETED, Future, wait


class Disposable(object, metaclass=ABCMeta):
    """Custom closing logic interface for async context management."""

    __slots__ = ()

    def __init__(self, **kwargs: T.Any) -> None:
        """Disposable constructor.

        Args
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)  # type: ignore

    @abstractmethod
    async def __adispose__(self) -> None:
        """This is where custom close logic must be implemented.

        Raises:
            NotImplemented

        """
        raise NotImplemented()

    async def __aenter__(self) -> "Disposable":
        return self

    async def __aexit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional[TracebackType],
    ) -> None:
        await self.__adispose__()


async def adispose(*disposables: Disposable) -> None:
    """External access to disposable magic method.

    See also: :meth:`~.Disposable.__adispose__`

    Arguments:
        disposables: Objects to be disposed.

    """
    if not disposables:
        return

    done, pending = await wait(
        tuple(
            T.cast(T.Awaitable[bool], disposable.__aexit__(None, None, None))
            for disposable in disposables
        ),
        return_when=ALL_COMPLETED,
    )  # type: T.Set[Future[bool]], T.Set[Future[bool]]

    assert not pending
    for fut in done:
        exc = fut.exception()
        if exc:
            raise exc
