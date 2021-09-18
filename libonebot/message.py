"""

"""
from typing import Union, Optional, Iterable


class MessageSegment:
    def __init__(self, data: Optional[Union[str, dict]] = "", msg_type: str = "text"):
        self._msg_seg = {"type": msg_type}
        if self._msg_seg["type"] == "text" and isinstance(data, str):
            self._msg_seg["data"] = {"text": data}
        elif isinstance(data, dict):
            self._msg_seg["data"] = data
        else:
            raise TypeError

    def __str__(self) -> str:
        return str(self._msg_seg)

    def __repr__(self) -> str:
        return repr(self._msg_seg)


class Message:
    def __init__(
        self, msg: Optional[Union[str, MessageSegment, Iterable[MessageSegment]]] = None
    ):
        self.segments = []
        if isinstance(msg, str) and len(msg) > 0:
            self.segments.append(MessageSegment(msg))
        elif isinstance(msg, MessageSegment):
            self.segments.append(msg)
        elif isinstance(msg, Iterable):
            for m in msg:
                if isinstance(m, MessageSegment):
                    self.segments.append(m)
                else:
                    raise TypeError(f"Expected MessageSegment but get {str(type(m))}")

    def __str__(self) -> str:
        s = ""
        for segment in self.segments:
            s += str(segment)
        return s

    def __repr__(self) -> str:
        s = ""
        for segment in self.segments:
            s += repr(segment)
        return s
