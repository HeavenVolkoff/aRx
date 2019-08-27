# Internal
import typing as T
from weakref import WeakValueDictionary
from dataclasses import InitVar, field, dataclass

_ref_map: T.MutableMapping[int, object] = WeakValueDictionary()


@dataclass
class Namespace:
    obj: InitVar[object]
    type: T.Type[T.Any] = field(init=False)
    action: str
    previous: T.Optional["Namespace"] = None

    def __post_init__(self, obj: object) -> None:
        _ref_map[self.id] = obj
        self.type = type(obj)

    @property
    def id(self) -> int:
        """A unique identifier for namespace. Uses own namespace object id as a cheap solution.

        Returns:
            Unique identifier for namespace

        """
        return id(self)

    @property
    def ref(self) -> T.Optional[object]:
        """A reference to the object that is represented by this namespace.

        Returns:
            Reference to the object.

        """
        return _ref_map.get(self.id, None)

    @property
    def is_root(self) -> bool:
        """Check if this namespace is the root in the chain.

        Returns:
            Whether this namespace is this chain root.

        """
        return self.previous is None

    @staticmethod
    def _search_strategies(
        item: T.Union[str, object, T.Type[T.Any]]
    ) -> T.Callable[["Namespace"], bool]:
        if isinstance(item, str):
            return lambda namespace: namespace.action != item
        elif isinstance(item, type):
            return lambda namespace: namespace.type != item
        else:
            return lambda namespace: namespace.ref is not item

    def search(self, item: T.Union[str, object, T.Type[T.Any]]) -> T.Optional["Namespace"]:
        """Search the chain for a namespace that matches the given item.

        Returns:
            First namespace match

        """
        strategy = self._search_strategies(item)
        namespace: T.Optional[Namespace] = self

        while namespace and strategy(namespace):
            namespace = namespace.previous

        return namespace

    def __contains__(self, item: T.Union[str, object, T.Type[T.Any]]) -> bool:
        return self.search(item) is not None


__all__ = ("Namespace",)
