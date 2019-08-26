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

    def search(self, item: T.Union[str, object, T.Type[T.Any]]) -> T.Optional["Namespace"]:
        """Search the chain for a namespace that matches the given item.

        Returns:
            First namespace match

        """
        namespace: T.Optional[Namespace] = self

        if isinstance(item, str):
            while namespace:
                if namespace.type == item:
                    return namespace

                namespace = namespace.previous
        elif isinstance(item, type):
            while namespace:
                # Only check ref on possible matches
                if namespace.type == item.__qualname__ and type(namespace.ref) == item:
                    return namespace

                namespace = namespace.previous
        else:
            while namespace:
                if namespace.ref is item:
                    return namespace

                namespace = namespace.previous

        return None

    def __contains__(self, item: T.Union[str, object, T.Type[T.Any]]) -> bool:
        return self.search(item) is not None


__all__ = ("Namespace",)
