# Internal
import typing as T
from abc import ABCMeta, abstractmethod
from types import TracebackType

# External
from async_tools.context_manager import AbstractAsyncContextManager

AsyncContextManager_t = T.TypeVar("AsyncContextManager_t", bound="AsyncContextManager")


class AsyncContextManager(AbstractAsyncContextManager, metaclass=ABCMeta):
    """An abstract base class for asynchronous context managers."""

    async def __aenter__(self: AsyncContextManager_t) -> AsyncContextManager_t:
        """Return `self` upon entering the runtime context."""
        return self

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: T.Optional[T.Type[BaseException]],
        exc_value: T.Optional[BaseException],
        traceback: T.Optional[TracebackType],
    ) -> T.Optional[bool]:
        """Raise any exception triggered within the runtime context."""
        return None
