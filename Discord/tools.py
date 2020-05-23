from functools import wraps

import discord.utils
import discord.ext.commands

from bdd_connect import db, Tables


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


# Renvoie le channel privé d'un utilisateur

def private_chan(member):
    chan_id = Tables["Joueurs"].query.filter_by(discord_id=member.id).one()._chan_id
    return get(member.guild.channels, id=chan_id)


# DÉCORATEUR : supprime le message et exécute la commande dans la conv privée si elle a été appellée ailleurs
# (utilisable que dans un Cog, de toute façon tout devra être cogé à terme)

def private(cmd):

    @wraps(cmd)
    async def new_cmd(self, ctx, *args, **kwargs):              # Cette commande est renvoyée à la place de cmd
        if not ctx.channel.name.startswith("conv-bot-"):        # Si pas déjà dans une conv bot :
        # if not member.has_role("MJ") and not ctx.channel.name.beginswith("conv-bot-"):
            await ctx.message.delete()                          # On supprime le message,
            ctx.channel = private_chan(ctx, ctx.author)         # On remplace le chan dans le contexte d'appel par le chan privé,
            await ctx.send(f"{quote(ctx.message.content)}\n"    # On envoie un warning dans le chan privé,
                           f"{ctx.author.mention} :warning: Cette commande est interdite en dehors de ta conv privée ! :warning:\n"
                           f"J'ai supprimé ton message, et j'exécute la commande ici :")
        return await cmd(self, ctx, *args, **kwargs)            # Et on appelle cmd, avec le contexte modifié !

    return new_cmd



# Teste si le message contient un mot de la liste trigWords, les mots de trigWords doivent etre en minuscule

def checkTrig(m,trigWords):
    return m.content in trigWords

# Teste si user possède le role roles
def checkRole(member,nom : str):
    role = role(user, nom)
    return role in member.roles

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
