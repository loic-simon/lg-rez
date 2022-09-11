"""lg-rez / blocs / Console d'administration (avancé)

Permet de contrôler le bot depuis la console le faisant tourner.

"""

import os
import sys
import asyncio

import aioconsole
import asyncode
import discord

from lgrez import config


class CaptureLogs:
    """Context manager: capture messages posted to :attr:`.config.Channel.logs`.

    Only capture messages posted by the bot itself: these messages
    are not sent at all to Discord.
    """

    def __init__(self) -> None:
        """Initialize self."""
        self._chan = config.Channel.logs
        self._calls = []

        async def _cor(text: str, *args, **kwargs):
            self._calls.append(text)

        class _ProxyChannel(discord.TextChannel):
            def __init__(self) -> None:
                # We inherit TextChannel for type checks, but we
                # do NOT want to create a new TextChannel object
                pass

            def __getattribute__(slf, attr):
                if attr == "send":
                    return _cor
                return getattr(self._chan, attr)

        self.proxy = _ProxyChannel()

    def __enter__(self):
        """Enter the context: start capturing."""
        config.Channel.logs = self.proxy
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context: stop capturing."""
        config.Channel.logs = self._chan

    @property
    def text(self) -> str:
        """The messages sent in the channel, joined with newlines."""
        return "\n".join(self._calls)


class AdminConsole(asyncode.AsyncInteractiveConsole):
    """Python console to control LGBot from the running shell.

    (subclass of :class:`asyncode.AsyncInteractiveConsole`)

    Args:
        locals, filename: see :class:`asyncode.AsyncInteractiveConsole`.
    """

    def __init__(
        self,
        locals: dict = {},
        filename: str = "__console__",
    ) -> None:
        """Initialize self"""
        locals["_console"] = self
        super().__init__(locals, filename)

    async def interact(
        self,
        banner: str | None = None,
        exitmsg: str | None = "Byebye!",
    ) -> None:
        """Launches the console.

        (see :meth:`asyncode.AsyncInteractiveConsole.interact`)
        """
        await aioconsole.aprint("\nLaunching interactive console...")

        if banner is None:
            base = (
                'Type "help", "copyright", "credits" or "license" for '
                'more information.\nasync REPL: use "await" directly '
                "instead of asyncio.run()."
            )
            warn = "WARNING: Sending KeyboardInterrupt (^C) will stop the whole LGBot."
            banner = f"Python {sys.version} on {sys.platform}\n{base}\n{warn}"

        await super().interact(banner, exitmsg)

    async def write(self, data: str) -> None:
        """Method called on each print / repr / traceback...

        Relies on :meth:`aioconsole.aprint`.

        Args:
            data: text to display.
        """
        if not hasattr(sys, "ps1"):
            sys.ps1 = ">>> "
        if not hasattr(sys, "ps2"):
            sys.ps2 = "... "

        await aioconsole.aprint(data, end="")

    async def raw_input(self, prompt: str = "") -> str:
        """Method called when the console waits for next instruction.

        Relies on :meth:`aioconsole.ainput`.

        Args:
            prompt: optional text to send before waiting for input.

        Returns:
            The new instruction to compute.
        """
        if prompt:
            await self.write(prompt)

        return await aioconsole.ainput()


async def run_admin_console(locals: dict) -> None:
    """Launch the Admin console and restart it if crashing.

    Args:
        locals: the objects accessible from the console.
    """
    if os.isatty(sys.stdin.fileno()):  # Lancement depuis un terminal
        await asyncio.sleep(2)
        cons = AdminConsole(locals=locals)
        await cons.interact()
        await aioconsole.aprint("Admin console closed (bot still runs).")


async def execute_command(entree: str) -> str:
    """Execute a command.

    Create a fake message in the #logs channel by the server owner,
    and process it while capturing the output in the channel.

    Args:
        entree: The command to execute (must begin with the
            command prefix)

    Returns:
        The messages get in response to the command execution,
        joined with newlines.
    """
    message = (await config.Channel.logs.history(limit=1).flatten())[0]
    # On a besoin de récupérer un message, ici le dernier de #logs
    message.author = config.guild.owner
    message.content = entree
    ctx = await config.bot.get_context(message)

    _calls = []

    async def _cor(text, *args, **kwargs):
        _calls.append(text)

    ctx.send = _cor
    ctx.reply = _cor

    with CaptureLogs() as cc:
        await config.bot.invoke(ctx)

    text = "\n".join(_calls)
    if cc.text:
        text += f"\n[LOGGED] > {cc.text}"
    text = text.replace('"""', '\\"\\"\\"')
    return f'print("""{text}""")'
