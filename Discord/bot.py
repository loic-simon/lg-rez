import os
import asyncio
import logging
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv

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
        self.in_command = []       # Joueurs actuellement dans une commande
        self.in_stfu = []

bot = SuperBot(command_prefix=COMMAND_PREFIX, description="Bonjour")

@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None

#bot.add_check(commands.max_concurrency(1, per=commands.BucketType.user))

@bot.check
async def already_in_command(ctx):
    return ctx.author.id not in ctx.bot.in_command

@bot.before_invoke      # Appelé seulement si les checks sont OK, donc pas déjà dans bot.in_command
async def add_to_in_command(ctx):
    ctx.bot.in_command.append(ctx.author.id)

@bot.after_invoke
async def remove_from_in_command(ctx):
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

    try:
        ctx = await bot.get_context(message)
        await bot.invoke(ctx)                   # On trigger toutes les commandes

        if (not message.content.startswith(COMMAND_PREFIX)      # Si pas une commande
            and message.channel.name.startswith("conv-bot")     # et dans un channel de conversation bot
            and message.author.id not in bot.in_command         # et pas déjà dans une commande (vote...)
            and message.channel.id not in bot.in_stfu):         # et le channel est mas en stfu_mode

            await IA.main(message)

    except Exception:
        await tools.log(message, (
            f"{tools.role(message, 'MJ').mention} ALED : Exception Python !"
            f"{tools.code_bloc(traceback.format_exc())}"
        ))


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


@bot.command()
@commands.has_role("MJ")
async def do(ctx, *, txt):

    class Answer():
        def __init__(self):
            self.rep = ""
    a = Answer()

    exec(f"a.rep = {txt}", globals(), locals())
    if asyncio.iscoroutine(a.rep):
        a.rep = await a.rep

    await ctx.send(f"Entrée : {tools.code(txt)}\nSortie :\n{a.rep}")


@bot.command()
@commands.has_role("MJ")
async def co(ctx):
    """lance un test d'inscription comme si on se connectait au serv pour la première fois"""
    await inscription.main(bot, ctx.author)

@bot.command()
@commands.has_role("MJ")
async def dropbot(ctx):
    """Vide les listes de SuperBot"""
    bot.in_command = []
    bot.in_stfu = []

# Trigger si erreur dans une commande
@bot.event
async def on_command_error(ctx, exc):
    db.session.rollback()       # Dans le doute, on vide la session SQL
    if isinstance(exc, commands.CommandInvokeError) and isinstance(exc.original, RuntimeError):
        await ctx.send(f"Mission aborted.")
    else:
        await ctx.send(f"<CommandError> {type(exc).__name__}: {str(exc)}")


# Exécute le tout (bloquant, rien n'est exécuté après)
bot.run(TOKEN)
