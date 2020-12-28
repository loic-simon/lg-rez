"""lg-rez / features / Commandes spéciales

Commandes spéciales (méta-commandes, imitant ou impactant le déroulement des autres ou le fonctionnement du bot)

"""

import asyncio
import re
import sys

import discord
from discord.ext import commands

from lgrez import __version__, config, features, blocs
from lgrez.blocs import tools, realshell
from lgrez.blocs.bdd import *       # toutes les tables dans globals()



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
            code: instructions valides dans le contexte du fichier ``bot.py`` (utilisables notemment : ``ctx``, ``config.session``, ``tables``...)

        Si ``code`` est une coroutine, elle sera awaited (ne pas inclure ``await`` dans ``code``).

        Aussi connue sous le nom de « faille de sécurité », cette commande permet de faire environ tout ce qu'on veut sur le bot (y compris le crasher, importer des modules, exécuter des fichiers .py... même si c'est un peu compliqué) voire d'impacter le serveur sur lequel le bot tourne si on est motivé.

        À utiliser avec parcimonie donc, et QUE pour du développement/debug !
        """
        class Answer():
            rep = None
        a = Answer()

        locs = globals()
        locs["ctx"] = ctx
        exec(f"a.rep = {code}", locs)
        if asyncio.iscoroutine(a.rep):
            a.rep = await a.rep
        await ctx.send(tools.code_bloc(a.rep))


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
            id = ''.join(c for c in cible if c.isdigit())           # Si la chaîne contient un nombre, on l'extrait
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
        qui, _, quoi = qui_quoi.partition(" " + ctx.bot.command_prefix)         # !doas <@!id> !vote R ==> qui = "<@!id>", quoi = "vote R"
        joueur = await tools.boucle_query_joueur(ctx, qui.strip())

        ctx.message.content = ctx.bot.command_prefix + quoi
        ctx.message.author = joueur.member

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

            if command in commandes:            # Si commande existante
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
