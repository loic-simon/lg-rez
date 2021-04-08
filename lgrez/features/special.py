"""lg-rez / features / Commandes spéciales

Commandes spéciales (méta-commandes, imitant ou impactant le
déroulement des autres ou le fonctionnement du bot)

"""

import asyncio
import re
import sys

# Unused imports because useful for !do / !shell globals
import discord
from discord.ext import commands

from lgrez import __version__, config, features, blocs, bdd
from lgrez.blocs import tools, realshell, one_command
from lgrez.bdd import *       # toutes les tables dans globals()


async def _filter_runnables(commands, ctx):
    """Retourne les commandes pouvant run parmis commands"""
    runnables = []
    with one_command.bypass(ctx):
        # On désactive la limitation de une commande simultanée
        # sinon can_run renvoie toujours False
        for cmd in commands:
            try:
                runnable = await cmd.can_run(ctx)
            except Exception:
                runnable = False
            if runnable:
                runnables.append(cmd)
    return runnables


class Special(commands.Cog):
    """Commandes spéciales (méta-commandes et expérimentations)"""

    @one_command.do_not_limit
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
            code: instructions valides dans le contexte du LGbot
                (utilisables notemment : ``ctx``, ``config``, ``blocs``,
                ``features``, ``bdd``, ``<table>``...)

        Si ``code`` est une coroutine, elle sera awaited
        (ne pas inclure ``await`` dans ``code``).

        Aussi connue sous le nom de « faille de sécurité », cette
        commande permet de faire environ tout ce qu'on veut sur le bot
        (y compris le crasher, importer des modules, exécuter des
        fichiers .py... même si c'est un peu compliqué) voire d'impacter
        le serveur sur lequel le bot tourne si on est motivé.

        À utiliser avec parcimonie donc, et QUE pour du
        développement/debug !
        """
        class Answer:
            rep = None
        _a = Answer()

        locs = globals()
        locs["ctx"] = ctx
        locs["_a"] = _a
        exec(f"_a.rep = {code}", locs)
        if asyncio.iscoroutine(_a.rep):
            _a.rep = await _a.rep
        await tools.send_code_blocs(ctx, str(_a.rep))


    @commands.command()
    @tools.mjs_only
    async def shell(self, ctx):
        """Lance un terminal Python directement dans Discord (COMMANDE MJ)

        Envoyer ``help`` dans le pseudo-terminal pour plus
        d'informations sur son fonctionnement.

        Évidemment, les avertissements dans ``!do`` s'appliquent ici :
        ne pas faire n'imp avec cette commande !! (même si ça peut être
        très utile, genre pour ajouter des gens en masse à un channel)
        """
        locs = globals()
        locs["ctx"] = ctx
        shell = realshell.RealShell(ctx.channel, locs)
        try:
            await shell.interact()
        except realshell.RealShellExit as exc:
            raise tools.CommandExit(*exc.args or ["!shell: Forced to end."])


    @commands.command()
    @tools.mjs_only
    async def co(self, ctx, cible=None):
        """Lance la procédure d'inscription pour un membre (COMMANDE MJ)

        Fat comme si on se connectait au serveur pour la première fois.

        Args:
            cible: le nom exact ou la mention (``@joueur``) du joueur
                à inscrire, par défaut le lançeur de la commande.

        Cette commande est principalement destinée aux tests de
        développement, mais peut être utile si un joueur chibre son
        inscription (à utiliser dans son channel, ou ``#bienvenue``
        (avec ``!autodestruct``) si même le début a chibré).
        """
        if cible:
            try:
                member = tools.member(cible)
            except ValueError:
                await ctx.send("Cible introuvable.")
                return
        else:
            member = ctx.author

        await features.inscription.main(member)


    @commands.command()
    @tools.mjs_only
    async def doas(self, ctx, *, qui_quoi):
        """Exécute une commande en tant qu'un autre joueur (COMMANDE MJ)

        Args:
            qui_quoi: nom de la cible (nom/mention d'un joueur INSCRIT)
                suivi de la commande à exécuter (commençant par un ``!``).

        Example:
            ``!doas Vincent Croquette !vote Annie Colin``
        """
        sep = " " + config.bot.command_prefix
        qui, _, quoi = qui_quoi.partition(sep)
        # !doas <@!id> !vote R ==> qui = "<@!id>", quoi = "vote R"
        if not quoi:
            raise commands.UserInputError(f"'{sep}' not found in qui_quoi")
        joueur = await tools.boucle_query_joueur(ctx, qui.strip())

        ctx.message.content = config.bot.command_prefix + quoi
        ctx.message.author = joueur.member

        await ctx.send(f":robot: Exécution en tant que {joueur.nom} :")
        with one_command.bypass(ctx):
            await config.bot.process_commands(ctx.message)


    @commands.command(aliases=["autodestruct", "ad"])
    @tools.mjs_only
    async def secret(self, ctx, *, quoi):
        """Supprime le message puis exécute la commande (COMMANDE MJ)

        Args:
            quoi: commande à exécuter, commençant par un ``!``

        Utile notemment pour faire des commandes dans un channel public,
        pour que la commande (moche) soit immédiatement supprimée.
        """
        await ctx.message.delete()

        ctx.message.content = quoi

        with one_command.bypass(ctx):
            await config.bot.process_commands(ctx.message)


    @one_command.do_not_limit
    @commands.command()
    @tools.private
    async def stop(self, ctx):
        """Peut débloquer des situations compliquées (beta)

        Ne pas utiliser cette commande sauf en cas de force majeure
        où plus rien ne marche, et sur demande d'un MJ (après c'est
        pas dit que ça marche mieux après l'avoir utilisée)
        """
        if ctx.channel.id in config.bot.in_command:
            config.bot.in_command.remove(ctx.channel.id)
        await ctx.send("Te voilà libre, camarade !")


    @commands.command(aliases=["aide", "aled", "oskour"])
    async def help(self, ctx, *, command=None):
        """Affiche la liste des commandes utilisables et leur utilisation

        Args:
            command (optionnel): nom exact d'une commande à expliquer
                (ou un de ses alias)

        Si ``command`` n'est pas précisée, liste l'ensemble des commandes
        accessibles à l'utilisateur.
        """
        pref = config.bot.command_prefix
        cogs = config.bot.cogs                  # Dictionnaire nom: cog
        commandes = {cmd.name: cmd for cmd in config.bot.commands}
        aliases = {alias: nom for nom, cmd in commandes.items()
                   for alias in cmd.aliases}
        # Dictionnaire alias: nom de la commande

        len_max = max(len(cmd) for cmd in commandes)

        def descr_command(cmd):
            return f"\n  - {pref}{cmd.name.ljust(len_max)}  {cmd.short_doc}"

        if not command:
            # Pas d'argument ==> liste toutes les commandes

            r = f"{config.bot.description} (v{__version__})"
            for cog in cogs.values():
                runnables = await _filter_runnables(cog.get_commands(), ctx)
                if not runnables:
                    # pas de runnables dans le cog, on passe
                    continue

                r += f"\n\n{type(cog).__name__} - {cog.description} :"
                for cmd in runnables:       # pour chaque commande runnable
                    r += descr_command(cmd)

            runnables_hors_cog = await _filter_runnables(
                (cmd for cmd in config.bot.commands if not cmd.cog), ctx
            )
            if runnables_hors_cog:
                r += "\n\nCommandes isolées :"
                for cmd in runnables_hors_cog:
                    r += descr_command(cmd)

            r += (f"\n\nUtilise <{pref}help command> pour "
                  "plus d'information sur une commande.")

        else:
            # Aide détaillée sur une commande
            if command.startswith(pref):
                # Si le joueur fait !help !command (ou !help ! command)
                command = command.lstrip(pref).strip()
            if command in aliases:
                # Si !help d'un alias
                command = aliases[command]

            if command in commandes:            # Si commande existante
                cmd = commandes[command]

                doc = cmd.help or ""
                doc = doc.replace("``", "`")
                doc = doc.replace("Args:", "Arguments :")
                doc = doc.replace("Warning:", "Avertissement :")
                doc = re.sub(r":\w+?:`[\.~!]*(.+?)`", r"`\1`", doc)
                # enlève les :class: et consors

                if isinstance(cmd, commands.Group):
                    r = (f"{pref}{command} <option> [args...] – {doc}\n\n"
                         "Options :\n")

                    scommands = sorted(cmd.commands, key=lambda cmd: cmd.name)
                    options = [f"{scmd.name} {scmd.signature}"
                               for scmd in scommands]
                    slen_max = max(len(opt) for opt in options)
                    r += "\n".join(f"    - {pref}{command} "
                                   f"{opt.ljust(slen_max)}  {scmd.short_doc}"
                                   for scmd, opt in zip(scommands, options))
                else:
                    r = f"{pref}{command} {cmd.signature} – {doc}"

                if cmd.aliases:         # Si la commande a des alias
                    r += f"\n\nAlias : {pref}" + f", {pref}".join(cmd.aliases)

            else:
                r = (f"Commande '{pref}{command}' non trouvée.\n"
                     f"Utilise '{pref}help' pour la liste des commandes.")

        r += ("\n\nSi besoin, n'hésite pas à appeler un MJ "
              "en les mentionnant (@MJ).")

        await tools.send_code_blocs(ctx, r, sep="\n\n")
        # On envoie, en séparant enntre les cogs de préférence


    @commands.command(aliases=["about", "copyright", "licence", "auteurs"])
    async def apropos(self, ctx):
        """Informations et mentions légales du projet

        N'hésitez-pas à nous contacter pour en savoir plus !
        """
        embed = discord.Embed(
            title=f"**LG-bot** - v{__version__}",
            description=config.bot.description
        ).set_author(
            name="À propos de ce bot :",
            icon_url=config.bot.user.avatar_url,
        ).set_image(
            url=("https://gist.githubusercontent.com/loic-simon/"
                 "66c726053323017dba67f85d942495ef/raw/"
                 "48f2607a61f3fc1b7285fd64873621035c6fbbdb/logo_espci.png"),
        ).add_field(
            name="Auteurs",
            value="Loïc Simon\nTom Lacoma",
            inline=True,
        ).add_field(
            name="Licence",
            value="Projet open-source sous licence MIT\n"
                  "https://opensource.org/licenses/MIT",
            inline=True,
        ).add_field(
            name="Pour en savoir plus :",
            value="https://github.com/loic-simon/lg-rez",
            inline=False,
        ).add_field(
            name="Copyright :",
            value=":copyright: 2021 Club BD-Jeux × GRIs – ESPCI Paris - PSL",
            inline=False,
        ).set_footer(
            text="Retrouvez-nous sur Discord : LaCarpe#1674, TaupeOrAfk#3218",
        )
        await ctx.send(embed=embed)
