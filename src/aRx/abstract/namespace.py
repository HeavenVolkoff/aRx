__all__ = ("Namespace", "get_namespace")

# Internal
import typing as T
from weakref import WeakValueDictionary
from dataclasses import dataclass

ref_map: T.MutableMapping[int, object] = WeakValueDictionary()


@dataclass
class Namespace:
    type: T.Type[T.Any]
    action: str
    previous: T.Optional["Namespace"]

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
        return ref_map.get(self.id, None)

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


def get_namespace(obj: object, action: str, previous: T.Optional[Namespace] = None) -> Namespace:
    """Generate namespace for given namespace.

    Args:
        obj: Object for which to generate namespace.
        action: Action represented by namespace.
        previous: Previous namespace in chain.

    Returns:
        Namespace.

    """
    namespace = Namespace(type=type(obj), action=action, previous=previous)

    ref_map[namespace.id] = obj

    return namespace
