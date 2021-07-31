"""

"""
from typing import Dict, Optional, Iterable, Any
from pydantic import BaseModel


class Action(BaseModel):
    action: str
    params: Dict[str, Any] = {}
    echo: Dict = {}


class CoreAction(Action):
    pass


def _core_action_set_factory() -> Iterable[CoreAction]:
    action_list = ["send_message"]
    core_action_set = set()
    for action in action_list:
        pass


CoreActionSet = set()
