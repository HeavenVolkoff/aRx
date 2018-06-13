# Internal
from asyncio import InvalidStateError


class ARxError(Exception):
    """aRx base error class."""
    pass


class ObserverClosedError(ARxError, InvalidStateError):
    """aRx error for when observer is used when closed."""

    def __init__(self, instance):
        """ObserverClosedError constructor.

        Arguments:
            instance: Observer instance.
        """
        super().__init__(f"{type(instance).__name__} is closed")

    pass


class SingleStreamMultipleError(ARxError, InvalidStateError):
    """aRx error for when single streams are subscribe more than once."""

    def __init__(self, instance):
        """SingleStreamMultipleError constructor.

        Arguments:
            instance: SingleStream instance.
        """
        super().__init__(
            f"Can't assign multiple observers to {type(instance).__name__}"
        )

    pass
