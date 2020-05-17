import discord.utils

# Analyse de l'entrée de la commande

def command_arg(ctx):        # sépare la commande en trois blocs ["!rename", "cible", "nom"]
    return ctx.message.content.split(maxsplit=1)[1]


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
    
def code_bloc(s, langage=None):
    return f"```{langage}\n{s}```"
    
def quote(s):
    return f"> {s}"
    
def quote_bloc(s):
    return f">>> {s}"
    
def spoiler(s):
    return f"||{s}||"
