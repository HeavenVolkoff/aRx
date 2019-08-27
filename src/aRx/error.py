# Internal
import typing as T

if T.TYPE_CHECKING:
    from .protocols import ObserverProtocol


class ARxError(Exception):
    """aRx base error class."""

    pass


class ObserverError(ARxError):
    """aRx error exclusive to :class:`~aRx.abstract.observers.Observer`."""

    pass


class ConsumerClosedError(ARxError):
    """aRx error used dy :class:`~.observers.consumer.Consumer`.

    Signalize when it closed without any result.

    """

    pass


class ObserverClosedError(ObserverError):
    """aRx error for when :class:`~aRx.abstract.observers.Observer` is used when closed."""

    def __init__(self, instance: "ObserverProtocol[T.Any]") -> None:
        """ObserverClosedError constructor.

        Arguments:
            instance: :class:`~aRx.abstract.observers.Observer` instance.

        """
        super().__init__(f"{type(instance).__qualname__} is closed")

    pass


class SingleStreamError(ARxError):
    """aRx error exclusive to :class:`~aRx.streams.single_stream.SingleStream`."""

    pass


__all__ = (
    "ARxError",
    "ObserverError",
    "ConsumerClosedError",
    "ObserverClosedError",
    "SingleStreamError",
)
