import os
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

import tools
import bdd_connect

from features import annexe, IA, inscription


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
    await member.create_dm()
    await member.dm_channel.send(f"Hi {member.name}, welcome to my Discord server!")
    await inscription.main(bot,member)


# Trigger à chaque message
@bot.event
async def on_message(message):
    if message.author == bot.user:          # Sécurité pour éviter les boucles infinies
        return

    ctx = await bot.get_context(message)
    await bot.invoke(ctx)                   # On trigger toutes les commandes

    if not message.content.startswith(COMMAND_PREFIX):      # Si pas une commande (+ conditions sur les channels ? à venir), on appelle l'IA
        rep = await IA.main(message.content)

        if rep:                     # Si l'IA a un truc à dire
            await message.channel.send(rep)



# Commandes définies dans les fichiers annexes !
#   (un cog par fichier dans features, sauf IA.py)

bot.add_cog(annexe.Annexe(bot))



@bot.command()
@commands.has_role("MJ")
async def do(ctx, *, txt):

    class Answer():
        def __init__(self):
            self.rep = ""
    a = Answer()

    exec(f"a.rep = {txt}", globals(), locals())
    await ctx.send(f"Entrée : {tools.code(txt)}\nSortie :\n{a.rep}")


@bot.command()
@commands.has_role("MJ")
async def testInscription(ctx):
    await inscription.main(bot, ctx.author)


# Trigger si erreur dans une commande
@bot.event
async def on_command_error(ctx, error):
    await ctx.send(f"{type(error).__name__}: {str(error)}")


# Exécute le tout (bloquant, rien n'est exécuté après)
bot.run(TOKEN)
