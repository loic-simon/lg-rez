"""lg-rez / blocs / Émulation de terminal Python (avancé)

Permet d'utiliser un terminal Python directement dans Discord
(implémentation de https://pypi.org/project/asyncode).

"""

import re
import sys
import enum
import asyncio

import asyncode

from lgrez import config
from lgrez.blocs import tools


def _py_bloc(data):
    return tools.code_bloc(data, "py")


class RealShellExit(RuntimeError):
    """Terminal exited (:exc:`SystemExit` catched or stop button).

    Derivates from :exc:`RuntimeError`.
    """
    pass


class RSCommand(enum.Enum):
    """:class:`~enum.Enum`: Shell controll commands.

    These commands allow to control the shell in ways impossible with
    plain Discord messages: change indentation (leading spaces in
    messages are stripped), send empty lines, send EOF (^D).

    Enum values are unicode emojis codepoints used for emoji control
    of the shell. Override this class (you may not define all values to
    disable some features) to change them.

    Emojis are displayed in the same order members are defined:

    Attributes:
        HOME: Reset indentation to 0.
        UNTAB: Decreases indentation by one level.
        TAB: Increases indentation by one level.
        ENTER: Send empty line.
        EOF: Send EOF signal (^D in \*nix, ^Z + Enter in Windows.)
    """
    HOME = "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}"
    UNTAB = "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}"
    TAB = "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}"
    ENTER = "\N{LEFTWARDS ARROW WITH HOOK}"     # close to "enter" sign
    EOF = "\N{BLACK SQUARE FOR STOP}"


class RealShell(asyncode.AsyncInteractiveConsole):
    """Python shell inside LGBot.

    (subclass of :class:`asyncode.AsyncInteractiveConsole`)

    Args:
        channel (discord.TextChannel): Chan in which run the shell
            (show and wait for commands). While the shell is running,
            every message in this channel will be interpreted and
            deleted by this shell.
        locals, filename: passed to
            :class:`asyncode.AsyncInteractiveConsole`.
    """
    def __init__(self, channel, locals={}, filename="!shell"):
        """Initialize self"""
        self.bot = config.bot
        self.channel = channel

        self.message = None
        self.content = ""
        self.indent = 0
        self.rsbuffer = ""

        locals["_shell"] = self
        super().__init__(locals, filename)

    async def interact(self, banner=None, exitmsg="Byebye!"):
        """Launchs the shell.

        (see :meth:`asyncode.AsyncInteractiveConsole.interact`)
        """
        wait = _py_bloc("Launching Python shell...\n")
        self.message = await self.channel.send(wait)

        if banner is None:
            base = ('Type "help", "copyright", "credits" or "license" for '
                    'more information.\nasync REPL: use "await" directly '
                    'instead of asyncio.run().\n')
            dsc = ('Discord implementation: the caret (‸) indicates the '
                   'current position of the cursor.\nUse control reactions or '
                   'send "<", ">", "=" to (un)indent it and send empty lines.')
            banner = f"Python {sys.version} on {sys.platform}\n{base}\n{dsc}\n"

        try:
            await super().interact(banner, exitmsg)
        except SystemExit as exc:
            await self.write(f"\n{exitmsg}", refresh=True, show_caret=False)
            raise RealShellExit(*exc.args)
        finally:
            await self.message.clear_reactions()

    async def control(self, command, times=1):
        """Applies the effect of a shell control.

        Args:
            command (.RSCommand): shell command to compute.
            times (int): repeat the command several times. Makes sense
                for :attr:`.RSCommand.TAB` and :attr:`.RSCommand.UNTAB`
                only.

        Returns:
            - ``None`` -- if further instructions are needed.
            - :class:`str` -- if instruction is complete (push this into
              the shell!)

        Raises:
            .RealShellExit: if asked to stop shell (EOF).
        """
        if not isinstance(command, RSCommand):
            command = RSCommand(command)

        if command is RSCommand.HOME:           # Reset indentation
            if self.indent > 0:
                self.indent = 0
                await self.write("", refresh=True)
        if command is RSCommand.UNTAB:          # Unindent
            if self.indent > 0:
                self.indent -= min(times, self.indent)
                await self.write("", refresh=True)
        elif command is RSCommand.TAB:          # Indent
            self.indent += times
            await self.write("", refresh=True)
        elif command is RSCommand.ENTER:        # Newline
            # Send empty str (impossible through Discord)
            return ""
        elif command is RSCommand.EOF:          # STOP
            raise RealShellExit("Arrêt du shell.")

        return None

    async def _check_reacts(self):
        """Preliminar step of self.get_order().

        Returns (True, <value to be returned>) if a react has been
        anticipated, else False.
        """
        reacts = self.message.reactions     # Réactons déjà présentes
        if not reacts:
            # On ajoute les emojis si pas déjà présents (nouveau message)
            for command in RSCommand:
                await self.message.add_reaction(command.value)
        else:
            # Sinon, on regarde si un emoji est déjà cliqué
            try:
                react = next(r for r in reacts if r.count > 1)
            except StopIteration:
                # Pas le cas ==> on poursuit
                pass
            else:
                # C'est le cas : on trouve l'utilisateur
                async for user in react.users():
                    if user != self.bot.user:
                        # On enlève la réaction
                        await react.remove(user)
                        break
                command = RSCommand(react.emoji.name)
                # Et on applique la commande
                control_ret = await self.control(command)
                return (True, control_ret)

        return False

    async def get_order(self):
        """Waits for an order (message or reaction) from a member.

        Add reactions if not present (new message) and waits for
        an interaction.

        Returns:
            - ``None`` -- if further instructions are needed.
            - :class:`str` -- if instruction is complete (push this into
              the shell!)

        Raises:
            .RealShellExit: if asked to stop shell (EOF).
        """
        res = await self._check_reacts()
        if res:         # Réaction anticipée, control effectué
            return res[1]

        def react_check(payload):
            # Check REACT : bon message et pas react du bot
            return (payload.message_id == self.message.id
                    and payload.user_id != self.bot.user.id)

        def message_check(mess):
            # Check MESSAGE : bon channel et pas du bot
            return (mess.channel == self.channel
                    and mess.author != self.bot.user)

        react_task = asyncio.create_task(self.bot.wait_for(
            'raw_reaction_add', check=react_check))
        mess_task = asyncio.create_task(tools.wait_for_message(
            check=message_check, trigger_on_commands=True))
        # On exécute les deux tâche concurremment
        done, pending = await asyncio.wait(
            {react_task, mess_task},
            return_when=asyncio.FIRST_COMPLETED
        )

        for task in pending:
            task.cancel()
        done_task = next(iter(done))        # done = tâche complétée

        if done_task == react_task:         # Clic sur emoji de contrôle
            payload = done_task.result()
            # On enlève la réaction
            await self.message.remove_reaction(payload.emoji, payload.member)
            command = RSCommand(payload.emoji.name)
            return (await self.control(command))

        else:                               # Réponse par message / STOP
            message = done_task.result()
            text = message.content
            await message.delete()

            if (match := re.match("^<+", text)):
                await self.control(RSCommand.UNTAB, times=match.end())
                text = text[match.end():]
            elif (match := re.match("^>+", text)):
                await self.control(RSCommand.TAB, times=match.end())
                text = text[match.end():]

            if text == "=":
                return (await self.control(RSCommand.ENTER))
            else:
                return (text or None)

    async def write(self, data, *, refresh=False, show_caret=True):
        """Method called on each print / repr / traceback...

        Updates Discord message only if text ends with a prompt
        (:attr:`sys.ps1` or :attr:`sys.ps2`); adds it to an internal
        buffer otherwise.

        Args:
            data (str): text to display.
            refresh (bool): if ``True``, updates message whatever
                ``data`` is.
            show_caret (bool): if ``False``, does not display the
                cursor position (‸); implies that the shell is not
                ready for further instructions.
        """
        if not hasattr(sys, "ps1"):
            sys.ps1 = '>>> '
        if not hasattr(sys, "ps2"):
            sys.ps2 = '... '

        if refresh or data.endswith(sys.ps1) or data.endswith(sys.ps2):
            # Prompt / refresh demandé
            data = self.rsbuffer + data       # On vide le buffer
            self.rsbuffer = ""
        else:
            self.rsbuffer += data             # On remplit le buffer
            return

        # Auto-indent à l'entrée dans un nouveau bloc
        if data.endswith(f":\n{sys.ps2}"):
            self.indent += 1

        # Ajout caret d'insertion pour indiquer la position du curseur
        if show_caret:
            insert = " " * (self.indent * 4) + "‸"
        else:
            insert = ""

        # Actualisation message / nouvau si plein
        if len(self.content + data + insert) < 1990:
            self.content += data
            await self.message.edit(content=_py_bloc(self.content + insert))
        else:
            # On enlève les commandes du message
            await self.message.clear_reactions()

            blocs = tools.smooth_split(data, N=1990)
            # On modifie le texte actuel
            self.content = blocs[-1]
            blocs[-1] += insert

            for bloc in blocs:
                message = await self.channel.send(_py_bloc(bloc))

            # On modifie le message actuel = dernier envoyé
            self.message = message

    async def raw_input(self, prompt=""):
        """Method called when the shell waits for next instruction.

        Calls :meth:`.get_order` until it returns a :class:`str` (or
        propagates :exc:`.RealShellExit`) then displays it in the shell
        (without caret) before returning its value.

        Args:
            prompt (str): optional text to send before waiting for
                input.

        Returns:
            :class:`str` -- new instruction to compute.
        """
        if prompt:
            await self.write(prompt, refresh=True)

        entree = None
        while entree is None:
            # Modifie l'indentation, stop ou récupère une ligne
            entree = await self.get_order()

        entree = " " * (self.indent * 4) + entree
        # Affiche l'entrée
        await self.write(entree + "\n", refresh=True, show_caret=False)
        return entree
