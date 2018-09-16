__all__ = ("Disposable", "adispose")

import typing as T
from abc import ABCMeta, abstractmethod
from asyncio import AbstractEventLoop, gather as agather, get_event_loop


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

    async def __aexit__(self, exc_type, value, traceback):
        await self.__adispose__()


async def adispose(*disposables: Disposable, loop: T.Optional[AbstractEventLoop] = None):
    """External access to disposable magic method.

    See also: :meth:`~.Disposable.__adispose__`

    Arguments:
        disposables: Objects to be disposed.
        loop: Event loop.

    """
    if loop is None:
        loop = get_event_loop()

    await agather(*(disposable.__adispose__() for disposable in disposables), loop=loop)
