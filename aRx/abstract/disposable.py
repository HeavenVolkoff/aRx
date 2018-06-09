__all__ = ("Disposable", "adispose")

# Internal
from abc import ABCMeta, abstractmethod


class Disposable(object, metaclass=ABCMeta):
    """Interface for custom closing logic for async context management."""

    __slots__ = ()

    def __init__(self, **kwargs):
        """Disposable constructor.

        Args
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

    @abstractmethod
    async def __adispose__(self):
        """Implementation of custom close logic."""
        return NotImplemented

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, value, traceback) -> None:
        await self.__adispose__()


async def adispose(disposable: Disposable):
    await disposable.__adispose__()
