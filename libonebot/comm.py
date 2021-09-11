"""

"""
import asyncio
import requests
import websockets

from typing import Awaitable

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from hypercorn.asyncio import serve
from hypercorn.config import Config

from .bus import ActionBus
from .action import Action


class Comm:
    def __init__(self, logger):
        self._close_flag = False
        self._action_bus = None

    async def push_event(self, *args, **event_data) -> Awaitable:
        raise NotImplementedError

    def register_action_handler(self, action_bus: ActionBus) -> None:
        self._action_bus = action_bus

    async def run(self) -> Awaitable:
        pass

    def close(self):
        self._close_flag = True


class CommHTTP(Comm):
    def __init__(self, logger, host, port):
        super().__init__(logger)
        self._host = host
        self._port = port
        self._server_app = FastAPI()

        async def _action_handler(action: Action) -> Awaitable:
            result = await self._action_bus.emit(**action.dict())
            result = dict(result)
            result["echo"] = action.echo
            return result

        self._server_app.post("/")(_action_handler)

    async def run(self) -> Awaitable:
        config = Config()
        config.bind = [f"{self._host}:{self._port}"]
        await serve(self._server_app, config)


class CommHTTPWebHook(Comm):
    def __init__(self, logger, host):
        super().__init__(logger)
        self._host = host
        self._http_session = requests.session()
        self._event_queue = asyncio.Queue()

    async def push_event(self, *args, **event_data) -> Awaitable:
        await self._event_queue.put(event_data)

    async def run(self) -> Awaitable:
        loop = asyncio.get_event_loop()

        async def push():
            while True:
                eve = await self._event_queue.get()
                self._http_session.post(self._host, data=eve)

        task = loop.create_task(push())
        await task


class CommWS(Comm):
    def __init__(self, logger, host, port):
        super().__init__(logger)
        self._host = host
        self._port = port
        self._server_app = FastAPI()
        self._event_queues = set()

        async def websocket_endpoint(websocket: WebSocket):
            loop = asyncio.get_event_loop()
            event_queue = asyncio.Queue()
            self._event_queues.add(event_queue)
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
                self._event_queues.remove(event_queue)

        self._server_app.websocket("/ws")(websocket_endpoint)

    async def push_event(self, *args, **event_data) -> Awaitable:
        await asyncio.gather(*[queue.put(event_data) for queue in self._event_queues])

    async def run(self) -> Awaitable:
        config = Config()
        config.bind = [f"{self._host}:{self._port}"]
        await serve(self._server_app, config)


class CommWSReverse(Comm):
    def __init__(self, logger, host, port, reconnect):
        super().__init__(logger)
        self._host = host
        self._port = port
        self._reconnect = reconnect
        self._event_queue = asyncio.Queue()

    async def push_event(self, *args, **event_data) -> Awaitable:
        self._event_queue.put(event_data)

    async def run(self) -> Awaitable:
        while True and not self._close_flag:
            try:
                async with websockets.connect(
                    f"ws://{self._host}:{self._port}"
                ) as websocket:
                    try:

                        async def receive():
                            while True:
                                act = await websocket.receive_json()
                                result = await self._action_bus.emit(**act)
                                result["echo"] = act["echo"]
                                await websocket.send_json(result)

                        async def send():
                            while True:
                                eve = await self._event_queue.get()
                                await websocket.send_json(eve)

                        await asyncio.gather(send(), receive(), return_exceptions=True)
                    except websockets.ConnectionClosed:
                        pass
            except:
                pass
            await asyncio.sleep(self._reconnect)
