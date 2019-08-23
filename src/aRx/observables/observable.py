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


async def pipe(
    observable: ObservableProtocol[K],
    transformer: T.Union[T.Awaitable[TransformerProtocol[K, L]], TransformerProtocol[K, L]],
) -> TransformerProtocol[K, L]:
    transformer = await attempt_await(transformer)

    if not isinstance(transformer, TransformerProtocol):
        raise ValueError("Argument must be a Transformer")

    await observe(observable, transformer, keep_alive=transformer.keep_alive)
    return transformer


class Observable(ObservableProtocol[K], metaclass=ABCMeta):
    """Observable abstract class.

    Base class for defining an object through which data flows and can be observed.

    The data can be observed by :class:`~.Observer`.

    The logic that defines how the data is observed is specific for each Observable type,
    and must be implemented in the magic method :meth:`~.Observable.__observe__`.
    """

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
    ) -> T.Coroutine[None, None, TransformerProtocol[K, L]]:
        """Shortcut for :meth:`~.Observable.__observe__` magic method.

        Args:
            transformer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """
        return pipe(self, transformer)


__all__ = ("Observable",)
