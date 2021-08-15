import libonebot
import asyncio


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


onebot = libonebot.OneBot()


@onebot.on_action("send_message")
async def send_message(*args, **kwargs):
    print(f"Action send_message received {str(kwargs)}")
    kwargs["action"] = ACTION_DATA1["action"]
    assert kwargs == ACTION_DATA1
    return ACTION_RESULT1


@onebot.on_action("group_system_message", "qq")
async def group_system_message(*args, **kwargs):
    print(f"Extended action qq_group_system_message received {str(kwargs)}")
    kwargs["action"] = ACTION_DATA2["action"]
    assert kwargs == ACTION_DATA2
    return ACTION_RESULT2


if __name__ == "__main__":
    onebot.run()
