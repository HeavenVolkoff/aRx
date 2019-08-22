# Internal
import typing as T
from abc import abstractmethod

# External
import typing_extensions as Te

# Project
from .observer_protocol import ObserverProtocol

K = T.TypeVar("K", covariant=True)


class ObservableProtocol(Te.Protocol[K]):
    @abstractmethod
    async def __observe__(self, observer: ObserverProtocol[K]) -> None:
        """Interface through which observers are registered to observe the data flow.

        Define how each observers is registered into this observables and the
        mechanisms necessary for data flow and propagation.

        Arguments:
            observer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """
        raise NotImplementedError()

    @abstractmethod
    async def __dispose__(self, observer: ObserverProtocol[K]) -> None:
        """Interface through which observers are registered to observe the data flow.

        Define how each observers is registered into this observables and the
        mechanisms necessary for data flow and propagation.

        Arguments:
            observer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """
        raise NotImplementedError()
