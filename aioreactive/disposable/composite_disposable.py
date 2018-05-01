# Internal
from asyncio import iscoroutinefunction

# Project
from .. import abstract


class CompositeDisposable(abstract.Disposable):
    def __init__(
        self, a: abstract.Disposable, b: abstract.Disposable,
        *rest: abstract.Disposable
    ) -> None:
        disposables = [a, b] + list(rest)

        for disposable in disposables:
            if not iscoroutinefunction(disposable):
                raise TypeError("Parameters must be coroutines")

        self._disposables = disposables

    async def __adispose__(self) -> None:
        for disposable in self._disposables:
            await disposable.__adispose__()
