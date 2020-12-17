"""lg-rez / blocs / Outils divers et variés

Récupération d'objets Discord, décorateurs pour commandes, structures d'interaction dans les channels, utilitaires d'emojis, de date/temps, de formatage...

"""

from functools import wraps
import asyncio
import datetime
import unidecode
import re

import discord
import discord.utils
from discord.ext import commands

from lgrez.blocs import bdd, bdd_tools
from lgrez.blocs.bdd import Tables, Joueurs, Roles, BaseActions, Actions, BaseActionsRoles, Taches, Triggers, Reactions, CandidHaro
# on importe toutes les tables, plus simple pour y accéder depuis des réactions etc (via eval_accols)


### ---------------------------------------------------------------------------
### Utilitaires de récupération d'objets Discord (détectent les mentions)
### ---------------------------------------------------------------------------

#: Raccourci pour :func:`discord.utils.get`
get = discord.utils.get


def _find_by_mention_or_name(collec, val, pattern=None, must_be_found=False, raiser=None):
    """Utilitaire pour la suite : trouve <val> dans <collec>

    [pattern]           Motif RegEx à utiliser pour la recherche
    [must_be_found]     Si True, raise une AssertionError si <val> est introuvable
    [raiser]            Nom de la fonction à envoyer dans l'exception si introuvable
    """
    if not val:
        item = None
    elif pattern and (match := re.search(pattern, val)):
        item = get(collec, id=int(match.group(1)))
    else:
        item = get(collec, name=val)

    if must_be_found:
        assert item, f"{raiser or 'tools._find_by_mention_or_name'} : Élément {val} introuvable"

    return item


def channel(arg, nom, must_be_found=True):
    """Renvoie l'objet associé au salon ``#nom``.

    Args:
        nom (:class:`str`): nom du channel (texte/vocal/catégorie) ou sa mention (détection directe par regex)
        arg (:class:`~discord.ext.commands.Context` | :class:`~discord.Guild` | :class:`~discord.Member` | :class:`~discord.abc.GuildChannel`): argument "connecté" au serveur, permettant de remonter aux channels
        must_be_found (:class:`bool`): si ``True`` (défaut), raise une :exc:`AssertionError` si le channel ``#nom`` n'existe pas (si ``False``, renvoie ``None``)

    Returns:
        :class:`discord.abc.GuildChannel`
    """
    try:
        channels = arg.channels if isinstance(arg, discord.Guild) else arg.guild.channels
    except AttributeError:
        raise TypeError("tools.channel : Impossible de remonter aux channels depuis l'argument trasmis")
    return _find_by_mention_or_name(channels, nom, pattern="<#([0-9]{18})>",
                                   must_be_found=must_be_found, raiser="tools.channel")


def role(arg, nom, must_be_found=True):
    """Renvoie l'objet associé au rôle ``@&nom``.

    Args:
        nom (:class:`str`): nom du rôle ou sa mention (détection directe par regex)
        arg (:class:`~discord.ext.commands.Context` | :class:`~discord.Guild` | :class:`~discord.Member` | :class:`~discord.abc.GuildChannel`): argument "connecté" au serveur, permettant de remonter aux rôles
        must_be_found (:class:`bool`): si ``True`` (défaut), raise une :exc:`AssertionError` si le channel ``@&nom`` n'existe pas (si ``False``, renvoie ``None``)

    Returns:
        :class:`discord.Role`
    """
    try:
        roles = arg.roles if isinstance(arg, discord.Guild) else arg.guild.roles
    except AttributeError:
        raise TypeError("tools.role : Impossible de remonter aux rôles depuis l'argument trasmis")
    return _find_by_mention_or_name(roles, nom, pattern="<@&([0-9]{18})>",
                                   must_be_found=must_be_found, raiser="tools.role")


def member(arg, nom, must_be_found=True):
    """Renvoie l'objet associé au membre ``@nom``.

    Args:
        nom (:class:`str`): nom du joueur ou sa mention (détection directe par regex)
        arg (:class:`~discord.ext.commands.Context` | :class:`~discord.Guild` | :class:`~discord.Member` | :class:`~discord.abc.GuildChannel`): argument "connecté" au serveur, permettant de remonter aux membres
        must_be_found (:class:`bool`): si ``True`` (défaut), raise une :exc:`AssertionError` si le membre ``@nom`` n'existe pas (si ``False``, renvoie ``None``)

    Returns:
        :class:`discord.Member`
    """
    try:
        members = arg.members if isinstance(arg, discord.Guild) else arg.guild.members
    except AttributeError:
        raise TypeError("tools.member : Impossible de remonter aux membres depuis l'argument trasmis")
    return _find_by_mention_or_name(members, nom, pattern="<@!([0-9]{18})>",
                                   must_be_found=must_be_found, raiser="tools.member")


def emoji(arg, nom, must_be_found=True):
    """Renvoie l'objet associé à l'emoji ``:nom:``.

    Args:
        nom (:class:`str`): nom de l'emoji (texte/vocal/catégorie) ou son utilisation (détection directe par regex)
        arg (:class:`~discord.ext.commands.Context` | :class:`~discord.Guild` | :class:`~discord.Member` | :class:`~discord.abc.GuildChannel`): argument "connecté" au serveur, permettant de remonter aux emojis
        must_be_found (:class:`bool`): si ``True`` (défaut), raise une :exc:`AssertionError` si l'emoji ``:nom:`` n'existe pas (si ``False``, renvoie ``None``)

    Returns:
        :class:`discord.Emoji`
    """
    try:
        emojis = arg.emojis if isinstance(arg, discord.Guild) else arg.guild.emojis
    except AttributeError:
        raise TypeError("tools.emoji : Impossible de remonter aux emojis depuis l'argument trasmis")
    return _find_by_mention_or_name(emojis, nom, pattern="<:.*:([0-9]{18})>",
                                   must_be_found=must_be_found, raiser="tools.emoji")


def private_chan(member, must_be_found=True):
    """Renvie le channel privé d'un joueur

    Args:
        member (:class:`discord.Member`): membre du serveur
        must_be_found (:class:`bool`): si ``True`` (défaut), raise une :exc:`AssertionError` si le channel n'existe pas (si ``False``, renvoie ``None``)

    Returns:
        :class:`discord.TextChannel`
    """
    joueur = Joueurs.query.get(member.id)
    assert joueur, f"tools.private_chan : Joueur {member} introuvable"
    chan = member.guild.get_channel(joueur.chan_id_)
    if must_be_found:
        assert chan, f"tools.private_chan : Chan privé de {joueur} introuvable"
    return chan


# Appel aux MJs
def mention_MJ(arg):
    """Renvoie la mention du rôle "MJ" si le joueur n'est pas un MJ, ``"@MJ"`` sinon.

    Args:
        arg (:class:`~discord.Member` | :class:`~discord.ext.commands.Context`): membre ou contexte d'un message envoyé par un membre
    """
    member = arg.author if hasattr(arg, "author") else arg
    if hasattr(member, "top_role") and member.top_role.name == "MJ":    # Si webhook, pas de top_role
        return "@MJ"
    else:
        return role(arg, "MJ").mention



### ---------------------------------------------------------------------------
### Exceptions
### ---------------------------------------------------------------------------

class CommandExit(RuntimeError):
    """Lever cette exception force l'arrêt immédiat d'une commande, et empêche le bot de réagir à nouveau

    Sous-classe de :exc:`RuntimeError`
    """
    pass


### ---------------------------------------------------------------------------
### Décorateurs pour les différentes commandes, en fonction de leur usage
### ---------------------------------------------------------------------------

#: décorateur pour commande (:func:`discord.ext.commands.check`) : commandes exécutables uniquement par un MJ ou un webhook
mjs_only = commands.check_any(commands.check(lambda ctx: ctx.message.webhook_id), commands.has_role("MJ"))

#: décorateur pour commande (:func:`discord.ext.commands.check`) : commandes exécutables par un MJ, un rédacteur ou un webhook (pour IA)
mjs_et_redacteurs = commands.check_any(commands.check(lambda ctx: ctx.message.webhook_id), commands.has_any_role("MJ", "Rédacteur"))

#: décorateur pour commande (:func:`discord.ext.commands.check`) : commandes exécutables uniquement par un joueur (inscrit en base), vivant ou mort
joueurs_only = commands.has_any_role("Joueur en vie", "Joueur mort")

#: décorateur pour commande (:func:`discord.ext.commands.check`)  : commandes exécutables uniquement par un joueur vivant
vivants_only = commands.has_role("Joueur en vie")

# @tools.private
def private(cmd):
    """Décorateur pour commande : lors d'une invocation de la commande décorée hors d'un channel privé (``#conv-bot-``), supprime le message d'invocation et exécute la commande dans le channel privée de l'invoqueur.

    Ce décorateur n'est utilisable que sur une commande définie dans un Cog.
    Si le joueur ayant utilisé la commande n'a pas de chan privé (pas en base), raise une :exc:`AssertionError`.

    Utilisable en combinaison avec :func:`.joueurs_only` et :func:`.vivants_only` (pas avec les autres attention, vu que seuls les joueurs ont un channel privé)
    """
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
    """Attend et renvoie le premier message reçu rencontrant les critères demandés.

    Surcouche de :meth:`discord.ext.commands.Bot.wait_for` permettant d'ignorer les commandes et de réagir au mot-clé ``stop``.

    Args:
        bot (:class:`.LGBot`): bot connecté au serveur
        check (:class:`function`\(:class:`discord.Message` -> :class:`bool`\)): fonction validant ou non chaque message
        trigger_on_commands (:class:`bool`): si ``False`` (défaut), un message respectant ``check`` sera ignoré si c'est une commande.

    Returns:
        :class:`discord.Message`

    Si le message est ``"stop"`` ou ``"!stop"`` (ou autre casse), raise une exception :exc:`.CommandExit` (même si le message respecte ``check``).
    """
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
        if message.author == bot.user:
            raise CommandExit(ital("(Arrêt commande précédente)"))
        else:
            raise CommandExit("Arrêt demandé")
    else:
        return message


# Raccourci pratique
async def wait_for_message_here(ctx, trigger_on_commands=False):
    """Attend et renvoie le premier message reçu dans <ctx>.

    Surcouche de :func:`.wait_for_message` filtrant uniquement les messages envoyés dans ``ctx.channel`` par quelqu'un d'autre que le bot

    Args:
        ctx (:class:`discord.ext.commands.Context`): contexte d'une commande
        trigger_on_commands: passé directement à :func:`.wait_for_message`

    Returns:
        :class:`discord.Message`
    """
    def trig_check(message):
        return (message.channel == ctx.channel and message.author != ctx.bot.user)

    message = await wait_for_message(ctx.bot, check=trig_check, trigger_on_commands=trigger_on_commands)
    return message


# Permet de boucler question -> réponse tant que la réponse vérifie pas les critères nécessaires dans chan
async def boucle_message(bot, chan, in_message, condition_sortie, rep_message=None):
    """Permet de lancer une boucle question/réponse tant que la réponse ne vérifie pas une condition

    Args:
        bot (:class:`.LGBot`): bot connecté au serveur
        chan (:class:`discord.TextChannel`): channel dans lequel lancer la boucle
        condition_sortie (:class:`function`\(:class:`discord.Message` -> :class:`bool`\)): fonction validant ou non chaque message
        in_message (:class:`str`): si défini, message à envoyer avant la boucle
        rep_message (:class:`str`): si défini, permet de définir un message de boucle différent de ``in_message`` (identique si ``None``). Doit être défini si ``in_message`` n'est pas défini.

    Returns:
        :class:`discord.Message`
    """
    if not rep_message:
        rep_message = in_message
    if not rep_message:
        raise ValueError("tools.boucle_message : [in_message] ou [rep_message] doit être défini !")

    def check_chan(m): #C heck que le message soit envoyé par l'utilisateur et dans son channel perso
        return m.channel == chan and m.author != bot.user

    await chan.send(in_message)
    rep = await wait_for_message(bot, check_chan)
    while not condition_sortie(rep):
        await chan.send(rep_message)
        rep = await wait_for_message(bot, check_chan)

    return rep


async def boucle_query_joueur(ctx, cible=None, message=None, sensi=0.5):
    """Retourne un joueur (entrée de BDD) d'après son nom

    Args:
        ctx (:class:`discord.ext.commands.Context`): contexte d'une commande
        cible (:class:`str`): premier essai de cible (donnée par le joueur dans l'appel à une commande, par exemple)
        message (:class:`str`): si défini (et ``cible`` non définie), message à envoyer avant la boucle
        sensi (:class:`float`): sensibilité de la recherche (c.f. :func:`.bdd_tools.find_nearest`)

    Returns:
        :class:`.bdd.Joueurs`

    Attend que le joueur entre un nom de joueur, et boucle 5 fois au max (avant de l'insulter et de raise une erreur) pour chercher le plus proche joueur dans la table :class:`.bdd.Joueurs`.
    """
    if message and not cible:
        await ctx.send(message)

    for i in range(5):
        if i == 0 and cible:            # Au premier tour, si on a donné une cible
            rep = cible
        else:
            mess = await wait_for_message_here(ctx)
            rep = mess.content.strip("()[]{}<>")

        if id := ''.join([c for c in rep if c.isdigit()]):      # Si la chaîne contient un nombre, on l'extrait
            if joueur := Joueurs.query.get(int(id)):                # Si cet ID correspond à un utilisateur, on le récupère
                return joueur                                       # On a trouvé l'utilisateur !

        nearest = bdd_tools.find_nearest(rep, Joueurs, carac="nom", sensi=sensi, solo_si_parfait=False, match_first_word=True)     # Sinon, recherche au plus proche

        if not nearest:
            await ctx.send("Aucune entrée trouvée, merci de réessayer :")

        elif nearest[0][1] == 1 and not (len(nearest) > 1 and nearest[1][1] == 1):        # Si le score le plus haut est égal à 1...
            return nearest[0][0]        # ...renvoyer l'entrée correspondante

        elif len(nearest) == 1:
            m = await ctx.send(f"Je n'ai trouvé qu'une correspondance : {nearest[0][0].nom}\nÇa part ?")
            if await yes_no(ctx.bot, m):
                return nearest[0][0]
            else:
                await ctx.send("Bon d'accord, alors qui ?")

        else:
            s = "Les joueurs les plus proches de ton entrée sont les suivants : \n"
            for i, j in enumerate(nearest[:10]):
                s += f"{emoji_chiffre(i+1)}. {j[0].nom} \n"
            m = await ctx.send(s + ital("Tu peux les choisir en réagissant à ce message, ou en répondant au clavier."))
            n = await choice(ctx.bot, m, min(10, len(nearest)))
            return nearest[n-1][0]

    await ctx.send("Et puis non, tiens ! \n https://giphy.com/gifs/fuck-you-middle-finger-ryan-stiles-x1kS7NRIcIigU")
    raise RuntimeError("Le joueur est trop con, je peux rien faire")


# Récupère un input par réaction
async def wait_for_react_clic(bot, message, emojis={}, *, process_text=False,
                              text_filter=lambda s: True, post_converter=None, trigger_all_reacts=False, trigger_on_commands=False):
    """Ajoute des reacts à un message et attend que quelqu'un appuie sur une

    Args:
        bot (:class:`.LGBot`): bot connecté au serveur
        message (:class:`discord.Message`): message où ajouter les réactions
        emojis (:class:`list` | :class:`dict`): reacts à ajouter, éventuellement associés à une valeur qui sera retournée au clic sur l'emoji
        process_text (:class:`bool`): si ``True``, détecte aussi la réponse par message et retourne ledit message (défaut : ``False``)
        text_filter (:class:`function`\(:class:`str` -> :class:`bool`\)): si ``process_text``, ne réagit qu'aux messages pour lesquels ``text_filter(message)`` renvoie ``True`` (défaut : tous)
        post_converter (:class:`function`\(:class:`str` -> :class:`object`\)): si ``process_text`` et que l'argument est défini, le message détecté est passé dans cette fonction avant d'être renvoyé
        trigger_all_reacts (:class:`bool`): si ``True``, détecte l'ajout des toutes les réactions (et pas seulement celles dans ``emojis``) et renvoie l'emoji directement si il n'est pas dans ``emojis`` (défaut : ``False``)
        trigger_on_commands (:class:`bool`): passé directement à :func:`.wait_for_message`.

    Returns:
        :class:`str`, représentant

            - le nom de l'emoji si ``emojis`` est une liste et clic sur une des reacts, ou si ``trigger_all_reacts`` vaut ``True`` et ajout d'une autre react ;
            - le message reçu si ``process_text`` vaut ``True``, que ``post_converter`` n'est pas défini et réaction à un message
    OU
        :class:`object`, représentant

            - la valeur associée si ``emojis`` est un dictionnaire et clic sur une des reacts ;
            - la valeur retournée par ``post_converter`` si il est défini, que ``process_text`` vaut ``True`` et réaction à un message
    """

    if not isinstance(emojis, dict):        # Si emoji est une liste, on en fait un dictionnaire
        emojis = {emoji: emoji for emoji in emojis}

    try:    # Si une erreur dans ce bloc, on supprime les emojis du bot (sinon c'est moche)
        for emoji in emojis:                    # On ajoute les emojis
            await message.add_reaction(emoji)

        emojis_names = {emoji.name if hasattr(emoji, "name") else emoji: emoji for emoji in emojis}
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
        done_task = next(iter(done))        # done = tâche réussie

        if done_task.get_name() == "react":
            emoji = done_task.result().emoji
            if trigger_all_reacts and emoji.name not in emojis_names:
                ret = emoji
            else:
                ret = emojis.get(emoji) or emojis.get(emojis_names.get(emoji.name))     # Si clic sur react, done.result = react

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
    """Ajoute les reacts ✅ et ❎ à message et renvoie ``True`` ou ``False`` en fonction de l'emoji cliqué OU de la réponse textuelle détectée

    Surcouche de :func:`wait_for_react_clic` pour demander une confirmation / question fermée simplement.

    Args:
        bot (:class:`.LGBot`): bot connecté au serveur
        message (:class:`discord.Message`): message où ajouter les réactions

    Réponses textuelles reconnues :
        - Pour ``True`` : ``["oui", "o", "yes", "y", "1", "true"]``
        - Pour ``False`` : ``["non", "n", "no", "n", "0", "false"]``

    ainsi que toutes leurs variations de casse.

    Returns:
        :class:`bool`
    """
    yes_words = ["oui", "o", "yes", "y", "1", "true"]
    yes_no_words = yes_words + ["non", "n", "no", "n", "0", "false"]
    return await wait_for_react_clic(
        bot, message, emojis={"✅": True, "❎": False}, process_text=True,
        text_filter=lambda s: s.lower() in yes_no_words, post_converter=lambda s: s.lower() in yes_words)


# Surcouche de wait_for_react_clic pour demander de choisir dans une liste simplement
async def choice(bot, message, N, start=1, *, additionnal={}):
    """Ajoute des reacts chiffres (1️⃣, 2️⃣, 3️⃣...) à message et renvoie le numéro cliqué OU détecté par réponse textuelle

    Surcouche de :func:`wait_for_react_clic` pour demander de choisir dans une liste simplement.

    Args:
        bot (:class:`.LGBot`): bot connecté au serveur
        message (:class:`discord.Message`): message où ajouter les réactions
        N (:class:`int`): chiffre jusqu'auquel aller, inclus (``<= 10``)
        start (:class:`int`): chiffre auquel commencer (``<= N``, défaut ``1``)
        additionnal (:class:`dict`): dictionnaire emoji à ajouter après les chiffres -> valeur renvoyée si cliqué

    Réponses textuelles reconnues : nombres seuls entre ``start`` et ``N``

    Returns:
        :class:`int`
    """
    emojis = {emoji_chiffre(i): i for i in range(start, N+1)}
    if additionnal:
        emojis.update(additionnal)
    return await wait_for_react_clic(
        bot, message, emojis=emojis, process_text=True,
        text_filter=lambda s: s.isdigit() and start <= int(s) <= N, post_converter=int)


async def sleep(chan, x):
    """Pause l'exécution d'une commande en affichant l'indicateur *typing* ("*LGBot est en train d'écrire...*") sur un salon

    Permat d'afficher plusieurs messages d'affillée en laissant le temps de lire, tout en indiquant que le bot n'a pas fini d'écrire

    Args:
        chan (:class:`discord.abc.Messageable`): salon / contexte /... sur lequel attendre
        x (:class:`float`): temps à attendre, en secondes
    """
    async with chan.typing():
        await asyncio.sleep(x)



### ---------------------------------------------------------------------------
### Utilitaires d'emojis
### ---------------------------------------------------------------------------

def emoji_camp(arg, camp):
    """Renvoie l'emoji associé à un camp donné.

    Args:
        arg (:class:`~discord.ext.commands.Context` | :class:`~discord.Guild` | :class:`~discord.Member` | :class:`~discord.abc.GuildChannel`): argument "connecté" au serveur, permettant de remonter aux emojis
        camp (str): parmis ``"village"``, ``"loups"``, ``"nécro"``, ``"solitaire"``, ``"autre"``

    Returns:
        :class:`discord.Emoji` or `""`
    """
    d = {"village": "village",
         "loups": "lune",
         "nécro": "necro",
         "solitaire": "pion",
         "autre": "pion"}
    if camp in d:
        return emoji(arg, d[camp])
    else:
        return ""


def montre(heure=None):
    """Renvoie l'emoji horloge (🕧, 🕓, 🕝...) le plus proche d'une heure donnée

    Args:
        heure (:class:`str`): heure à représenter au format ``"XXh"`` ou ``"XXhMM"`` (défaut : heure actuelle)

    Returns:
        :class:`str`
    """
    if heure and isinstance(heure, str):
        heure, minute = heure.split("h")
        heure = int(heure) % 12
        minute = int(minute) % 60 if minute else 0
    else:
        now = datetime.datetime.now()
        heure = now.hour % 12
        minute = now.minute

    if 15 < minute < 45:        # Demi heure
        L = ["🕧", "🕜", "🕝", "🕞", "🕟", "🕠", "🕡", "🕢", "🕣", "🕤", "🕥", "🕦"]
    else:                       # Heure pile
        L = ["🕛", "🕐", "🕑", "🕒", "🕓", "🕔", "🕕", "🕖", "🕗", "🕘", "🕙", "🕚"]
    return L[heure] if minute < 45 else L[(heure + 1) % 12]


def emoji_chiffre(chiffre, multi=False):
    """Renvoie l'emoji / les emojis 0️⃣, 1️⃣, 2️⃣... correspond à un chiffre/nombre

    Args:
        chiffre (:class:`int`): chiffre/nombre à représenter
        multi (:class:`bool`): si ``True``, ``chiffre`` peut être n'importe quel entier positif, dont les chiffres seront convertis séparément ; sinon (par défaut), ``chiffre`` doit être un entier entre ``0`` et ``10``.

    Returns:
        :class:`str`
    """
    if isinstance(chiffre, int) and 0 <= chiffre <= 10:
        return ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][chiffre]
    elif multi and str(chiffre).isdigit():
        return ''.join([emoji_chiffre(int(c)) for c in str(chiffre)])
    else:
        raise ValueError("L'argument de tools.emoji_chiffre doit être un entier entre 0 et 10 OU un entier positif avec multi=True")


def super_chiffre(chiffre, multi=False):
    """Renvoie le(s) caractère(s) Unicode ⁰, ¹, ²... correspond à un chiffre/nombre

    Args:
        chiffre (:class:`int`): chiffre/nombre à représenter
        multi (:class:`bool`): si ``True``, ``chiffre`` peut être n'importe quel entier positif, dont les chiffres seront convertis séparément ; sinon (par défaut), ``chiffre`` doit être un entier entre ``0`` et ``9``.

    Returns:
        :class:`str`
    """
    if isinstance(chiffre, int) and 0 <= chiffre <= 9:
        return ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"][chiffre]
    elif multi and str(chiffre).isdigit():
        return ''.join([super_chiffre(int(c)) for c in str(chiffre)])
    else:
        raise ValueError("L'argument de tools.super_chiffre doit être un entier entre 0 et 9 OU un entier positif avec multi=True")


def sub_chiffre(chiffre, multi=False):
    """Renvoie le(s) caractère(s) unicode ₀, ₁, ₂... correspond à un chiffre/nombre

    Args:
        chiffre (:class:`int`): chiffre/nombre à représenter
        multi (:class:`bool`): si ``True``, ``chiffre`` peut être n'importe quel entier positif, dont les chiffres seront convertis séparément ; sinon (par défaut), ``chiffre`` doit être un entier entre ``0`` et ``9``.

    Returns:
        :class:`str`
    """
    if isinstance(chiffre, int) and 0 <= chiffre <= 9:
        return ["₀", "₁", "₂", "₃", "₄", "₅", "₆", "₇", "₈", "₉"][chiffre]
    elif multi and str(chiffre).isdigit():
        return ''.join([sub_chiffre(int(c)) for c in str(chiffre)])
    else:
        raise ValueError("L'argument de tools.sub_chiffre doit être un entier entre 0 et 9 OU un entier positif avec multi=True")



### ---------------------------------------------------------------------------
### Utilitaires de date / temps, notemment liées aux horaires de jeu
### ---------------------------------------------------------------------------

def heure_to_time(heure):
    """Convertit l'écriture d'une heure en objet :class:`datetime.time`

    Args:
        heure (:class:`str`): heure au format ``HHh``, ``HHhMM`` ou ``HH:MM``

    Returns:
        :class:`datetime.time`
    """
    try:
        if "h" in heure:
            hh, mm = heure.split("h")
        else:
            hh, mm = heure.split(":")
        return datetime.time(int(hh), int(mm) if mm else 0)
    except ValueError as exc:
        raise ValueError(f"Valeur \"{heure}\" non convertible en temps") from exc


def time_to_heure(tps, sep="h", force_minutes=False):
    """Convertit un objet :class:`datetime.time` en heure (version maison de :meth:`datetime.time.strftime`)

    Args:
        tps (:class:`datetime.time`): temps à convertir
        sep (:class:`str`): séparateur heures / minutes à utiliser (défaut ``"h"``)
        force_minutes (:class:`bool`): si ``False`` (défaut), les minutes ne sont indiquées que si différentes de ``0``.

    Returns:
        :class:`str` (``""`` si ``tps`` est ``None``)
    """
    if tps:
        if force_minutes or tps.minute > 0:
            return f"{tps.hour}{sep}{tps.minute:02}"
        else:
            return f"{tps.hour}{sep}"
    else:
        return ""


# Renvoie le datetime correspondant au prochain moment ou tps arrive DANS LES HORAIRES DU JEU : du dimanche 19:00:00 au vendredi 18:59:59.
def next_occurence(tps):
    """Renvoie le timestamp correspondant à la prochaine occurence d'une heure donnée

    Renvoie le prochain timestamp arrivant DANS LES HORAIRES DU JEU : du dimanche 19:00:00 au vendredi 18:59:59.

    Args:
        tps (:class:`datetime.time`): heure dont on veut connaître la prochaine occurence

    Returns:
        :class:`datetime.datetime`
    """
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


def debut_pause():
    """Renvoie le timestamp correspondant au prochain vendredi 19h

    Returns:
        :class:`datetime.datetime`
    """
    pause_time = datetime.time(hour=19)
    pause_wday = 4          # Vendredi

    now = datetime.datetime.now()
    jour = now.date()
    if pause_time <= now.time():        # Si plus tôt dans la journée que l'heure actuelle
        jour += datetime.timedelta(days=1)       # on réfléchit comme si on était demain très tôt

    pause_jour = jour + datetime.timedelta(days=(pause_wday - jour.weekday()) % 7)      # Jour décalé du nombre de jours avant vendredi
    return datetime.datetime.combine(pause_jour, pause_time)         # passage de date et time à datetime


def fin_pause():
    """Renvoie le timestamp correspondant au prochain dimanche 19h

    Returns:
        :class:`datetime.datetime`
    """
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
def smooth_split(mess, N=1990, sep='\n', rep=''):
    """Sépare un message en une liste de messages moins longs qu'un nombre de caractères donné

    Très utile pour envoyer des messages de (potentiellement) plus de 2000 caractères (limitation Discord)

    Args:
        mess (:class:`str`): message à couper
        N (:class:`int`): taille maximale des messages formés (défaut ``1990``, pour avoir un peu de marge et permettre d'entourer de ``````` par exemple)
        sep (:class:`str`) : caractères où séparer préférentiellement le texte (défaut : sauts de ligne). Si ``mess`` contient une sous-chaîne plus longue que ``N`` ne contenant pas ``sep``, le message est tronqué à la limite.
        rep (:class:`str`) : chaîne ajoutée à la fin de chaque message formé (tronqué du séparateur final) (défaut : aucune)

    Returns:
        :class:`list`\[:class:`str`\]
    """
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


async def send_blocs(messageable, mess, *, N=1990, sep='\n', rep=''):
    """Envoie un (potentiellement long) message en le coupant en blocs si nécaissaire

    Surcouche de :func:`.smooth_split` envoyant directement les messages formés

    Retourne la liste des messages envoyés

    Args:
        messageable (:class:`discord.abc.Messageable`): objet où envoyer le message (:class:`~discord.ext.commands.Context` ou :class:`~discord.TextChannel`)
        mess (:class:`str`): message à envoyer
        N, sep, rep: *identique à* :func:`.smooth_split`

    Returns:
        :class:`list`\[:class:`discord.Message`\]
    """
    messages = []
    for bloc in smooth_split(mess, N=N, sep=sep, rep=rep):
        messages.append(await messageable.send(bloc))

    return messages


async def send_code_blocs(messageable, mess, *, N=1990, sep='\n', rep='', prefixe="", langage=""):
    """Envoie un (potentiellement long) message sous forme de bloc(s) de code

    Retourne la liste des messages envoyés

    :Paramètres:
        messageable, mess, N, sep, rep: *identiques à :func:`.send_blocs`*
        prefixe (:class:`str`): texte à mettre hors des code blocs, au début du premier message
        language: *identique à* :func:`.code_bloc`

    Returns:
        :class:`list`\[:class:`discord.Message`\]
    """
    if prefixe:
        prefixe = prefixe.rstrip() + "\n"

    messages = []
    for i, bloc in enumerate(smooth_split(prefixe + mess, N=N, sep=sep, rep=rep)):
        if prefixe and i == 0:
            bloc = bloc[len(prefixe):]
            message = await messageable.send(prefixe + code_bloc(bloc, langage=langage))
        else:
            message = await messageable.send(code_bloc(bloc, langage=langage))
        messages.append(message)

    return messages


# Log dans #logs
async def log(arg, message, *, code=False, N=1990, sep='\n', rep='', prefixe="", langage=""):
    """Envoie un message dans le channel ``#logs``

    Retourne la liste des messages envoyés

    Args:
        arg (:class:`~discord.ext.commands.Context` | :class:`~discord.Guild` | :class:`~discord.Member` | :class:`~discord.abc.GuildChannel`): argument "connecté" au serveur, permettant de remonter aux channels
        message (:class:`str`): message à log
        code (:class:`bool`): si ``True``, log sous forme de bloc(s) de code (défaut ``False``)
        N, sep, rep: *identique à* :func:`.send_blocs`
        prefixe: *identique à* :func:`.send_code_blocs`, simplement ajouté avant ``message`` si ``code`` vaut ``False``
        language: *identique à* :func:`.send_code_blocs`, sans effet si `code` vaut ``False``

    Returns:
        :class:`list`\[:class:`discord.Message`\]
    """
    logchan = channel(arg, "logs")
    if code:
        return (await send_code_blocs(logchan, message, N=N, sep=sep, rep=rep, prefixe=prefixe, langage=langage))
    else:
        if prefixe:
            message = prefixe.rstrip() + "\n" + message
        return (await send_blocs(logchan, message, N=N, sep=sep, rep=rep))



### ---------------------------------------------------------------------------
### Autres fonctions diverses
### ---------------------------------------------------------------------------

async def create_context(bot, member, content):
    """Simule qu'un membre a envoyé une message dans son chan privé et "génère" le contexte associé

    Args:
        bot (:class:`.LGBot`): bot connecté au serveur
        member (:class:`discord.Member`): membre dont on veut simuler l'action. **Doit être inscrit en base** (pour avoir un chan privé)
        content (:class:`str`): message à "faire envoyer" au joueur, généralement une commande


    Utile notemment pour simuler des commandes à partir de clics sur des réactions.

    Returns:
        :class:`discord.ext.commands.Context`
    """
    chan = private_chan(member)
    message = (await chan.history(limit=1).flatten())[0]        # On a besoin de récupérer un message, ici le dernier de la conv privée
    message.author = member
    message.content = content
    return await bot.get_context(message)


def nom_role(role, prefixe=False):
    """Retourne le nom d'un rôle à partir de son *slug*

    Args:
        role (:class:`str`): :attr:`.bdd.Roles.slug` à chercher
        prefile (:class:`bool`): inclure le préfixe ou non

    Returns:
        :class:`str` (:attr:`.bdd.Roles.slug`) | ``None`` (si non trouvé)
    """
    if role := Roles.query.get(role):
        if prefixe:
            return f"{role.prefixe}{role.nom}"
        else:
            return role.nom
    else:
        return None


# Remove accents
def remove_accents(s):
    """Enlève les accents d'un chaîne, mais conserve les caractères spéciaux non linguistiques (emojis...)

    Version plus douce de ``unidecode.unidecode``.

    Args:
        s (:class:`str`): chaîne à désaccentuer

    Returns:
        :class:`str`
    """
    p = re.compile("([À-ʲΆ-ת])")      # Abracadabrax, c'est moche mais ça marche (source : tkt frère)
    return p.sub(lambda c: unidecode.unidecode(c.group()), s)


# Évaluation d'accolades
def eval_accols(rep, globals_=None, locals_=None, debug=False):
    """Replace chaque bloc entouré par des ``{}`` par leur évaluation Python.

    Args:
        globals_ (:class:`dict`): variables globales du contexte d'évaluation (passé à :func:`eval`)
        locals_ (:class:`dict`): variables locales du contexte d'évaluation (passé à :func:`eval`)
        debug (:class:`bool`): si ``True``, insère le message d'erreur (type et texte de l'exception dans le message) ensuite si une exception est levée durant l'évaluation (défaut ``False``)

    Penser à passer les :func:`globals` et :func:`locals` si besoin. Généralement, il faut passer :func:`locals` qui contient ``ctx``, etc... mais pas :func:`globals` si on veut bénéficier de tous les modules importés dans ``tools.py`` (tous les modules du projet ou presque).
    """
    if globals_ is None:
        globals_ = globals()
    if locals_ is None:
        locals_ = globals_

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
                        evrep += str(eval(expr, globals_, locals_))       # eval("expr") = expr
                    except Exception as e:
                        evrep += "{" + expr + "}"                   # Si erreur, on laisse {expr} non évaluée
                        if debug:
                            evrep += code(f"->!!! {e} !!!")
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
    """Formate une chaîne comme texte en **gras** dans Discord

    Args:
        s (:class:`str`): chaîne à formater

    Returns:
        :class:`str`
    """
    return f"**{s}**"

def ital(s):
    """Formate une chaîne comme texte en *italique* dans Discord

    Args:
        s (:class:`str`): chaîne à formater

    Returns:
        :class:`str`
    """
    return f"*{s}*"

def soul(s):
    """Formate une chaîne comme texte souligné dans Discord

    Args:
        s (:class:`str`): chaîne à formater

    Returns:
        :class:`str`
    """
    return f"__{s}__"

def strike(s):
    """Formate une chaîne comme texte barré dans Discord

    Args:
        s (:class:`str`): chaîne à formater

    Returns:
        :class:`str`
    """
    return f"~~{s}~~"

def code(s):
    """Formate une chaîne comme ``code`` (inline) dans Discord

    Args:
        s (:class:`str`): chaîne à formater

    Returns:
        :class:`str`
    """
    return f"`{s}`"

def code_bloc(s, langage=""):
    """Formate une chaîne comme un bloc de code dans Discord

    Args:
        s (:class:`str`): chaîne à formater
        langage (:class:`str`): langage du code, permet la coloration syntaxique (sur ordinateur uniquement)

    Langages supportés (non exhaustif ?) : ``asciidoc``, ``autohotkey``, ``bash``, ``coffeescript``, ``cpp`` (C++), ``cs`` (C#), ``css``, ``diff``, ``fix``, ``glsl``, ``ini``, ``json``, ``md``, (markdown), ``ml``, ``prolog``, ``py``, ``tex``, ``xl``, ``xml``

    Returns:
        :class:`str`
    """
    return f"```{langage}\n{s}```"

def quote(s):
    """Formate une chaîne comme citation (inline) dans Discord

    Args:
        s (:class:`str`): chaîne à formater

    Returns:
        :class:`str`
    """
    return f"> {s}"

def quote_bloc(s):
    """Formate une chaîne comme bloc de citation (multiline) dans Discord

    Args:
        s (:class:`str`): chaîne à formater

    Returns:
        :class:`str`
    """
    return f">>> {s}"

def spoiler(s):
    """Formate une chaîne comme spoiler (cliquer pour afficher) dans Discord

    Args:
        s (:class:`str`): chaîne à formater

    Returns:
        :class:`str`
    """
    return f"||{s}||"
