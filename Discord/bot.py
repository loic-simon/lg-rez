import os
import asyncio
import logging
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv

import tools
import bdd_connect

from features import annexe, IA, inscription, informations, sync, open_close, remplissage_bdd


logging.basicConfig(level=logging.WARNING)

# Récupération du token du bot et de l'ID du serveur
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))


# Création du bot
COMMAND_PREFIX = "!"
bot = commands.Bot(command_prefix=COMMAND_PREFIX, description="Bonjour")

@bot.check
async def globally_block_dms(ctx):
    return ctx.guild is not None

#bot.add_check(commands.max_concurrency(1, per=commands.BucketType.user))

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

        if not message.content.startswith(COMMAND_PREFIX):      # Si pas une commande (+ conditions sur les channels ? à venir), on appelle l'IA
            rep = await IA.main(message.content)

            if rep:                     # Si l'IA a un truc à dire
                await message.channel.send(rep)
    except:
        await tools.log(message, (
            f"{tools.role(message, 'MJ').mention} ALED : Exception Python !"
            f"{tools.code_bloc(traceback.format_exc())}"
        ))


# Commandes définies dans les fichiers annexes !
#   (un cog par fichier dans features, sauf IA.py)

bot.add_cog(annexe.Annexe(bot))
bot.add_cog(informations.Informations(bot))
bot.add_cog(sync.Sync(bot))
bot.add_cog(open_close.OpenClose(bot))
bot.add_cog(remplissage_bdd.RemplissageBDD(bot))


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
@commands.max_concurrency(1, per=commands.BucketType.user)
async def co(ctx):
    """lance un test d'inscription comme si on se connectait au serv pour la première fois"""
    await inscription.main(bot, ctx.author)


# Trigger si erreur dans une commande
@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"{type(error).__name__}: {str(error)}")


# Exécute le tout (bloquant, rien n'est exécuté après)
bot.run(TOKEN)
