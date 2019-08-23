# Internal
import typing as T
from asyncio import gather
from dataclasses import dataclass

# External
import typing_extensions as Te
from async_tools.context import AsyncExitStack

# Project
from ..protocols import ObserverProtocol, ObservableProtocol, TransformerProtocol

# Generic Types
K = T.TypeVar("K")
L = T.TypeVar("L")
M = T.TypeVar("M")


class Pipe(T.Generic[K, L], T.Awaitable[T.AsyncContextManager[T.Any]]):
    def __init__(self) -> None:
        self.__inner__: T.List[
            T.Union[ObserverProtocol[L], ObservableProtocol[K], TransformerProtocol[K, L]]
        ] = []

    def __or__(self, transformer: TransformerProtocol[L, M]) -> "Pipe[L, M]":
        p = T.cast(Pipe[L, M], self)

        p.__append__(transformer)
        return p

    def __gt__(self, observer: ObserverProtocol[L]) -> T.Awaitable[Te.AsyncContextManager[T.Any]]:
        """Shortcut for :meth:`~.Observable.__observe__` magic method.

        Args:
            observer: Observer which will be registered.

        Returns:
            :class:`~.disposable.Disposable` that undoes this subscription.

        """
        self.__append__(observer)
        # TODO: Improve this
        return self

    async def __await_impl__(self) -> T.AsyncContextManager[T.Any]:
        from ..operations import observe

        main_ctx = AsyncExitStack()
        pipe_list: T.Iterator[T.Tuple[ObservableProtocol[T.Any], ObserverProtocol[T.Any]]] = (
            zip(self.__inner__[:-1], self.__inner__[1:])  # type: ignore
        )

        for ctx in await gather(
            *(observe(observable, observer) for observable, observer in pipe_list)
        ):
            await main_ctx.enter_async_context(ctx)

        return main_ctx

    def __await__(self) -> T.Generator[None, None, T.AsyncContextManager[T.Any]]:
        return self.__await_impl__().__await__()

    __iter__ = __await__  # make compatible with 'yield from'.

    def __append__(self, value: T.Any) -> None:
        self.__inner__.append(value)
