"""lg-rez / blocs / Outils divers et variés

Récupération d'objets Discord, décorateurs pour commandes, structures
d'interaction dans les channels, utilitaires d'emojis, de date/temps,
de formatage...

"""

import asyncio
import datetime
import functools
import re

import discord
import discord.utils
from discord.ext import commands
import unidecode

from lgrez import config, bdd
from lgrez.bdd import *
# on importe toutes les tables, plus simple pour y accéder depuis des
# réactions etc (via eval_accols)


# ---------------------------------------------------------------------------
# Utilitaires de récupération d'objets Discord (détectent les mentions)
# ---------------------------------------------------------------------------

#: Raccourci pour :func:`discord.utils.get`
get = discord.utils.get


def _find_by_mention_or_name(collec, val, pattern=None, must_be_found=False,
                             raiser=None):
    """Utilitaire pour la suite : trouve <val> dans <collec>

    [pattern]       Motif RegEx à utiliser pour la recherche
    [must_be_found] Si True, raise une ValueError si <val> est introuvable
    [raiser]        Nom de la fonction à envoyer dans l'exception si
                    introuvable
    """
    if not val:
        item = None
    elif pattern and (match := re.search(pattern, val)):
        item = get(collec, id=int(match.group(1)))
    else:
        item = get(collec, name=val)

    if must_be_found and not item:
        if raiser is None:
            raiser = "tools._find_by_mention_or_name"
        raise ValueError(f"{raiser} : Élément '{val}' introuvable")

    return item


def channel(nom, must_be_found=True):
    """Renvoie l'objet associé au salon ``#nom``.

    Args:
        nom (:class:`str`): nom du channel (texte/vocal/catégorie) ou sa
            mention (détection directe par regex)
        must_be_found (:class:`bool`): si ``True`` (défaut), raise une
            :exc:`ValueError` si le channel ``#nom`` n'existe pas
            (si ``False``, renvoie ``None``)

    Returns:
        :class:`discord.abc.GuildChannel`
    """
    return _find_by_mention_or_name(
        config.guild.channels, nom, pattern="<#([0-9]{18})>",
        must_be_found=must_be_found, raiser="tools.channel"
    )


def role(nom, must_be_found=True):
    """Renvoie l'objet associé au rôle ``@&nom``.

    Args:
        nom (:class:`str`): nom du rôle ou sa mention
            (détection directe par regex)
        must_be_found (:class:`bool`): si ``True`` (défaut), raise une
            :exc:`ValueError` si le channel ``@&nom`` n'existe pas
            (si ``False``, renvoie ``None``)

    Returns:
        :class:`discord.Role`
    """
    return _find_by_mention_or_name(
        config.guild.roles, nom, pattern="<@&([0-9]{18})>",
        must_be_found=must_be_found, raiser="tools.role"
    )


def member(nom, must_be_found=True):
    """Renvoie l'objet associé au membre ``@nom``.

    Args:
        nom (:class:`str`): nom du joueur ou sa mention
            (détection directe par regex)
        must_be_found (:class:`bool`): si ``True`` (défaut),
            raise une :exc:`ValueError` si le membre ``@nom`` n'existe pas
            (si ``False``, renvoie ``None``)

    Returns:
        :class:`discord.Member`
    """
    return _find_by_mention_or_name(
        config.guild.members, nom, pattern="<@!([0-9]{18})>",
        must_be_found=must_be_found, raiser="tools.member"
    )


def emoji(nom, must_be_found=True):
    """Renvoie l'objet associé à l'emoji ``:nom:``.

    Args:
        nom (:class:`str`): nom de l'emoji (texte/vocal/catégorie)
            ou son utilisation (détection directe par regex)
        must_be_found (:class:`bool`): si ``True`` (défaut), raise une
            :exc:`ValueError` si l'emoji ``:nom:`` n'existe pas
            (si ``False``, renvoie ``None``)

    Returns:
        :class:`discord.Emoji`
    """
    return _find_by_mention_or_name(
        config.guild.emojis, nom, pattern="<:.*:([0-9]{18})>",
        must_be_found=must_be_found, raiser="tools.emoji"
    )


# Appel aux MJs
def mention_MJ(arg):
    """Renvoie la mention ou le nom du rôle MJ

        - Si le joueur n'est pas un MJ, renvoie la mention de
          :attr:`config.Role.mj`
        - Sinon, renvoie son nom (pour ne pas rameuter tout le monde).

    Args:
        arg (:class:`~discord.Member` |\
            :class:`~discord.ext.commands.Context`):
            membre ou contexte d'un message envoyé par un membre

    Returns:
        :class:`str`
    """
    member = arg.author if isinstance(arg, commands.Context) else arg
    if (isinstance(member, discord.Member)
        and member.top_role >= config.Role.mj):
        # Pas un webhook et (au moins) MJ
        return f"@{config.Role.mj.name}"
    else:
        return config.Role.mj.mention


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class CommandExit(RuntimeError):
    """Fin de commande demandée.

    Lever cette exception force l'arrêt immédiat d'une commande,
    et empêche le bot de réagir à nouveau.

    Dérive de :exc:`RuntimeError`.
    """
    pass


# ---------------------------------------------------------------------------
# Décorateurs pour les différentes commandes, en fonction de leur usage
# ---------------------------------------------------------------------------

#: Décorateur pour commande (:func:`discord.ext.commands.check`) :
#: commande exécutable uniquement par un :attr:`MJ <.config.Role.mj>`
#: ou un webhook (tâche planifiée)
mjs_only = commands.check_any(
    commands.check(lambda ctx: ctx.message.webhook_id),
    commands.has_role(config.Role.get_raw("mj"))        # nom du rôle
)

#: Décorateur pour commandes d'IA (:func:`discord.ext.commands.check`) :
#: commande exécutable par un :attr:`MJ <.config.Role.mj>`, un
#: :attr:`Rédacteur <.config.Role.redacteur>` ou un webhook (tâche planifiée)
mjs_et_redacteurs = commands.check_any(
    mjs_only,
    commands.has_role(config.Role.get_raw("redacteur"))
)

#: Décorateur pour commande (:func:`discord.ext.commands.check`) :
#: commande exécutable uniquement par un joueur,
#: :attr:`vivant <.config.Role.joueur_en_vie>` ou
#: :attr:`mort <.config.Role.joueur_mort>`.
joueurs_only = commands.has_any_role(
    config.Role.get_raw("joueur_en_vie"),
    config.Role.get_raw("joueur_mort")
)

#: Décorateur pour commande (:func:`discord.ext.commands.check`) :
#: commande exécutable uniquement par un
#: :attr:`joueur vivant <.config.Role.joueur_en_vie>`
vivants_only = commands.has_role(config.Role.get_raw("joueur_en_vie"))


def private(callback):
    """Décorateur : commande utilisable dans son chan privé uniquement.

    Lors d'une invocation de la commande décorée hors d'un channel privé
    (commençant par :attr:`config.private_chan_prefix`), supprime le
    message d'invocation et exécute la commande dans le channel privé
    de l'invoqueur.

    Ce décorateur n'est utilisable que sur une commande définie dans un
    Cog. Si le joueur ayant utilisé la commande n'a pas de chan privé
    (pas en base), raise une :exc:`ValueError`.

    Utilisable en combinaison avec :func:`.joueurs_only` et
    :func:`.vivants_only` (pas avec les autres attention, vu que seuls
    les joueurs ont un channel privé).
    """
    @functools.wraps(callback)
    async def new_callback(self, ctx, *args, **kwargs):
        if not ctx.channel.name.startswith(config.private_chan_prefix):
            await ctx.message.delete()
            # chan dans le contexte d'appel = chan privé
            ctx.channel = Joueur.from_member(ctx.author).private_chan
            await ctx.send(
                f"{quote(ctx.message.content)}\n"
                f"{ctx.author.mention} :warning: Cette commande est interdite"
                f" en dehors de ta conv privée ! :warning:\n"
                f"J'ai supprimé ton message, et j'exécute la commande ici :"
            )
        # Dans tous les cas, appelle callback (avec le contexte modifié)
        return await callback(self, ctx, *args, **kwargs)

    return new_callback


# ---------------------------------------------------------------------------
# Commandes d'interaction avec les joueurs : input, boucles, confirmation...
# ---------------------------------------------------------------------------

# Commande générale, à utiliser à la place de bot.wait_for('message', ...)
async def wait_for_message(check, trigger_on_commands=False):
    """Attend le premier message reçu rencontrant les critères demandés.

    Surcouche de :meth:`discord.ext.commands.Bot.wait_for` permettant
    d'ignorer les commandes et de réagir au mot-clé ``stop``.

    Args:
        check (Callable[:class:`discord.Message` -> :class:`bool`]):
            fonction validant ou non chaque message.
        trigger_on_commands (bool): si ``False`` (défaut), un message
            respectant ``check`` sera ignoré si c'est une commande.

    Returns:
        :class:`discord.Message`

    Raises:
        .CommandExit: si le message est un des :obj:`.config.stop_keywords`
            (insensible à la casse), même si il respecte ``check``
    """
    stop_keywords = [kw.lower() for kw in config.stop_keywords]

    if trigger_on_commands:
        # on trigger en cas de STOP
        def trig_check(m):
            return (check(m) or m.content.lower() in stop_keywords)
    else:
        def trig_check(m):
            # on ne trigger pas sur les commandes et on trigger en cas de STOP
            return ((check(m)
                     and not m.content.startswith(config.bot.command_prefix))
                    or m.content.lower() in stop_keywords)

    message = await config.bot.wait_for('message', check=trig_check)
    if message.content.lower() in stop_keywords:
        if message.author == config.bot.user:
            raise CommandExit(ital("(Arrêt commande précédente)"))
        else:
            raise CommandExit("Arrêt demandé")
    else:
        return message


# Raccourci pratique
async def wait_for_message_here(ctx, trigger_on_commands=False):
    """Attend et renvoie le premier message reçu dans <ctx>.

    Surcouche de :func:`.wait_for_message` filtrant uniquement les
    messages envoyés dans ``ctx.channel`` par quelqu'un d'autre que
    le bot.

    Args:
        ctx (discord.ext.commands.Context): contexte d'une commande.
        trigger_on_commands: passé directement à
            :func:`.wait_for_message`.

    Returns:
        :class:`discord.Message`
    """
    def trig_check(message):
        return (message.channel == ctx.channel
                and message.author != ctx.bot.user)

    message = await wait_for_message(check=trig_check,
                                     trigger_on_commands=trigger_on_commands)
    return message


# Permet de boucler question -> réponse tant que la réponse ne
# vérifie pas les critères nécessaires
async def boucle_message(chan, in_message, condition_sortie, rep_message=None):
    """Boucle question/réponse jusqu'à qu'une condition soit vérifiée.

    Args:
        chan (discord.TextChannel): salon dans lequel lancer la boucle.
        condition_sortie (Callable[:class:`discord.Message` -> :class:`bool`]):
            fonction validant ou non chaque message.
        in_message (str): si défini, message à envoyer avant la boucle.
        rep_message (str): si défini, permet de définir un message de
            boucle différent de ``in_message`` (identique si ``None``).
            Doit être défini si ``in_message`` n'est pas défini.

    Returns:
        :class:`discord.Message`
    """
    if not rep_message:
        rep_message = in_message
    if not rep_message:
        raise ValueError("tools.boucle_message : `in_message` ou "
                         "`rep_message` doit être défini !")

    def check_chan(m):
        # Message envoyé pas par le bot et dans le bon chan
        return m.channel == chan and m.author != config.bot.user

    if in_message:
        await chan.send(in_message)
    rep = await wait_for_message(check_chan)
    while not condition_sortie(rep):
        await chan.send(rep_message)
        rep = await wait_for_message(check_chan)

    return rep


async def boucle_query(ctx, table, col=None, cible=None, filtre=None,
                       sensi=0.5, direct_detector=None, message=None):
    """Fait trouver à l'utilisateur une entrée de BDD d'après son nom.

    Args:
        ctx (discord.ext.commands.Context): contexte d'une commande.
        table (.bdd.base.TableMeta): table dans laquelle rechercher.
        col (~sqlalchemy.schema.Column): colonne dans laquelle rechercher
            (passé à :meth:`~.bdd.base.TableMeta.find_nearest`).
        cible (str): premier essai de cible (donnée par le joueur dans
            l'appel à une commande, par exemple).
        filtre: passé à :meth:`~.bdd.base.TableMeta.find_nearest`.
        sensi (float): sensibilité de la recherche (voir
            :meth:`~.bdd.TableMeta.find_nearest`).
        direct_detector (Callable[str] -> :attr:`table` | ``None``):
            pré-détecteur éventuel, appellé sur l'entrée utilisateur
            avant :meth:`~.bdd.TableMeta.find_nearest` ; si cette
            fonction renvoie un résultat, il est immédiatement renvoyé.
        message (str): si défini (et ``cible`` non défini), message à
            envoyer avant la boucle.

    Returns:
        Instance de :attr:`table` sélectionnée

    Attend que le joueur entre un nom, et boucle 5 fois au max
    (avant de l'insulter et de raise une erreur) pour chercher
    l'entrée la plus proche.
    """
    if message and not cible:
        await ctx.send(message)

    for i in range(5):
        if i == 0 and cible:
            # Au premier tour, si on a donné une cible
            rep = cible
        else:
            mess = await wait_for_message_here(ctx)
            rep = mess.content.strip("()[]{}<>")    # dézèlificateur

        # Détection directe
        if direct_detector:
            dir = direct_detector(rep)
            if dir:
                return dir

        # Sinon, recherche au plus proche
        nearest = table.find_nearest(rep, col=col, sensi=sensi, filtre=filtre,
                                     solo_si_parfait=False,
                                     match_first_word=True)

        if not nearest:
            await ctx.send("Aucune entrée trouvée, merci de réessayer :")

        elif len(nearest) == 1:         # Une seule correspondance
            result, score = nearest[0]
            if score == 1:          # parfait
                return result

            mess = await ctx.send("Je n'ai trouvé qu'une correspondance : "
                                  f"{bold(result)}.\nÇa part ?")
            if await yes_no(mess):
                return result
            else:
                await ctx.send("Bon d'accord, alors qui ?")

        else:
            text = ("Les résultats les plus proches de ton entrée "
                    "sont les suivants : \n")
            for i, (result, score) in enumerate(nearest[:10]):
                text += f"{emoji_chiffre(i + 1)}. {result} \n"
            mess = await ctx.send(
                text + ital("Tu peux les choisir en réagissant à ce "
                            "message, ou en répondant au clavier.")
            )
            n = await choice(mess, min(10, len(nearest)))
            return nearest[n - 1][0]

    await ctx.send("Et puis non, tiens !\nhttps://giphy.com/gifs/fuck-you-"
                   "middle-finger-ryan-stiles-x1kS7NRIcIigU")
    raise RuntimeError("Le joueur est trop con, je peux rien faire")


async def boucle_query_joueur(ctx, cible=None, message=None,
                              sensi=0.5, filtre=None):
    """Retourne un joueur (entrée de BDD) d'après son nom.

    Args:
        ctx (discord.ext.commands.Context): contexte d'une commande.
        cible (str): premier essai de cible (donnée par le joueur dans
            l'appel à une commande, par exemple).
        message (str): si défini (et ``cible`` non défini), message à
            envoyer avant la boucle.
        sensi (float): sensibilité de la recherche (voir
            :meth:`~.bdd.TableMeta.find_nearest`).
        filtre: passé à :meth:`~.bdd.TableMeta.find_nearest`.

    Returns:
        :class:`.bdd.Joueur`

    Attend que le joueur entre un nom de joueur, et boucle 5 fois au
    max (avant de l'insulter et de raise une erreur) pour chercher le
    plus proche joueur dans la table :class:`.bdd.Joueur`.
    """
    # Détection directe par ID / nom exact
    def direct_detector(rep):
        mem = member(rep, must_be_found=False)
        if mem:
            try:                    # Récupération du joueur
                return Joueur.from_member(mem)
            except ValueError:          # pas inscrit en base
                pass

        return None

    res = await boucle_query(ctx, Joueur, col=Joueur.nom, cible=cible,
                             sensi=sensi, filtre=filtre,
                             direct_detector=direct_detector,
                             message=message)
    return res


# Récupère un input par réaction
async def wait_for_react_clic(message, emojis={}, *, process_text=False,
                              text_filter=None, first_text=None,
                              post_converter=None,
                              trigger_all_reacts=False,
                              trigger_on_commands=False):
    """Ajoute des reacts à un message et attend une interaction.

    Args:
        message (discord.Message): message où ajouter les réactions.
        emojis (:class:`list` | :class:`dict`): reacts à ajouter,
            éventuellement associés à une valeur qui sera retournée
            si clic sur l'emoji.
        process_text (bool): si ``True``, détecte aussi la réponse par
            message et retourne le texte du message (défaut : ``False``).
        text_filter (Callable[:class:`str` -> :class:`bool`]): si
            ``process_text``, ne réagit qu'aux messages pour lesquels
            ``text_filter(message)`` renvoie ``True`` (défaut : tous).
        first_text (str): si ``process_text``, texte considéré comme la
            première réponse textuelle reçue (si il vérifie
            ``text_filter``, les emojis ne sont pas ajoutés et cette
            fonction retourne directement).
        post_converter (Callable[:class:`str` -> Any]): si
            ``process_text`` et que l'argument est défini, le message
            détecté est passé dans cette fonction avant d'être renvoyé.
        trigger_all_reacts (bool): si ``True``, détecte l'ajout de
            toutes les réactions (pas seulement celles dans ``emojis``)
            et renvoie l'emoji directement si il n'est pas dans
            ``emojis`` (défaut : ``False``).
        trigger_on_commands (bool): passé à :func:`.wait_for_message`.

    Returns:
        - :class:`str` -- représentant
            - le nom de l'emoji si ``emojis`` est une liste et clic sur
              une des reacts, ou si ``trigger_all_reacts`` vaut ``True``
              et ajout d'une autre react ;
            - le message reçu si ``process_text`` vaut ``True``, que
              ``post_converter`` n'est pas défini et réaction à un
              message ;
        - Any -- représentant
            - la valeur associée si ``emojis`` est un dictionnaire et
              clic sur une des reacts ;
            - la valeur retournée par ``post_converter`` si il est
              défini, que ``process_text`` vaut ``True`` et réaction
              à un message.
    """
    if not isinstance(emojis, dict):
        # Si emoji est une liste, on en fait un dictionnaire
        emojis = {emoji: emoji for emoji in emojis}

    if text_filter is None:
        def text_filter(text):
            return True

    if process_text and first_text:
        if text_filter(first_text):     # passe le filtre
            return post_converter(first_text) if post_converter else first_text

    try:
        # Si une erreur dans ce bloc, on supprime les emojis
        # du message (sinon c'est moche)
        for emoji in emojis:
            try:
                await message.add_reaction(emoji)
            except discord.errors.HTTPException:
                await message.channel.send(f"*Emoji {emoji} inconnu, ignoré*")

        emojis_names = {emoji.name if hasattr(emoji, "name")
                        else emoji: emoji for emoji in emojis}

        def react_check(react):
            # Check REACT : bon message, bon emoji, et pas react du bot
            name = react.emoji.name
            return (react.message_id == message.id
                    and react.user_id != config.bot.user.id
                    and (trigger_all_reacts or name in emojis_names))

        react_task = asyncio.create_task(
            config.bot.wait_for('raw_reaction_add', check=react_check)
        )

        if process_text:
            # Check MESSAGE : bon channel, pas du bot, et filtre
            def message_check(mess):
                return (mess.channel == message.channel
                        and mess.author != config.bot.user
                        and text_filter(mess.content))
        else:
            # On process DANS TOUS LES CAS, mais juste pour détecter
            # les stop_keywords si process_text == False
            def message_check(mess):
                return False

        mess_task = asyncio.create_task(
            wait_for_message(check=message_check,
                             trigger_on_commands=trigger_on_commands)
        )

        done, pending = await asyncio.wait([react_task, mess_task],
                                           return_when=asyncio.FIRST_COMPLETED)
        # Le bot attend ici qu'une des deux tâches aboutisse
        for task in pending:
            task.cancel()
        done_task = next(iter(done))        # done = tâche aboutie

        if done_task == react_task:         # Réaction
            emoji = done_task.result().emoji
            if trigger_all_reacts and emoji.name not in emojis_names:
                ret = emoji
            else:
                ret = (emojis.get(emoji)
                       or emojis.get(emojis_names.get(emoji.name)))

            for emoji in emojis:
                # On finit par supprimer les emojis mis par le bot
                await message.remove_reaction(emoji, config.bot.user)

        else:       # Réponse par message / STOP
            mess = done_task.result().content
            ret = post_converter(mess) if post_converter else mess
            await message.clear_reactions()

    except Exception:
        await message.clear_reactions()
        raise

    return ret


async def yes_no(message, first_text=None):
    """Demande une confirmation / question fermée à l'utilisateur.

    Surcouche de :func:`wait_for_react_clic` : ajoute les reacts
    ✅ et ❎ à un message et renvoie ``True`` ou ``False`` en fonction
    de l'emoji cliqué OU de la réponse textuelle détectée.

    Args:
        message (discord.Message): message où ajouter les réactions.
        first_text (str): passé à :func:`wait_for_react_clic`.

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
        message, emojis={"✅": True, "❎": False}, process_text=True,
        first_text=first_text,
        text_filter=lambda s: s.lower() in yes_no_words,
        post_converter=lambda s: s.lower() in yes_words,
    )

yes_no_maybe_i_dont_know_can_you_repeat_the_question = yes_no


async def choice(message, N, start=1, *, additionnal={}):
    """Demande à l'utilisateur de choisir entre plusieurs options numérotées.

    Surcouche de :func:`wait_for_react_clic` : ajoute des reacts
    chiffres (1️⃣, 2️⃣, 3️⃣...) et renvoie le numéro cliqué OU détecté
    par réponse textuelle.

    Args:
        message (discord.Message): message où ajouter les réactions.
        N (int): chiffre jusqu'auquel aller, inclus (``<= 10``).
        start (int): chiffre auquel commencer (entre ``0`` et ``N``,
            défaut ``1``).
        additionnal (dict[:class:`discord.Emoji` | :class:`str`, Any]):
            emojis optionnels à ajouter après les chiffres et valeur
            renvoyée si cliqué.

    Réponses textuelles reconnues : chiffres entre ``start`` et ``N``.

    Returns:
        :class:`int` (ou la valeur associée si emoji choisi dans
        ``additionnal``)
    """
    emojis = {emoji_chiffre(i): i for i in range(start, N + 1)}
    emojis.update(additionnal)
    return await wait_for_react_clic(
        message, emojis=emojis, process_text=True,
        text_filter=lambda s: s.isdigit() and start <= int(s) <= N,
        post_converter=int,
    )


async def sleep(chan, tps):
    """Attend un temps donné en avertissant l'utilisateur.

    Pause l'exécution d'une commande en affichant l'indicateur *typing*
    ("*LGBot est en train d'écrire...*") sur un salon.

    Permat d'afficher plusieurs messages d'affillée en laissant le temps
    de lire, tout en indiquant que le bot n'a pas fini d'écrire.

    Args:
        chan (discord.abc.Messageable): salon / contexte /... sur lequel
            attendre.
        tps (float): temps à attendre, en secondes.
    """
    async with chan.typing():
        await asyncio.sleep(tps)


# ---------------------------------------------------------------------------
# Utilitaires d'emojis
# ---------------------------------------------------------------------------

def montre(heure=None):
    """Renvoie l'emoji horloge le plus proche d'une heure donnée.

    Args:
        heure (str): heure à représenter, au format ``"XXh"`` ou
            ``"XXhMM"`` (défaut : heure actuelle).

    Returns:
        :class:`str` (🕧, 🕓, 🕝...)
    """
    if heure and isinstance(heure, str):
        heure, minute = heure.split("h")
        heure = int(heure) % 12
        minute = int(minute) % 60 if minute else 0
    else:
        now = datetime.datetime.now()
        heure = now.hour % 12
        minute = now.minute

    if minute >= 45:
        heure = (heure + 1) % 12

    if 15 < minute < 45:        # Demi heure
        L = ["\N{CLOCK FACE TWELVE-THIRTY}",    "\N{CLOCK FACE ONE-THIRTY}",
             "\N{CLOCK FACE TWO-THIRTY}",       "\N{CLOCK FACE THREE-THIRTY}",
             "\N{CLOCK FACE FOUR-THIRTY}",      "\N{CLOCK FACE FIVE-THIRTY}",
             "\N{CLOCK FACE SIX-THIRTY}",       "\N{CLOCK FACE SEVEN-THIRTY}",
             "\N{CLOCK FACE EIGHT-THIRTY}",     "\N{CLOCK FACE NINE-THIRTY}",
             "\N{CLOCK FACE TEN-THIRTY}",       "\N{CLOCK FACE ELEVEN-THIRTY}"]
    else:                       # Heure pile
        L = ["\N{CLOCK FACE TWELVE OCLOCK}",    "\N{CLOCK FACE ONE OCLOCK}",
             "\N{CLOCK FACE TWO OCLOCK}",       "\N{CLOCK FACE THREE OCLOCK}",
             "\N{CLOCK FACE FOUR OCLOCK}",      "\N{CLOCK FACE FIVE OCLOCK}",
             "\N{CLOCK FACE SIX OCLOCK}",       "\N{CLOCK FACE SEVEN OCLOCK}",
             "\N{CLOCK FACE EIGHT OCLOCK}",     "\N{CLOCK FACE NINE OCLOCK}",
             "\N{CLOCK FACE TEN OCLOCK}",       "\N{CLOCK FACE ELEVEN OCLOCK}"]
    return L[heure]


def emoji_chiffre(chiffre, multi=False):
    """Renvoie l'emoji / les emojis chiffre correspondant à un chiffre/nombre.

    Args:
        chiffre (int): chiffre/nombre à représenter.
        multi (bool): si ``True``, ``chiffre`` peut être n'importe quel
            entier positif, dont les chiffres seront convertis
            séparément ; sinon (par défaut), ``chiffre`` doit être un
            entier entre ``0`` et ``10``.

    Returns:
        :class:`str` (0️⃣, 1️⃣, 2️⃣...)
    """
    if isinstance(chiffre, int) and 0 <= chiffre <= 10:
        return ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣",
                "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][chiffre]
    elif multi and str(chiffre).isdigit():
        return "".join([emoji_chiffre(int(chr)) for chr in str(chiffre)])
    else:
        raise ValueError("L'argument de tools.emoji_chiffre doit être un "
                         "entier entre 0 et 10 OU un entier positif avec "
                         "multi=True")


def super_chiffre(chiffre, multi=False):
    """Renvoie le(s) caractère(s) exposant correspondant à un chiffre/nombre.

    Args:
        chiffre (int): chiffre/nombre à représenter.
        multi (bool): si ``True``, ``chiffre`` peut être n'importe quel
            entier positif, dont les chiffres seront convertis
            séparément ; sinon (par défaut), ``chiffre`` doit être un
            entier entre ``0`` et ``9``.

    Returns:
        :class:`str` (⁰, ¹, ²...)
    """
    if isinstance(chiffre, int) and 0 <= chiffre <= 9:
        return ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"][chiffre]
    elif multi and str(chiffre).isdigit():
        return ''.join([super_chiffre(int(chr)) for chr in str(chiffre)])
    else:
        raise ValueError("L'argument de tools.super_chiffre doit être un "
                         "entier entre 0 et 9 OU un entier positif avec "
                         "multi=True")


def sub_chiffre(chiffre, multi=False):
    """Renvoie le(s) caractère(s) indice correspondant à un chiffre/nombre.

    Args:
        chiffre (int): chiffre/nombre à représenter.
        multi (bool): si ``True``, ``chiffre`` peut être n'importe quel
            entier positif, dont les chiffres seront convertis
            séparément ; sinon (par défaut), ``chiffre`` doit être un
            entier entre ``0`` et ``9``.

    Returns:
        :class:`str` (₀, ₁, ₂...)
    """
    if isinstance(chiffre, int) and 0 <= chiffre <= 9:
        return ["₀", "₁", "₂", "₃", "₄", "₅", "₆", "₇", "₈", "₉"][chiffre]
    elif multi and str(chiffre).isdigit():
        return ''.join([sub_chiffre(int(c)) for c in str(chiffre)])
    else:
        raise ValueError("L'argument de tools.sub_chiffre doit être un "
                         "entier entre 0 et 9 OU un entier positif avec "
                         "multi=True")


# ---------------------------------------------------------------------------
# Utilitaires de date / temps, notemment liées aux horaires de jeu
# ---------------------------------------------------------------------------

def heure_to_time(heure):
    """Convertit l'écriture d'une heure en objet :class:`datetime.time`.

    Args:
        heure (str): heure au format ``HHh``, ``HHhMM`` ou ``HH:MM``.

    Returns:
        :class:`datetime.time`

    Raises:
        ValueError: conversion impossible (mauvais format)
    """
    try:
        if "h" in heure:
            hh, mm = heure.split("h")
        else:
            hh, mm = heure.split(":")
        return datetime.time(int(hh), int(mm) if mm else 0)
    except ValueError as exc:
        raise ValueError(f"Valeur \"{heure}\" non convertible "
                         "en temps") from exc


def time_to_heure(tps, sep="h", force_minutes=False):
    """Convertit un objet :class:`datetime.time` en heure.

    (version maison de :meth:`datetime.time.strftime`)

    Args:
        tps (datetime.time): temps à convertir.
        sep (str): séparateur heures / minutes à utiliser
            (défaut ``"h"``).
        force_minutes (bool): si ``False`` (défaut), les minutes
            ne sont indiquées que si différentes de ``0``.

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


def next_occurence(tps):
    """Renvoie la prochaine occurence temporelle d'une heure donnée.

    Renvoie le prochain timestamp arrivant DANS LES HORAIRES DU JEU :
    entre :func:`.tools.fin_pause` et :func:`.tools.debut_pause`.

    Args:
        tps (datetime.time): heure dont on veut connaître
            la prochaine occurence.

    Returns:
        :class:`datetime.datetime`
    """
    now = datetime.datetime.now()
    jour = now.date()
    if tps < now.time():
        # Si plus tôt dans la journée que l'heure actuelle,
        # on réfléchit comme si on était demain
        jour += datetime.timedelta(days=1)

    test_dt = datetime.datetime.combine(jour, tps)
    if test_dt < debut_pause() and not en_pause():
        # Prochaine occurence avant la pause : OK
        return test_dt

    # Sinon, programmer après la pause
    finp = fin_pause()
    jour = finp.date()
    if tps < finp.time():
        # Si plus tôt dans la journée que l'heure de reprise,
        # on réfléchit comme si on était le lendemain
        jour += datetime.timedelta(days=1)

    return datetime.datetime.combine(jour, tps)


def debut_pause():
    """Renvoie le timestamp correspondant au prochain vendredi 19h.

    Returns:
        :class:`datetime.datetime`
    """
    pause_time = datetime.time(hour=19)
    pause_wday = 4          # Vendredi

    now = datetime.datetime.now()
    jour = now.date()
    if pause_time < now.time():
        # Si plus tôt dans la journée que l'heure actuelle,
        # on réfléchit comme si on était demain
        jour += datetime.timedelta(days=1)

    ddays = (pause_wday - jour.weekday()) % 7
    # Jour décalé du nombre de jours avant vendredi
    pause_jour = jour + datetime.timedelta(days=ddays)
    return datetime.datetime.combine(pause_jour, pause_time)


def fin_pause():
    """Renvoie le timestamp correspondant au prochain dimanche 19h.

    Returns:
        :class:`datetime.datetime`
    """
    reprise_time = datetime.time(hour=19)
    reprise_wday = 6        # Dimanche

    now = datetime.datetime.now()
    jour = now.date()
    if reprise_time < now.time():
        # Si plus tôt dans la journée que l'heure actuelle,
        # on réfléchit comme si on était demain
        jour += datetime.timedelta(days=1)

    ddays = (reprise_wday - jour.weekday()) % 7
    # Jour décalé du nombre de jours avant vendredi
    reprise_jour = jour + datetime.timedelta(days=ddays)
    return datetime.datetime.combine(reprise_jour, reprise_time)


def en_pause():
    """Détermine si le jeu est actuellement en pause hebdomadaire.

    Si il n'y a pas de pause (:func:`.fin_pause` = :func:`.debut_pause`),
    renvoie toujours ``False``.

    Returns:
        :class:`bool`
    """
    return fin_pause() < debut_pause()


# ---------------------------------------------------------------------------
# Split et log
# ---------------------------------------------------------------------------

def smooth_split(mess, N=1990, sep='\n', rep=''):
    """Sépare un message en une blocs moins longs qu'une limite donnée.

    Très utile pour envoyer des messages de (potentiellement) plus de
    2000 caractères (limitation Discord).

    Args:
        mess (str): message à découper.
        N (int): taille maximale des messages formés (défaut ``1990``,
            pour avoir un peu de marge par rapport à la limitation, et
            permettre d'entourer de ``````` par exemple)
        sep (str): caractères où séparer préférentiellement le texte
            (défaut : sauts de ligne). Si ``mess`` contient une
            sous-chaîne plus longue que ``N`` ne contenant pas ``sep``,
            le message sera tronqué à la limite.
        rep (str) : chaîne ajoutée à la fin de chaque message formé
            (tronqué du séparateur final) (défaut : aucune).

    Returns:
        :class:`list`\[:class:`str`\]
    """
    mess = str(mess)
    LM = []             # Liste des messages
    psl = 0             # indice du Précédent Saut de Ligne
    L = len(mess)
    while psl + N < L:
        if mess.count(sep, psl, psl + N + len(sep)):
            # +len(sep) parce que si sep est à la fin, on le dégage
            i = psl + N - mess[psl: psl + N + len(sep)][::-1].find(sep)
            # un peu sombre mais vrai, tkt frère
            LM.append(mess[psl: i] + rep)
            psl = i + 1     # on élimine le \n
        else:
            LM.append(mess[psl: psl + N] + rep)
            psl += N

    if psl < L:
        LM.append(mess[psl:])   # ce qui reste
    return LM


async def send_blocs(messageable, mess, *, N=1990, sep='\n', rep=''):
    """Envoie un message en le coupant en blocs si nécaissaire.

    Surcouche de :func:`.smooth_split` envoyant directement
    les messages formés.

    Args:
        messageable (discord.abc.Messageable): objet où envoyer le
            message (:class:`~discord.ext.commands.Context` ou
            :class:`~discord.TextChannel`).
        mess (str): message à envoyer
        N, sep, rep: passé à :func:`.smooth_split`.

    Returns:
        list[discord.Message]: La liste des messages envoyés.
    """
    messages = []
    for bloc in smooth_split(mess, N=N, sep=sep, rep=rep):
        messages.append(await messageable.send(bloc))

    return messages


async def send_code_blocs(messageable, mess, *, N=1990, sep='\n', rep='',
                          prefixe="", langage=""):
    """Envoie un (potentiellement long) message sous forme de bloc(s) de code.

    Équivalent de :func:`.send_blocs` avec formatage de chaque bloc
    dans un bloc de code.

    Args:
        messageable, mess, N, sep, rep: voir :func:`.send_blocs`.
        prefixe (str): texte optionnel à mettre hors des code blocs,
            au début du premier message.
        language (str): voir :func:`.code_bloc`.

    Returns:
        list[discord.Message]: La liste des messages envoyés.
    """
    mess = str(mess)

    if prefixe:
        prefixe = prefixe.rstrip() + "\n"

    blocs = smooth_split(prefixe + mess, N=N, sep=sep, rep=rep)

    messages = []
    for i, bloc in enumerate(blocs):
        if prefixe and i == 0:
            bloc = bloc[len(prefixe):]
            message = await messageable.send(
                prefixe + code_bloc(bloc, langage=langage))
        else:
            message = await messageable.send(code_bloc(bloc, langage=langage))
        messages.append(message)

    return messages


async def log(message, *, code=False, N=1990, sep='\n', rep='',
              prefixe="", langage=""):
    """Envoie un message dans le channel :attr:`config.Channel.logs`.

    Surcouche de :func:`.send_blocs` / :func:`.send_code_blocs`.

    Args:
        message (str): message à log.
        code (bool): si ``True``, log sous forme de bloc(s) de code
            (défaut ``False``).
        N, sep, rep: passé à :func:`.send_blocs` /
            :func:`.send_code_blocs`.
        prefixe: voir :func:`.send_code_blocs`, simplement ajouté avant
            ``message`` si ``code`` vaut ``False``.
        language: *identique à* :func:`.send_code_blocs`, ignoré
            si `code` vaut ``False``.

    Returns:
        list[discord.Message]: La liste des messages envoyés.
    """
    logchan = config.Channel.logs
    if code:
        return (await send_code_blocs(logchan, message, N=N, sep=sep, rep=rep,
                                      prefixe=prefixe, langage=langage))
    else:
        if prefixe:
            message = prefixe.rstrip() + "\n" + message
        return (await send_blocs(logchan, message, N=N, sep=sep, rep=rep))


# ---------------------------------------------------------------------------
# Autres fonctions diverses
# ---------------------------------------------------------------------------

async def create_context(member, content):
    """Génère le contexte associé au message d'un membre dans son chan privé.

    Args:
        member (discord.Member): membre dont on veut simuler l'action.
            **Doit être inscrit en base** (pour avoir un chan privé).
        content (str): message à "faire envoyer" au joueur,
            généralement une commande.

    Utile notemment pour simuler des commandes à partir de clics sur
    des réactions.

    Returns:
        :class:`discord.ext.commands.Context`
    """
    chan = Joueur.from_member(member).private_chan
    message = (await chan.history(limit=1).flatten())[0]
    # On a besoin de récupérer un message, ici le dernier de la conv privée
    message.author = member
    message.content = content
    ctx = await config.bot.get_context(message)
    return ctx


def remove_accents(text):
    """Enlève les accents d'un chaîne, mais conserve les caractères spéciaux.

    Version plus douce de ``unidecode.unidecode``, conservant notemment
    les emojis, ...

    Args:
        text (str): chaîne à désaccentuer.

    Returns:
        :class:`str`
    """
    p = re.compile("([À-ʲΆ-ת])")
    # Abracadabrax, c'est moche mais ça marche (source : tkt frère)
    return p.sub(lambda c: unidecode.unidecode(c.group()), text)


# Évaluation d'accolades
def eval_accols(rep, globals_=None, locals_=None, debug=False):
    """Replace chaque bloc entouré par des ``{}`` par leur évaluation Python.

    Args:
        globals_ (dict): variables globales du contexte d'évaluation
            (passé à :func:`eval`).
        locals_ (dict): variables locales du contexte d'évaluation
            (passé à :func:`eval`).
        debug (bool): si ``True``, insère le message d'erreur (type et
            texte de l'exception) dans le message à l'endroit où une
            exception est levée durant l'évaluation (défaut ``False``).

    Penser à passer les :func:`globals` et :func:`locals` si besoin.
    Généralement, il faut passer :func:`locals` qui contient ``ctx``,
    etc... mais pas :func:`globals` si on veut bénéficier de tous les
    modules importés dans ``tools.py``.
    """
    if globals_ is None:
        globals_ = globals()
    if locals_ is None:
        locals_ = globals_

    if "{" not in rep:          # Si pas d'expressions, on renvoie direct
        return rep

    evrep = ""                  # Réponse évaluée
    expr = ""                   # Expression à évaluer
    noc = 0                     # Nombre de { non appariés
    for car in rep:
        if car == "{":
            if noc:             # Expression en cours :
                expr += car         # on garde le {
            noc += 1
        elif car == "}":
            noc -= 1
            if noc:             # idem
                expr += car
            else:               # Fin d'une expression
                try:                # On essaie d'évaluer la chaîne
                    evrep += str(eval(expr, globals_, locals_))
                except Exception as e:
                    # Si erreur, on laisse {expr} non évaluée
                    evrep += "{" + expr + "}"
                    if debug:
                        evrep += code(f"->!!! {e} !!!")
                expr = ""
        elif noc:               # Expression en cours
            expr += car
        else:                   # Pas d'expression en cours
            evrep += car
    if noc:     # Si expression jamais finie (nombre impair de {)
        evrep += "{" + expr
    return evrep


# ---------------------------------------------------------------------------
# Utilitaires de formatage de texte
# ---------------------------------------------------------------------------

def bold(text):
    """Formate une chaîne comme texte en **gras** dans Discord.

    Args:
        text (str): chaîne à formater.

    Returns:
        :class:`str`
    """
    return f"**{text}**"


def ital(text):
    """Formate une chaîne comme texte en *italique* dans Discord.

    Args:
        text (str): chaîne à formater.

    Returns:
        :class:`str`
    """
    return f"*{text}*"


def soul(text):
    """Formate une chaîne comme texte souligné dans Discord.

    Args:
        text (str): chaîne à formater.

    Returns:
        :class:`str`
    """
    return f"__{text}__"


def strike(text):
    """Formate une chaîne comme texte barré dans Discord.

    Args:
        text (str): chaîne à formater.

    Returns:
        :class:`str`
    """
    return f"~~{text}~~"


def code(text):
    """Formate une chaîne comme ``code`` (inline) dans Discord.

    Args:
        text (str): chaîne à formater.

    Returns:
        :class:`str`
    """
    return f"`{text}`"


def code_bloc(text, langage=""):
    """Formate une chaîne comme un bloc de code dans Discord.

    Args:
        text (str): chaîne à formater.
        langage (str): langage du code, pour coloration syntaxique.

    Langages supportés (non exhaustif ?) : ``asciidoc``, ``autohotkey``,
    ``bash``, ``coffeescript``, ``cpp`` (C++), ``cs`` (C#), ``css``,
    ``diff``, ``fix``, ``glsl``, ``ini``, ``json``, ``md``, (markdown),
    ``ml``, ``prolog``, ``py``, ``tex``, ``xl``, ``xml``

    Returns:
        :class:`str`
    """
    return f"```{langage}\n{text}```"


def quote(text):
    """Formate une chaîne comme citation (inline) dans Discord.

    Args:
        text (str): chaîne à formater.

    Returns:
        :class:`str`
    """
    return f"> {text}"


def quote_bloc(text):
    """Formate une chaîne comme bloc de citation (multiline) dans Discord.

    Args:
        text (str): chaîne à formater.

    Returns:
        :class:`str`
    """
    return f">>> {text}"


def spoiler(text):
    """Formate une chaîne comme spoiler (cliquer pour afficher) dans Discord.

    Args:
        text (str): chaîne à formater.

    Returns:
        :class:`str`
    """
    return f"||{text}||"
