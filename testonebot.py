import libonebot
import asyncio


EVENT_DATA = {
    "user_id": "12234",
    "self_id": "123234",
    "messsage": "sajghds",
    "type": "message",
    "detail_type": "",
    "sub_type": "",
    "extended": {"data": "blah", "count": 0},
}
ACTION_DATA1 = {
    "action": "send_message",
    "params": {"user_id": "123", "message": "abcc"},
    "echo": {"id": "1"},
}

ACTION_DATA2 = {
    "action": "qq_group_system_message",
    "params": {"group_id": "123", "message": [{"type": "text"}, {"type": "text"}]},
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

CONFIG = {
    "http": {"enable": True, "host": "127.0.0.1", "port": 8080},
    "http_webhook": {"enable": True, "host": "https://127.0.0.1:5700"},
    "ws": {"enable": True, "host": "127.0.0.1", "port": 8081},
}


onebot = libonebot.OneBot(CONFIG)


@onebot.on_action("send_message")
async def send_message(**kwargs):
    print(f"Action send_message received {str(kwargs)}")
    assert kwargs == ACTION_DATA1["params"]
    return ACTION_RESULT1


@onebot.on_action("qq_group_system_message")
async def group_system_message(**kwargs):
    print(f"Extended action qq_group_system_message received {str(kwargs)}")
    assert kwargs == ACTION_DATA2["params"]
    return ACTION_RESULT2


async def onebot_main():
    async def count():
        while True:
            print(f'Sending event with count {EVENT_DATA["extended"]["count"]}')
            await onebot.push_event(**EVENT_DATA)
            EVENT_DATA["extended"]["count"] += 1
            await asyncio.sleep(5)

    await asyncio.gather(onebot.run(), count())


if __name__ == "__main__":
    asyncio.run(onebot_main())
