from discord.ext import commands
import tools
from bdd_connect import db, cache_TDB

async def main(bot, member):
    if chan:=tools.get(member.guild.text_channels, topic=f"{member.id}"):
        await chan.send(f"Tu as déjà un channel à ton nom, {member.mention}")
        return

    print(f"{member.id}")

    chan = await member.guild.create_text_channel(f"conv-bot-{member.name}", category = tools.get(member.guild.channels, name="CONVERSATION BOT"), topic=f"{member.id}") #Crée le channel "perso-nom" avec le topic "member.id"

    await chan.set_permissions(member, read_messages = True, send_messages=True)

    await chan.send(f"yousk2 {member.mention}")
