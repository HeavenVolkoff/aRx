__all__ = (
    "ARxError", "ObserverError", "ObserverClosedError", "SingleStreamError",
    "MultiStreamError", "ARxWarning"
)

# Internal
import typing as T


class ARxError(Exception):
    """aRx base error class."""
    pass


class ObserverError(ARxError):
    """aRx error exclusive to :class:`~aRx.abstract.observer.Observer`."""
    pass


class ObserverClosedError(ObserverError):
    """aRx error for when :class:`~aRx.abstract.observer.Observer` is used when closed."""

    def __init__(self, instance):
        """ObserverClosedError constructor.

        Arguments:
            instance: :class:`~aRx.abstract.observer.Observer` instance.

        """
        super().__init__(f"{type(instance).__qualname__} is closed")

    pass


class SingleStreamError(ARxError):
    """aRx error exclusive to :class:`~aRx.stream.single_stream.SingleStream`."""
    pass


class MultiStreamError(ARxError):
    """aRx error exclusive to :class:`~aRx.stream.multi_stream.MultiStream`."""
    pass


class ARxWarning(Warning):
    """aRx base warning class."""

    def __init__(self, msg: str, exception: T.Optional[Exception] = None):
        """ARxWarning constructor.
        
        Arguments:
            msg: Warning message.
            exception: Optional exception to be added to the warning message.

        """
        if exception is not None:
            from traceback import TracebackException
            msg += (
                "\n" +
                "".join(TracebackException.from_exception(exception).format())
            )

        super().__init__(msg)
