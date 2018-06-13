__all__ = ("Disposable", "adispose")

# Internal
from abc import ABCMeta, abstractmethod


class Disposable(object, metaclass=ABCMeta):
    """Custom closing logic interface for async context management."""

    __slots__ = ()

    def __init__(self, **kwargs):
        """Disposable constructor.

        Args
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

    @abstractmethod
    async def __adispose__(self):
        """This is where custom close logic must be implemented.

        Raises:
            NotImplemented

        """
        raise NotImplemented()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, value, traceback) -> None:
        await self.__adispose__()


async def adispose(disposable: Disposable):
    """External access to disposable magic method.

    See also: :meth:`~.Disposable.__adispose__`

    Arguments:
        disposable: Object to be disposed.

    """
    await disposable.__adispose__()
