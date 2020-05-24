from functools import wraps
import asyncio

import discord.utils
import discord.ext.commands

from bdd_connect import db, Tables


# Récupération rapide

get = discord.utils.get

def channel(arg, nom):      # Renvoie le channel #nom. arg peut être de type Context, Guild, User/Member, Channel
    if hasattr(arg, "banner"):      # méthode immonde pour détécter si c'est une Guild
        return get(arg.channels, name=nom)
    elif hasattr(arg, "guild"):
        return get(arg.guild.channels, name=nom)
    else:
        return TypeError("tools.channel : Impossible de remonter aux channels depuis l'argument trasmis")

def role(arg, nom):         # Renvoie le rôle nom. arg peut être de type Context, Guild, User/Member, Channel
    if hasattr(arg, "banner"):     # méthode immonde pour détécter si c'est une Guild
        return get(arg.roles, name=nom)
    elif hasattr(arg, "guild"):
        return get(arg.guild.roles, name=nom)
    else:
        return TypeError("tools.role : Impossible de remonter aux rôles depuis l'argument trasmis")

def member(arg, nom):       # Renvoie le membre @member. arg peut être de type Context, Guild, User/Member, Channel
    if hasattr(arg, "banner"):     # méthode immonde pour détécter si c'est une Guild
        return get(arg.members, display_name=nom)
    elif hasattr(arg, "guild"):
        return get(arg.guild.members, display_name=nom)
    else:
        return TypeError("tools.member : Impossible de remonter aux membres depuis l'argument trasmis")

def emoji(arg, nom):        # Renvoie l'emoji :nom:. arg peut être de type Context, Guild, User/Member, Channel
    if hasattr(arg, "banner"):     # méthode immonde pour détécter si c'est une Guild
        return get(arg.emojis, name=nom)
    elif hasattr(arg, "guild"):
        return get(arg.guild.emojis, name=nom)
    else:
        return TypeError("tools.member : Impossible de remonter aux emojis depuis l'argument trasmis")


# Renvoie le channel privé d'un utilisateur.

def private_chan(member):
    chan_id = Tables["Joueurs"].query.filter_by(discord_id=member.id).one()._chan_id
    return get(member.guild.channels, id=int(chan_id))


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


# Demande une réaction dans un choix (vrai/faux par défaut)

async def wait_for_react_clic(bot, message, emojis={"✅":True, "❎":False}, process_text=True, text_filter=lambda s:True):
    """Ajoute les reacts dans emojis à message, attend que quelqu'un appuie sur une, puis retourne :
        - soit le nom de l'emoji si emoji est une liste ;
        - soit la valeur associée si emoji est un dictionnaire.
        
    Si process_text=True, détecte aussi la réponse par message et retourne ledit message."""
    
    if not isinstance(emojis, dict):        # Si emoji est une liste, on en fait un dictionnaire
        emojis = {emoji:emoji for emoji in emojis}
        
    for emoji in emojis:                    # On ajoute les emojis
        await message.add_reaction(emoji)

    tasks = []      # Tâches qu'on va exécuter en parallèle
        
    emojis_names = [emoji.name if hasattr(emoji, "name") else emoji for emoji in emojis]
    def react_check(react):                 # Check REACT : bon message, pas un autre emoji, et pas react du bot
        return (react.message_id == message.id) and (react.emoji.name in emojis_names) and (react.user_id != bot.user.id)        
    tasks.append(asyncio.create_task(bot.wait_for('raw_reaction_add', check=react_check), name="react"))
    
    if process_text:
        def message_check(mess):                # Check MESSAGE : bon channel, pas du bot, et filtre (optionnel)
            return (mess.channel == message.channel) and (mess.author != bot.user) and text_filter(mess.content)
        tasks.append(asyncio.create_task(bot.wait_for('message', check=message_check), name="mess"))
    
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)      # On lance
    done = list(done)[0]
        
    if done.get_name() == "react":
        ret = emojis[done.result().emoji.name]      # Si clic sur react, done.result = react
    else:
        ret = done.result().content                 # Si envoi de message, done.result = message
        
    for emoji in emojis:
        await message.remove_reaction(emoji, bot.user)         # On finit par supprimer les emojis mis par le bot
        
    return ret





# Teste si le message contient un mot de la liste trigWords, les mots de trigWords doivent etre en minuscule

def checkTrig(m,trigWords):
    return m.content in trigWords

# Teste si user possède le role roles
def checkRole(member,nom : str):
    role = role(user, nom)
    return role in member.roles

#Permet de boucler question -> réponse tant que la réponse vérifie pas les critères nécessaires dans chan
async def boucleMessage(bot, chan, inMessage, conditionSortie, trigCheck = lambda m : m.channel==chan, repMessage="none"):
    """
    Permet de lancer une boucle question/réponse tant que la réponse ne vérifie pas conditionSortie
    chan est le channel dans lequel lancer la boucle
    trigCheck est la condition de détection du message dans le bot.wait_for
    inMessage est le premier message envoyé pour demander une réponse
    repMessage permet de définir un message de boucle différent du message d'accueil (identique si défini sur "none" ou non renseigné)
    """


    if repMessage=="none":
        repMessage = inMessage
    await chan.send(inMessage)
    rep = await bot.wait_for('message', check=trigCheck)
    while not conditionSortie(rep):
        await chan.send(repMessage)
        rep = await bot.wait_for('message', check=trigCheck)
    return rep

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
