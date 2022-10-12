"""lg-rez / LGBot

Classe principale"""

from __future__ import annotations
import asyncio

import logging
import sys
import time
import traceback
import typing

import discord
import readycheck

from lgrez import __version__, commands, config, bdd
from lgrez.blocs import env, tools, console
from lgrez.features import gestion_ia, inscription


async def _check_and_prepare_objects(bot: LGBot) -> None:
    # Start admin console in the background
    asyncio.create_task(console.run_admin_console(globals()))

    if not config.is_setup:
        return

    if len(config.guild.channels) < 20:
        config.is_setup = False
        # *really* needed objects, even if nothing is setup
        config.Channel.logs = config.guild.text_channels[0]
        await tools.log("Server not setup - call `/setup` !")
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
            await tools.log(msg, code=True, prefix=f"{atmj} ERREURS :")
        except readycheck.NotReadyError:
            config.Channel.logs = config.guild.text_channels[0]
            msg += "\n-- Routing logs to this channel."
            await tools.log(msg, code=True, prefix=f"{atmj} ERREURS :")

    elif len(errors) < config._missing_objects:
        if errors:
            # Erreurs résolues, il en reste
            msg = f"{len(errors)} errors:\n - " + "\n - ".join(errors)
            logging.error(msg)
            await tools.log(msg, code=True, prefix=f"Erreurs restantes :")
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
            name=bot.user.name, avatar=await bot.user.avatar.read()
        )
        await tools.log(f"Webhook de tâches planifiées créé")


# ---- Définition classe principale


class LGBot(discord.Client):
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

    def __init__(self, **kwargs):
        """Initialize self"""
        super().__init__(
            intents=discord.Intents.all(),
            activity=discord.Activity(type=discord.ActivityType.listening, name="vos demandes ➡️ /help"),
            **kwargs,
        )

        self.GUILD_ID = int(env.load("LGREZ_SERVER_ID"))
        self.in_stfu = []
        self.in_fals = []
        self.tasks = {}

        self.tree = commands.LGCommandTree(self, self.GUILD_ID)
        self.tree.register_commands()

    async def setup_hook(self) -> None:
        print(f"     Connected to the gateway")
        print("[3/4] Loading application (bot.setup_hook)...")

        # Déclaration des commandes
        guild = discord.Object(id=self.GUILD_ID)
        await self.tree.sync(guild=guild)
        print(f"     Application loaded: {self.application}")

    async def on_ready(self) -> None:
        """Méthode appelée par Discord au démarrage du bot.

        Vérifie le serveur (appelle :meth:`check_and_prepare_objects`),
        log et affiche publiquement que le bot est fonctionnel (activité) ;
        restaure les tâches planifiées éventuelles et exécute celles manquées.

        Si :attr:`config.output_liveness` vaut ``True``, lance le système
        :meth:`.i_am_alive` (écriture chaque minute sur un fichier disque)
        """
        if config.is_ready:
            return

        print("[4/4] Initialization (bot.on_ready)...")

        guild = self.get_guild(self.GUILD_ID)
        if not guild:
            raise RuntimeError(f"on_ready : Serveur d'ID {self.GUILD_ID} (``LGREZ_SERVER_ID``) introuvable")

        print(f"      Connected to '{guild.name}'! ({len(guild.channels)} channels, {len(guild.members)} members)")
        config.guild = guild

        # Start liveness regular output
        if config.output_liveness:
            self.i_am_alive()

        # Préparations des objects globaux
        await self.check_and_prepare_objects()

        await tools.log("Just rebooted!")

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

    async def on_message(self, message: discord.Message) -> None:
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
        if not config.is_setup:
            return

        if message.author == self.user:  # Pas de boucles infinies
            return

        if not message.guild:
            await message.reply("Je n'accepte pas les messages privés, désolé !")
            return

        if message.guild != config.guild:
            return

        if not message.webhook_id and message.author.top_role == config.Role.everyone:
            # Pas de rôle affecté : le bot te calcule même pas
            return

        if message.channel.name.startswith(config.private_chan_prefix) and message.channel.id not in self.in_stfu:
            # Conditions d'IA respectées (voir doc) : on trigger
            await gestion_ia.process_ia(message, message.reply)

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Méthode appelée par Discord à une exception hors commande.

        Log en mentionnant les MJs. Cette méthode permet de gérer les
        exceptions sans briser la loop du bot (i.e. il reste en ligne).

        Args:
            event: Nom de l'évènement ayant généré une erreur (``"member_join"``, ``"message"``...)
            *args, \**kwargs: Arguments passés à la fonction traitant l'évènement : ``member``, ``message``...
        """
        etype, exc, tb = sys.exc_info()  # Exception ayant causé l'appel

        if isinstance(exc, (bdd.SQLAlchemyError, bdd.DriverOperationalError)):  # Erreur SQL
            try:
                config.session.rollback()  # On rollback la session
                await tools.log("Rollback session")
            except readycheck.NotReadyError:
                pass

        await tools.log(traceback.format_exc(), code=True, prefix=f"{config.Role.mj.mention} ALED : Exception Python !")

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
        asyncio.get_running_loop().call_later(60, self.i_am_alive, filename)

    # Lancement du bot
    def run(self) -> None:
        """Prépare puis lance le bot (bloquant).

        Récupère les informations de connexion, établit la connexion
        à la base de données puis lance le bot.
        """
        print(f"--- LGBot v{__version__} ---")
        print(f"  * Front : discord.py v{discord.__version__}")

        # Récupération du token du bot et de l'ID du serveur
        LGREZ_DISCORD_TOKEN = env.load("LGREZ_DISCORD_TOKEN")

        # Connexion BDD
        print("[1/4] Connecting to database...")
        bdd.connect()
        url = config.engine.url
        print(f"      Connected to {url.host}/{url.database}!")

        # Enregistrement
        config.bot = self

        # Lancement du bot (bloquant)
        print("[2/3] Connecting to Discord...")
        super().run(LGREZ_DISCORD_TOKEN)

        print("\nDisconnected.")
