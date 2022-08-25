"""lg-rez / LGBot

Classe principale

"""

from __future__ import annotations

import asyncio
import enum
import logging
import sys
import time
import traceback
import typing

import discord
from discord.ext import commands
import readycheck

from lgrez import __version__, config, bdd
from lgrez.blocs import env, tools, one_command, console
from lgrez.features import (
    actions_publiques,
    annexe,
    chans,
    communication,
    IA,
    informations,
    inscription,
    open_close,
    special,
    sync,
    taches,
    voter_agir,
)


#: Description par défaut du bot
default_description: str = "LG-bot – Plateforme pour parties endiablées de Loup-Garou"


async def _check_and_prepare_objects(bot: LGBot) -> None:
    # Start admin console in the background
    asyncio.create_task(console.run_admin_console(globals()))

    if not config.is_setup:
        return

    async for entry in config.guild.audit_logs(
        oldest_first=True, user=config.bot.user, action=discord.AuditLogAction.guild_update
    ):
        if entry.reason == "Guild set up!":
            break
    else:
        config.is_setup = False
        # *really* needed objects, even if nothing is setup
        config.Channel.logs = config.guild.text_channels[0]
        await tools.log("Server not setup - call `!setup` !")
        return

    errors = []

    def prepare_attributes(
        rc_class: type[readycheck.ReadyCheck],
        discord_type: type,
        converter: typing.Callable[[str], typing.Any],
    ) -> None:
        """Rend prêt les attributs d'une classe ReadyCheck"""
        for attr in rc_class:
            raw = rc_class.get_raw(attr)
            # Si déjà prêt, on actualise quand même (reconnexion)
            name = raw.name if isinstance(raw, discord_type) else raw
            try:
                ready = converter(name)
            except ValueError:
                qualname = f"config.{rc_class.__name__}.{attr}"
                errors.append(f"{discord_type.__name__} {qualname} = " f'"{name}" non trouvé !')
            else:
                setattr(rc_class, attr, ready)

    prepare_attributes(config.Role, discord.Role, tools.role)
    prepare_attributes(config.Channel, discord.TextChannel, tools.channel)
    prepare_attributes(config.Emoji, discord.Emoji, tools.emoji)

    try:
        tools.channel(config.private_chan_category_name)
    except ValueError:
        errors.append(
            f"catégorie config.private_chan_category_name = " f'"{config.private_chan_category_name}" non trouvée'
        )

    try:
        tools.channel(config.boudoirs_category_name)
    except ValueError:
        errors.append(f"catégorie config.boudoirs_category_name = " f'"{config.boudoirs_category_name}" non trouvée')

    try:
        tools.channel(config.old_boudoirs_category_name)
    except ValueError:
        errors.append(
            f"catégorie config.old_boudoirs_category_name = " f'"{config.old_boudoirs_category_name}" non trouvée'
        )

    if len(errors) > config._missing_objects:
        # Nouvelles erreurs
        msg = f"LGBot.on_ready: {len(errors)} errors:\n - " + "\n - ".join(errors)
        logging.error(msg)

        try:
            atmj = config.Role.mj.mention
        except readycheck.NotReadyError:
            atmj = "@everyone"

        try:
            await tools.log(msg, code=True, prefixe=f"{atmj} ERREURS :")
        except readycheck.NotReadyError:
            config.Channel.logs = config.guild.text_channels[0]
            msg += "\n-- Routing logs to this channel."
            await tools.log(msg, code=True, prefixe=f"{atmj} ERREURS :")

    elif len(errors) < config._missing_objects:
        if errors:
            # Erreurs résolues, il en reste
            msg = f"{len(errors)} errors:\n - " + "\n - ".join(errors)
            logging.error(msg)
            await tools.log(msg, code=True, prefixe=f"Erreurs restantes :")
        else:
            # Toutes erreurs résolues
            await tools.log("Configuration rôles/chans/emojis OK.")

    config._missing_objects = len(errors)

    # Webhook
    existing = await config.Channel.logs.webhooks()

    if existing:
        config.webhook = existing[0]
    else:  # Création du webhook
        config.webhook = await config.Channel.logs.create_webhook(
            name=bot.user.name, avatar=await bot.user.avatar_url.read()
        )
        await tools.log(f"Webhook de tâches planifiées créé")


def _showexc(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


class CommandErrorType(enum.Enum):
    STOP: enum.auto()
    COMMAND_INVOKE_ERROR: enum.auto()
    COMMAND_NOT_FOUND: enum.auto()
    COMMAND_DISABLED: enum.auto()
    BAD_USAGE: enum.auto()
    MJS_ONLY: enum.auto()
    JOUEURS_ONLY: enum.auto()
    VIVANTS_ONLY: enum.auto()
    ALREADY_IN_COMMAND: enum.auto()
    OTHER_CHECK_FAILED: enum.auto()
    OTHER: enum.auto()


# ---- Définition classe principale


class LGBot(commands.Bot):
    """Bot communautaire pour parties de Loup-Garou à la PCéenne.

    Classe fille de :class:`discord.ext.commands.Bot`, implémentant les
    commandes et fonctionnalités du Loup-Garou de la Rez.

    Args:
        command_prefix: passé à :class:`discord.ext.commands.Bot`
        case_insensitive: passé à :class:`discord.ext.commands.Bot`
        description: idem, défaut \: :attr:`lgrez.bot.default_description`
        \*\*kwargs: autres options de :class:`~discord.ext.commands.Bot`

    Warning:
        LG-Bot n'est **pas** thread-safe : seule une instance du bot
        peut tourner en parallèle dans un interpréteur.

        (Ceci est du aux objets de :mod:`.config`, contenant directement
        le bot, le serveur Discord, la session de connexion BDD... ;
        cette limitation résulte d'une orientation volontaire du module
        depuis sa version 2.0 pour simplifier et optimiser la
        manipulation des objects et fonctions).

    Attributes:
        GUILD_ID (int): L'ID du serveur sur lequel tourne le bot
            (normalement toujours :attr:`config.guild` ``.id``).
            Vaut ``None`` avant l'appel à :meth:`run`, puis la valeur
            de la variable d'environnement ``LGREZ_SERVER_ID``.
        in_command (list[int]): IDs des salons dans lesquels une
            commande est en cours d'exécution.
        in_stfu (list[int]): IDs des salons en mode STFU.
        in_fals (list[int]): IDs des salons en mode Foire à la saucisse.
        tasks (dict[int (.bdd.Tache.id), asyncio.TimerHandle]):
            Tâches planifiées actuellement en attente. Privilégier
            plutôt l'emploi de :attr:`.bdd.Tache.handler`.

    """

    def __init__(self, command_prefix: str = "!", case_insensitive: bool = True, description: str = None, **kwargs):
        """Initialize self"""
        # Paramètres par défaut
        if description is None:
            description = default_description

        # Construction du bot Discord
        super().__init__(
            command_prefix=command_prefix, description=description, case_insensitive=case_insensitive, **kwargs
        )

        # Définition attributs personnalisés
        self.GUILD_ID = None
        self.in_stfu = []
        self.in_fals = []
        self.tasks = {}

        # Système de limitation à une commande à la fois
        self.in_command = []
        self.add_check(one_command.not_in_command)
        self.before_invoke(one_command.add_to_in_command)
        self.after_invoke(one_command.remove_from_in_command)

        # Commandes joueur : information, actions privés et publiques
        self.add_cog(informations.Informations(self))
        self.add_cog(voter_agir.VoterAgir(self))
        self.add_cog(actions_publiques.ActionsPubliques(self))
        # Commandes MJs : gestion votes/actions, synchro GSheets,
        # planifications, posts et embeds...
        self.add_cog(open_close.OpenClose(self))
        self.add_cog(sync.Sync(self))
        self.add_cog(taches.GestionTaches(self))
        self.add_cog(communication.Communication(self))
        # Commandes mixtes : comportement de l'IA et trucs divers
        self.add_cog(IA.GestionIA(self))
        self.add_cog(annexe.Annexe(self))
        self.add_cog(chans.GestionChans(self))
        # Commandes spéciales, méta-commandes...
        self.remove_command("help")
        self.add_cog(special.Special(self))

    # Réactions aux différents évènements
    async def on_ready(self) -> None:
        """Méthode appelée par Discord au démarrage du bot.

        Vérifie le serveur (appelle :meth:`check_and_prepare_objects`),
        log et affiche publiquement que le bot est fonctionnel
        (activité) ;  restaure les tâches planifiées éventuelles
        et exécute celles manquées.

        Si :attr:`config.output_liveness` vaut ``True``, lance
        :attr:`bot.i_am_alive <.LGBot.i_am_alive>`
        (écriture chaque minute sur un fichier disque)
        """
        print("[3/3] Initialization (bot.on_ready)...")

        if config.is_ready:
            await tools.log("[`on_ready` called but bot already ready, ignored]")
            # On remet l'activité, qui peut sauter sinon
            await self.set_presence()
            return

        config.loop = self.loop  # Enregistrement loop

        guild = self.get_guild(self.GUILD_ID)
        if not guild:
            raise RuntimeError(f"on_ready : Serveur d'ID {self.GUILD_ID} (``LGREZ_SERVER_ID``) introuvable")

        print(f"      Connected to '{guild.name}'! " f"({len(guild.channels)} channels, {len(guild.members)} members)")

        # Start liveness regular output
        if config.output_liveness:
            self.i_am_alive()

        # Préparations des objects globaux
        config.guild = guild
        await self.check_and_prepare_objects()

        await tools.log("Just rebooted!")
        await self.set_presence()

        # Tâches planifiées
        taches = bdd.Tache.query.all()
        for tache in taches:
            # Si action manquée, l'exécute immédiatement, sinon l'enregistre
            tache.register()

        if taches:
            await tools.log(f"{len(taches)} tâches planifiées récupérées en base et reprogrammées.")

        config.is_ready = True
        print("      Initialization complete.")
        print("\nListening for events.")

    async def set_presence(self):
        return await self.change_presence(
            activity=discord.Activity(type=discord.ActivityType.listening, name="vos demandes (!help)")
        )

    async def on_member_join(self, member: discord.Member) -> None:
        """Méthode appelée par Discord à l'arrivée d'un nouveau membre.

        Log et lance le processus d'inscription.

        Args:
            member: Le membre qui vient d'arriver.
        """
        await tools.log(f"Arrivée de {member.name}#{member.discriminator} sur le serveur")
        await inscription.main(member)

    async def on_member_remove(self, member: discord.Member) -> None:
        """Méthode appelée par Discord au départ d'un membre du serveur.

        Log en mentionnant les MJs.

        Args:
            member: Le joueur qui vient de partir.
        """
        await tools.log(
            f"{tools.mention_MJ(member)} ALERTE : départ du serveur de "
            f"{member.display_name} ({member.name}#{member.discriminator}) !"
        )

    async def on_guild_message(self, message: discord.Message) -> None:
        """Méthode appelée par Discord à chaque message sur le serveur.

        Invoque l'ensemble des commandes, ou les règles d'IA si
            - Le message n'est pas une commande
            - Le message est posté dans un channel privé (dont le nom
              commence par :attr:`config.private_chan_prefix`)
            - Il n'y a pas déjà de commande en cours dans ce channel
            - Le channel n'est pas en mode STFU

        Ne fait rien si le message est envoyé par le bot lui-même
        ou par un membre sans aucun rôle affecté.

        Args:
            message: Le message qui vient d'être posté.
        """
        if message.author == self.user:  # Pas de boucles infinies
            return

        if (
            config.is_setup
            and not message.webhook_id  # Pas un webhook
            and message.author.top_role == config.Role.everyone
        ):
            # Pas de rôle affecté : le bot te calcule même pas
            return

        if message.content.startswith(self.command_prefix + " "):
            message.content = self.command_prefix + message.content[2:]

        # On trigger toutes les commandes
        # (ne PAS remplacer par bot.process_commands(message), en théorie
        # c'est la même chose mais ça détecte pas les webhooks...)
        ctx = await self.get_context(message)
        await self.invoke(ctx)

        if (
            not message.content.startswith(self.command_prefix)
            and message.channel.name.startswith(config.private_chan_prefix)
            and message.channel.id not in self.in_command
            and message.channel.id not in self.in_stfu
        ):
            # Conditions d'IA respectées (voir doc) : on trigger
            await IA.process_IA(message)

    async def on_private_message(self, message: discord.Message) -> None:
        """Méthode appelée par Discord à la réception d'un message privé.

        Répond gentiment que ça ne sert à rien.

        Args:
            message: Le message qui vient d'être posté.
        """
        await message.channel.send("Je n'accepte pas les messages privés, désolé !")

    async def on_reaction_add(
        self,
        emoji: discord.Emoji,
        reactor: discord.Member,
        channel: discord.TextChannel | None,
    ) -> None:
        """Méthode appelée à l'ajout d'une réaction.

        Appelle la fonction adéquate si le membre est un joueur
        inscrit, est sur un chan de conversation bot et a cliqué sur
        :attr:`config.Emoji.bucher`, :attr:`~config.Emoji.maire`,
        :attr:`~config.Emoji.lune` ou :attr:`~config.Emoji.action`.

        Args:
            emoji: L'emoji ajouté.
            reactor: Le membre qui a réagi.
            guild_id: L'ID du serveur où la réaction a eu lieu.
            channel_id: L'ID du salon où la réaction a eu lieu.
        """
        if not channel or not channel.name.startswith(config.private_chan_prefix):
            # Pas dans un chan privé
            return

        if config.Role.joueur_en_vie not in reactor.roles:
            # Pas un joueur en vie
            return

        if emoji == config.Emoji.bucher:
            ctx = await tools.create_context(reactor, "!vote")
            await ctx.send(f"{emoji} > " + tools.bold("Vote pour le condamné du jour :"))
            await self.invoke(ctx)  # On trigger !vote

        elif emoji == config.Emoji.maire:
            ctx = await tools.create_context(reactor, "!votemaire")
            await ctx.send(f"{emoji} > " + tools.bold("Vote pour le nouveau maire :"))
            await self.invoke(ctx)  # On trigger !votemaire

        elif emoji == config.Emoji.lune:
            ctx = await tools.create_context(reactor, "!voteloups")
            await ctx.send(f"{emoji} > " + tools.bold("Vote pour la victime des loups :"))
            await self.invoke(ctx)  # On trigger !voteloups

        elif emoji == config.Emoji.action:
            ctx = await tools.create_context(reactor, "!action")
            await ctx.send(f"{emoji} > " + tools.bold("Action :"))
            await self.invoke(ctx)  # On trigger !action

    # Gestion des erreurs
    async def on_command_error(
        self,
        ctx: discord.Context,
        exc: Exception,
    ) -> None:
        """Méthode appelée par Discord à un exception dans une commande.

        Analyse l'erreur survenue et informe le joueur de manière
        adéquate en fonction, en mentionnant les MJs si besoin.

        Args:
            ctx: Contexte dans lequel
                l'exception a été levée
            exc (.discord.CommandError): Exception levée
        """
        match self.get_error_type(exc):
            case CommandErrorType.STOP:
                await ctx.send(str(exc.original) or "Mission aborted.")
                return

            case CommandErrorType.COMMAND_INVOKE_ERROR:
                if isinstance(exc.original, (bdd.SQLAlchemyError, bdd.DriverOperationalError)):  # Erreur BDD
                    try:
                        config.session.rollback()  # On rollback la session
                        await tools.log("Rollback session")
                    except readycheck.NotReadyError:
                        pass

                # Dans tous les cas, si erreur à l'exécution
                prefixe = "Oups ! Un problème est survenu à l'exécution de la commande  :grimacing: :"

                if not config.is_setup or ctx.message.webhook_id or ctx.author.top_role == config.Role.mj:
                    # MJ / webhook : affiche le traceback complet
                    e = traceback.format_exception(type(exc.original), exc.original, exc.original.__traceback__)
                    await tools.send_code_blocs(ctx, "".join(e), prefixe=prefixe)
                else:
                    # Pas MJ : exception seulement
                    await ctx.send(f"{prefixe}\n{tools.mention_MJ(ctx)} ALED – " + tools.ital(_showexc(exc.original)))

            case CommandErrorType.COMMAND_NOT_FOUND:
                await ctx.send(
                    f"Hum, je ne connais pas cette commande  :thinking:\n"
                    f"Utilise {tools.code('!help')} pour voir la liste des commandes."
                )

            case CommandErrorType.COMMAND_DISABLED:
                await ctx.send("Cette commande est désactivée. Pas de chance !")

            case CommandErrorType.BAD_USAGE:
                c = (ctx.invoked_parents or [ctx.invoked_with])[0]
                await ctx.send(
                    f"Hmm, ce n'est pas comme ça qu'on utilise cette commande ! "
                    f"({tools.code(_showexc(exc))})\n*Tape "
                    f"`!help {c}` pour plus d'informations.*"
                )

            case CommandErrorType.MJS_ONLY:
                await ctx.send("Hé ho toi, cette commande est réservée aux MJs !  :angry:")

            case CommandErrorType.JOUEURS_ONLY:
                await ctx.send(
                    "Cette commande est réservée aux joueurs ! "
                    "(parce qu'ils doivent être inscrits en base, toussa) "
                    f"({tools.code('!doas')} est là en cas de besoin)"
                )

            case CommandErrorType.VIVANTS_ONLY:
                await ctx.send("Désolé, cette commande est réservée aux joueurs en vie !")

            case CommandErrorType.ALREADY_IN_COMMAND:
                if ctx.command.name in ["addIA", "modifIA"]:
                    # addIA / modifIA : droit d'enregistrer les commandes, donc chut
                    return
                await ctx.send(
                    f"Impossible d'utiliser une commande pendant "
                    "un processus ! (vote...)\n"
                    f"Envoie {tools.code(config.stop_keywords[0])} "
                    "pour arrêter le processus."
                )

            case CommandErrorType.OTHER_CHECK_FAILED:
                # Autre check non vérifié
                await ctx.send(
                    f"Tiens, il semblerait que cette commande ne puisse "
                    f"pas être exécutée ! {tools.mention_MJ(ctx)} ?\n"
                    f"({tools.ital(_showexc(exc))})"
                )

            case CommandErrorType.OTHER | _:
                await ctx.send(
                    f"Oups ! Une erreur inattendue est survenue  :grimacing:\n"
                    f"{tools.mention_MJ(ctx)} ALED – {tools.ital(_showexc(exc))}"
                )

    def get_error_type(self, exc: Exception) -> CommandErrorType:
        if isinstance(exc, commands.CommandInvokeError):
            if isinstance(exc.original, tools.CommandExit):  # STOP envoyé
                return CommandErrorType.STOP

            return CommandErrorType.COMMAND_INVOKE_ERROR

        elif isinstance(exc, commands.CommandNotFound):
            return CommandErrorType.COMMAND_NOT_FOUND

        elif isinstance(exc, commands.DisabledCommand):
            return CommandErrorType.COMMAND_DISABLED

        elif isinstance(exc, (commands.ConversionError, commands.UserInputError)):
            return CommandErrorType.BAD_USAGE

        elif isinstance(exc, commands.CheckAnyFailure):
            return CommandErrorType.MJS_ONLY

        elif isinstance(exc, commands.MissingAnyRole):
            return CommandErrorType.JOUEURS_ONLY

        elif isinstance(exc, commands.MissingRole):
            return CommandErrorType.VIVANTS_ONLY

        elif isinstance(exc, one_command.AlreadyInCommand):
            return CommandErrorType.ALREADY_IN_COMMAND

        elif isinstance(exc, commands.CheckFailure):
            return CommandErrorType.OTHER_CHECK_FAILED

        return CommandErrorType.OTHER

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Méthode appelée par Discord à une exception hors commande.

        Log en mentionnant les MJs. Cette méthode permet de gérer les
        exceptions sans briser la loop du bot (i.e. il reste en ligne).

        Args:
            event: Nom de l'évènement ayant généré une erreur
                (``"member_join"``, ``"message"``...)
            *args, \**kwargs: Arguments passés à la fonction traitant
                l'évènement : ``member``, ``message``...
        """
        etype, exc, tb = sys.exc_info()  # Exception ayant causé l'appel

        if isinstance(exc, (bdd.SQLAlchemyError, bdd.DriverOperationalError)):  # Erreur SQL
            try:
                config.session.rollback()  # On rollback la session
                await tools.log("Rollback session")
            except readycheck.NotReadyError:
                pass

        await tools.log(
            traceback.format_exc(), code=True, prefixe=f"{config.Role.mj.mention} ALED : Exception Python !"
        )

        # On remonte l'exception à Python (pour log, ne casse pas la loop)
        raise

    async def on_guild_update(self, always: bool = False) -> None:
        """Méthode appelée lors de la modification du serveur.

        Ex : création/modification/suppression d'un chan, d'un emoji...
        Vérifie que cette modification n'impacte pas le bon fonctionnement
            du jeu.

        Args:
            always: Si ``True``, force une re-vérification de tous les
                objets (suppression) ; sinon, ne revérifie que si un
                objet était manquant, pour corriger l'information.
        """
        if always or config._missing_objects:
            await self.check_and_prepare_objects()

    # Checks en temps réels des modifs des objets nécessaires au bot
    async def check_and_prepare_objects(self):
        """Vérifie et prépare les objets Discord nécessaires au bot.

        Remplit :class:`.config.Role`, :class:`.config.Channel`,
        :class:`.config.Emoji`, :attr:`config.private_chan_category_name`,
        :attr:`config.boudoirs_category_name` et :attr:`config.webhook`
        avec les objets Discord correspondants, et avertit les MJs en cas
        d'éléments manquants.
        """
        await _check_and_prepare_objects(self)

    # Système de vérification de vie
    def i_am_alive(self, filename: str = "alive.log") -> None:
        """Témoigne que le bot est en vie et non bloqué.

        Exporte le temps actuel (UTC) et planifie un nouvel appel
        dans 60s. Ce processus n'est lancé que si
        :attr:`config.output_liveness` est mis à ``True`` (*opt-in*).

        Args:
            filename: fichier où exporter le temps actuel
                (écrase le contenu).
        """
        with open(filename, "w") as f:
            f.write(str(time.time()))
        self.loop.call_later(60, self.i_am_alive, filename)

    # Lancement du bot
    def run(self, **kwargs) -> None:
        """Prépare puis lance le bot (bloquant).

        Récupère les informations de connexion, établit la connexion
        à la base de données puis lance le bot.

        Args:
            \**kwargs: Passés à :meth:`discord.ext.commands.Bot.run`.
        """
        print(f"--- LGBot v{__version__} ---")
        print(f"  * Front : discord.py v{discord.__version__}")

        # Récupération du token du bot et de l'ID du serveur
        LGREZ_DISCORD_TOKEN = env.load("LGREZ_DISCORD_TOKEN")
        self.GUILD_ID = int(env.load("LGREZ_SERVER_ID"))

        # Connexion BDD
        print("[1/3] Connecting to database...")
        bdd.connect()
        url = config.engine.url
        print(f"      Connected to {url.host}/{url.database}!")

        # Enregistrement
        config.bot = self

        # Lancement du bot (bloquant)
        print("[2/3] Connecting to Discord...")
        super().run(LGREZ_DISCORD_TOKEN, **kwargs)

        print("\nDisconnected.")
