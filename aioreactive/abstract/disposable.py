from abc import ABCMeta, abstractmethod


class Disposable(metaclass=ABCMeta):
    """A disposable class with a context manager.

    Must implement the cancel method. Will cancel on exit."""

    @abstractmethod
    def __dispose__(self):
        return NotImplemented

    def __enter__(self):
        """Enter context management."""
        return self

    def __exit__(self, type, value, traceback) -> None:
        """Exit context management."""
        self.__dispose__()


class AsyncDisposable(metaclass=ABCMeta):
    """A disposable class with a context manager.

    Must implement the cancel method. Will cancel on exit."""

    @abstractmethod
    async def __adispose__(self):
        return NotImplemented

    async def __aenter__(self):
        """Enter context management."""
        return self

    async def __aexit__(self, type, value, traceback) -> None:
        """Exit context management."""
        await self.__adispose__()
