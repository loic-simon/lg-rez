"""lg-rez / blocs / Émulation de terminal Python (avancé)

Ce module n'a pas grand chose à voir avec le projet dans son ensemble, et était plus une expérimentation personnelle qu'autre chose. Il est néanmoins implémenté par la commande :meth:`\!shell <.bot.Special.Special.shell.callback>`.

Globalement, il s'agit d'une version (très incomplète) du module :mod:`code` de Python, ajoutant un fonctionnement dans un environnement asynchrone. Il y aurait moyen de le réécrire beaucoup plus simplement (et beaucoup plus puissamment) en enveloppant le code à exécuter dans une fonction *async*, en l'envoyant dans un :class:`~code.InteractiveInterpreter` et en *awaitant* le résultat.

Par conséquent, ce module n'est pas considéré comme part de l'API publique ``lgrez`` et non documenté ici. Les plus curieux iront voir le code source !
"""

import re
import sys
import enum
import traceback
import asyncio

import asyncode

from lgrez.blocs import tools


def _py_bloc(data):
    return f"```py\n{data}```"


class RealShellExit(RuntimeError):
    pass

class RSCommand(enum.Enum):
    """Unicode emojis used for shell controll commands"""
    HOME = "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}"
    UNTAB = "\N{BLACK LEFT-POINTING DOUBLE TRIANGLE}"
    TAB = "\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE}"
    ENTER = "\N{LEFTWARDS ARROW WITH HOOK}"     # close to "enter" sign
    EOF = "\N{BLACK SQUARE FOR STOP}"


class RealShell(asyncode.AsyncInteractiveConsole):          # Les attributs de cette classe peuvent être modifiés via exec
    """Terminal Python"""

    def __init__(self, bot, channel, locals={}, filename="!shell"):
        """Initialize self"""
        self.bot = bot
        self.channel = channel

        self.message = None
        self.content = ""
        self.indent = 0
        self.rsbuffer = ""

        locals["_shell"] = self
        super().__init__(locals, filename)


    async def interact(self, banner=None, exitmsg="Byebye!"):
        self.message = await self.channel.send(_py_bloc("Launching Python shell...\n"))

        if banner is None:
            cprt = 'Type "help", "copyright", "credits" or "license" for more information.'
            aw = 'async REPL: use "await" directly instead of "asyncio.run()".\n'
            dsc = 'Discord implementation: the caret (‸) indicates the current position of the cursor.\nUse control reactions or send "<", ">", "=" to (un)indent it and send empty lines.'
            banner = f"Python {sys.version} on {sys.platform}\n{cprt}\n{aw}\n{dsc}\n"

        try:
            await super().interact(banner, exitmsg)
        except SystemExit as exc:
            await self.write(f"\n{exitmsg}", refresh=True, show_caret=False)
            raise RealShellExit(*exc.args)
        finally:
            await self.message.clear_reactions()



    async def control(self, command, N=1):
        """Applique l'effet demandé au clic sur un emoji de contrôle du shell"""
        if not isinstance(command, RSCommand):
            command = RSCommand(command)

        if command is RSCommand.HOME and self.indent > 0:       # Reset indentation
            self.indent = 0
            await self.write("", refresh=True)          # on actualise le message
        if command is RSCommand.UNTAB and self.indent > 0:      # Unindent
            self.indent -= max(N, self.indent)
            await self.write("", refresh=True)
        elif command is RSCommand.TAB:          # Indent
            self.indent += N
            await self.write("", refresh=True)
        elif command is RSCommand.ENTER:        # Newline
            return ""       # Send empty str (impossible through Discord)
        elif command is RSCommand.EOF:          # STOP
            raise RealShellExit("Arrêt du shell.")

        return None


    async def get_order(self):
        """Récupère une instruction (message ou contrôle) de l'utilisateur"""
        reacts = self.message.reactions     # Réactons déjà présentes
        if not reacts:
            for command in RSCommand:       # On ajoute les emojis si pas déjà présents (nouveau message)
                await self.message.add_reaction(command.value)
        else:
            try:                                # Sinon, on regarde si un emoji est déjà cliqué
                react = next(r for r in reacts if r.count > 1)
            except StopIteration:                       # Pas le cas ==> on poursuit
                pass
            else:
                async for user in react.users():        # C'est le cas : on trouve l'utilisateur,
                    if user != self.bot.user:
                        await react.remove(user)            # On enlève la réaction,
                        break
                command = RSCommand(react.emoji.name)
                return (await self.control(command))             # Et on applique la commande

        def react_check(payload):       # Check REACT : bon message et pas react du bot
            return (payload.message_id == self.message.id and payload.user_id != self.bot.user.id)

        def message_check(mess):        # Check MESSAGE : bon channel et pas du bot
            return (mess.channel == self.channel and mess.author != self.bot.user)

        react_task = asyncio.create_task(self.bot.wait_for('raw_reaction_add', check=react_check), name="react")
        mess_task = asyncio.create_task(tools.wait_for_message(self.bot, check=message_check, trigger_on_commands=True))
        # On exécute les deux tâche concurremment
        done, pending = await asyncio.wait([react_task, mess_task], return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
        done_task = next(iter(done))        # done = tâche complétée

        if done_task.get_name() == "react":     # Clic sur emoji de contrôle
            payload = done_task.result()            # Si clic sur react, done.result = RawReactionActionEvent payload
            await self.message.remove_reaction(payload.emoji, payload.member)
            command = RSCommand(payload.emoji.name)
            return (await self.control(command))

        else:                                   # Réponse par message / STOP
            message = done_task.result()            # Si envoi de message, done.result = Message
            text = message.content
            await message.delete()

            if m := re.match("^<+", text):
                await self.control(RSCommand.UNTAB, N=m.end())
                text = text[m.end():]
            elif m := re.match("^>+", text):
                await self.control(RSCommand.TAB, N=m.end())
                text = text[m.end():]

            if text == "=":
                return (await self.control(RSCommand.ENTER))
            else:
                return (text or None)



    async def write(self, data, *, refresh=False, show_caret=True):
        """Fonction appellée par le shell à chaque print() / repr / traceback...

        N'affiche text que si il se termine par un prompt (sys.ps1 ou sys.ps2) ; l'ajoute à un buffer interne dans le cas contraire.
        Si refresh vaut True, actualise le message quelque soit text.
        """
        if refresh or data.endswith(sys.ps1) or data.endswith(sys.ps2):     # Prompt / refresh demandé
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
            insert = " "*(self.indent*4) + "‸"
        else:
            insert = ""

        # Actualisation message / nouvau si plein
        if len(self.content + data + insert) < 1990:
            self.content += data
            await self.message.edit(content=_py_bloc(self.content + insert))
        else:
            await self.message.clear_reactions()      # On enlève les commandes du message

            blocs = tools.smooth_split(data, N=1990)
            self.content = blocs[-1]                 # On modifie le texte actuel
            blocs[-1] += insert

            for bloc in blocs:
                message = await self.channel.send(_py_bloc(bloc))

            self.message = message        # On modifie le message actuel = dernier envoyé





    async def raw_input(self, prompt=""):
        """Fonction appellée par le shell à chaque input() / attente d'instruction"""
        if prompt:
            await self.write(prompt)

        entree = None
        while entree is None:
            entree = await self.get_order()      # Modifie l'indentation, stop ou récupère une ligne

        entree = " "*(self.indent*4) + entree
        await self.write(entree + "\n", refresh=True, show_caret=False)       # Affiche l'entrée
        return entree
