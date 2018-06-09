# Project
from ..abstract.disposable import Disposable, adispose


class CompositeDisposable(Disposable):
    @staticmethod
    def validate_mapper(disposable):
        return isinstance(disposable, Disposable)

    def __init__(
        self, a: Disposable, b: Disposable, *rest: Disposable, **kwargs
    ) -> None:
        disposables = (a, b) + rest

        if not all(map(self.validate_mapper, disposables)):
            raise TypeError("Parameters must be disposable")

        super().__init__(**kwargs)

        self._disposables = disposables

    async def __adispose__(self) -> None:
        for disposable in self._disposables:
            await adispose(disposable)
