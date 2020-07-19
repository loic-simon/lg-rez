from functools import wraps
import asyncio
import datetime
import unidecode
import re

import discord
import discord.utils
from discord.ext import commands

from bdd_connect import db, Tables, Joueurs, Roles, BaseActions, Actions, BaseActionsRoles, Taches, Triggers, Reactions, CandidHaro
# on importe toutes les tables, plus simple pour y accéder depuis des réactions etc (via eval_accols)
from blocs import bdd_tools


### ---------------------------------------------------------------------------
### Utilitaires de récupération d'objets Discord (détectent les mentions)
### ---------------------------------------------------------------------------

get = discord.utils.get

def find_by_mention_or_name(collec, val, pattern=None, must_be_found=False, raiser=None):         # Utilitaire pour la suite
    if not val:
        item = None
    elif pattern and (match := re.search(pattern, val)):
        item = get(collec, id=int(match.group(1)))
    else:
        item = get(collec, name=val)

    if must_be_found:
        assert item, f"{raiser or 'tools.find_by_mention_or_name'} : Élément {val} introuvable"

    return item


def channel(arg, nom, must_be_found=True):         # Renvoie le channel #nom. arg peut être de type Context, Guild, User/Member, Channel
    try:
        channels = arg.channels if isinstance(arg, discord.Guild) else arg.guild.channels
    except AttributeError:
        raise TypeError("tools.channel : Impossible de remonter aux channels depuis l'argument trasmis")
    return find_by_mention_or_name(channels, nom, pattern="<#([0-9]{18})>",
                                   must_be_found=must_be_found, raiser="tools.channel")


def role(arg, nom, must_be_found=True):            # Renvoie le rôle @&nom. arg peut être de type Context, Guild, User/Member, Channel
    try:
        roles = arg.roles if isinstance(arg, discord.Guild) else arg.guild.roles
    except AttributeError:
        raise TypeError("tools.role : Impossible de remonter aux rôles depuis l'argument trasmis")
    return find_by_mention_or_name(roles, nom, pattern="<@&([0-9]{18})>",
                                   must_be_found=must_be_found, raiser="tools.role")


def member(arg, nom, must_be_found=True):          # Renvoie le membre @member. arg peut être de type Context, Guild, User/Member, Channel
    try:
        members = arg.members if isinstance(arg, discord.Guild) else arg.guild.members
    except AttributeError:
        raise TypeError("tools.member : Impossible de remonter aux membres depuis l'argument trasmis")
    return find_by_mention_or_name(members, nom, pattern="<@!([0-9]{18})>",
                                   must_be_found=must_be_found, raiser="tools.member")


def emoji(arg, nom, must_be_found=True):           # Renvoie l'emoji :nom:. arg peut être de type Context, Guild, User/Member, Channel
    try:
        emojis = arg.emojis if isinstance(arg, discord.Guild) else arg.guild.emojis
    except AttributeError:
        raise TypeError("tools.emoji : Impossible de remonter aux emojis depuis l'argument trasmis")
    return find_by_mention_or_name(emojis, nom, pattern="<:.*:([0-9]{18})>",
                                   must_be_found=must_be_found, raiser="tools.emoji")


# Renvoie le channel privé d'un utilisateur
def private_chan(member, must_be_found=True):
    joueur = Joueurs.query.get(member.id)
    assert joueur, f"tools.private_chan : Joueur {member} introuvable"
    chan = member.guild.get_channel(joueur._chan_id)
    if must_be_found:
        assert chan, f"tools.private_chan : Chan privé de {joueur} introuvable"
    return chan


# Appel aux MJs
def mention_MJ(arg):        # Renvoie @MJ si le joueur n'est pas un MJ. arg peut être de type Context ou User/Member
    member = arg.author if hasattr(arg, "author") else arg
    if hasattr(member, "top_role") and member.top_role.name == "MJ":    # Si webhook, pas de top_role
        return "@MJ"
    else:
        return role(arg, "MJ").mention



### ---------------------------------------------------------------------------
### Décorateurs pour les différentes commandes, en fonction de leur usage
### ---------------------------------------------------------------------------

# @tools.mjs_only : commande exécutables uniquement par un MJ ou un webhook
mjs_only = commands.check_any(commands.check(lambda ctx: ctx.message.webhook_id), commands.has_any_role("MJ", "Bot"))

# @tools.joueurs_only : commande exécutables uniquement par un joueur (inscrit en base), vivant ou mort
joueurs_only = commands.has_any_role("Joueur en vie", "Joueur mort")

# @tools.vivants_only : commande exécutables uniquement par un joueur vivant
vivants_only = commands.has_role("Joueur en vie")

# @tools.private : supprime le message et exécute la commande dans la conv privée si elle a été appellée ailleurs (utilisable que dans un Cog)
# Utilisable en combinaison avec joueurs_only et vivants_only (pas avec les autres attention, vu que seuls les joueurs ont un channel privé)
def private(cmd):
    @wraps(cmd)
    async def new_cmd(self, ctx, *args, **kwargs):              # Cette commande est renvoyée à la place de cmd
        if not ctx.channel.name.startswith("conv-bot-"):            # Si pas déjà dans une conv bot :
            await ctx.message.delete()                                  # On supprime le message,
            ctx.channel = private_chan(ctx.author)                      # On remplace le chan dans le contexte d'appel par le chan privé,
            await ctx.send(f"{quote(ctx.message.content)}\n"            # On envoie un warning dans le chan privé,
                           f"{ctx.author.mention} :warning: Cette commande est interdite en dehors de ta conv privée ! :warning:\n"
                           f"J'ai supprimé ton message, et j'exécute la commande ici :")
        return await cmd(self, ctx, *args, **kwargs)                # Et on appelle cmd, avec le contexte modifié !

    return new_cmd



### ---------------------------------------------------------------------------
### Commandes d'interaction avec les joueurs : input, boucles, confirmation...
### ---------------------------------------------------------------------------

# Commande générale, à utiliser à la place de bot.wait_for('message', ...)
async def wait_for_message(bot, check, trigger_on_commands=False):
    if trigger_on_commands:
        def trig_check(m):
            return (check(m) or m.content.lower() in ["stop", "!stop"])         # et on trigger en cas de STOP
    else:
        def trig_check(m):
            return ((check(m)
                     and not m.content.startswith(bot.command_prefix))          # on ne trigger pas sur les commandes
                    or m.content.lower() in ["stop", "!stop"])                  # et on trigger en cas de STOP

    message = await bot.wait_for('message', check=trig_check)
    if message.content.lower() in ["stop", "!stop"]:
        raise RuntimeError("Arrêt demandé")
    else:
        return message


# Permet de boucler question -> réponse tant que la réponse vérifie pas les critères nécessaires dans chan
async def boucle_message(bot, chan, in_message, condition_sortie, trig_check=lambda m: m.channel == chan and m.author != bot.user, rep_message=None):
    """Permet de lancer une boucle question/réponse tant que la réponse ne vérifie pas condition_sortie

    chan est le channel dans lequel lancer la boucle
    trig_check est la condition de détection du message dans le bot.wait_for
    in_message est le premier message envoyé pour demander une réponse
    rep_message permet de définir un message de boucle différent du message d'accueil (identique si None)
    """
    if not rep_message:
        rep_message = in_message
    await chan.send(in_message)
    rep = await wait_for_message(bot, check=trig_check)
    while not condition_sortie(rep):
        await chan.send(rep_message)
        rep = await wait_for_message(bot, check=trig_check)
    return rep


async def boucle_query_joueur(ctx, cible=None, message=None, sensi=0.5):
    """Demande <message>, puis attend que le joueur entre un nom de joueur, et boucle 5 fois au max (avant de l'insulter)
    pour chercher le plus proche joueurs dans la table Joueurs
    """
    if message and not cible:
        await ctx.send(message)

    trig_check = lambda m: m.channel == ctx.channel and m.author != ctx.bot.user

    for i in range(5):
        if i == 0 and cible:            # Au premier tour, si on a donné une cible
            rep = cible
        else:
            mess = await wait_for_message(ctx.bot, check=trig_check)
            rep = mess.content

        if id := ''.join([c for c in rep if c.isdigit()]):      # Si la chaîne contient un nombre, on l'extrait
            if joueur := Joueurs.query.get(int(id)):                # Si cet ID correspond à un utilisateur, on le récupère
                return joueur                                       # On a trouvé l'utilisateur !

        nearest = await bdd_tools.find_nearest(rep, Joueurs, carac="nom", sensi=sensi)     # Sinon, recherche au plus proche

        if not nearest:
            await ctx.send("Aucune entrée trouvée, merci de réessayer")

        elif nearest[0][1] == 1:        # Si le score le plus haut est égal à 1...
            return nearest[0][0]        # ...renvoyer l'entrée correspondante

        elif len(nearest) == 1:
            m = await ctx.send(f"Je n'ai trouvé qu'une correspondance : {nearest[0][0].nom}\nÇa part ?")
            if await yes_no(ctx.bot, m):
                return nearest[0][0]
            else:
                await ctx.send("Bon d'accord, alors tu votes contre qui ?")

        else:
            s = "Les joueurs les plus proches de ton entrée sont les suivants : \n"
            for i, j in enumerate(nearest[:10]):
                s += f"{emoji_chiffre(i+1)}. {j[0].nom} \n"
            m = await ctx.send(s + "Tu peux les choisir en réagissant à ce message, ou en répondant au clavier.")
            n = await choice(ctx.bot, m, min(10, len(nearest)))
            return nearest[n-1][0]

    await ctx.send("Et puis non, tiens ! \n https://giphy.com/gifs/fuck-you-middle-finger-ryan-stiles-x1kS7NRIcIigU")
    raise RuntimeError("Le joueur est trop con, je peux rien faire")


# Récupère un input par réaction
async def wait_for_react_clic(bot, message, emojis={}, *, process_text=False,
                              text_filter=lambda s: True, post_converter=None, trigger_all_reacts=False, trigger_on_commands=False):
    """Ajoute les reacts dans emojis à message, attend que quelqu'un appuie sur une, puis renvoie :
        - soit le nom de l'emoji si emoji est une liste ;
        - soit la valeur associée si emoji est un dictionnaire.

    Si process_text == True, détecte aussi la réponse par message et retourne ledit message (défaut False).
    De plus, si text_filter (fonction str -> bool) est défini, ne réagit qu'aux messages pour lesquels text_filter(message) = True.
    De plus, si post_converter (fonction str -> ?) est défini, le message détecté est passé dans cette fonction avant d'être renvoyé.

    Si trigger_all_reacts == True, détecte l'ajout des toutes les réactions (et pas seulement celles dans emojis) et renvoie, si l'emoji directement si il n'est pas dans emojis (défaut False).
    Enfin, trigger_on_commands est passé directement à wait_for_message.
    """

    if not isinstance(emojis, dict):        # Si emoji est une liste, on en fait un dictionnaire
        emojis = {emoji: emoji for emoji in emojis}

    try:    # Si une erreur dans ce bloc, on supprime les emojis du bot (sinon c'est moche)
        for emoji in emojis:                    # On ajoute les emojis
            await message.add_reaction(emoji)

        emojis_names = [emoji.name if hasattr(emoji, "name") else emoji for emoji in emojis]
        def react_check(react):                     # Check REACT : bon message, pas un autre emoji, et pas react du bot
            return (react.message_id == message.id
                    and react.user_id != bot.user.id
                    and (trigger_all_reacts or react.emoji.name in emojis_names))

        react_task = asyncio.create_task(bot.wait_for('raw_reaction_add', check=react_check), name="react")

        if process_text:
            def message_check(mess):        # Check MESSAGE : bon channel, pas du bot, et filtre
                return (mess.channel == message.channel
                        and mess.author != bot.user
                        and text_filter(mess.content))
        else:
            def message_check(mess):        # On process DANS TOUS LES CAS, mais juste pour détecter "stop" si process_text == False
                return False

        mess_task = asyncio.create_task(wait_for_message(bot, check=message_check, trigger_on_commands=True), name="mess")

        done, pending = await asyncio.wait([react_task, mess_task], return_when=asyncio.FIRST_COMPLETED)      # On lance
        # Le bot attend ici qu'une des deux tâches aboutissent
        done_task = list(done)[0]        # done = tâche réussie

        if done_task.get_name() == "react":
            emoji = done_task.result().emoji
            if trigger_all_reacts and emoji.name not in emojis_names:
                ret = emoji
            else:
                ret = emojis[emoji.name]                            # Si clic sur react, done.result = react

            for emoji in emojis:
                await message.remove_reaction(emoji, bot.user)      # On finit par supprimer les emojis mis par le bot

        else:   # Réponse par message / STOP
            mess = done_task.result().content                # Si envoi de message, done.result = message
            ret = post_converter(mess) if post_converter else mess
            await message.clear_reactions()

    except Exception as exc:
        await message.clear_reactions()
        raise exc from Exception

    return ret


# Surcouche de wait_for_react_clic pour demander une confirmation / question fermée simplement
async def yes_no(bot, message):
    """Ajoute les reacts ✅ et ❎ à message et renvoie True ou False en fonction de l'emoji cliqué OU de la réponse textuelle détectée."""
    yes_words = ["oui", "o", "yes", "y", "1", "true"]
    yes_no_words = yes_words + ["non", "n", "no", "n", "0", "false"]
    return await wait_for_react_clic(
        bot, message, emojis={"✅": True, "❎": False}, process_text=True,
        text_filter=lambda s: s.lower() in yes_no_words, post_converter=lambda s: s.lower() in yes_words)


# Surcouche de wait_for_react_clic pour demander de choisir dans une liste simplement
async def choice(bot, message, N):
    """Ajoute les reacts 1️⃣, 2️⃣, 3️⃣... [N] à message et renvoie le numéro cliqué OU détecté par réponse textuelle. (N <= 10)"""
    return await wait_for_react_clic(
        bot, message, emojis={emoji_chiffre(i): i for i in range(1, N+1)}, process_text=True,
        text_filter=lambda s: s.isdigit() and 1 <= int(s) <= N, post_converter=int)


# Attend x secondes en affichant l'indicateur typing... sur le chat
async def sleep(chan, x):
    async with chan.typing():
        await asyncio.sleep(x)



### ---------------------------------------------------------------------------
### Utilitaires d'emojis
### ---------------------------------------------------------------------------

def montre(heure=None):
    """Renvoie l'emoji horloge correspondant à l'heure demandée (str "XXh" our "XXh30", actuelle si non précisée)"""

    if heure and isinstance(heure, str):
        heure, minute = heure.split("h")
        heure = int(heure) % 12
        minute = int(minute) % 60 if minute else 0
    else:
        tps = datetime.datetime.now().time()
        heure = tps.hour % 12
        minute = tps.minute

    if 15 < minute < 45:        # Demi heure
        L = ["🕧", "🕜", "🕝", "🕞", "🕟", "🕠", "🕡", "🕢", "🕣", "🕤", "🕥", "🕦"]
    else:                       # Heure pile
        L = ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"]
    return L[heure] if minute < 45 else L[(heure + 1) % 12]


def emoji_chiffre(chiffre: int, multi=False):
    if 0 <= chiffre <= 10:
        return ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][chiffre]
    elif multi:
        return ''.join([emoji_chiffre(int(c)) for c in str(chiffre)])
    else:
        raise ValueError("L'argument de emoji_chiffre doit être un entier entre 0 et 10")

def super_chiffre(chiffre: int, multi=False):
    if 0 <= chiffre <= 9:
        return ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"][chiffre]
    elif multi:
        return ''.join([super_chiffre(int(c)) for c in str(chiffre)])
    else:
        raise ValueError("L'argument de super_chiffre doit être un entier entre 0 et 9")

def sub_chiffre(chiffre: int, multi=False):
    if 0 <= chiffre <= 9:
        return ["₀", "₁", "₂", "₃", "₄", "₅", "₆", "₇", "₈", "₉"][chiffre]
    elif multi:
        return ''.join([sub_chiffre(int(c)) for c in str(chiffre)])
    else:
        raise ValueError("L'argument de sub_chiffre doit être un entier entre 0 et 9")



### ---------------------------------------------------------------------------
### Utilitaires de date / temps, notemment liées aux horaires de jeu
### ---------------------------------------------------------------------------

# Convertit HHh[MM] en objet Time
def heure_to_time(heure):
    try:
        hh, mm = heure.split("h")
        return datetime.time(int(hh), int(mm) if mm else 0)
    except ValueError as exc:
        raise ValueError(f"Valeur \"{heure}\" non convertible en temps") from exc


# Renvoie le datetime correspondant au prochain moment ou tps arrive DANS LES HORAIRES DU JEU : du dimanche 19:00:00 au vendredi 18:59:59.
def next_occurence(tps):
    pause = datetime.time(hour=19)

    now = datetime.datetime.now()
    jour = now.date()
    if tps <= now.time():       # Si plus tôt dans la journée que l'heure actuelle
        jour += datetime.timedelta(days=1)       # on réfléchit comme si on était demain très tôt

    wd = jour.weekday()         # Jour de la semaine, Lu = 0 ... Di = 6

    if tps < pause:
        if wd <= 4:                 # Avant 19h du lundi au vendredi : OK
            pass
        else:                       # Avant 19h mais on est samedi/dimanche
            jour += datetime.timedelta(days=(7-wd))
    else:
        if wd <= 3 or wd == 6:      # Après 19h du dimanche au jeudi : OK
            pass
        else:                       # Après 19h et on est vendredi/samedi
            jour += datetime.timedelta(days=(6-wd))

    return datetime.datetime.combine(jour, tps)         # passage de date et time à datetime


# Renvoie le datetime correspondant au prochain vendredi 19h
def debut_pause():
    pause_time = datetime.time(hour=19)
    pause_wday = 4          # Vendredi

    now = datetime.datetime.now()
    jour = now.date()
    if pause_time <= now.time():        # Si plus tôt dans la journée que l'heure actuelle
        jour += datetime.timedelta(days=1)       # on réfléchit comme si on était demain très tôt

    pause_jour = jour + datetime.timedelta(days=(pause_wday - jour.weekday()) % 7)      # Jour décalé du nombre de jours avant vendredi
    return datetime.datetime.combine(pause_jour, pause_time)         # passage de date et time à datetime


# Renvoie le datetime correspondant au prochain dimanche 19h
def fin_pause():
    reprise_time = datetime.time(hour=19)
    reprise_wday = 6        # Dimanche

    now = datetime.datetime.now()
    jour = now.date()
    if reprise_time <= now.time():      # Si plus tôt dans la journée que l'heure actuelle
        jour += datetime.timedelta(days=1)      # on réfléchit comme si on était demain très tôt

    reprise_jour = jour + datetime.timedelta(days=(reprise_wday - jour.weekday()) % 7)      # Jour décalé du nombre de jours avant vendredi
    return datetime.datetime.combine(reprise_jour, reprise_time)        # passage de date et time à datetime



### ---------------------------------------------------------------------------
### Split et log
### ---------------------------------------------------------------------------

# Sépare <mess> en une liste de messages de moins de <N>=2000 mots (limitation Discord), en séparant aux <sep>=sauts de ligne si possible.
# Ajoute <rep> à la fin des messages tronqués de leur séparateur final.
def smooth_split(mess :str, N=1990, sep='\n', rep=''):
    mess = str(mess)
    LM = []             # Liste des messages
    psl = 0             # indice du Précédent Saut de Ligne
    L = len(mess)
    while psl + N < L:
        if mess.count(sep, psl, psl+N+len(sep)):       # +len(sep) parce que si sep est à la fin, on le dégage
            i = psl + N - mess[psl: psl+N+len(sep)][::-1].find(sep)      # un peu sombre mais vrai, tkt frère
            LM.append(mess[psl: i] + rep)
            psl = i + 1     # on élimine le \n
        else:
            LM.append(mess[psl: psl + N])
            psl += N

    if psl < L:
        LM.append(mess[psl:])   # ce qui reste
    return LM

# Envoie dans <messageable> (ctx / channel) mess sous forme de blocs de code
async def send_code_blocs(messageable, mess, **kwargs):
    [await messageable.send(code_bloc(bloc)) for bloc in smooth_split(mess, **kwargs)]

# Envoie dans <messageable> (ctx / channel) mess
async def send_blocs(messageable, mess, **kwargs):
    [await messageable.send(bloc) for bloc in smooth_split(mess, **kwargs)]

# Log dans #logs
async def log(arg, message, code=False):
    """Envoie <message> dans le channel #logs. <arg> peut être de type Context, Guild, User/Member, Channel"""
    logchan = channel(arg, "logs")
    if code:
        await send_code_blocs(logchan, message)
    else:
        [await logchan.send(bloc) for bloc in smooth_split(message)]



### ---------------------------------------------------------------------------
### Autres fonctions diverses
### ---------------------------------------------------------------------------

# Crée un contexte à partir d'un message_id : simule que <member> a envoyé <content> dans son chan privé

async def create_context(bot, message_id, member, content):
    chan = private_chan(member)
    message = (await chan.history(limit=1).flatten())[0]        # On a besoin de récupérer un message, ici le dernier de la conv privée
    # message = await chan.fetch_message(message_id)
    message.author = member
    message.content = content
    return await bot.get_context(message)


# Retourne le nom du slug role (None si non trouvé)
def nom_role(role):
    if role := Roles.query.get(role):
        return role.nom
    else:
        return None


# Remove accents
def remove_accents(s):
    p = re.compile("([À-ʲΆ-ת])")      # Abracadabrax, c'est moche mais ça marche (source : tkt frère)
    return p.sub(lambda c: unidecode.unidecode(c.group()), s)


# Replace chaque bloc entouré par des {} par leur évaluation Python si aucune erreur n'est levée, sinon laisse l'expression telle quelle
# Penser à passer les globals() et locals() si besoin. Généralement, il faut passer locals() qui contient ctx, etc... mais pas globals() si on veut bénéficier de tous les modules importés dans tools.py

def eval_accols(rep, globals=None, locals=None, debug=False):
    if "{" in rep:              # Si contient des expressions
        evrep = ""                  # Réponse évaluée
        expr = ""                   # Expression à évaluer
        noc = 0                     # Nombre de { non appariés
        for c in rep:
            if c == "{":
                if noc:             # Expression en cours :
                    expr += c           # on garde le {
                noc += 1
            elif c == "}":
                noc -= 1
                if noc:             # idem
                    expr += c
                else:               # Fin d'une expression
                    try:                                            # On essaie d'évaluer la chaîne
                        evrep += str(eval(expr, globals, locals))       # eval("expr") = expr
                    except Exception as e:
                        evrep += "{" + expr + "}"                   # Si erreur, on laisse {expr} non évaluée
                        if debug:
                            evrep += tools.code(f"->!!! {e} !!!")
                    expr = ""
            elif noc:               # Expression en cours
                expr += c
            else:                   # Pas d'expression en cours
                evrep += c
        if noc:     # Si expression jamais finie (nombre impair de {)
            evrep += "{" + expr
        return evrep
    else:
        return rep



### ---------------------------------------------------------------------------
### Utilitaires de formatage de texte
### ---------------------------------------------------------------------------

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
