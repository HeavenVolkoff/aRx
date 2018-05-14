from asyncio import InvalidStateError


class ReactiveError(Exception):
    pass


class ObserverClosedError(ReactiveError, InvalidStateError):
    def __init__(self, instance):
        super().__init__(f"{type(instance).__name__} is closed")

    pass


class SingleStreamMultipleError(ReactiveError, InvalidStateError):
    def __init__(self, instance):
        super().__init__(
            f"Can't assign multiple observers to {type(instance).__name__}"
        )

    pass
