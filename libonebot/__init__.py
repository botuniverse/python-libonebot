"""

"""

import asyncio
import logging
import requests
import websockets

from typing import Optional, Callable, Awaitable, Coroutine, Iterable, Dict, Any

from .bus import ActionBus, EventBus
from .comm import CommHTTP, CommHTTPWebHook, CommWS, CommWSReverse
from .event import Event
from .action import Action
from .exceptions import ConfigError

__all__ = []
HTTP_HOST = "127.0.0.1"
HTTP_PORT = 8080
HTTP_WEBHOOK = "http://127.0.0.1:5700"
WS_HOST = "127.0.0.1"
WS_PORT = 8081
WS_REVERSE_HOST = "127.0.0.1"
WS_REVERSE_PORT = 5701
WS_RECONNECT_INTERVAL = 5000


class OneBot:
    def __init__(self, config: Dict = None, logger=None):
        self._comm_http = None
        self._comm_http_webhook = None
        self._comm_ws = None
        self._comm_ws_reverse = None
        if logger:
            self.logger = logger
        else:
            self.logger = logging.Logger("libonebot")
            self.logger.setLevel(logging.INFO)
        self._action_bus = ActionBus()
        self._event_bus = EventBus()
        self.configure(config)

    def _register_http(self, host: str, port: int) -> None:
        """
        注册HTTP通信
        :return:
        """
        self._comm_http = CommHTTP(self.logger, host, port)
        self._comm_http.register_action_handler(self._action_bus)

    def _register_http_webhook(self, host: str) -> None:
        self._comm_http_webhook = CommHTTPWebHook(self.logger, host)
        self._event_bus.subscribe(self._comm_http_webhook.push_event)

    def _register_websocket(self, host: str, port: int) -> None:
        """
        注册WebSocket通信
        :return:
        """
        self._comm_ws = CommWS(self.logger, host, port)
        self._comm_ws.register_action_handler(self._action_bus)
        self._event_bus.subscribe(self._comm_ws.push_event)

    def _register_websocket_reverse(self, host: str, port: int, reconnect: int) -> None:
        self._comm_ws_reverse = CommWSReverse(self.logger, host, port, reconnect)
        self._comm_ws_reverse.register_action_handler(self._action_bus)
        self._event_bus.subscribe(self._comm_ws_reverse.push_event)

    def configure(self, config: Dict) -> None:
        try:
            if "http" in config.keys() and config["http"]["enable"]:
                if not self._comm_http:
                    self._register_http(config["http"]["host"], config["http"]["port"])
            if "http_webhook" in config.keys() and config["http_webhook"]["enable"]:
                if not self._comm_http_webhook:
                    self._register_http_webhook(config["http_webhook"]["host"])
            if "ws" in config.keys() and config["ws"]["enable"]:
                if not self._comm_ws:
                    self._register_websocket(config["ws"]["host"], config["ws"]["port"])
            if "ws_reverse" in config.keys() and config["ws_reverse"]["enable"]:
                if not self._comm_ws_reverse:
                    self._register_websocket_reverse(
                        config["ws_reverse"]["host"],
                        config["ws_reverse"]["port"],
                        config["ws_reverse"]["reconnect_interval"],
                    )
        except KeyError as e:
            raise ConfigError("Invalid Config: ", e)

    def on_action(
        self, action: str, platform: Optional[str] = ""
    ) -> Callable[[Callable], Any]:
        def api_deco(func: Callable) -> Callable:
            async def inner(*args, **kwargs):
                return await func(*args, **kwargs)

            if platform:
                self.register_extended_action(
                    platform=platform, action=action, func=inner
                )
            else:
                self.register_action(action=action, func=inner)

            return inner

        return api_deco

    def register_action(self, action: str, func: Callable):
        self._action_bus.subscribe(action, func)

    def register_extended_action(self, action: str, platform: str, func: Callable):
        action_name = f"{platform}_{action}"
        self._action_bus.subscribe(action_name, func)

    async def push_event(self, **event_data) -> None:
        await self._event_bus.emit(**event_data)

    async def push_extended_event(self, platform: str, event_data) -> None:
        if "sub_type" in event_data:
            sub_type = event_data["sub_type"]
            if not sub_type.startswith(platform):
                sub_type = f"{platform}_{sub_type}"
            event_data["sub_type"] = sub_type
        await self.push_event(**event_data)

    async def run(self):
        communication = []
        if self._comm_http:
            communication.append(self._comm_http.run())
        if self._comm_http_webhook:
            communication.append(self._comm_http_webhook.run())
        if self._comm_ws:
            communication.append(self._comm_ws.run())
        if self._comm_ws_reverse:
            communication.append(self._comm_ws_reverse.run())
        await asyncio.gather(*communication)
