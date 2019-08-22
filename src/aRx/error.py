# Internal
import traceback


class ARxError(Exception):
    """aRx base error class."""

    pass


class ARxWarning(UserWarning):
    """aRx base error class."""

    pass


class ObserverError(ARxError):
    """aRx error exclusive to :class:`~aRx.abstract.observers.Observer`."""

    pass


class ObserverClosedError(ObserverError):
    """aRx error for when :class:`~aRx.abstract.observers.Observer` is used when closed."""

    def __init__(self, instance: object) -> None:
        """ObserverClosedError constructor.

        Arguments:
            instance: :class:`~aRx.abstract.observers.Observer` instance.

        """
        super().__init__(f"{type(instance).__qualname__} is closed")

    pass


class ObserverClosedWarning(ARxWarning):
    def __init__(self, msg: str, exc: Exception):
        super().__init__(msg)
        self.exc = exc

    def __str__(self) -> str:
        return (
            super().__str__()
            + "\n"
            + "".join(traceback.format_exception(None, self.exc, self.exc.__traceback__))
        )


class SingleStreamError(ARxError):
    """aRx error exclusive to :class:`~aRx.streams.single_stream.SingleStream`."""

    pass


class MultiStreamError(ARxError):
    """aRx error exclusive to :class:`~aRx.streams.multi_stream.MultiStream`."""

    pass


__all__ = (
    "ARxError",
    "ARxWarning",
    "ObserverError",
    "ObserverClosedError",
    "ObserverClosedWarning",
    "SingleStreamError",
    "MultiStreamError",
)
