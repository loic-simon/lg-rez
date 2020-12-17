import sys
import asyncio
import logging
import traceback
import time
import datetime
import re

import discord
from discord.ext import commands

from lgrez import __version__
from lgrez.blocs import tools, bdd, env, bdd_tools, gsheets, webhook, realshell
from lgrez.blocs.bdd import Tables, Joueurs, Actions, Roles
from lgrez.features import annexe, IA, inscription, informations, sync, open_close, voter_agir, taches, actions_publiques, communication


logging.basicConfig(level=logging.WARNING)



### Checks et système de blocage

class AlreadyInCommand(commands.CheckFailure):
    """Exception levée lorsq'un member veut lancer une commande dans un salon déjà occupé.

    Classe fille de :exc:`discord.ext.commands.CheckFailure`.
    """
    pass

async def already_in_command(ctx):
    """Check (:class:`discord.ext.commands.Check`) : vérifie si le joueur est actuellement dans une commande.

    Si non, raise une exception :exc:`AlreadyInCommand`.

    Args:
        ctx (:class:`discord.ext.commands.Context`): contexte d'invocation de la commande.
    """
    if (ctx.channel.id in ctx.bot.in_command
        and ctx.command.name not in ["stop", "panik"]):     # Cas particuliers : !stop/!panik

        await ctx.send("stop", delete_after=0)      # On envoie (discrètement) l'ordre d'arrêt commande précédente
        await asyncio.sleep(1)                      # On attend qu'il soit pris en compte
        if ctx.channel.id in ctx.bot.in_command:    # Si ça n'a pas suffit
            raise AlreadyInCommand()                    # on raise l'erreur
        else:
            return True
    else:
        return True

# @bot.before_invoke
async def add_to_in_command(ctx):
    """Ajoute le channel de ``ctx`` à la liste des channels dans une commande.

    Cette fonction est appellée avant chaque appel de fonction.
    Elle est appellée seulement si les checks sont OK, donc pas si le salon est déjà dans :attr:`ctx.bot.in_command <.LGBot.in_command>`.

    Args:
        ctx (:class:`discord.ext.commands.Context`): contexte d'invocation de la commande.
    """
    if ctx.command.name != "stop" and not ctx.message.webhook_id:
        ctx.bot.in_command.append(ctx.channel.id)

# @bot.after_invoke
async def remove_from_in_command(ctx):
    """Retire le channel de ``ctx`` de la liste des channels dans une commande.

    Cette fonction est appellée après chaque appel de fonction.
    Elle attend 0.5 secondes avant d'enlever le joueur afin d'éviter que le bot réagisse « nativement » (IA) à un message déjà traité par un :func:`.tools.wait_for_message` ayant mené à la fin de la commande.

    Args:
        ctx (:class:`discord.ext.commands.Context`): contexte d'invocation de la commande.
    """
    await asyncio.sleep(0.5)        # On attend un peu
    if ctx.channel.id in ctx.bot.in_command:
        ctx.bot.in_command.remove(ctx.channel.id)



### Réactions aux différents évènements

# Au démarrage du bot
async def _on_ready(bot):
    """Méthode appellée par Discord au démarrage du bot.

    Vérifie le serveur, log et affiche publiquement que le bot est fonctionnel ; restaure les tâches planifiées éventuelles et exécute celles manquées.

    Si :attr:`bot.config <.LGBot.config>` ``["output_liveness"]`` vaut ``True``, lance :attr:`bot.i_am_alive <.LGBot.i_am_alive>` (écriture chaque minute sur un fichier disque)
    """
    if bot.config.get("output_liveness"):
        bot.i_am_alive()            # Start liveness regular output

    guild = bot.get_guild(bot.GUILD_ID)
    assert guild, f"on_ready : Guilde d'ID {bot.GUILD_ID} introuvable"

    print(f"{bot.user} connecté au serveur « {guild.name} » (id : {guild.id})\n")
    print(f"Guild Members: " + " - ".join([member.display_name for member in guild.members]))
    print(f"\nChannels: " + " - ".join([channel.name for channel in guild.text_channels]))

    await tools.log(guild, "Juste rebooted!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="vos demandes (!help)"))

    # Tâches planifiées
    now = datetime.datetime.now()
    r = 0

    for tache in Tables["Taches"].query.all():
        delta = (tache.timestamp - now).total_seconds()
        TH = bot.loop.call_later(delta, taches.execute, tache, bot.loop)  # Si delta < 0 (action manquée), l'exécute immédiatement, sinon attend jusqu'à tache.timestamp
        bot.tasks[tache.id] = TH
        # r += f"Récupération de la tâche {tools.code(tache.timestamp.strftime('%d/%m/%Y %H:%M:%S'))} > {tools.code(tache.commande)}\n"
        r += 1

    if r:
        await tools.log(guild, f"{r} tâches planifiées récupérées en base et reprogrammées.")


# À l'arrivée d'un membre sur le serveur
async def _on_member_join(bot, member):
    """Méthode appellée par Discord à l'arrivée d'un joueur sur le serveur.

    Log et lance le processus d'inscription.

    Ne fait rien si l'arrivée n'est pas sur le serveur :attr:`GUILD_ID`.

    Args:
        member (:class:`discord.Member`): Le joueur qui vient d'arriver.
    """
    if member.guild.id != bot.GUILD_ID:            # Bon serveur
        return

    await tools.log(member, f"Arrivée de {member.name}#{member.discriminator} sur le serveur")
    await inscription.main(bot, member)


# Au départ d'un membre du serveur
async def _on_member_remove(bot, member):
    """Méthode appellée par Discord au départ d'un joueur du serveur.

    Log en mentionnant les MJs.

    Ne fait rien si le départ n'est pas du serveur :attr:`GUILD_ID`.

    Args:
        member (:class:`discord.Member`): Le joueur qui vient de partir.
    """
    if member.guild.id != bot.GUILD_ID:            # Bon serveur
        return

    await tools.log(member, f"{tools.mention_MJ(member)} ALERTE : départ de {member.display_name} ({member.name}#{member.discriminator}) du serveur !!")


# À chaque message
async def _on_message(bot, message):
    """Méthode appellée par Discord à la réception d'un message.

    Invoque l'ensemble des commandes, ou les règles d'IA si
        - Le message n'est pas une commande
        - Le message est posté dans un channel privé (#conv-bot-...)
        - Il n'y a pas déjà de commande en cours dans ce channel
        - Le channel n'est pas en mode STFU

    Ne fait rien si le message n'est pas sur le serveur :attr:`GUILD_ID` ou qu'il est envoyé par le bot lui-même ou par un membre sans aucun rôle affecté.

    Args:
        member (:class:`discord.Member`): Le joueur qui vient d'arriver.
    """

    if message.author == bot.user:              # Sécurité pour éviter les boucles infinies
        return

    if not message.guild:                       # Message privé
        await message.channel.send("Je n'accepte pas les messages privés, désolé !")
        return

    if message.guild.id != bot.GUILD_ID:        # Mauvais serveur
        return

    if not message.webhook_id:                  # Pas un webhook
        if message.author.top_role == tools.role(message, "@everyone"):     # Pas de rôle affecté
            return                                                              # le bot te calcule même pas

    if message.content.startswith(bot.command_prefix + " "):
        message.content = bot.command_prefix + message.content[2:]

    await bot.invoke(await bot.get_context(message))        # On trigger toutes les commandes
    # (ne PAS remplacer par bot.process_commands(message), en théorie c'est la même chose mais ça détecte pas les webhooks...)

    if (not message.content.startswith(bot.command_prefix)  # Si pas une commande
        and message.channel.name.startswith("conv-bot")     # et dans un channel de conversation bot
        and message.channel.id not in bot.in_command        # et pas déjà dans une commande (vote...)
        and message.channel.id not in bot.in_stfu):         # et le channel est pas en mode STFU

        await IA.process_IA(bot, message)                       # On trigger les règles d'IA


# À chaque réaction ajoutée
async def _on_raw_reaction_add(bot, payload):
    """Méthode appellée par Discord à l'ajout d'une réaction sur un message.

    Appelle la fonction adéquate si le joueur est en base et a cliqué sur ":bucher:", ":maire:", ":lune:" ou ":action:".

    Ne fait rien si la réaction n'est pas sur le serveur :attr:`GUILD_ID`.

    Args:
        payload (:class:`discord.RawReactionActionEvent`): Paramètre "statique" (car le message n'est pas forcément dans le cache du bot, par exemple si il a été reboot depuis).

    Quelques attributs utiles :
        - ``payload.member`` (:class:`discord.Member`) : Membre ayant posé la réaction
        - ``payload.emoji`` (:class:`discord.PartialEmoji`) : PartialEmoji envoyé
        - ``payload.message_id`` (int) : ID du message réacté
    """
    if payload.guild_id != bot.GUILD_ID:            # Mauvais serveur
        return

    reactor = payload.member
    if reactor == bot.user:
        return

    if payload.emoji == tools.emoji(reactor, "bucher"):
        if not Joueurs.query.get(reactor.id):        # Gens pas en base
            return

        ctx = await tools.create_context(bot, reactor, "!vote")
        if ctx.guild.get_channel(payload.channel_id).name.startswith("conv-bot"):
            await ctx.send(f"""{payload.emoji} > {tools.bold("Vote pour le condamné du jour :")}""")
            await bot.invoke(ctx)       # On trigger !vote

    elif payload.emoji == tools.emoji(reactor, "maire"):
        if not Joueurs.query.get(reactor.id):        # Gens pas en base
            return

        ctx = await tools.create_context(bot, reactor, "!votemaire")
        if ctx.guild.get_channel(payload.channel_id).name.startswith("conv-bot"):
            await ctx.send(f"""{payload.emoji} > {tools.bold("Vote pour le nouveau maire :")}""")
            await bot.invoke(ctx)       # On trigger !votemaire

    elif payload.emoji == tools.emoji(reactor, "lune"):
        if not Joueurs.query.get(reactor.id):        # Gens pas en base
            return

        ctx = await tools.create_context(bot, reactor, "!voteloups")
        if ctx.guild.get_channel(payload.channel_id).name.startswith("conv-bot"):
            await ctx.send(f"""{payload.emoji} > {tools.bold("Vote pour la victime des loups :")}""")
            await bot.invoke(ctx)       # On trigger !voteloups

    elif payload.emoji == tools.emoji(reactor, "action"):
        if not Joueurs.query.get(reactor.id):        # Gens pas en base
            return

        ctx = await tools.create_context(bot, reactor, "!action")
        if ctx.guild.get_channel(payload.channel_id).name.startswith("conv-bot"):
            await ctx.send(f"""{payload.emoji} > {tools.bold("Action :")}""")
            await bot.invoke(ctx)       # On trigger !voteloups


# Gestion des erreurs dans les commandes
async def _on_command_error(bot, ctx, exc):
    """Méthode appellée par Discord à chaque exception levée dans une commande.

    Analyse l'erreur survenue et informe le joueur de manière adéquate en fonction, en mentionnant les MJs si besoin.

    Ne fait rien si l'exception n'a pas eu lieu sur le serveur :attr:`GUILD_ID`.

    Args:
        ctx (:class:`discord.ext.commands.Context`): Contexte dans lequel l'exception a été levée
        exc (:class:`discord.ext.commands.CommandError`): Exception levée
    """
    if ctx.guild.id != bot.GUILD_ID:            # Mauvais serveur
        return

    if isinstance(exc, commands.CommandInvokeError) and isinstance(exc.original, tools.CommandExit):     # STOP envoyé
        await ctx.send(str(exc.original) or "Mission aborted.")

    elif isinstance(exc, commands.CommandInvokeError):
        if isinstance(exc.original, bdd.SQLAlchemyError) or isinstance(exc.original, bdd.DriverOperationalError):       # Erreur SQL
            if bdd.session:
                await tools.log(ctx, "Rollback session")
                bdd.session.rollback()          # On rollback la session

        await ctx.send(f"Oups ! Un problème est survenu à l'exécution de la commande  :grimacing:\n"
                       f"{tools.mention_MJ(ctx)} ALED – "
                       f"{tools.ital(f'{type(exc.original).__name__}: {str(exc.original)}')}")

    elif isinstance(exc, commands.CommandNotFound):
        await ctx.send(f"Hum, je ne connais pas cette commande  :thinking:\n"
                       f"Utilise {tools.code('!help')} pour voir la liste des commandes.")

    elif isinstance(exc, commands.DisabledCommand):
        await ctx.send(f"Cette commande est désactivée. Pas de chance !")

    elif isinstance(exc, commands.ConversionError) or isinstance(exc, commands.UserInputError):
        await ctx.send(f"Hmm, ce n'est pas comme ça qu'on utilise cette commande ! Petit rappel : ({tools.code(f'{type(exc).__name__}: {exc}')})")
        ctx.message.content = f"!help {ctx.command.name}"
        ctx = await bot.get_context(ctx.message)
        await ctx.reinvoke()

    elif isinstance(exc, commands.CheckAnyFailure):         # Normalement raise que par @tools.mjs_only
        await ctx.send("Hé ho toi, cette commande est réservée aux MJs !  :angry:")

    elif isinstance(exc, commands.MissingAnyRole):          # Normalement raise que par @tools.joueurs_only
        await ctx.send("Cette commande est réservée aux joueurs ! (parce qu'ils doivent être inscrits en base, toussa)"
                       f"({tools.code('!doas')} est là en cas de besoin)")

    elif isinstance(exc, commands.MissingRole):             # Normalement raise que par @tools.vivants_only
        await ctx.send("Désolé, cette commande est réservée aux joueurs en vie !")

    elif isinstance(exc, AlreadyInCommand) and ctx.command.name not in ["addIA", "modifIA"]:
        await ctx.send(f"Impossible d'utiliser une commande pendant un processus ! (vote...)\n"
                       f"Envoie {tools.code('stop')} pour arrêter le processus.")

    elif isinstance(exc, commands.CheckFailure):        # Autre check non vérifié
        await ctx.send(f"Tiens, il semblerait que cette commande ne puisse pas être exécutée ! {tools.mention_MJ(ctx)} ?\n"
                       f"({tools.ital(f'{type(exc).__name__}: {str(exc)}')})")

    else:
        await ctx.send(f"Oups ! Une erreur inattendue est survenue  :grimacing:\n"
                       f"{tools.mention_MJ(ctx)} ALED – "
                       f"{tools.ital(f'{type(exc).__name__}: {str(exc)}')}")


# Erreurs non gérées par le code précédent (hors du cadre d'une commande)
async def _on_error(bot, event, *args, **kwargs):
    """Méthode appellée par Discord à chaque exception remontant au-delà d'une commande.

    Log en mentionnant les MJs. Cette méthode permet de gérer les exceptions sans briser la loop du bot (i.e. il reste en ligne).

    Args:
        event (str): Nom de l'évènement ayant généré une erreur (``"member_join"``, ``"message"``...)
        *args, \**kwargs: Arguments passés à la fonction traitant l'évènement : ``member``, ``message``...
    """
    etype, exc, tb = sys.exc_info()         # Exception ayant causé l'appel

    guild = bot.get_guild(bot.GUILD_ID)
    assert guild, f"on_error : Serveur {bot.GUILD_ID} introuvable - Erreur initiale : \n{traceback.format_exc()}"

    if isinstance(exc, bdd.SQLAlchemyError) or isinstance(exc, bdd.DriverOperationalError):     # Erreur SQL
        if bdd.session:
            bdd.session.rollback()          # On rollback la session
            await tools.log(guild, "Rollback session")

    await tools.log(guild, traceback.format_exc(), code=True,
        prefixe=f"{tools.role(guild, 'MJ').mention} ALED (with prefix) : Exception Python !")

    raise        # On remonte l'exception à Python (pour log, ça ne casse pas la loop)



### Commandes spéciales

class Special(commands.Cog):
    """Special - Commandes spéciales (méta-commandes, imitant ou impactant le déroulement des autres)"""

    @commands.command(aliases=["kill"])
    @tools.mjs_only
    async def panik(self, ctx):
        """Tue instantanément le bot, sans confirmation (COMMANDE MJ)

        PAAAAANIK
        """
        sys.exit()


    @commands.command()
    @tools.mjs_only
    async def do(self, ctx, *, code):
        """Exécute du code Python et affiche le résultat (COMMANDE MJ)

        Args:
            code: instructions valides dans le contexte du fichier ``bot.py`` (utilisables notemment : ``ctx``, ``bdd.session``, ``Tables``...)

        Si ``code`` est une coroutine, elle sera awaited (ne pas inclure ``await`` dans ``code``).

        Aussi connue sous le nom de « faille de sécurité », cette commande permet de faire environ tout ce qu'on veut sur le bot (y compris le crasher, importer des modules, exécuter des fichiers .py... même si c'est un peu compliqué) voire d'impacter le serveur sur lequel le bot tourne si on est motivé.

        À utiliser avec parcimonie donc, et QUE pour du développement/debug !
        """
        class Answer():
            def __init__(self):
                self.rep = ""
        a = Answer()
        exec(f"a.rep = {code}")
        if asyncio.iscoroutine(a.rep):
            a.rep = await a.rep
        await ctx.send(f"Entrée : {tools.code(code)}\nSortie :\n{a.rep}")


    @commands.command()
    @tools.mjs_only
    async def shell(self, ctx):
        """Lance un pseudo-terminal Python (COMMANDE MJ)

        Envoyer ``help`` dans le pseudo-terminal pour plus d'informations sur son fonctionnement.

        Évidemment, les avertissements dans ``!do`` s'appliquent ici : ne pas faire n'imp avec cette commande !! (même si ça peut être très utile, genre pour ajouter des gens en masse à un channel)
        """
        locs = globals()
        locs["ctx"] = ctx
        shell = realshell.RealShell(ctx.bot, ctx.channel, locs)
        try:
            await shell.interact()
        except realshell.RealShellExit as exc:
            raise tools.CommandExit(*exc.args if exc else "!shell: Forced to end.")


    @commands.command()
    @tools.mjs_only
    async def co(self, ctx, cible=None):
        """Lance la procédure d'inscription comme si on se connectait au serveur pour la première fois (COMMANDE MJ)

        Args:
            cible: la MENTION (``@joueur``) du joueur à inscrire, par défaut le lançeur de la commande.

        Cette commande est principalement destinée aux tests de développement, mais peut être utile si un joueur chibre son inscription (à utiliser dans son channel, ou ``#bienvenue`` (avec ``!autodestruct``) si même le début a chibré).
        """
        if cible:
            id = ''.join([c for c in cible if c.isdigit()])         # Si la chaîne contient un nombre, on l'extrait
            if id and (member := ctx.guild.get_member(int(id))):          # Si c'est un ID d'un membre du serveur
                pass
            else:
                await ctx.send("Cible introuvable.")
                return
        else:
            member = ctx.author

        await inscription.main(ctx.bot, member)


    @commands.command()
    @tools.mjs_only
    async def doas(self, ctx, *, qui_quoi):
        """Exécute une commande en tant qu'un autre joueur (COMMANDE MJ)

        Args:
            qui_quoi: nom de la cible (nom ou mention d'un joueur INSCRIT) suivi de la commande à exécuter (commençant par un ``!``).

        Example:
            ``!doas Vincent Croquette !vote Annie Colin``
        """
        qui, quoi = qui_quoi.split(" " + ctx.bot.command_prefix, maxsplit=1)       # !doas <@!id> !vote R ==> qui = "<@!id>", quoi = "vote R"
        joueur = await tools.boucle_query_joueur(ctx, qui.strip() or None, Tables["Joueurs"])
        member = ctx.guild.get_member(joueur.discord_id)
        assert member, f"!doas : Member {joueur} introuvable"

        ctx.message.content = ctx.bot.command_prefix + quoi
        ctx.message.author = member

        await ctx.send(f":robot: Exécution en tant que {joueur.nom} :")
        await remove_from_in_command(ctx)       # Bypass la limitation de 1 commande à la fois
        await ctx.bot.process_commands(ctx.message)
        await add_to_in_command(ctx)


    @commands.command(aliases=["autodestruct", "ad"])
    @tools.mjs_only
    async def secret(self, ctx, *, quoi):
        """Supprime le message puis exécute la commande (COMMANDE MJ)

        Args:
            quoi: commande à exécuter, commençant par un ``!``

        Utile notemment pour faire des commandes dans un channel public, pour que la commande (moche) soit immédiatement supprimée.
        """
        await ctx.message.delete()

        ctx.message.content = quoi

        await remove_from_in_command(ctx)       # Bypass la limitation de 1 commande à la fois
        await ctx.bot.process_commands(ctx.message)
        await add_to_in_command(ctx)


    @commands.command()
    @tools.private
    async def stop(self, ctx):
        """Peut débloquer des situations compliquées (beta)

        Ne pas utiliser cette commande sauf en cas de force majeure où plus rien ne marche, et sur demande d'un MJ (après c'est pas dit que ça marche mieux après l'avoir utilisée)
        """
        if ctx.channel.id in ctx.bot.in_command:
            ctx.bot.in_command.remove(ctx.channel.id)
        ctx.send("Te voilà libre, camarade !")


    ### 6 bis - Gestion de l'aide

    @commands.command(aliases=["aide", "aled", "oskour"])
    async def help(self, ctx, *, command=None):
        """Affiche la liste des commandes utilisables et leur utilisation

        Args:
            command (optionnel): nom exact d'une commande à expliquer (ou un de ses alias)

        Si ``command`` n'est pas précisée, liste l'ensemble des commandes accessibles à l'utilisateur.
        """

        pref = ctx.bot.command_prefix
        cogs = ctx.bot.cogs                                                                 # Dictionnaire nom: cog
        commandes = {cmd.name: cmd for cmd in ctx.bot.commands}                             # Dictionnaire nom: commande
        aliases = {alias: nom for nom, cmd in commandes.items() for alias in cmd.aliases}   # Dictionnaire alias: nom de la commande

        len_max = max(len(cmd) for cmd in commandes)

        if not command:         # Pas d'argument ==> liste toutes les commandes
            ctx.bot.in_command.remove(ctx.channel.id)   # On désactive la limitation de une commande simultanée sinon can_run renvoie toujours False
            async def filter_runnables(commands):           # Obligé parce que can_run doit être await, donc c'est compliqué
                """Retourne la liste des commandes pouvant run parmis commands"""
                runnables = []
                for cmd in commands:
                    try:
                        runnable = await cmd.can_run(ctx)
                    except Exception:       # Parfois can_run raise une exception pour dire que la commande est pas runnable
                        runnable = False
                    if runnable:
                        runnables.append(cmd)
                return runnables

            r = f"""{ctx.bot.description} (v{__version__})"""
            for cog in cogs.values():
                runnables = await filter_runnables(cog.get_commands())
                if runnables:                           # pour chaque cog contenant des runnables
                    r += f"\n\n{cog.description} :"
                    for cmd in runnables:               # pour chaque commande runnable
                        r += f"\n  - {pref}{cmd.name.ljust(len_max)}  {cmd.short_doc}"

            runnables_hors_cog = await filter_runnables(cmd for cmd in ctx.bot.commands if not cmd.cog)
            if runnables_hors_cog:
                r += f"\n\nCommandes isolées :"
                for cmd in runnables_hors_cog:
                    r += f"\n  - {pref}{cmd.name.ljust(len_max)}  {cmd.short_doc}"

            r += f"\n\nUtilise <{pref}help command> pour plus d'information sur une commande."

            ctx.bot.in_command.append(ctx.channel.id)   # On réactive la limitation

        else:       # Aide détaillée sur une commande
            if command.startswith(pref):        # Si le joueur fait !help !command
                command = command.lstrip(pref)
            if command in aliases:              # Si !help d'un alias
                command = aliases[command]      # On remplace l'alias par sa commande

            if command in commandes:             # Si commande existante
                cmd = commandes[command]

                doc = cmd.help or ""
                doc = doc.replace("``", "`")
                doc = doc.replace("Args:", "Arguments :")
                doc = re.sub(r":\w+?:`[\.~!]*(.+?)`", r"`\1`", doc)

                r = f"{pref}{command} {cmd.signature} – {doc}\n"
                if cmd_aliases := [alias for alias,cmd in aliases.items() if cmd == command]:       # Si la commande a des alias
                    r += f"\nAlias : {pref}" + f", {pref}".join(cmd_aliases)

            else:
                r = f"Commande <{command}> non trouvée.\nUtilise <{pref}help> pour la liste des commandes."

        r += "\nSi besoin, n'hésite pas à appeler un MJ en les mentionnant (@MJ)."
        await tools.send_code_blocs(ctx, r, sep="\n\n")     # On envoie, en séparant en blocs de 2000 caractères max



# Définition classe principale

class LGBot(commands.Bot):
    """Bot Discord pour parties de Loup-Garou à la PCéenne.

    Classe fille de :class:`discord.ext.commands.Bot`, utilisable exactement de la même manière.
    """
    def __init__(self, command_prefix="!", description=None, case_insensitive=True,
                 intents=discord.Intents.all(), member_cache_flags=discord.MemberCacheFlags.all(), **kwargs):
        """Initialize self"""
        if not description:
            description = "LG-bot – Plateforme pour parties endiablées de Loup-Garou"

        super().__init__(
            command_prefix=command_prefix,
            description=description,
            case_insensitive=case_insensitive,
            intents=intents,
            member_cache_flags=member_cache_flags,
            **kwargs
        )

        #: :class:`int`: L'ID du serveur sur lequel tourne le bot.
        #: Vaut ``None`` avant l'appel à :meth:`run`, puis la valeur de la variable d'environnement ``LGREZ_SERVER_ID``.
        self.GUILD_ID = None

        #: :class:`dict`: Personalisation du bot (à définir avant l'appel à :meth:`run`), utilisable par les différentes fonctionnalités
        #: (exemples : ``bot.config["debut_saison"]``, ``bot.config["demande_porte"]``...)
        self.config = {}

        #: :class:`list`\[:class:`int`\]: IDs des salons dans lequels une commande est en cours d'exécution.
        self.in_command = []
        #: :class:`list`\[:class:`int`\]: IDs des salons en mode STFU.
        self.in_stfu = []
        #: :class:`list`\[:class:`int`\]: IDs des salons en mode Foire à la saucisse.
        self.in_fals = []
        #: :class:`dict`\[:class:`int` (:attr:`.bdd.Taches.id`), :class:`asyncio.TimerHandle`]): Tâches planifiées actuellement en attente.
        self.tasks = {}

        # Checks et système de blocage
        self.add_check(already_in_command)

        self.before_invoke(add_to_in_command)
        self.after_invoke(remove_from_in_command)

        # Chargement des commandes (définies dans les fichiers annexes, un cog par fichier dans features)
        self.add_cog(informations.Informations(self))            # Information du joueur
        self.add_cog(voter_agir.VoterAgir(self))                 # Voter ou agir
        self.add_cog(actions_publiques.ActionsPubliques(self))   # Haros et candidatures
        self.add_cog(IA.GestionIA(self))                         # Ajout, liste, modification des règles d'IA
        self.add_cog(open_close.OpenClose(self))                 # Ouverture/fermeture votes/actions (appel par webhook)
        self.add_cog(sync.Sync(self))                            # Synchronisation depuis GSheets
        self.add_cog(taches.GestionTaches(self))                 # Tâches planifiées
        self.add_cog(communication.Communication(self))          # Envoi de messages et embeds
        self.add_cog(annexe.Annexe(self))                        # Ouils divers et plus ou moins inutiles

        self.remove_command("help")
        self.add_cog(Special(self))         # Commandes spéciales, méta-commandes...


    # Réactions aux différents évènements
    async def on_ready(self):
        await _on_ready(self)
    on_ready.__doc__ = _on_ready.__doc__

    async def on_member_join(self, member):
        await _on_member_join(self, member)
    on_member_join.__doc__ = _on_member_join.__doc__

    async def on_member_remove(self, member):
        await _on_member_remove(self, member)
    on_member_remove.__doc__ = _on_member_remove.__doc__

    async def on_message(self, message):
        await _on_message(self, message)
    on_message.__doc__ = _on_message.__doc__

    async def on_raw_reaction_add(self, payload):
        await _on_raw_reaction_add(self, payload)
    on_raw_reaction_add.__doc__ = _on_raw_reaction_add.__doc__


    # Gestion des erreurs
    async def on_command_error(self, ctx, exc):
        await _on_command_error(self, ctx, exc)
    on_command_error.__doc__ = _on_command_error.__doc__

    async def on_error(self, event, *args, **kwargs):
        await _on_error(self, event, *args, **kwargs)
    on_error.__doc__ = _on_error.__doc__


    # Système de vérification de vie
    def i_am_alive(self, filename="alive.log"):
        """Exporte le temps actuel (UTC) et planifie un nouvel appel dans 60s

        Args:
            filename (:class:`str`): fichier où exporter le temps actuel
        """
        with open(filename, "w") as f:
            f.write(str(time.time()))
        self.loop.call_later(60, self.i_am_alive, filename)


    # Lancement du bot
    def run(self, *args, **kwargs):
        """Prépare puis lance le bot (bloquant).

        Récupère les informations de connection, établit la connection à la base de données puis lance le bot.

        Args:
            *args, \**kwargs: Passés à :meth:`discord.ext.commands.Bot.run`.
        """
        # Récupération du token du bot et de l'ID du serveur
        LGREZ_DISCORD_TOKEN = env.load("LGREZ_DISCORD_TOKEN")
        self.GUILD_ID = int(env.load("LGREZ_SERVER_ID"))

        # Connection BDD
        bdd.connect()

        # Lancement du bot
        super().run(LGREZ_DISCORD_TOKEN, *args, **kwargs)
