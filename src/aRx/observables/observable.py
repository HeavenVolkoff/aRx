# Internal
import typing as T
from abc import ABCMeta

# External
import typing_extensions as Te

# External
from async_tools import attempt_await

# Project
from ..protocols import ObserverProtocol, ObservableProtocol, TransformerProtocol
from ..operations.observe_op import observe

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


class Observable(ObservableProtocol[K], metaclass=ABCMeta):
    """Observable abstract class.

    Base class for defining an object through which data flows and can be observed.

    The data can be observed by :class:`~.Observer`.

    The logic that defines how the data is observed is specific for each Observable type,
    and must be implemented in the magic method :meth:`~.Observable.__observe__`.
    """

    def __init__(self, **kwargs: T.Any) -> None:
        """Observable constructor.

        Arguments:
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)  # type: ignore

    @T.overload
    def __gt__(
        self, observer: T.Awaitable[ObserverProtocol[K]]
    ) -> T.Awaitable[Te.AsyncContextManager[None]]:
        ...

    @T.overload
    def __gt__(self, observer: ObserverProtocol[K]) -> T.Awaitable[Te.AsyncContextManager[None]]:
        ...

    def __gt__(self, observer: T.Any) -> T.Awaitable[Te.AsyncContextManager[None]]:
        """Shortcut for :meth:`~.Observable.__observe__` magic method.

        Args:
            observer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """
        return observe(self, observer)

    def __or__(
        self,
        transformer: T.Union[T.Awaitable[TransformerProtocol[K, L]], TransformerProtocol[K, L]],
    ) -> TransformerProtocol[K, L]:
        """Shortcut for :meth:`~.Observable.__observe__` magic method.

        Args:
            transformer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """

        if not isinstance(transformer, TransformerProtocol):
            raise ValueError("Argument must be a Transformer")

        observe(self, transformer, keep_alive=transformer.keep_alive)

        return transformer


__all__ = ("Observable",)
