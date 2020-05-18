import discord.utils
import discord.ext.commands


# Récupération rapide

get = discord.utils.get

def channel(ctx, nom):
    return get(ctx.guild.channels, name=nom)

def role(ctx, nom):
    return get(ctx.guild.roles, name=nom)

def member(ctx, nom):
    return get(ctx.guild.members, display_name=nom)


# Log dans #logs

async def log(ctx, message):
    await discord.utils.get(ctx.guild.channels, name="logs").send(message)


# Formattage de texte dans Discord

def bold(s):
    return f"**{s}**"
    
def ital(s):
    return f"*{s}*"
    
def soul(s):
    return f"__{s}__"
    
def strike(s):
    return f"~~{s}~~"

def code(s):
    return f"`{s}`"
    
def code_bloc(s, langage=""):
    return f"```{langage}\n{s}```"
    
def quote(s):
    return f"> {s}"
    
def quote_bloc(s):
    return f">>> {s}"
    
def spoiler(s):
    return f"||{s}||"
