"""

"""
from typing import Dict, Optional, Callable
from pydantic import BaseModel


class Event(BaseModel):
    user_id: Optional[str]
    self_id: str
    message: Optional[str]
    type: str
    detail_type: str
    sub_type: str
    id: int
    time: int
    platform: str
    extended: Optional[Dict]


class CoreEvent(Event):
    pass
