import asyncio
import cmd
import json
import threading
import time

import aiohttp
from hypercorn.asyncio import serve
from hypercorn.config import Config
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from libonebot import OneBot, Event

CONFIG = {
    "http": {"enable": True, "host": "127.0.0.1", "port": 8080},
    "http_webhook": {"enable": True, "host": "http://127.0.0.1:5700"},
    "ws": {"enable": True, "host": "127.0.0.1", "port": 8081},
    "ws_reverse": {
        "enable": True,
        "host": "127.0.0.1",
        "port": 5701,
        "reconnect_interval": 5000,
    },
}


EVENT_DATA = {
    "user_id": "test1",
    "self_id": "test2",
    "message": "",
    "type": "message",
    "detail_type": "private",
    "sub_type": "",
    "extended": {},
    "platform": "repltest",
}


class OneBotRepl:
    def __init__(self):
        self._id = 0
        self.onebot = OneBot(CONFIG)

        @self.onebot.on_action("send_message")
        async def onebot_action_handler(**params):
            print(f"libOneBot received send_message Action: {str(params)}")
            return {"retcode": 0, "status": "Test Succeed!"}

        self.http_webhook_user = FastAPI()

        @self.http_webhook_user.post("/")
        def event(eve: Event):
            print(f"Bot received Event from HTTP Webhook: {str(eve.dict())}")
            return {}

        self.ws_reverse_user = FastAPI()
        self.ws_reverse_user_connection = None

        @self.ws_reverse_user.websocket("/")
        async def ws_reverse_user_handler(websocket: WebSocket):
            await websocket.accept()
            self.ws_reverse_user_connection = websocket
            try:

                async def receive():
                    while True:
                        eve = await websocket.receive_json()
                        print(
                            f"Bot received Event or Action result from WebSocket reverse: {str(eve)}"
                        )

                await receive()
            except WebSocketDisconnect:
                self.ws_reverse_user_connection = None

    def run(self):
        # t1 = threading.Thread(
        #     target=self.httpwebhook_user.run, kwargs={"host": "127.0.0.1", "port": 5700}
        # )
        # t1.daemon = True
        # t1.start()
        loop = asyncio.get_event_loop()
        config1 = Config()
        config1.bind = ["127.0.0.1:5700"]
        loop.create_task(serve(self.http_webhook_user, config1))
        config2 = Config()
        config2.bind = ["127.0.0.1:5701"]
        loop.create_task(serve(self.ws_reverse_user, config2))
        loop.create_task(self.onebot.run())

        def repl():
            time.sleep(1)

            async def receive():
                async with websockets.connect("ws://127.0.0.1:8081/ws") as websocket:
                    self.ws_user = websocket
                    while True:
                        eve = await self.ws_user.recv()
                        eve = json.loads(eve)
                        print(
                            f"User received Event or Action result from WebSocket: {str(eve)}"
                        )

            loop.create_task(receive())

            while True:
                print(
                    "(1) HTTP Action\n(2) HTTP get_latest_events\n(3) WebSocket Action\n(4) WebSocket Reverse "
                    "Action\n(5) HTTP Webhook/WS/WS Reverse Event\n(6) Quit OneBot REPL"
                )
                selection = input("Enter ID for communication to test: ")
                selection = selection.strip()
                if selection in ["1", "3", "4"]:
                    message = input("Please enter message for send_message Action: ")
                    if selection == "1":
                        loop.create_task(self.test_http_action_message(message))
                    elif selection == "3":
                        loop.create_task(self.test_ws_action_message(message))
                    elif selection == "4":
                        loop.create_task(self.test_ws_reverse_action_message(message))
                elif selection == "2":
                    loop.create_task(self.test_http_get_latest_events())
                elif selection == "5":
                    message = input("Please enter message for message Event: ")
                    event = EVENT_DATA.copy()
                    event["message"] = message
                    event["time"] = int(time.time())
                    event["id"] = self._id
                    self._id += 1
                    print(f"OneBot pushed Event: {str(event)}")
                    loop.create_task(self.onebot.push_event(**event))
                elif selection == "6":
                    break
                time.sleep(1)
            loop.stop()

        async def setup():
            await asyncio.sleep(1)
            self.http_user = aiohttp.ClientSession()

        loop.create_task(setup())
        t2 = threading.Thread(target=repl)
        t2.daemon = True
        t2.start()
        loop.run_forever()

    async def test_http_action_message(self, message):
        action = self.action_message(message)
        print(f"Bot sent Action with HTTP: {str(action)}")
        result = await self.http_user.post(
            "http://127.0.0.1:8080",
            json=action,
        )
        print(f"Bot received Action result from HTTP: {str(await result.json())}")

    async def test_ws_action_message(self, message):
        action = self.action_message(message)
        print(f"Bot sent Action with WebSocket: {str(action)}")
        await self.ws_user.send(json.dumps(action))

    async def test_ws_reverse_action_message(self, message):
        action = self.action_message(message)
        print(f"Bot sent Action with WebSocket reverse: {str(action)}")
        await self.ws_reverse_user_connection.send_json(action)

    async def test_http_get_latest_events(self):
        action = {
            "action": "get_latest_events",
            "params": {},
            "echo": {"id": self._id},
        }
        self._id += 1
        print(f"Bot sent Action with HTTP: {str(action)}")
        result = await self.http_user.post("http://127.0.0.1:8080", json=action)
        print(f"Bot received Action result from HTTP: {str(await result.json())}")

    def action_message(self, message):
        action = {
            "action": "send_message",
            "params": {"user_id": "dest", "message": message},
            "echo": {"id": self._id},
        }
        self._id += 1
        return action


if __name__ == "__main__":
    ob = OneBotRepl()
    ob.run()
