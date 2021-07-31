"""

"""

import asyncio
from collections import defaultdict
from typing import Callable, List, Any

from .utils import run_async_funcs


class ActionBus:
    def __init__(self):
        self._subscribers = defaultdict(set)

    def subscribe(self, action: str, func: Callable) -> None:
        self._subscribers[action].add(func)

    def unsubscribe(self, action: str, func: Callable) -> None:
        if func in self._subscribers[action]:
            self._subscribers[action].remove(func)

    async def emit(self, action: str = "", *args, **kwargs):
        if action:
            await run_async_funcs(self._subscribers[action], *args, **kwargs)
        else:
            tasks = []
            for funcs in self._subscribers.values():
                tasks.append(run_async_funcs(funcs, *args, **kwargs))
            await run_async_funcs(tasks, *args, **kwargs)
