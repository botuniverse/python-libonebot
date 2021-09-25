"""

"""


class OneBotError(Exception):
    """Base class for OneBot Exceptions"""


class ConfigError(OneBotError):
    pass


class ActionError(OneBotError):
    pass


class ActionRequestError(ActionError):
    pass


class ActionHandleError(ActionError):
    pass
