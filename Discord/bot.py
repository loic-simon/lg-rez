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
from features import annexe, IA, inscription, informations, sync, open_close, voter_agir, remplissage_bdd, taches


logging.basicConfig(level=logging.WARNING)


### 1 - Récupération du token du bot et de l'ID du serveur
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))


### 2 - Création du bot
COMMAND_PREFIX = "!"
class SuperBot(commands.Bot):
    def __init__(self, **kwargs):
        commands.Bot.__init__(self, **kwargs)
        self.in_command = []        # IDs des joueurs dans une commande
        self.in_stfu = []           # IDs des salons en mode STFU (IA off)
        self.tasks = {}             # Dictionnaire des tâches en attente (id: TimerHandle)

bot = SuperBot(command_prefix=COMMAND_PREFIX,
               description="LG-bot – Plateforme pour parties endiablées de Loup-Garou",
)


### 3 - Checks et système de blocage
class AlreadyInCommand(commands.CheckFailure):
    pass

@bot.check
async def already_in_command(ctx):
    if (ctx.author.id in ctx.bot.in_command and ctx.command.name != "stop"):    # Cas particulier : !stop
        raise AlreadyInCommand()
    else:
        return True

@bot.before_invoke      # Appelé seulement si les checks sont OK, donc pas déjà dans bot.in_command
async def add_to_in_command(ctx):
    if ctx.command.name != "stop" and not ctx.message.webhook_id:
        ctx.bot.in_command.append(ctx.author.id)

@bot.after_invoke
async def remove_from_in_command(ctx):
    if ctx.command.name != "stop" and not ctx.message.webhook_id:
        ctx.bot.in_command.remove(ctx.author.id)


### 4 - Réactions aux différents évènements

# Au démarrage du bot
@bot.event
async def on_ready():
    guild = bot.get_guild(GUILD_ID)
    print(f"{bot.user} connecté au serveur « {guild.name} » (id : {guild.id})\n")
    print(f"Guild Members: " + " - ".join([member.display_name for member in guild.members]))
    print(f"\nChannels: " + " - ".join([channel.name for channel in guild.text_channels]))
    
    await tools.log(guild, "Juste rebooted!")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="vos demandes (!help)"))
    
    # Tâches planifiées
    now = datetime.datetime.now()
    r = ""
    
    for tache in Tables["Taches"].query.all():
        delta = (tache.timestamp - now).total_seconds()
        TH = bot.loop.call_later(delta, taches.execute, tache)  # Si delta < 0 (action manquée), l'exécute immédiatement, sinon attend jusqu'à tache.timestamp
        bot.tasks[tache.id] = TH
        r += f"Récupération de la tâche {tools.code(tache.timestamp.strftime('%d/%m/%Y %H:%M:%S'))} > {tools.code(tache.commande)}\n"
    
    if r:
        await tools.log(guild, r)
    

# À l'arrivée d'un membre sur le serveur
@bot.event
async def on_member_join(member):
    await inscription.main(bot,member)


# À chaque message
@bot.event
async def on_message(message):
    if message.author == bot.user:          # Sécurité pour éviter les boucles infinies
        return
    if not message.guild:                   # Message privé
        await message.channel.send("Je n'accepte pas les messages privés, désolé !")
        return

    await bot.invoke(await bot.get_context(message))        # On trigger toutes les commandes 
    # (ne PAS remplacer par bot.process_commands(message), en théorie c'est la même chose mais ça détecte pas les webhooks...)
    
    if (not message.content.startswith(bot.command_prefix)  # Si pas une commande
        and message.channel.name.startswith("conv-bot")     # et dans un channel de conversation bot
        and message.author.id not in bot.in_command         # et pas déjà dans une commande (vote...)
        and message.channel.id not in bot.in_stfu):         # et le channel est pas en mode STFU
        
        await IA.process_IA(bot, message)                       # On trigger les règles d'IA


# À chaque réaction ajoutée
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
        await bot.invoke(ctx)       # On trigger !votemaire
        
    elif payload.emoji == tools.emoji(reactor, "lune"):
        ctx = await tools.create_context(bot, payload.message_id, reactor, "!voteloups")
        await ctx.send(f"""{payload.emoji} > {tools.bold("Vote pour la victime des loups :")}""")
        await bot.invoke(ctx)       # On trigger !voteloups
        

### 5 - Commandes (définies dans les fichiers annexes, un cog par fichier dans features)

# Commandes MJ / bot
bot.add_cog(sync.Sync(bot))                         # Synchronisation TDB (appel par webhook)
bot.add_cog(open_close.OpenClose(bot))              # Ouverture/fermeture votes/actions (appel par webhook)
bot.add_cog(remplissage_bdd.RemplissageBDD(bot))    # Drop et remplissage table de données
bot.add_cog(IA.GestionIA(bot))                      # Ajout, liste, modification des règles d'IA
bot.add_cog(taches.GestionTaches(bot))              # Tâches planifiées

# Commandes joueurs
bot.add_cog(annexe.Annexe(bot))                     # Ouils divers et plus ou moins inutiles
bot.add_cog(informations.Informations(bot))         # Information du joueur
bot.add_cog(voter_agir.VoterAgir(bot))              # Voter ou agir


### 6 - Commandes spéciales
class Special(commands.Cog):
    """Special - Commandes spéciales (méta-commandes, imitant ou impactant le déroulement des autres)"""

    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def do(self, ctx, *, code):
        """Exécute du code Python et affiche le résultat (COMMANDE MJ)
        
        <code> doit être du code valide dans le contexte du fichier bot.py (utilisables notemment : bot, ctx, db, Tables...)
        Si <code> est une coroutine, elle sera awaited (ne pas inclure "await" dans <code>).
        
        Aussi connue sous le nom de « faille de sécurité », cette commande permet de faire environ tout ce qu'on veut sur le bot (y compris le crasher, importer des modules, exécuter des fichiers .py... même si c'est un peu compliqué) voire d'impacter le serveur sur lequel le bot tourne si on est motivé.
        
        À utiliser avec parcimonie donc, et QUE pour du développement/debug !
        """
        class Answer():
            def __init__(self):
                self.rep = ""
        a = Answer()
        exec(f"a.rep = {code}", globals(), locals())
        if asyncio.iscoroutine(a.rep):
            a.rep = await a.rep
        await ctx.send(f"Entrée : {tools.code(code)}\nSortie :\n{a.rep}")


    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def co(self, ctx, cible=None):
        """Lance la procédure d'inscription comme si on se connectait au serveur pour la première fois (COMMANDE MJ)
        
        [cible] la MENTION (@joueur) du joueur à inscrire, par défaut le lançeur de la commande.
        Cette commande est principalement destinée aux tests de développement, mais peut être utile si un joueur chibre son inscription (à utiliser dans son channel, ou #bienvenue (avec !autodestruct) si même le début a chibré).
        """
        if cible:
            id = ''.join([c for c in cible if c.isdigit()])         # Si la chaîne contient un nombre, on l'extrait
            if id and ctx.guild.get_member(int(id)):                # Si c'est un ID d'un membre du serveur
                joueur = ctx.guild.get_member(int(id))
            else:
                await ctx.send("Cible introuvable.")
                return
        else:
            joueur = ctx.author
            
        await inscription.main(bot, joueur)
        
        
    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def doas(self, ctx, *, qui_quoi):
        """Exécute une commande en tant qu'un autre joueur (COMMANDE MJ)
        
        <qui_quoi> doit être le nom de la cible (nom ou mention d'un joueur INSCRIT) suivi de la commande à exécuter (commençant par un !).
        
        Ex. !doas Vincent Croquette !vote Annie Colin
        """
        qui, quoi = qui_quoi.split(" " + bot.command_prefix, maxsplit=1)       # !doas <@!id> !vote R ==> qui = "<@!id>", quoi = "vote R"
        joueur = await tools.boucle_query_joueur(ctx, qui.strip() or None, Tables["Joueurs"])
        
        ctx.message.content = bot.command_prefix + quoi
        ctx.message.author = ctx.guild.get_member(joueur.discord_id)
        
        await ctx.send(f":robot: Exécution en tant que {joueur.nom} :")
        await ctx.bot.process_commands(ctx.message)
        
        
    @commands.command(aliases=["autodestruct", "ad"])
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
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


    ### 6 bis - Gestion de l'aide    
    bot.remove_command("help")
    
    @commands.command()
    async def help(self, ctx, *, command=None):
        """Affiche la liste des commandes utilisables et leur utilisation
        
        [command] : nom exact d'une commande à expliquer (ou un de ses alias)
        Si [command] n'est pas précisé, liste l'ensemble des commandes accessibles à l'utilisateur.
        """
        
        pref = bot.command_prefix
        cogs = bot.cogs                                                                     # Dictionnaire nom: cog
        commandes = {cmd.name: cmd for cmd in bot.commands}                                 # Dictionnaire nom: commande
        aliases = {alias: nom for nom, cmd in commandes.items() for alias in cmd.aliases}   # Dictionnaire alias: nom de la commande
        
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
                
                r = f"{pref}{command} {cmd.signature} – {cmd.help}\n"
                # r += f"\n\nUtilise <{pref}help> pour la liste des commandes ou <{pref}help command> pour plus d'information sur une commande."
                if cmd_aliases := [alias for alias,cmd in aliases.items() if cmd == command]:       # Si la commande a des alias
                    r += f"\nAlias : {pref}" + f", {pref}".join(cmd_aliases)
                    
            else:
                r = f"Commande <{command}> non trouvée.\nUtilise <{pref}help> pour la liste des commandes."
                     
        r += "\nSi besoin, n'hésite pas à appeler un MJ en les mentionnant (@MJ)."
        [await ctx.send(tools.code_bloc(m)) for m in tools.smooth_split(r, sep="\n\n")]
        

bot.add_cog(Special(bot))


### 7 - Gestion des erreurs
@bot.event
async def on_command_error(ctx, exc):
    db.session.rollback()       # Dans le doute, on vide la session SQL
    if isinstance(exc, commands.CommandInvokeError) and isinstance(exc.original, RuntimeError):     # STOP envoyé
        await ctx.send("Mission aborted.")
    
    elif isinstance(exc, commands.CommandInvokeError):
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
    
    elif isinstance(exc, commands.MissingRole) or isinstance(exc, commands.CheckAnyFailure):
        await ctx.send("Hé ho toi, cette commande est réservée aux MJs !  :angry:")
    
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
@bot.event
async def on_error(event, *args, **kwargs):
    db.session.rollback()       # Dans le doute, on vide la session SQL
    guild = bot.get_guild(GUILD_ID)
    await tools.log(guild, (
        f"{tools.role(guild, 'MJ').mention} ALED : Exception Python !"
        f"{tools.code_bloc(traceback.format_exc())}"
    ))
    raise        # On remonte l'exception à Python


### 8 - Exécute le tout (bloquant, rien n'est exécuté après)
bot.run(TOKEN)
# try:
#     bot.loop.run_until_complete(bot.start(TOKEN))
# except KeyboardInterrupt:
#     bot.loop.run_until_complete(bot.logout())
#     # cancel all tasks lingering
# finally:
#     bot.loop.close()
