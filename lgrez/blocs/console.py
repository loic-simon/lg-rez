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


class CaptureLogs():
    """Context manager: capture the messages posted to a Discord channel.

    Only capture messages posted by the bot itself: these messages
    are not sent at all to Discord.

    Args:
        chan (discord.TextChannel): the channel to capture.
    """
    def __init__(self):
        """Initialize self."""
        self._chan = config.Channel.logs
        self._calls = []

        async def _cor(text, *args, **kwargs):
            self._calls.append(text)

        class _ProxyChannel(discord.TextChannel):
            def __init__(self):
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
    def text(self):
        """str: The messages sent in the channel, joined with newlines."""
        return "\n".join(self._calls)


class AdminConsole(asyncode.AsyncInteractiveConsole):
    """Python console to control LGBot from the running shell.

    (subclass of :class:`asyncode.AsyncInteractiveConsole`)

    Args:
        locals, filename: see :class:`asyncode.AsyncInteractiveConsole`.
    """
    def __init__(self, locals={}, filename="__console__"):
        """Initialize self"""
        locals["_console"] = self
        super().__init__(locals, filename)

    async def interact(self, banner=None, exitmsg="Byebye!"):
        """Launchs the console.

        (see :meth:`asyncode.AsyncInteractiveConsole.interact`)
        """
        await aioconsole.aprint("\nLaunching interactive console...")

        if banner is None:
            base = ('Type "help", "copyright", "credits" or "license" for '
                    'more information.\nasync REPL: use "await" directly '
                    'instead of asyncio.run().')
            warn = ('WARNING: Sending KeyboardInterrupt (^C) will stop '
                    'the whole LGBot.')
            banner = f"Python {sys.version} on {sys.platform}\n{base}\n{warn}"

        await super().interact(banner, exitmsg)

    async def write(self, data):
        """Method called on each print / repr / traceback...

        Relies on :meth:`aioconsole.aprint`.

        Args:
            data (str): text to display.
        """
        if not hasattr(sys, "ps1"):
            sys.ps1 = '>>> '
        if not hasattr(sys, "ps2"):
            sys.ps2 = '... '

        await aioconsole.aprint(data, end="")

    async def raw_input(self, prompt=""):
        """Method called when the console waits for next instruction.

        Relies on :meth:`aioconsole.ainput`.

        Args:
            prompt (str): optional text to send before waiting for
                input.

        Returns:
            :class:`str`: The new instruction to compute.
        """
        if prompt:
            await self.write(prompt)

        entree = await aioconsole.ainput()

        if entree.startswith(config.bot.command_prefix):
            # Exécution de commande
            entree = await execute_command(entree)

        return entree


async def run_admin_console(locals):
    """Launch the Admin console and restart it if crashing.

    Args:
        locals (dict): the objects accessible from the console.
    """
    if os.isatty(sys.stdin.fileno()):   # Lancement depuis un terminal
        await asyncio.sleep(1)
        cons = AdminConsole(locals=locals)
        await cons.interact()
        await aioconsole.aprint("Admin console closed (bot still runs).")


async def execute_command(entree):
    """Execute a command.

    Create a fake message in the #logs channel by the server owner,
    and process it while capturing the output in the channel.

    Args:
        entree (str): The command to execute (must begin with the
            command prefix)

    Returns:
        str: The messages get in response to the command execution,
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
