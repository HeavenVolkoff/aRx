__all__ = ("current_task",)

# Internal
import asyncio

current_task = getattr(asyncio, "current_task", asyncio.Task.current_task)
