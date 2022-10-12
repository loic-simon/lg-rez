"""lg-rez / LGBot

Commandes"""

import traceback
import types
import typing

import discord
from discord import app_commands
import inspect
import readycheck

from lgrez import config, bdd
from lgrez.blocs import tools
from lgrez.blocs.journey import DiscordJourney
from lgrez.commons import UserInputError, CommandAbortedError
from lgrez.features import (
    actions_publiques,
    annexe,
    chans,
    communication,
    gestion_ia,
    informations,
    open_close,
    special,
    sync,
    taches,
    voter_agir,
)

if typing.TYPE_CHECKING:
    from lgrez.bot import LGBot


def _showexc(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


class LGCommandTree(app_commands.CommandTree):
    def __init__(self, client: "LGBot", guild_id: int) -> None:
        super().__init__(client)
        self.guild = discord.Object(id=guild_id)
        self.enabled_commands: dict[str, app_commands.Command | app_commands.Group] = {}
        self.enabled_commands_and_subcommands: dict[str, app_commands.Command] = {}
        self.disabled_commands: dict[str, app_commands.Command | app_commands.Group] = {}

    def register_commands(self) -> None:
        # Commandes joueur : information, actions privés et publiques
        self._add_module_commands(informations)
        self._add_module_commands(voter_agir)
        self._add_module_commands(actions_publiques)
        # # Commandes MJs : gestion votes/actions, synchro GSheets, planifications, posts et embeds...
        self._add_module_commands(open_close)
        self._add_module_commands(sync)
        self._add_module_commands(taches)
        self._add_module_commands(communication)
        # # Commandes mixtes : comportement de l'IA et trucs divers
        self._add_module_commands(gestion_ia)
        self._add_module_commands(annexe)
        self._add_module_commands(chans)
        # # Commandes spéciales, méta-commandes...
        self._add_module_commands(special)

        # Commandes désactivées de base (activées par /open vote)
        self.disable_command("vote")
        self.disable_command("votemaire")
        self.disable_command("voteloups")
        self.disable_command("haro")
        self.disable_command("candid")

    def _add_module_commands(self, module: types.ModuleType) -> None:
        for name, value in inspect.getmembers(module):
            if isinstance(value, (app_commands.Command, app_commands.Group)):
                if value.parent:  # Sous-commande
                    self.enabled_commands_and_subcommands[value.qualified_name] = value
                else:
                    self.add_command(value, guild=self.guild)
                    self.enabled_commands[value.qualified_name] = value
            if isinstance(value, app_commands.ContextMenu):
                self.add_command(value, guild=self.guild)

    def enable_command(self, name: str) -> bool:
        if name in self.enabled_commands:
            return False
        if name in self.disabled_commands:
            command = self.disabled_commands.pop(name)
            self.add_command(command, guild=self.guild)
            self.enabled_commands[name] = command
            if isinstance(command, app_commands.Group):
                for subcommand in command.walk_commands():
                    self.enabled_commands_and_subcommands[subcommand.qualified_name] = subcommand
            return True
        else:
            raise LookupError(f"Commande non déclarée : {name}")

    def disable_command(self, name: str) -> bool:
        if name in self.disabled_commands:
            return False
        if name in self.enabled_commands:
            command = self.enabled_commands.pop(name)
            self.remove_command(name, guild=self.guild)
            self.disabled_commands[name] = command
            if isinstance(command, app_commands.Group):
                for subcommand in command.walk_commands():
                    self.enabled_commands_and_subcommands.pop(subcommand.qualified_name, None)
            return True
        else:
            raise LookupError(f"Commande non déclarée : {name}")

    def get_command_by_name(self, name: str) -> app_commands.Command | None:
        return self.enabled_commands_and_subcommands.get(name)

    async def on_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        """Méthode appelée par Discord à un exception dans une commande.

        Analyse l'erreur survenue et informe le joueur de manière
        adéquate en fonction, en mentionnant les MJs si besoin.

        Args:
            interaction: Interaction ayant causé l'exception
            error: Exception levée
        """
        message = "Strange Exception"

        running_interaction = DiscordJourney.RUNNING_INTERACTION or interaction
        DiscordJourney.RUNNING_INTERACTION = None

        match error:
            case CommandAbortedError():
                return  # Already handled (button change)

            case app_commands.CommandInvokeError():
                if isinstance(error.original, (bdd.SQLAlchemyError, bdd.DriverOperationalError)):  # Erreur BDD
                    try:
                        config.session.rollback()  # On rollback la session
                        await tools.log("Rollback session")
                    except readycheck.NotReadyError:
                        pass

                # Dans tous les cas, si erreur à l'exécution
                command = interaction.command.name
                prefix = f":x: Oups ! Un problème est survenu à l'exécution de la commande `{command}` :grimacing: :"

                if not config.is_setup or (
                    isinstance(interaction.user, discord.Member) and interaction.user.top_role >= config.Role.mj
                ):
                    # MJ / webhook : affiche le traceback complet
                    tb = traceback.format_exception(type(error.original), error.original, error.original.__traceback__)
                    await tools.send_blocs(running_interaction, "".join(tb), code=True, prefix=prefix)
                    return
                else:
                    # Pas MJ : exception seulement
                    message = f"{prefix}\n{config.Role.mj.mention} ALED – " + tools.ital(_showexc(error.original))

            case app_commands.CommandNotFound():
                message = (
                    ":x: Hum, je ne connais pas cette commande  :thinking:\n"
                    f"Utilise {tools.code('!help')} pour voir la liste des commandes."
                )

            case app_commands.MissingRole() if error.missing_role == config.Role.get_raw("mj"):
                message = ":x: Hé ho toi, cette commande est réservée aux MJs !  :angry:"

            case app_commands.MissingRole() if error.missing_role == config.Role.get_raw("joueur_en_vie"):
                message = ":x: Désolé, cette commande est réservée aux joueurs en vie !"

            case app_commands.MissingAnyRole():
                message = (
                    ":x: Cette commande est réservée aux joueurs ! (parce qu'ils doivent être inscrits en base) "
                    f"({tools.code('/doas')} est là en cas de besoin)"
                )

            case UserInputError():
                # Autre check non vérifié
                message = f':x: Argument "{error.param}" invalide : {error.message}'

            case app_commands.CheckFailure():
                # Autre check non vérifié
                if interaction.response.is_done():  # Déjà géré
                    return
                message = (
                    ":x: Tiens, il semblerait que cette commande ne puisse pas être exécutée ! "
                    f"{tools.mention_MJ(interaction)} ?\n({tools.ital(_showexc(error))})"
                )

            case _:
                message = (
                    f":x: Oups ! Une erreur inattendue est survenue  :grimacing:\n"
                    f"{tools.mention_MJ(interaction)} ALED – {tools.ital(_showexc(error))}"
                )

        await tools.send_blocs(interaction, message)
