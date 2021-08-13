"""

"""
from typing import Dict, Optional, Iterable, Any
from pydantic import BaseModel


class Action(BaseModel):
    action: str
    params: Dict[str, Any] = {}
    echo: Dict = {}


class ActionDict(dict):
    def __getattr__(self, item: str) -> Any:
        return self[item]


_core_actions = {
    "send_message": "send_message",
}

CoreActions = ActionDict(_core_actions)


# def _core_action_set_factory() -> Iterable[CoreActions]:
#     action_list = ["send_message"]
#     core_action_set = set()
#     for action in action_list:
#         pass
