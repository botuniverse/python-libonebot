"""

"""
from typing import Dict, Optional, Callable


class Event(dict):
    user_id: Optional[str]
    self_id: str
    message: str
    type: str
    detail_type: Optional[str]
    sub_type: Optional[str]
    extended: Optional[Dict]


class CoreEvent(Event):
    pass
