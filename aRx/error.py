# Internal
import typing as T

from traceback import TracebackException


class ARxError(Exception):
    """aRx base error class."""
    pass


class ObserverError(ARxError):
    """aRx error exclusive to observer."""
    pass


class ObserverClosedError(ObserverError):
    """aRx error for when observer is used when closed."""

    def __init__(self, instance):
        """ObserverClosedError constructor.

        Arguments:
            instance: Observer instance.

        """
        super().__init__(f"{type(instance).__name__} is closed")

    pass


class SingleStreamError(ARxError):
    """aRx error for when SingleStream are subscribe more than once."""
    pass


class ARxWarning(Warning):
    """aRx base warning class."""

    def __init__(self, msg: str, error: T.Optional[Exception] = None):
        if error is not None:
            msg += (
                "\n" +
                "".join(TracebackException.from_exception(error).format())
            )

        super().__init__(msg)


class DisposeWarning(ARxWarning):
    """aRx error for when dispose fails."""
    pass
