"""lg-rez / LGBot

Classe principale

"""

import logging
import sys
import time
import traceback

import discord
from discord.ext import commands

from lgrez import __version__, config, bdd
from lgrez.blocs import env, tools, one_command, ready_check
from lgrez.features import *        # Tous les sous-modules


#: str: Description par défaut du bot
default_descr = "LG-bot – Plateforme pour parties endiablées de Loup-Garou"


async def _check_and_prepare_objects(bot):
    errors = []

    def prepare_attributes(rc_class, discord_type, converter):
        """Rend prêt les attributs d'une classe ReadyCheck"""
        for attr in rc_class:
            raw = rc_class.get_raw(attr)
            # Si déjà prêt, on actualise quand même (reconnexion)
            name = raw.name if isinstance(raw, discord_type) else raw
            try:
                ready = converter(name)
            except ValueError:
                qualname = f"config.{rc_class.__name__}.{attr}"
                errors.append(f"{discord_type.__name__} {qualname} = "
                              f"\"{name}\" non trouvé !")
            else:
                setattr(rc_class, attr, ready)

    prepare_attributes(config.Role, discord.Role, tools.role)
    prepare_attributes(config.Channel, discord.TextChannel, tools.channel)
    prepare_attributes(config.Emoji, discord.Emoji, tools.emoji)

    try:
        tools.channel(config.private_chan_category_name)
    except ValueError:
        errors.append(f"catégorie config.private_chan_category_name = "
                      f"\"{config.private_chan_category_name}\" non trouvée")

    try:
        tools.channel(config.boudoirs_category_name)
    except ValueError:
        errors.append(f"catégorie config.boudoirs_category_name = "
                      f"\"{config.boudoirs_category_name}\" non trouvée")

    if len(errors) > config._missing_objects:
        # Nouvelles erreurs
        msg = (f"LGBot.on_ready: {len(errors)} errors:\n - "
               + "\n - ".join(errors))
        logging.error(msg)

        try:
            atmj = config.Role.mj.mention
        except ready_check.NotReadyError:
            atmj = "@everyone"

        try:
            await tools.log(msg, code=True, prefixe=f"{atmj} ERREURS :")
        except ready_check.NotReadyError:
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
    else:           # Création du webhook
        config.webhook = await config.Channel.logs.create_webhook(
            name=bot.user.name,
            avatar=await bot.user.avatar_url.read()
        )
        await tools.log(f"Webhook de tâches planifiées créé")


# ---- Réactions aux différents évènements

# Au démarrage du bot
async def _on_ready(bot):
    config.loop = bot.loop          # Enregistrement loop

    guild = bot.get_guild(bot.GUILD_ID)
    if not guild:
        raise RuntimeError(f"on_ready : Serveur d'ID {bot.GUILD_ID} "
                           "(``LGREZ_SERVER_ID``) introuvable")

    print(f"      Connected to '{guild.name}'! "
          f"({len(guild.channels)} channels, {len(guild.members)} members)")

    if config.output_liveness:
        bot.i_am_alive()            # Start liveness regular output

    print("[3/3] Initialization (bot.on_ready)...")

    # Préparations des objects globaux
    config.guild = guild
    await bot.check_and_prepare_objects()

    await tools.log("Just rebooted!")
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name="vos demandes (!help)"
    ))

    # Tâches planifiées
    taches = bdd.Tache.query.all()
    for tache in taches:
        # Si action manquée, l'exécute immédiatement, sinon l'enregistre
        tache.register()

    if taches:
        await tools.log(f"{len(taches)} tâches planifiées récupérées "
                        "en base et reprogrammées.")

    print("      Initialization complete.")
    print("\nListening for events.")


# À l'arrivée d'un membre sur le serveur
async def _on_member_join(bot, member):
    if member.guild != config.guild:        # Mauvais serveur
        return

    await tools.log(f"Arrivée de {member.name}#{member.discriminator} "
                    "sur le serveur")
    await inscription.main(member)


# Au départ d'un membre du serveur
async def _on_member_remove(bot, member):
    if member.guild != config.guild:        # Mauvais serveur
        return

    await tools.log(
        f"{tools.mention_MJ(member)} ALERTE : départ du serveur de "
        f"{member.display_name} ({member.name}#{member.discriminator}) !")


# À chaque message
async def _on_message(bot, message):
    if message.author == bot.user:          # Pas de boucles infinies
        return

    if not message.guild:                   # Message privé
        await message.channel.send(
            "Je n'accepte pas les messages privés, désolé !"
        )
        return

    if message.guild != config.guild:       # Mauvais serveur
        return

    if (not message.webhook_id              # Pas un webhook
        and message.author.top_role == config.Role.everyone):
        # Pas de rôle affecté : le bot te calcule même pas
        return

    if message.content.startswith(bot.command_prefix + " "):
        message.content = bot.command_prefix + message.content[2:]

    # On trigger toutes les commandes
    # (ne PAS remplacer par bot.process_commands(message), en théorie
    # c'est la même chose mais ça détecte pas les webhooks...)
    ctx = await bot.get_context(message)
    await bot.invoke(ctx)

    if (not message.content.startswith(bot.command_prefix)
        and message.channel.name.startswith(config.private_chan_prefix)
        and message.channel.id not in bot.in_command
        and message.channel.id not in bot.in_stfu):
        # Conditions d'IA respectées (voir doc) : on trigger
        await IA.process_IA(message)


# À chaque réaction ajoutée
async def _on_raw_reaction_add(bot, payload):
    reactor = payload.member
    if reactor == bot.user:                         # Boucle infinie
        return

    if payload.guild_id != config.guild.id:         # Mauvais serveur
        return

    chan = config.guild.get_channel(payload.channel_id)
    if not chan.name.startswith(config.private_chan_prefix):
        # Pas dans un chan privé
        return

    if config.Role.joueur_en_vie not in reactor.roles:
        # Pas un joueur en vie
        return

    if payload.emoji == config.Emoji.bucher:
        ctx = await tools.create_context(reactor, "!vote")
        await ctx.send(
            f"{payload.emoji} > "
            + tools.bold("Vote pour le condamné du jour :")
        )
        await bot.invoke(ctx)       # On trigger !vote

    elif payload.emoji == config.Emoji.maire:
        ctx = await tools.create_context(reactor, "!votemaire")
        await ctx.send(
            f"{payload.emoji} > "
            + tools.bold("Vote pour le nouveau maire :")
        )
        await bot.invoke(ctx)       # On trigger !votemaire

    elif payload.emoji == config.Emoji.lune:
        ctx = await tools.create_context(reactor, "!voteloups")
        await ctx.send(
            f"{payload.emoji} > "
            + tools.bold("Vote pour la victime des loups :")
        )
        await bot.invoke(ctx)       # On trigger !voteloups

    elif payload.emoji == config.Emoji.action:
        ctx = await tools.create_context(reactor, "!action")
        await ctx.send(f"{payload.emoji} > " + tools.bold("Action :"))
        await bot.invoke(ctx)       # On trigger !voteloups


# ---- Gestion des erreurs

def _showexc(exc):
    return f"{type(exc).__name__}: {exc}"


# Gestion des erreurs dans les commandes
async def _on_command_error(bot, ctx, exc):
    if ctx.guild != config.guild:               # Mauvais serveur
        return

    if isinstance(exc, commands.CommandInvokeError):
        if isinstance(exc.original, tools.CommandExit):     # STOP envoyé
            await ctx.send(str(exc.original) or "Mission aborted.")
            return

        if isinstance(exc.original,                         # Erreur BDD
                      (bdd.SQLAlchemyError, bdd.DriverOperationalError)):
            try:
                config.session.rollback()           # On rollback la session
                await tools.log("Rollback session")
            except ready_check.NotReadyError:
                pass

        # Dans tous les cas (sauf STOP), si erreur à l'exécution
        prefixe = ("Oups ! Un problème est survenu à l'exécution de "
                   "la commande  :grimacing: :")

        if ctx.message.webhook_id or ctx.author.top_role >= config.Role.mj:
            # MJ / webhook : affiche le traceback complet
            e = traceback.format_exception(type(exc.original), exc.original,
                                           exc.original.__traceback__)
            await tools.send_code_blocs(ctx, "".join(e), prefixe=prefixe)
        else:
            # Pas MJ : exception seulement
            await ctx.send(f"{prefixe}\n{tools.mention_MJ(ctx)} ALED – "
                           + tools.ital(_showexc(exc.original)))

    elif isinstance(exc, commands.CommandNotFound):
        await ctx.send(
            f"Hum, je ne connais pas cette commande  :thinking:\n"
            f"Utilise {tools.code('!help')} pour voir la liste des commandes."
        )

    elif isinstance(exc, commands.DisabledCommand):
        await ctx.send("Cette commande est désactivée. Pas de chance !")

    elif isinstance(exc, (commands.ConversionError, commands.UserInputError)):
        await ctx.send(
            f"Hmm, ce n'est pas comme ça qu'on utilise cette commande ! "
            f"({tools.code(_showexc(exc))})\n*Tape "
            f"`!help {ctx.invoked_with}` pour plus d'informations.*"
        )
        # ctx.message.content = f"!help {ctx.command.name}"
        # ctx = await bot.get_context(ctx.message)
        # await ctx.reinvoke()

    elif isinstance(exc, commands.CheckAnyFailure):
        # Normalement raise que par @tools.mjs_only
        await ctx.send(
            "Hé ho toi, cette commande est réservée aux MJs !  :angry:"
        )

    elif isinstance(exc, commands.MissingAnyRole):
        # Normalement raise que par @tools.joueurs_only
        await ctx.send(
            "Cette commande est réservée aux joueurs ! "
            "(parce qu'ils doivent être inscrits en base, toussa) "
            f"({tools.code('!doas')} est là en cas de besoin)"
        )

    elif isinstance(exc, commands.MissingRole):
        # Normalement raise que par @tools.vivants_only
        await ctx.send(
            "Désolé, cette commande est réservée aux joueurs en vie !"
        )

    elif isinstance(exc, one_command.AlreadyInCommand):
        if ctx.command.name in ["addIA", "modifIA"]:
            # addIA / modifIA : droit d'enregistrer les commandes, donc chut
            return
        await ctx.send(
            f"Impossible d'utiliser une commande pendant "
            "un processus ! (vote...)\n"
            f"Envoie {tools.code(config.stop_keywords[0])} "
            "pour arrêter le processus."
        )

    elif isinstance(exc, commands.CheckFailure):
        # Autre check non vérifié
        await ctx.send(
            f"Tiens, il semblerait que cette commande ne puisse "
            f"pas être exécutée ! {tools.mention_MJ(ctx)} ?\n"
            f"({tools.ital(_showexc(exc))})")

    else:
        await ctx.send(
            f"Oups ! Une erreur inattendue est survenue  :grimacing:\n"
            f"{tools.mention_MJ(ctx)} ALED – {tools.ital(_showexc(exc))}"
        )


# Erreurs non gérées par le code précédent (hors cadre d'une commande)
async def _on_error(bot, event, *args, **kwargs):
    etype, exc, tb = sys.exc_info()     # Exception ayant causé l'appel

    if isinstance(exc, (bdd.SQLAlchemyError,            # Erreur SQL
                        bdd.DriverOperationalError)):
        try:
            config.session.rollback()       # On rollback la session
            await tools.log("Rollback session")
        except ready_check.NotReadyError:
            pass

    await tools.log(
        traceback.format_exc(),
        code=True,
        prefixe=f"{config.Role.mj.mention} ALED : Exception Python !"
    )

    # On remonte l'exception à Python (pour log, ne casse pas la loop)
    raise


# ---- Définition classe principale

class LGBot(commands.Bot):
    """Bot Discord pour parties de Loup-Garou à la PCéenne.

    Classe fille de :class:`discord.ext.commands.Bot`, implémentant les
    commandes et fonctionnalités du Loup-Garou de la Rez.

    Args:
        command_prefix (str): passé à :class:`discord.ext.commands.Bot`
        case_insensitive (bool): passé à
            :class:`discord.ext.commands.Bot`
        description (str): idem, défaut \:
            :attr:`lgrez.bot.default_descr`
        intents (discord.Intents): idem, défaut \:
            :meth:`~discord.Intents.all()`. *Certaines commandes et
            fonctionnalités risquent de ne pas fonctionner avec une
            autre valeur.*
        member_cache_flags (discord.MemberCacheFlags): idem, défaut \:
            :meth:`~discord.MemberCacheFlags.all()`. *Certaines
            commandes et fonctionnalités risquent de ne pas fonctionner
            avec une autre valeur.*
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
        bot (int): L'ID du serveur sur lequel tourne le bot (normalement
            toujours :attr:`config.guild` ``.id``).  Vaut ``None`` avant
            l'appel à :meth:`run`, puis la valeur de la variable
            d'environnement ``LGREZ_SERVER_ID``.
        in_command (list[int]): IDs des salons dans lequels une
            commande est en cours d'exécution.
        in_stfu (list[int]): IDs des salons en mode STFU.
        in_fals (list[int]): IDs des salons en mode Foire à la saucisse.
        tasks (dict[int (.bdd.Tache.id), asyncio.TimerHandle]):
            Tâches planifiées actuellement en attente. Privilégier
            plutôt l'emploi de :attr:`.bdd.Tache.handler`.

    """
    def __init__(self, command_prefix="!", case_insensitive=True,
                 description=None, intents=None, member_cache_flags=None,
                 **kwargs):
        """Initialize self"""
        # Paramètres par défaut
        if description is None:
            description = default_descr
        if intents is None:
            intents = discord.Intents.all()
        if member_cache_flags is None:
            member_cache_flags = discord.MemberCacheFlags.all()

        # Construction du bot Discord.py
        super().__init__(
            command_prefix=command_prefix,
            description=description,
            case_insensitive=case_insensitive,
            intents=intents,
            member_cache_flags=member_cache_flags,
            **kwargs
        )

        # Définition attribus personnalisés
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
    async def on_ready(self):
        """Méthode appellée par Discord au démarrage du bot.

        Vérifie le serveur (appelle :meth:`check_and_prepare_objects`),
        log et affiche publiquement que le bot est fonctionnel
        (activité) ;  restaure les tâches planifiées éventuelles
        et exécute celles manquées.

        Si :attr:`config.output_liveness` vaut ``True``, lance
        :attr:`bot.i_am_alive <.LGBot.i_am_alive>`
        (écriture chaque minute sur un fichier disque)

        Voir :func:`discord.on_ready` pour plus d'informations.
        """
        await _on_ready(self)

    async def on_member_join(self, member):
        """Méthode appellée par l'API à l'arrivée d'un nouveau membre.

        Log et lance le processus d'inscription.

        Ne fait rien si l'arrivée n'est pas sur le serveur
        :attr:`config.guild`.

        Args:
            member (discord.Member): Le membre qui vient d'arriver.

        Voir :func:`discord.on_member_join` pour plus d'informations.
        """
        await _on_member_join(self, member)

    async def on_member_remove(self, member):
        """Méthode appellée par l'API au départ d'un membre du serveur.

        Log en mentionnant les MJs.

        Ne fait rien si le départ n'est pas du serveur
        :attr:`config.guild`.

        Args:
            member (discord.Member): Le joueur qui vient de partir.

        Voir :func:`discord.on_member_remove` pour plus d'informations.
        """
        await _on_member_remove(self, member)

    async def on_message(self, message):
        """Méthode appellée par l'API à la réception d'un message.

        Invoque l'ensemble des commandes, ou les règles d'IA si
            - Le message n'est pas une commande
            - Le message est posté dans un channel privé (dont le nom
              commence par :attr:`config.private_chan_prefix`)
            - Il n'y a pas déjà de commande en cours dans ce channel
            - Le channel n'est pas en mode STFU

        Ne fait rien si le message n'est pas sur le serveur
        :attr:`config.guild`, si il est envoyé par le bot lui-même
        ou par un membre sans aucun rôle affecté.

        Args:
            member (discord.Member): Le joueur qui vient d'arriver.

        Voir :func:`discord.on_message` pour plus d'informations.
        """
        await _on_message(self, message)

    async def on_raw_reaction_add(self, payload):
        """Méthode appellée par l'API à l'ajout d'une réaction.

        Appelle la fonction adéquate si le membre est un joueur
        inscrit, est sur un chan de conversation bot et a cliqué sur
        :attr:`config.Emoji.bucher`, :attr:`~config.Emoji.maire`,
        :attr:`~config.Emoji.lune` ou :attr:`~config.Emoji.action`.

        Ne fait rien si la réaction n'est pas sur le serveur
        :attr:`config.guild`.

        Args:
            payload (discord.RawReactionActionEvent): Paramètre
                limité (car le message n'est pas forcément dans le
                cache du bot, par exemple si il a été reboot depuis).

        Quelques attributs utiles :
          - ``payload.member`` (:class:`discord.Member`) : Membre
            ayant posé la réaction
          - ``payload.emoji`` (:class:`discord.PartialEmoji`) :
            PartialEmoji envoyé
          - ``payload.message_id`` (:class:`int`) : ID du message réacté

        Voir :func:`discord.on_raw_reaction_add` pour plus
        d'informations.
        """
        await _on_raw_reaction_add(self, payload)

    # Gestion des erreurs
    async def on_command_error(self, ctx, exc):
        """Méthode appellée par l'API à un exception dans une commande.

        Analyse l'erreur survenue et informe le joueur de manière
        adéquate en fonction, en mentionnant les MJs si besoin.

        Ne fait rien si l'exception n'a pas eu lieu sur le serveur
        :attr:`config.guild`.

        Args:
            ctx (discord.ext.commands.Context): Contexte dans lequel
                l'exception a été levée
            exc (discord.ext.commands.CommandError): Exception levée

        Voir :func:`discord.on_command_error` pour plus d'informations.
        """
        await _on_command_error(self, ctx, exc)

    async def on_error(self, event, *args, **kwargs):
        """Méthode appellée par l'API à une exception hors commande.

        Log en mentionnant les MJs. Cette méthode permet de gérer les
        exceptions sans briser la loop du bot (i.e. il reste en ligne).

        Args:
            event (str): Nom de l'évènement ayant généré une erreur
                (``"member_join"``, ``"message"``...)
            *args, \**kwargs: Arguments passés à la fonction traitant
                l'évènement : ``member``, ``message``...

        Voir :func:`discord.on_error` pour plus d'informations.
        """
        await _on_error(self, event, *args, **kwargs)

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

    async def on_guild_channel_delete(self, channel):
        if channel.guild == config.guild:
            await self.check_and_prepare_objects()

    async def on_guild_channel_update(self, before, after):
        if before.guild == config.guild and config._missing_objects:
            await self.check_and_prepare_objects()

    async def on_guild_channel_create(self, channel):
        if channel.guild == config.guild and config._missing_objects:
            await self.check_and_prepare_objects()

    async def on_guild_role_delete(self, role):
        if role.guild == config.guild:
            await self.check_and_prepare_objects()

    async def on_guild_role_update(self, before, after):
        if before.guild == config.guild and config._missing_objects:
            await self.check_and_prepare_objects()

    async def on_guild_role_create(self, channel):
        if role.guild == config.guild and config._missing_objects:
            await self.check_and_prepare_objects()

    async def on_guild_emojis_update(self, guild, before, after):
        if guild == config.guild:
            await self.check_and_prepare_objects()

    async def on_webhooks_update(self, channel):
        if channel == config.Channel.logs:
            await self.check_and_prepare_objects()

    # Système de vérification de vie
    def i_am_alive(self, filename="alive.log"):
        """Témoigne que le bot est en vie et non bloqué.

        Exporte le temps actuel (UTC) et planifie un nouvel appel
        dans 60s. Ce processus n'est lancé que si
        :attr:`config.output_liveness` est mis à ``True``.

        Args:
            filename (:class:`str`): fichier où exporter le temps
                actuel (écrase le contenu).
        """
        with open(filename, "w") as f:
            f.write(str(time.time()))
        self.loop.call_later(60, self.i_am_alive, filename)

    # Lancement du bot
    def run(self, **kwargs):
        """Prépare puis lance le bot (bloquant).

        Récupère les informations de connexion, établit la connexion
        à la base de données puis lance le bot.

        Args:
            \**kwargs: Passés à :meth:`discord.ext.commands.Bot.run`.
        """
        print(f"--- LGBot v{__version__} ---")

        # Récupération du token du bot et de l'ID du serveur
        LGREZ_DISCORD_TOKEN = env.load("LGREZ_DISCORD_TOKEN")
        self.GUILD_ID = int(env.load("LGREZ_SERVER_ID"))

        # Connection BDD
        print("[1/3] Connecting to database...")
        bdd.connect()
        print("      Connected!")

        # Enregistrement
        config.bot = self

        # Lancement du bot (bloquant)
        print("[2/3] Connecting to Discord...")
        super().run(LGREZ_DISCORD_TOKEN, **kwargs)

        print("\nDisconnected.")
