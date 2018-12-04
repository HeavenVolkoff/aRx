__all__ = ("Namespace", "get_namespace")

# Internal
import typing as T
from weakref import WeakKeyDictionary, WeakValueDictionary


class Namespace(T.NamedTuple):
    type: str
    previous: T.Optional["Namespace"]

    @property
    def id(self) -> int:
        """A unique identifier for namespace. Uses own namespace object id as a cheap solution"""
        return id(self)

    @property
    def ref(self) -> T.Optional[object]:
        """"""
        return ref_map.get(self.id, None)

    @property
    def is_root(self) -> bool:
        """"""
        return self.previous is None

    def search(self, item: T.Union[str, object, T.Type[T.Any]]) -> T.Optional["Namespace"]:
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
            # If no Namespace is assign to this item them we won't find any
            if item not in reverse_lookup:
                return None

            while namespace:
                if namespace.ref is item:
                    return namespace

                namespace = namespace.previous

        return None

    def __contains__(self, item: T.Union[str, object, T.Type[T.Any]]) -> bool:
        return self.search(item) is not None


ref_map: "WeakValueDictionary[int, object]" = WeakValueDictionary()
reverse_lookup: "WeakKeyDictionary[object, Namespace]" = WeakKeyDictionary()


def get_namespace(obj: object, previous: T.Optional[Namespace] = None) -> Namespace:
    namespace = reverse_lookup.get(obj, None)

    if namespace:
        return namespace

    namespace = Namespace(type=type(obj).__qualname__, previous=previous)

    ref_map[namespace.id] = obj
    reverse_lookup[obj] = namespace

    return namespace
