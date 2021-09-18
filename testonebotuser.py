import asyncio
import json

from flask import Flask, request
import websockets
import requests

EVENT_DATA = {
    "user_id": "12234",
    "self_id": "123234",
    "messsage": "sajghds",
    "type": "message",
    "detail_type": "",
    "sub_type": "",
    "extended": {"data": "blah"},
}
ACTION_DATA1 = {
    "action": "send_message",
    "params": {"user_id": "123", "message": "abcc"},
    "echo": {"id": "1"},
}

ACTION_DATA2 = {
    "action": "qq_group_system_message",
    "params": {"group_id": "123", "message": "abcc"},
    "echo": {"id": "2"},
}

ACTION_RESULT1 = {
    "status": "ok",
    "retcode": 0,
    "data": {},
    "echo": ACTION_DATA1["echo"],
}

ACTION_RESULT2 = {
    "status": "ok",
    "retcode": 0,
    "data": {},
    "echo": ACTION_DATA2["echo"],
}

onebot_user = Flask("user")


@onebot_user.route("/", methods=["POST"])
def event():
    print(f"Event received {str(request.json)}")
    assert dict(request.json) == EVENT_DATA
    return None


async def onebot_user_ws_test():
    async with websockets.connect("ws://127.0.0.1:8081/ws") as onebot_user_ws:
        while True:
            print(await onebot_user_ws.recv())


def onebot_user_http_test():
    result = requests.post("http://127.0.0.1:8080", json=ACTION_DATA1)
    assert result.json() == ACTION_RESULT1
    result = requests.post("http://127.0.0.1:8080", json=ACTION_DATA2)
    assert result.json() == ACTION_RESULT2


if __name__ == "__main__":
    onebot_user_http_test()
    asyncio.run(onebot_user_ws_test())
