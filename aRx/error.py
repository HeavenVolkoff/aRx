# Internal
from asyncio import InvalidStateError


class ARxError(Exception):
    """aRx base error class"""
    pass


class ObserverClosedError(ARxError, InvalidStateError):
    def __init__(self, instance):
        super().__init__(f"{type(instance).__name__} is closed")

    pass


class SingleStreamMultipleError(ARxError, InvalidStateError):
    def __init__(self, instance):
        super().__init__(
            f"Can't assign multiple observers to {type(instance).__name__}"
        )

    pass
