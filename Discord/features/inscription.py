from discord.ext import commands
import tools
from bdd_connect import db, cache_TDB

@bot.event
async def main(bot, member):
    for chan in member.guild.channels:
        if chan.topic == f"{member.id}":
            await member.dm_channel.send(f"Tu as déjà un channel à ton nom, {member.name}")
            return

    chan = await guild.create_text_channel(f"perso-{member.name}", category = "CONVERSATION BOT", topic=f"{member.id}") #Crée le channel "perso-nom" avec le topic "member.id"

    await chan.set_permissions(member, read_messages = True, write_messages=True)

    chan.send(f"yousk2 {member.name}")
