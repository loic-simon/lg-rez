import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID"))

bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")

    guild = bot.get_guild(GUILD_ID)

    print(
        f"{bot.user} is connected to the following guild:\n"
        f"{guild.name} (id: {guild.id})\n"
    )

    members = "\n - ".join([member.name for member in guild.members])
    print(f"Guild Members:\n - {members}")

    channels = "\n - ".join([channel.name for channel in guild.channels if isinstance(channel, discord.TextChannel)])
    print(f"Channels:\n - {channels}")


@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
        f'Hi {member.name}, welcome to my Discord server!'
    )


@bot.event
async def on_message(message):
    if message.author == bot.user:           # Sécurité pour éviter les boucles infinies
        return

    if 'lange' in message.content.lower():
        response = "LE LANGE !!!!!"
        await message.channel.send(response)


bot.run(TOKEN)

print("salut")
