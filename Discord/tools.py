import discord.utils
import discord.ext.commands


# Récupération rapide

get = discord.utils.get

def channel(arg, nom):      # Renvoie le channel #nom. arg peut être de type Context, Guild, User/Member, Channel
    if hasattr(arg, "channels"):
        return get(arg.channels, name=nom)
    elif hasattr(arg, "guild"):
        return get(arg.guild.channels, name=nom)
    else:
        return TypeError("tools.channel : Impossible de remonter aux channels depuis l'argument trasmis")

def role(arg, nom):         # Renvoie le rôle nom. arg peut être de type Context, Guild, User/Member, Channel
    if hasattr(arg, "roles"):
        return get(arg.roles, name=nom)
    elif hasattr(arg, "guild"):
        return get(arg.guild.roles, name=nom)
    else:
        return TypeError("tools.role : Impossible de remonter aux rôles depuis l'argument trasmis")

def member(arg, nom):       # Renvoie le membre @member. arg peut être de type Context, Guild, User/Member, Channel
    if hasattr(arg, "members"):
        return get(arg.members, display_name=nom)
    elif hasattr(arg, "guild"):
        return get(arg.guild.members, display_name=nom)
    else:
        return TypeError("tools.member : Impossible de remonter aux membres depuis l'argument trasmis")


# Log dans #logs

async def log(arg, message):
    await channel(arg, "logs").send(message)


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
