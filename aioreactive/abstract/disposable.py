from abc import ABCMeta, abstractmethod


class Disposable(metaclass=ABCMeta):
    """A disposable class with a context manager.

    Must implement the cancel method. Will cancel on exit."""

    __slots__ = ()

    @abstractmethod
    async def __adispose__(self):
        return NotImplemented

    async def __aenter__(self):
        """Enter context management."""
        return self

    async def __aexit__(self, exc_type, value, traceback) -> None:
        """Exit context management."""
        await self.__adispose__()
