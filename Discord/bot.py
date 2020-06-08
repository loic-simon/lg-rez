import os
import asyncio
import logging
import traceback
import datetime
import copy

import discord
from discord.ext import commands
from dotenv import load_dotenv

import blocs
import tools
from bdd_connect import db, Tables
from features import annexe, IA, inscription, informations, sync, open_close, voter_agir, remplissage_bdd


logging.basicConfig(level=logging.WARNING)

# Récupération du token du bot et de l'ID du serveur
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))


# Création du bot
COMMAND_PREFIX = "!"
class SuperBot(commands.Bot):
    def __init__(self, **kwargs):
        commands.Bot.__init__(self, **kwargs)
        self.in_command = []        # IDs des joueurs dans une commande
        self.in_stfu = []           # IDs des salons en mode STFU (IA off)

bot = SuperBot(command_prefix=COMMAND_PREFIX, description="Bonjour")

@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None


@bot.check
async def already_in_command(ctx):
    return (ctx.author.id not in ctx.bot.in_command
            or ctx.command.name in ["help", "stop"])    # Cas particulier : !stop

@bot.before_invoke      # Appelé seulement si les checks sont OK, donc pas déjà dans bot.in_command
async def add_to_in_command(ctx):
    if ctx.command.name != "stop":
        ctx.bot.in_command.append(ctx.author.id)

@bot.after_invoke
async def remove_from_in_command(ctx):
    if ctx.command.name != "stop":
        ctx.bot.in_command.remove(ctx.author.id)


# Trigger au démarrage du bot
@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    guild = bot.get_guild(GUILD_ID)
    print(f"{bot.user} connecté au serveur « {guild.name} » (id : {guild.id})\n")
    print(f"Guild Members:\n - " + "\n - ".join([member.name for member in guild.members]))
    print(f"\nChannels:\n - " + "\n - ".join([channel.name for channel in guild.text_channels]))
    
    await tools.log(guild, "Juste rebooted!")


# Trigger à l'arrivée d'un membre sur le serveur, crée un channel à son nom
@bot.event
async def on_member_join(member):
    await inscription.main(bot,member)


# Trigger à chaque message
@bot.event
async def on_message(message):
    if message.author == bot.user:          # Sécurité pour éviter les boucles infinies
        return

    ctx = await bot.get_context(message)
    await bot.invoke(ctx)                   # On trigger toutes les commandes

    if (not message.content.startswith(COMMAND_PREFIX)      # Si pas une commande
        and message.channel.name.startswith("conv-bot")     # et dans un channel de conversation bot
        and message.author.id not in bot.in_command         # et pas déjà dans une commande (vote...)
        and message.channel.id not in bot.in_stfu):         # et le channel est pas en stfu_mode

        await IA.main(ctx)


# Trigger à chaque réaction ajoutée
@bot.event
async def on_raw_reaction_add(payload):
    reactor = payload.member
    if reactor == bot.user or reactor.id in bot.in_command:         # Boucles infinies + gens dans une commande
        return

    if payload.emoji == tools.emoji(reactor, "volatron"):
        await reactor.guild.get_channel(payload.channel_id).send(f"{reactor.mention}, GET VOLATRONED !!!")
        
    elif payload.emoji == tools.emoji(reactor, "bucher"):
        ctx = await tools.create_context(bot, payload.message_id, reactor, "!vote")
        await ctx.send(f"""{payload.emoji} > {tools.bold("Vote pour le condamné du jour :")}""")
        await bot.invoke(ctx)       # On trigger !vote
        
    elif payload.emoji == tools.emoji(reactor, "maire"):
        ctx = await tools.create_context(bot, payload.message_id, reactor, "!votemaire")
        await ctx.send(f"""{payload.emoji} > {tools.bold("Vote pour le nouveau maire :")}""")
        await bot.invoke(ctx)       # On trigger !vote
        
    elif payload.emoji == tools.emoji(reactor, "lune"):
        ctx = await tools.create_context(bot, payload.message_id, reactor, "!voteloups")
        await ctx.send(f"""{payload.emoji} > {tools.bold("Vote pour la victime des loups :")}""")
        await bot.invoke(ctx)       # On trigger !vote
        

# Commandes définies dans les fichiers annexes !
#   (un cog par fichier dans features, sauf IA.py)

# Commandes MJ / bot
bot.add_cog(annexe.Annexe(bot))                     # Tests divers et inutiles
bot.add_cog(sync.Sync(bot))                         # Synchronisation TDB (appel par webhook)
bot.add_cog(open_close.OpenClose(bot))              # Ouverture/fermeture votes/actions (appel par webhook)
bot.add_cog(remplissage_bdd.RemplissageBDD(bot))    # Drop et remplissage table de données
bot.add_cog(IA.GestionIA(bot))

# Commandes joueurs
bot.add_cog(informations.Informations(bot))         # Information du joueur
bot.add_cog(voter_agir.VoterAgir(bot))              # Voter ou agir


# Commandes spéciales
class Special(commands.Cog):
    """Special - Commandes spéciales (méta-commandes, imitant ou impactant le déroulement des autres)"""

    @commands.command()
    @commands.has_role("MJ")
    async def do(self, ctx, *, txt):
        """Exécute du code Python et affiche le résultat (COMMANDE MJ)
        
        <txt> doit être du code valide dans le contexte du fichier bot.py (utilisables notemment : bot, ctx, db, Tables...)
        Si <txt> est une coroutine, elle sera awaited.
        
        Aussi connue sous le nom de « faille de sécurité », cette commande permet de faire environ tout ce qu'on veut sur le bot (y compris le crasher, importer des modules, exécuter des fichiers .py... même si c'est un peu compliqué) voire d'impacter le serveur sur lequel le bot tourne si on est motivé.
        
        À utiliser avec parcimonie donc, et QUE pour du développement/debug !
        """
        class Answer():
            def __init__(self):
                self.rep = ""
        a = Answer()
        exec(f"a.rep = {txt}", globals(), locals())
        if asyncio.iscoroutine(a.rep):
            a.rep = await a.rep
        await ctx.send(f"Entrée : {tools.code(txt)}\nSortie :\n{a.rep}")


    @commands.command()
    @commands.has_role("MJ")
    async def co(self, ctx, cible=None):
        """Lance la procédure d'inscription comme si on se connectait au serveur pour la première fois (COMMANDE MJ)
        
        [cible] le joueur à inscrire, par défaut le lançeur de la commande.
        Cette commande est principalement destinée aux tests de développement, mais peut être utile si un joueur chibre son inscription (nomamment en association avec !doas).
        """
        if id := ''.join([c for c in cible if c.isdigit()]):   # Si la chaîne contient un nombre, on l'extrait
            if ctx.guild.get_member(int(id)):                   # Si cet ID correspond à un utilisateur, on le récupère
                return [(user, 1)]                              # On a trouvé l'utilisateur !
        await inscription.main(bot, ctx.author)
        
        
    @commands.command()
    @commands.has_role("MJ")
    async def doas(self, ctx, *, qui_quoi):
        """Exécute une commande en tant qu'un autre joueur (COMMANDE MJ)
        
        <qui_quoi> doit être le nom de la cible (nom ou mention d'un joueur INSCRIT) suivi de la commande à exécuter (commençant par un !).
        
        Ex. !doas Vincent Croquette !vote Annie Colin
        """
        qui, quoi = qui_quoi.split(" " + bot.command_prefix, maxsplit=1)       # !doas <@!id> !vote R ==> qui = "<@!id>", quoi = "vote R"
        joueur = await tools.boucle_query_joueur(ctx, qui.strip() or None, Tables["Joueurs"])
        
        ctx.message.content = bot.command_prefix + quoi
        ctx.message.author = ctx.guild.get_member(joueur.discord_id)
        
        ctx.send(f":robot: Exécution en tant que {joueur.nom}:")
        await ctx.bot.process_commands(ctx.message)
        
        
    @commands.command()
    @commands.has_role("MJ")
    async def doin(self, ctx, *, apres_quoi):
        """Exécute une commande après X secondes (COMMANDE MJ)
        
        <apres_quoi> doit être un entier ou un flottant (nombre de secondes à attendre) suivi de la commande à exécuter (commençant par un !)
        
        Pas sûr de l'utilité de cette commande, mais bon elle existe
        """
        apres, quoi = apres_quoi.split(" ", maxsplit=1)      # !doin 15 !vote R ==> apres = "15", quoi = "!vote R"
        
        await asyncio.sleep(float(apres))
        ctx.message.content = quoi
        
        await remove_from_in_command(ctx)       # Bypass la limitation de 1 commande à la fois
        await ctx.bot.process_commands(ctx.message)
        await add_to_in_command(ctx)
        
        
    @commands.command(aliases=["autodestruct", "ad"])
    @commands.has_role("MJ")
    async def secret(self, ctx, *, quoi):
        """Supprime le message puis exécute la commande (COMMANDE MJ)
        
        <quoi> commande à exécuter, commençant par un !
        
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
        """Peut débloquer des situations compliquées
        
        Ne pas utiliser cette commande sauf en cas de force majeure où plus rien ne marche, et sur demande d'un MJ (après c'est pas dit que ça marche mieux après l'avoir utilisé)
        """
        if ctx.author.id in bot.in_command:
            bot.in_command.remove(ctx.author.id)
        ctx.send("Te voilà libre, camarade !")


    # Gestion de l'aide    
    bot.remove_command("help")
    
    @commands.command()
    async def help(self, ctx, *, command=None):
        """Affiche la liste des commandes utilisables et leur utilisation
        
        [command] : nom exact d'une commande à expliquer (ou un de ses alias)
        Si [command] n'est pas précisé, liste l'ensemble des commandes accessibles à l'utilisateur.
        """
        # hc = commands.DefaultLaHelpCommand()
        # setattr(hc, "context", ctx)
        # await hc.command_callback(ctx, command=command)
        
        pref = bot.command_prefix
        
        cogs = bot.cogs                                                                     # Dictionnaire nom: cog
        commandes = {cmd.name: cmd for cmd in bot.commands}                                 # Dictionnaire nom: commande
        aliases = {alias: nom for nom, cmd in commandes.items() for alias in cmd.aliases}    # Dictionnaire alias: nom de la commande
        
        n_max = max([len(cmd) for cmd in commandes])
        
        if not command:
            bot.in_command.remove(ctx.author.id)
            async def runnable_commands(cog):       # obligé parce que can_run doit être await, donc c'est compliqué
                L = []
                for cmd in cog.get_commands():
                    try:
                        runnable = await cmd.can_run(ctx)
                    except Exception:
                        runnable = False
                    if runnable:
                        L.append(cmd)
                return L
                
            r = f"""{bot.description}\n\n"""
            r += "\n\n".join([f"{cog.description} : \n  - " + "\n  - ".join(
                    [pref + cmd.name.ljust(n_max+2) + cmd.short_doc for cmd in runnables]           # pour chaque commande runnable
                ) for cog in cogs.values() if (runnables := await runnable_commands(cog))])         # pour chaque cog contenant des runnables
            r += f"\n\nUtilise <{pref}help command> pour plus d'information sur une commande."
            bot.in_command.append(ctx.author.id)
            
        else:
            if command.startswith(pref):        # Si le joueur fait !help !command
                command = command.lstrip(pref)
                
            if command in aliases:              # Si !help d'un alias
                command = aliases[command]      # On remplace l'alias par sa commande
                
            if command in commandes:             # Si commande existante
                cmd = commandes[command]
                
                r = f"{pref}{command} {cmd.signature} – {cmd.help}"
                # r += f"\n\nUtilise <{pref}help> pour la liste des commandes ou <{pref}help command> pour plus d'information sur une commande."
                if cmd_aliases := [alias for alias,cmd in aliases.items() if cmd == command]:       # Si la commande a des alias
                    r += f"\n\nAlias : {pref}" + ", {pref}".join(cmd_aliases)
                    
            else:
                r = f"Commande <{command}> non trouvée.\nUtilise <{pref}help> pour la liste des commandes."
                
        [await ctx.send(tools.code_bloc(m)) for m in tools.smooth_split(r, sep="\n\n")]
        

bot.add_cog(Special(bot))


# Gestion des erreurs

@bot.event
async def on_command_error(ctx, exc):
    db.session.rollback()       # Dans le doute, on vide la session SQL
    if isinstance(exc, commands.CommandInvokeError) and isinstance(exc.original, RuntimeError):     # STOP envoyé
        await ctx.send(f"Mission aborted.")
    else:
        await ctx.send(f"<CommandError> {type(exc).__name__}: {str(exc)}")

@bot.event
async def on_error(event, *args, **kwargs):
    db.session.rollback()       # Dans le doute, on vide la session SQL
    guild = bot.get_guild(GUILD_ID)
    await tools.log(guild, (
        f"{tools.role(guild, 'MJ').mention} ALED : Exception Python !"
        f"{tools.code_bloc(traceback.format_exc())}"
    ))
    raise        # On remonte l'exception à Python


# Exécute le tout (bloquant, rien n'est exécuté après)
bot.run(TOKEN)
