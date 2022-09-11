from discord import app_commands


class UserInputError(app_commands.AppCommandError):
    def __init__(self, param: str, message: str, *args: object) -> None:
        self.param = param
        self.message = message
        super().__init__(*args)


class CommandAbortedError(app_commands.AppCommandError):
    def __init__(self, msg: str | None = None) -> None:
        super().__init__(msg or "Mission aborted.")
