from asyncio import iscoroutinefunction

from aioreactive import abc


class AsyncDisposable(abc.AsyncDisposable):

    def __init__(self, dispose=None) -> None:
        if dispose:
            assert iscoroutinefunction(dispose)
        self._dispose = dispose

    async def __adispose__(self) -> None:
        await self._dispose()


class AsyncCompositeDisposable(AsyncDisposable):

    def __init__(self, *disposables) -> None:
        self._disposables = disposables

    async def __adispose__(self) -> None:
        for disposable in self._disposables:
            await disposable.__adispose__()
