"""## Asynchronous Reactive Extensions

A library to make asynchronous reactive programming in python easy to use.

Its main purpose is to provide a framework for reactive programming built
following python's standard on top of asyncio module's constructs.

<script>
    .. include:: ../../docs/rework-links.js
</script>

<details class="rework-link">
  <summary>Copyright</summary>

  .. include:: ../../COPYRIGHT.md
    :start-line:1

</details>

<details class="rework-link">
  <summary>License (Mozilla Public License Version 2.0)</summary>

  .. include:: ../../LICENSE.md
    :start-line:1

</details>

"""

# External
from importlib_metadata import version

try:
    __version__: str = version(__name__)
except Exception:  # pragma: no cover
    import traceback
    from warnings import warn

    warn(f"Failed to set version due to:\n{traceback.format_exc()}", ImportWarning)
    __version__ = "0.0a0"

__all__ = ("__version__",)
