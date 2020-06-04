import os
import asyncio
import logging
import traceback

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
            or ctx.command.name == "stop")    # Cas particulier : !stop

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
    members = "\n - ".join([member.name for member in guild.members])
    print(f"Guild Members:\n - {members}")
    channels = "\n - ".join([channel.name for channel in guild.channels if isinstance(channel, discord.TextChannel)])
    print(f"\nChannels:\n - {channels}\n")


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

        await IA.main(message)



# Trigger à chaque réaction ajoutée
@bot.event
async def on_raw_reaction_add(payload):
    reactor = payload.member
    if reactor == bot.user:          # Sécurité pour éviter les boucles infinies
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
        


# Trigger à chaque réaction ajoutée
@bot.event
async def on_reaction_add(reaction, user):
    await reaction.message.send(f"{reaction.emoji}")




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
    """Special : Commandes spéciales (méta-commandes, imitant ou impactant le déroulement des autres)"""

    @commands.command()
    @commands.has_role("MJ")
    async def do(self, ctx, *, txt):
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
    async def co(self, ctx):
        """lance un test d'inscription comme si on se connectait au serv pour la première fois"""
        await inscription.main(bot, ctx.author)
        
    @commands.command()
    @commands.has_role("MJ")
    async def doas(self, ctx, *, txt):
        """Exécute une commande en tant qu'un autre joueur"""
        qui, quoi = txt.split(" " + ctx.bot.command_prefix, maxsplit=1)      # !doas <@!id> !vote R ==> qui = "<@!id>", quoi = "vote R"
        joueur = await tools.boucle_query_joueur(ctx, qui.strip() or None, Tables["Joueurs"])
        
        ctx.message.content = ctx.bot.command_prefix + quoi
        ctx.message.author = ctx.guild.get_member(joueur.discord_id)
        
        ctx.send(f":robot: Exécution en tant que {joueur.nom}:")
        ctx = await bot.get_context(ctx.message)
        await ctx.bot.invoke(ctx)

    @commands.command()
    @tools.private
    async def stop(self, ctx):
        """Débloque si faussement coincé dans une commande"""
        if ctx.author.id in bot.in_command:
            bot.in_command.remove(ctx.author.id)
        ctx.send("Te voilà libre, camarade !")

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
