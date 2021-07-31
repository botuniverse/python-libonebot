"""

"""

import asyncio
import logging
import uvicorn
from typing import Optional, Callable, Awaitable, Coroutine, Iterable
from fastapi import FastAPI, WebSocket

from .bus import ActionBus
from .event import Event
from .action import Action, CoreActionSet

__all__ = []


class OneBot:
    def __init__(
        self,
        config_file: Optional[str] = None,
    ):
        self._server_app = FastAPI()
        self._register_action_handler(CoreActionSet)
        self._action_bus = ActionBus()

    def _register_action_handler(self, actions: Iterable[Action]):
        async def _action_handler(action: Action) -> None:
            await self._action_bus.emit(action=action.action, action_data=action)

        self._server_app.post("/")(_action_handler)
        for action_model in actions:
            self._server_app.post("/")

    def on_action(
        self, action: Optional[str] = None
    ) -> Callable[[Callable], Awaitable]:
        def api_deco(func: Callable) -> Awaitable:
            async def inner(*args, **kwargs):
                await func(*args, **kwargs)

            self._action_bus.subscribe(action, inner)

            return inner

        return api_deco

    def register_action(self, action: Action, func):
        self._action_bus.subscribe(action, func)

    def run(self):
        uvicorn.run(self._server_app, host="127.0.0.1", port=8080, log_level="debug")
