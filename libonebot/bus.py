"""

"""

import asyncio
from collections import defaultdict
from typing import Callable, List, Any, Dict

from .utils import run_async_funcs
from .action import Action


class ActionBus:
    def __init__(self):
        self._subscribers = defaultdict(Callable)

    def subscribe(self, action: str, func: Callable) -> None:
        self._subscribers[action] = func

    def unsubscribe(self, action: str, func: Callable) -> None:
        if func in self._subscribers[action]:
            self._subscribers[action] = None

    async def emit(self, action: str, params: Dict, **kwargs):
        result = await self._subscribers[action](**params)
        return result


class EventBus:
    def __init__(self):
        self._subscribers = set()

    def subscribe(self, func: Callable) -> None:
        self._subscribers.add(func)

    def unsubscribe(self, func: Callable) -> None:
        if func in self._subscribers:
            self._subscribers.remove(func)

    async def emit(self, *args, **kwargs) -> None:
        await run_async_funcs(self._subscribers, *args, **kwargs)
