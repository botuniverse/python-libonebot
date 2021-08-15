"""

"""

import asyncio
import logging
import requests
import uvicorn
from typing import Optional, Callable, Awaitable, Coroutine, Iterable
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from .bus import ActionBus, EventBus
from .event import Event
from .action import Action, CoreActions

__all__ = []
HTTP_HOST = "127.0.0.1"
HTTP_PORT = 8080
HTTP_WEBHOOK = "http://127.0.0.1:5700"
WS_HOST = "127.0.0.1"
WS_PORT = 8080
WS_REVERSE_HOST = "127.0.0.1"
WS_REVERSE_PORT = ""


class OneBot:
    def __init__(
        self,
        config_file: Optional[str] = None,
    ):
        self._server_app = FastAPI()
        self._register_action_handler(CoreActions.values())
        self._register_websocket()
        self._action_bus = ActionBus()
        self._event_bus = EventBus()
        self._http_session = requests.Session()
        self._register_http_webhook(HTTP_WEBHOOK)

    def _register_action_handler(self, actions: Iterable[str]) -> None:
        async def _action_handler(action: Action) -> Awaitable:
            result = await self._action_bus.emit(**action.dict())
            result = dict(result)
            result["echo"] = action.echo
            return result

        self._server_app.post("/")(_action_handler)
        # for action_model in actions:
        #     self._server_app.post("/")

    def _register_websocket(self) -> None:
        async def websocket_endpoint(websocket: WebSocket):
            event_queue = asyncio.Queue()

            async def enque_event(*args, **kwargs):
                await event_queue.put(kwargs)

            self._event_bus.subscribe(enque_event)
            await websocket.accept()
            try:

                async def receive():
                    while True:
                        act = await websocket.receive_json()
                        result = await self._action_bus.emit(**act)
                        result["echo"] = act["echo"]
                        await websocket.send_json(result)

                async def send():
                    while True:
                        eve = await event_queue.get()
                        await websocket.send_json(eve)

                await asyncio.gather(send(), receive(), return_exceptions=True)
            except WebSocketDisconnect:
                self._event_bus.unsubscribe(enque_event)

        self._server_app.websocket("/ws")(websocket_endpoint)

    def _register_http_webhook(self, http_host: str) -> None:
        async def send_event(*args, **event_data):
            self._http_session.post(http_host, data=event_data)

        self._event_bus.subscribe(send_event)

    def on_action(
        self, action: str, platform: Optional[str] = ""
    ) -> Callable[[Callable], Awaitable]:
        def api_deco(func: Callable) -> Awaitable:
            async def inner(*args, **kwargs):
                return await func(*args, **kwargs)

            if platform:
                self.register_extended_action(
                    platform=platform, action=action, func=inner
                )
            else:
                self.register_action(action=action, func=inner)

            return inner

        return api_deco

    def register_action(self, action: str, func: Callable):
        self._action_bus.subscribe(action, func)

    def register_extended_action(self, platform: str, action: str, func: Callable):
        action_name = f"{platform}_{action}"
        self._action_bus.subscribe(action_name, func)

    async def send_event(self, **event_data) -> None:
        await self._event_bus.emit(**event_data)

    async def send_extended_event(self, platform: str, **event_data) -> None:
        if "sub_type" in event_data:
            sub_type = event_data["sub_type"]
            if not sub_type.startswith(platform):
                sub_type = f"{platform}_{sub_type}"
            event_data["sub_type"] = sub_type
        await self.send_event(**event_data)

    def run(self):
        uvicorn.run(self._server_app, host=HTTP_HOST, port=HTTP_PORT, log_level="debug")
