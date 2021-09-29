"""

"""
import asyncio
import json
import traceback

import aiohttp
import msgpack
import websockets

from typing import Awaitable

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from hypercorn.asyncio import serve
from hypercorn.config import Config

from .bus import ActionBus
from .action import Action

GET_LATEST_EVENTS = "get_latest_events"


class Comm:
    def __init__(self, logger):
        self._close_flag = False
        self._action_bus = None
        self.logger = logger

    async def push_event(self, *args, **event_data) -> None:
        raise NotImplementedError

    def register_action_handler(self, action_bus: ActionBus) -> None:
        self._action_bus = action_bus

    async def run(self) -> None:
        pass

    def close(self):
        self._close_flag = True


class CommHTTP(Comm):
    def __init__(self, logger, host, port):
        super().__init__(logger)
        self.host = host
        self.port = port
        self._latest_events = None
        self._server_app = FastAPI()

        async def _action_handler(action: Action) -> dict:
            if action.action == GET_LATEST_EVENTS:
                result = await self._get_latest_events()
            else:
                result = await self._action_bus.emit(**action.dict())
                result = dict(result)
            result["echo"] = action.echo
            return result

        self._server_app.post("/")(_action_handler)

    async def push_event(self, *args, **event_data) -> None:
        await self._latest_events.put(event_data)
        if self._latest_events.qsize() == 20 + 1:
            await self._latest_events.get()

    async def _get_latest_events(self) -> dict:
        result = []
        while not self._latest_events.empty():
            result.append(await self._latest_events.get())
        return {"status": "ok", "retcode": 0, "data": result}

    async def run(self) -> None:
        config = Config()
        self._latest_events = asyncio.Queue()
        config.bind = [f"{self.host}:{self.port}"]
        await serve(self._server_app, config)


class CommHTTPWebHook(Comm):
    def __init__(self, logger, host):
        super().__init__(logger)
        self.host = host
        self._http_session = None

    async def push_event(self, *args, **event_data) -> None:
        try:
            await self._http_session.post(self.host, json=event_data)
        except aiohttp.ClientError:
            print(traceback.format_exc())

    async def run(self):
        self._http_session = aiohttp.ClientSession()


class CommWS(Comm):
    def __init__(self, logger, host, port):
        super().__init__(logger)
        self.host = host
        self.port = port
        self._server_app = FastAPI()
        self._event_queues = set()

        async def websocket_endpoint(websocket: WebSocket):
            event_queue = asyncio.Queue()
            self._event_queues.add(event_queue)
            await websocket.accept()
            try:

                async def receive():
                    while True:
                        act = parse_message(await websocket.receive())
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

    async def push_event(self, *args, **event_data) -> None:
        await asyncio.gather(*[queue.put(event_data) for queue in self._event_queues])

    async def run(self) -> None:
        config = Config()
        config.bind = [f"{self.host}:{self.port}"]
        await serve(self._server_app, config)


class CommWSReverse(Comm):
    def __init__(self, logger, host, port, reconnect):
        super().__init__(logger)
        self._host = host
        self._port = port
        self._reconnect = reconnect
        self._event_queues = set()

    async def push_event(self, *args, **event_data) -> None:
        await asyncio.gather(*[queue.put(event_data) for queue in self._event_queues])

    async def run(self) -> None:
        event_queue = asyncio.Queue()
        self._event_queues.add(event_queue)
        while True and not self._close_flag:
            try:
                async with websockets.connect(
                    f"ws://{self._host}:{self._port}"
                ) as websocket:
                    try:

                        async def receive():
                            while True:
                                act = parse_message(await websocket.receive())
                                result = await self._action_bus.emit(**act)
                                result["echo"] = act["echo"]
                                await websocket.send_json(result)

                        async def send():
                            while True:
                                eve = await event_queue.get()
                                await websocket.send_json(eve)

                        await asyncio.gather(send(), receive(), return_exceptions=True)
                    except websockets.ConnectionClosed:
                        self.logger.warning(
                            f"Connection closed. Reconnect in {self._reconnect} seconds"
                        )
            except websockets.WebSocketException:
                self.logger.warning(
                    f"Connect reverse WebSocket failed. Reconnect in {self._reconnect} seconds"
                )
            await asyncio.sleep(self._reconnect / 1000)


def parse_message(msg: dict):
    if "text" in msg.keys() and not msg["text"] is None:
        return json.loads(msg["text"])
    elif "bytes" in msg.keys() and not msg["bytes"] is None:
        return msgpack.unpackb(msg["bytes"])
    else:
        raise TypeError(f"Cannot parse message {str(msg)}")
