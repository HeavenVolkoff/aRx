__all__ = ("AsyncExitStack",)

try:
    # noinspection PyProtectedMember
    from contextlib import AsyncExitStack  # type: ignore
except ImportError:
    from async_exit_stack import AsyncExitStack
