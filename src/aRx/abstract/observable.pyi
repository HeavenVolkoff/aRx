# Internal
import typing as T
from abc import abstractmethod

# External
import typing_extensions as Te

# Project
from .observer import Observer
from .transformer import Transformer

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")


@Te.runtime
class Observable(Te.Protocol[K]):

    def __init__(self, **kwargs: T.Any) -> None:
        ...

    @abstractmethod
    def __observe__(
        self, observer: Observer[K], *, keep_alive: bool
    ) -> T.AsyncContextManager[None]:
        raise NotImplementedError()

    def __gt__(self, observer: Observer[K]) -> T.AsyncContextManager[None]:
        ...

    def __or__(self, transformer: Transformer[K, L]) -> Transformer[K, L]:
        ...

    def __add__(self, other: Observable[L]) -> Observable[T.Union[K, L]]:
        ...

    def __iadd__(self, other: Observable[L]) -> Observable[T.Union[K, L]]:
        ...
