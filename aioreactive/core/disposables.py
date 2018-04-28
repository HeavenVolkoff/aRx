# Internal
import typing as T
from asyncio import iscoroutinefunction

# Project
from .. import abstract
from .utils import anoop


class AsyncDisposable(abstract.AsyncDisposable):
    def __init__(self,
                 dispose: T.Callable[None, T.Awaitable[None]] = anoop) -> None:
        if not iscoroutinefunction(dispose):
            raise TypeError("Parameter dispose must be a coroutine")

        self._dispose = dispose

    async def __adispose__(self) -> None:
        await self._dispose()


class AsyncCompositeDisposable(abstract.AsyncDisposable):
    def __init__(
        self, a: AsyncDisposable, b: AsyncDisposable, *rest: AsyncDisposable
    ) -> None:
        disposables = [a, b] + rest

        for disposable in disposables:
            if not iscoroutinefunction(disposable):
                raise TypeError("Parameters must be coroutines")

        self._disposables = disposables

    async def __adispose__(self) -> None:
        for disposable in self._disposables:
            await disposable.__adispose__()
