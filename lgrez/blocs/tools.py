"""lg-rez / blocs / Outils divers et variés

Récupération d'objets Discord, décorateurs pour commandes, structures
d'interaction dans les channels, utilitaires d'emojis, de date/temps,
de formatage...

"""

from __future__ import annotations

import asyncio
import datetime
import functools
import re
import string
import typing
from typing import Any, Callable
import warnings

import discord
import discord.utils
from discord.ext import commands
import unidecode

from lgrez import config, bdd
from lgrez.blocs import one_command
from lgrez.bdd import *

# on importe toutes les tables, plus simple pour y accéder depuis des
# réactions etc (via eval_accols)


# ---------------------------------------------------------------------------
# Utilitaires de récupération d'objets Discord (détectent les mentions)
# ---------------------------------------------------------------------------


def _get(collec, **attrs):
    for elem in collec:
        if all(getattr(elem, attr) == value for attr, value in attrs.items()):
            return elem
    return None


_T = typing.TypeVar("_T")


def _find_by_mention_or_name(
    collec: typing.Collection[_T],
    val: str,
    pattern: str | None = None,
    must_be_found: bool = False,
    raiser: str | None = None,
) -> _T | None:
    """Utilitaire pour la suite : trouve un élément dans une liste.

    Args:
        collection: liste d'éléments.
        val: nom de l'élément à trouver, correspondant à son attribut
            ``name`` ou respectant une regex.
        pattern: motif regex à utiliser pour la recherche, si besoin.
        must_be_found: Si ``True``, raise une :exc:`ValueError` si
            ``val`` est introuvable.
        raiser: nom de la fonction à envoyer dans l'exception si
            introuvable (défaut : cette fonction).

    Returns:
        L'élément recherché, si on l'a trouvé.

    Raises:
        ValueError: Si ``must_be_found`` est ``True`` et que l'élément
            n'a pas été trouvé.
    """
    if not val:
        item = None
    elif pattern and (match := re.search(pattern, val)):
        item = _get(collec, id=int(match.group(1)))
    else:
        item = _get(collec, name=val)

    if must_be_found and not item:
        if raiser is None:
            raiser = "tools._find_by_mention_or_name"
        raise ValueError(f"{raiser} : Élément '{val}' introuvable")

    return item


@typing.overload
def channel(nom: str, must_be_found: typing.Literal[True] = True) -> discord.TextChannel | discord.CategoryChannel:
    ...


@typing.overload
def channel(nom: str, must_be_found: typing.Literal[False]) -> discord.TextChannel | discord.CategoryChannel | None:
    ...


def channel(nom, must_be_found=True):
    """Renvoie l'objet associé au salon ``#nom``.

    Args:
        nom: nom du channel (texte/vocal/catégorie) ou sa
            mention (détection directe par regex)
        must_be_found: si ``True`` (défaut), raise une
            :exc:`ValueError` si le channel ``#nom`` n'existe pas
            (si ``False``, renvoie ``None``)

    Returns:
        Le salon ou la catégorie Discord correspondant.
    """
    return _find_by_mention_or_name(
        config.guild.channels, nom, pattern="<#([0-9]{18})>", must_be_found=must_be_found, raiser="tools.channel"
    )


@typing.overload
def role(nom: str, must_be_found: typing.Literal[True] = True) -> discord.Role:
    ...


@typing.overload
def role(nom: str, must_be_found: typing.Literal[False] = True) -> discord.Role | None:
    ...


def role(nom, must_be_found=True):
    """Renvoie l'objet associé au rôle ``@&nom``.

    Args:
        nom: nom du rôle ou sa mention
            (détection directe par regex)
        must_be_found: si ``True`` (défaut), raise une
            :exc:`ValueError` si le channel ``@&nom`` n'existe pas
            (si ``False``, renvoie ``None``)

    Returns:
        Le rôle Discord correspondant.
    """
    return _find_by_mention_or_name(
        config.guild.roles, nom, pattern="<@&([0-9]{18})>", must_be_found=must_be_found, raiser="tools.role"
    )


@typing.overload
def member(nom: str, must_be_found: typing.Literal[True] = True) -> discord.Member:
    ...


@typing.overload
def member(nom: str, must_be_found: typing.Literal[False] = True) -> discord.Member | None:
    ...


def member(nom, must_be_found=True):
    """Renvoie l'objet associé au membre ``@nom``.

    Args:
        nom: nom du joueur ou sa mention
            (détection directe par regex)
        must_be_found: si ``True`` (défaut),
            raise une :exc:`ValueError` si le membre ``@nom`` n'existe pas
            (si ``False``, renvoie ``None``)

    Returns:
        Le membre Discord correspondant.
    """
    return _find_by_mention_or_name(
        config.guild.members, nom, pattern="<@!([0-9]{18})>", must_be_found=must_be_found, raiser="tools.member"
    )


@typing.overload
def emoji(nom: str, must_be_found: typing.Literal[True] = True) -> discord.Emoji:
    ...


@typing.overload
def emoji(nom: str, must_be_found: typing.Literal[False] = True) -> discord.Emoji | None:
    ...


def emoji(nom, must_be_found=True):
    """Renvoie l'objet associé à l'emoji ``:nom:``.

    Args:
        nom: nom de l'emoji (texte/vocal/catégorie)
            ou son utilisation (détection directe par regex)
        must_be_found: si ``True`` (défaut), raise une
            :exc:`ValueError` si l'emoji ``:nom:`` n'existe pas
            (si ``False``, renvoie ``None``)

    Returns:
        L'emoji Discord correspondant.
    """
    return _find_by_mention_or_name(
        config.guild.emojis, nom, pattern="<:.*:([0-9]{18})>", must_be_found=must_be_found, raiser="tools.emoji"
    )


# Appel aux MJs
def mention_MJ(arg: discord.Member | commands.Context) -> str:
    """Renvoie la mention ou le nom du rôle MJ

        - Si le joueur n'est pas un MJ, renvoie la mention de
          :attr:`config.Role.mj`
        - Sinon, renvoie son nom (pour ne pas rameuter tout le monde).

    Args:
        arg: Le membre ou le contexte d'un message envoyé par un membre.

    Returns:
        La chaîne à utiliser pour mentionner le rôle MJ.
    """
    member = arg.author if isinstance(arg, commands.Context) else arg
    if isinstance(member, discord.Member) and member.top_role >= config.Role.mj:
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
    commands.check(lambda ctx: ctx.message.webhook_id), commands.has_role(config.Role.get_raw("mj"))  # nom du rôle
)

#: Décorateur pour commandes d'IA (:func:`discord.ext.commands.check`) :
#: commande exécutable par un :attr:`MJ <.config.Role.mj>`, un
#: :attr:`Rédacteur <.config.Role.redacteur>` ou un webhook (tâche planifiée)
mjs_et_redacteurs = commands.check_any(mjs_only, commands.has_role(config.Role.get_raw("redacteur")))

#: Décorateur pour commande (:func:`discord.ext.commands.check`) :
#: commande exécutable uniquement par un joueur,
#: :attr:`vivant <.config.Role.joueur_en_vie>` ou
#: :attr:`mort <.config.Role.joueur_mort>`.
joueurs_only = commands.has_any_role(config.Role.get_raw("joueur_en_vie"), config.Role.get_raw("joueur_mort"))

#: Décorateur pour commande (:func:`discord.ext.commands.check`) :
#: commande exécutable uniquement par un
#: :attr:`joueur vivant <.config.Role.joueur_en_vie>`
vivants_only = commands.has_role(config.Role.get_raw("joueur_en_vie"))

_PS = typing.ParamSpec("_PS")
_RV = typing.TypeVar("_RV")


def private(callback: Callable[_PS, _RV]) -> Callable[_PS, _RV]:
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
    async def new_callback(cog, ctx, *args, **kwargs):
        if not ctx.channel.name.startswith(config.private_chan_prefix):
            await ctx.message.delete()
            await one_command.remove_from_in_command(ctx)
            # chan dans le contexte d'appel = chan privé
            ctx.channel = Joueur.from_member(ctx.author).private_chan
            await ctx.send(
                f"{quote(ctx.message.content)}\n"
                f"{ctx.author.mention} :warning: Cette commande est "
                f"interdite en dehors de ta conv privée ! :warning:\n"
                f"J'ai supprimé ton message, et j'exécute la commande ici :"
            )
            await one_command.add_to_in_command(ctx)
        # Dans tous les cas, appelle callback (avec le contexte modifié)
        return await callback(cog, ctx, *args, **kwargs)

    return new_callback


# ---------------------------------------------------------------------------
# Commandes d'interaction avec les joueurs : input, boucles, confirmation...
# ---------------------------------------------------------------------------

# Commande générale, à utiliser à la place de bot.wait_for('message', ...)
async def wait_for_message(
    check: Callable[[discord.Message], bool],
    trigger_on_commands: bool = False,
    chan: discord.TextChannel | None = None,
) -> discord.Message:
    """Attend le premier message reçu rencontrant les critères demandés.

    Surcouche de :meth:`discord.ext.commands.Bot.wait_for` permettant
    d'ignorer les commandes et de réagir au mot-clé ``stop``.

    Args:
        check: fonction validant ou non chaque message.
        trigger_on_commands: si ``False`` (défaut), un message
            respectant ``check`` sera ignoré si c'est une commande.
        chan (discord.TextChannel): le channel dans lequel le message
            est attendu (si applicable). Si ``None``, les messages
            d'arrêt (:obj:`config.stop_keywords`) peuvent ne pas être
            détectés (la fonction émettra un warning en ce sens).

    Returns:
        Le message reçu.

    Raises:
        .CommandExit: si le message est un des :obj:`.config.stop_keywords`
            (insensible à la casse), même si il respecte ``check``
    """
    stop_keywords = [kw.lower() for kw in config.stop_keywords]

    if chan:

        def stop_check(m):
            return m.channel == chan and m.content.lower() in stop_keywords

    else:
        warnings.warn(
            "lgrez.tools.wait_for_message called with `chan=None`, stop messages may be ignored.", stacklevel=2
        )

        def stop_check(m):
            return False

    if trigger_on_commands:
        # on trigger en cas de STOP
        def trig_check(m):
            return check(m) or stop_check(m)

    else:

        def trig_check(m):
            # on ne trigger pas sur les commandes et on trigger en cas de STOP
            return (check(m) and not m.content.startswith(config.bot.command_prefix)) or stop_check(m)

    message = await config.bot.wait_for("message", check=trig_check)
    if message.content.lower() in stop_keywords:
        if message.author == config.bot.user:
            raise CommandExit(ital("(Arrêt commande précédente)"))
        else:
            raise CommandExit("Arrêt demandé")
    else:
        return message


# Raccourci pratique
async def wait_for_message_here(ctx: commands.Context, trigger_on_commands: bool = False) -> discord.Message:
    """Attend et renvoie le premier message reçu dans <ctx>.

    Surcouche de :func:`.wait_for_message` filtrant uniquement les
    messages envoyés dans ``ctx.channel`` par quelqu'un d'autre que
    le bot.

    Args:
        ctx: le contexte d'une commande.
        trigger_on_commands: passé à :func:`.wait_for_message`.

    Returns:
        :class:`discord.Message`
    """

    def trig_check(message):
        return message.channel == ctx.channel and message.author != ctx.bot.user

    message = await wait_for_message(check=trig_check, chan=ctx.channel, trigger_on_commands=trigger_on_commands)
    return message


# Permet de boucler question -> réponse tant que la réponse ne
# vérifie pas les critères nécessaires
async def boucle_message(
    chan: discord.TextChannel,
    in_message: str,
    condition_sortie: Callable[[discord.Message], bool],
    rep_message: str | None = None,
) -> discord.Message:
    """Boucle question/réponse jusqu'à qu'une condition soit vérifiée.

    Args:
        chan: salon dans lequel lancer la boucle.
        condition_sortie: fonction validant ou non chaque message.
        in_message: si défini, message à envoyer avant la boucle.
        rep_message: si défini, permet de définir un message de
            boucle différent de ``in_message`` (identique si ``None``).
            Doit être défini si ``in_message`` n'est pas défini.

    Returns:
        Le message final validant les critères.
    """
    if not rep_message:
        rep_message = in_message
    if not rep_message:
        raise ValueError("tools.boucle_message : `in_message` ou `rep_message` doit être défini !")

    def check_chan(m):
        # Message envoyé pas par le bot et dans le bon chan
        return m.channel == chan and m.author != config.bot.user

    if in_message:
        await chan.send(in_message)
    rep = await wait_for_message(check_chan, chan=chan)
    while not condition_sortie(rep):
        await chan.send(rep_message)
        rep = await wait_for_message(check_chan, chan=chan)

    return rep


_Obj = typing.TypeVar("_Obj", bound=bdd.base.TableBase)


async def boucle_query(
    ctx: commands.Context,
    table: type[_Obj],
    col: sqlalchemy.Column | None = None,
    cible: str | None = None,
    filtre: sqlalchemy.sql.expression.BinaryExpression | None = None,
    sensi: float = 0.5,
    direct_detector: Callable[[str], _Obj] | None = None,
    message: str | None = None,
) -> _Obj:
    """Fait trouver à l'utilisateur une entrée de BDD d'après son nom.

    Args:
        ctx: contexte d'une commande.
        table: table dans laquelle rechercher.
        col: colonne dans laquelle rechercher (passé à :meth:`~.bdd.base.TableMeta.find_nearest`).
        cible: premier essai de cible (donnée par le joueur dans l'appel à une commande, par exemple).
        filtre: passé à :meth:`~.bdd.base.TableMeta.find_nearest`.
        sensi: sensibilité de la recherche (voir :meth:`~.bdd.TableMeta.find_nearest`).
        direct_detector: pré-détecteur éventuel, appellé sur l'entrée utilisateur
            avant :meth:`~.bdd.TableMeta.find_nearest` ; si cette
            fonction renvoie un résultat, il est immédiatement renvoyé.
        message: si défini (et ``cible`` non défini), message à envoyer avant la boucle.

    Returns:
        Instance de :attr:`table` sélectionnée.

    Attend que le joueur entre un nom, et boucle 5 fois au max (avant de l'insulter et de
    raise une erreur) pour chercher l'entrée la plus proche.
    """
    if message and not cible:
        await ctx.send(message)

    for i in range(5):
        if i == 0 and cible:
            # Au premier tour, si on a donné une cible
            rep = cible
        else:
            mess = await wait_for_message_here(ctx)
            rep = mess.content.strip("()[]{}<>")  # dézèlificateur

        # Détection directe
        if direct_detector:
            dir = direct_detector(rep)
            if dir:
                return dir

        # Sinon, recherche au plus proche
        nearest = table.find_nearest(
            rep, col=col, sensi=sensi, filtre=filtre, solo_si_parfait=False, match_first_word=True
        )

        if not nearest:
            await ctx.send("Aucune entrée trouvée, merci de réessayer : " + ital("(`stop` pour annuler)"))

        elif len(nearest) == 1:  # Une seule correspondance
            result, score = nearest[0]
            if score == 1:  # parfait
                return result

            mess = await ctx.send("Je n'ai trouvé qu'une correspondance : " f"{bold(result)}.\nÇa part ?")
            if await yes_no(mess):
                return result
            else:
                await ctx.send("Bon d'accord, alors qui ? " + ital("(`stop` pour annuler)"))

        else:
            text = "Les résultats les plus proches de ton entrée sont les suivants : \n"
            for i, (result, score) in enumerate(nearest[:10]):
                text += f"{emoji_chiffre(i + 1)}. {result} \n"
            mess = await ctx.send(
                text
                + ital(
                    "Tu peux les choisir en réagissant à ce message, ou en répondant au clavier. (`stop` pour annuler)"
                )
            )
            n = await choice(mess, min(10, len(nearest)))
            return nearest[n - 1][0]

    await ctx.send("Et puis non, tiens !\nhttps://giphy.com/gifs/fuck-you-middle-finger-ryan-stiles-x1kS7NRIcIigU")
    raise RuntimeError("Le joueur est trop con, je peux rien faire")


async def boucle_query_joueur(
    ctx: commands.Context,
    cible: str | None = None,
    message: str | None = None,
    sensi: float = 0.5,
    filtre: sqlalchemy.sql.expression.BinaryExpression | None = None,
) -> Joueur:
    """Retourne un joueur (entrée de BDD) d'après son nom.

    Args:
        ctx: le contexte d'une commande.
        cible: premier essai de cible (donnée par le joueur dans l'appel à une commande, par exemple).
        message: si défini (et ``cible`` non défini), message à envoyer avant la boucle.
        sensi: sensibilité de la recherche (voir :meth:`~.bdd.TableMeta.find_nearest`).
        filtre: passé à :meth:`~.bdd.TableMeta.find_nearest`.

    Returns:
        Le joueur choisi.

    Attend que le joueur entre un nom de joueur, et boucle 5 fois au
    max (avant de l'insulter et de raise une erreur) pour chercher le
    plus proche joueur dans la table :class:`.bdd.Joueur`.
    """
    # Détection directe par ID / nom exact
    def direct_detector(rep):
        mem = member(rep, must_be_found=False)
        if mem:
            try:  # Récupération du joueur
                return Joueur.from_member(mem)
            except ValueError:  # pas inscrit en base
                pass

        return None

    res = await boucle_query(
        ctx,
        Joueur,
        col=Joueur.nom,
        cible=cible,
        sensi=sensi,
        filtre=filtre,
        direct_detector=direct_detector,
        message=message,
    )
    return res


# Récupère un input par réaction
_Key = typing.TypeVar("_Key")
_RV = typing.TypeVar("_RV")


async def wait_for_react_clic(
    message: discord.Message,
    emojis: list[discord.Emoji] | dict[_Key, discord.Emoji] = {},
    *,
    process_text: bool = False,
    text_filter: Callable[[str], bool] | None = None,
    first_text: str | None = None,
    post_converter: Callable[[str], _RV] | None = None,
    trigger_all_reacts: bool = False,
    trigger_on_commands: bool = False,
) -> str | _Key | _RV:
    """Ajoute des reacts à un message et attend une interaction.

    Args:
        message: message où ajouter les réactions.
        emojis: reacts à ajouter, éventuellement associés à une valeur qui sera retournée si clic sur l'emoji.
        process_text: si ``True``, détecte aussi la réponse par message et retourne le texte du message.
        text_filter: si ``process_text``, ne réagit qu'aux messages pour lesquels
            ``text_filter(message)`` renvoie ``True`` (défaut : tous).
        first_text: si ``process_text``, texte considéré comme la première réponse textuelle reçue
            (si il vérifie ``text_filter``, les emojis ne sont pas ajoutés et cette fonction retourne directement).
        post_converter: si ``process_text`` et que l'argument est défini, le message
            détecté est passé dans cette fonction avant d'être renvoyé.
        trigger_all_reacts: si ``True``, détecte l'ajout de toutes les réactions (pas seulement celles dans ``emojis``)
            et renvoie l'emoji directement si il n'est pas dans ``emojis``
        trigger_on_commands: passé à :func:`.wait_for_message`.

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
        if text_filter(first_text):  # passe le filtre
            return post_converter(first_text) if post_converter else first_text

    try:
        # Si une erreur dans ce bloc, on supprime les emojis
        # du message (sinon c'est moche)
        for emoji in emojis:
            try:
                await message.add_reaction(emoji)
            except discord.errors.HTTPException:
                await message.channel.send(f"*Emoji {emoji} inconnu, ignoré*")

        emojis_names = {emoji.name if hasattr(emoji, "name") else emoji: emoji for emoji in emojis}

        def react_check(react):
            # Check REACT : bon message, bon emoji, et pas react du bot
            name = react.emoji.name
            return (
                react.message_id == message.id
                and react.user_id != config.bot.user.id
                and (trigger_all_reacts or name in emojis_names)
            )

        react_task = asyncio.create_task(config.bot.wait_for("raw_reaction_add", check=react_check))

        if process_text:
            # Check MESSAGE : bon channel, pas du bot, et filtre
            def message_check(mess):
                return mess.channel == message.channel and mess.author != config.bot.user and text_filter(mess.content)

        else:
            # On process DANS TOUS LES CAS, mais juste pour détecter
            # les stop_keywords si process_text == False
            def message_check(mess):
                return False

        mess_task = asyncio.create_task(
            wait_for_message(check=message_check, chan=message.channel, trigger_on_commands=trigger_on_commands)
        )

        done, pending = await asyncio.wait([react_task, mess_task], return_when=asyncio.FIRST_COMPLETED)
        # Le bot attend ici qu'une des deux tâches aboutisse
        for task in pending:
            task.cancel()
        done_task = next(iter(done))  # done = tâche aboutie

        if done_task == react_task:  # Réaction
            emoji = done_task.result().emoji
            if trigger_all_reacts and emoji.name not in emojis_names:
                ret = emoji
            else:
                ret = emojis.get(emoji) or emojis.get(emojis_names.get(emoji.name))

            for emoji in emojis:
                # On finit par supprimer les emojis mis par le bot
                await message.remove_reaction(emoji, config.bot.user)

        else:  # Réponse par message / STOP
            mess = done_task.result().content
            ret = post_converter(mess) if post_converter else mess
            await message.clear_reactions()

    except Exception:
        await message.clear_reactions()
        raise

    return ret


async def yes_no(message: discord.Message, first_text: str | None = None) -> bool:
    """Demande une confirmation / question fermée à l'utilisateur.

    Surcouche de :func:`wait_for_react_clic` : ajoute les reacts
    ✅ et ❎ à un message et renvoie ``True`` ou ``False`` en fonction
    de l'emoji cliqué OU de la réponse textuelle détectée.

    Args:
        message: message où ajouter les réactions.
        first_text: passé à :func:`wait_for_react_clic`.

    Réponses textuelles reconnues :
        - Pour ``True`` : ``["oui", "o", "yes", "y", "1", "true"]``
        - Pour ``False`` : ``["non", "n", "no", "n", "0", "false"]``

    ainsi que toutes leurs variations de casse.

    Returns:
        Oui ou non.
    """
    yes_words = ["oui", "o", "yes", "y", "1", "true"]
    yes_no_words = yes_words + ["non", "n", "no", "n", "0", "false"]
    return await wait_for_react_clic(
        message,
        emojis={"✅": True, "❎": False},
        process_text=True,
        first_text=first_text,
        text_filter=lambda s: s.lower() in yes_no_words,
        post_converter=lambda s: s.lower() in yes_words,
    )


_RV = typing.TypeVar("_RV")


async def choice(
    message: discord.Message, N: int, start: int = 1, *, additional: dict[discord.Emoji | str, _RV] = {}
) -> int | _RV:
    """Demande à l'utilisateur de choisir entre plusieurs options numérotées.

    Surcouche de :func:`wait_for_react_clic` : ajoute des reacts
    chiffres (1️⃣, 2️⃣, 3️⃣...) et renvoie le numéro cliqué OU détecté
    par réponse textuelle.

    Args:
        message: message où ajouter les réactions.
        N: chiffre jusqu'auquel aller, inclus (``<= 10``).
        start: chiffre auquel commencer (entre ``0`` et ``N``, défaut ``1``).
        additional: emojis optionnels à ajouter après les chiffres et valeur renvoyée si cliqué.

    Réponses textuelles reconnues : chiffres entre ``start`` et ``N``.

    Returns:
        Le nombre choisi (ou la valeur associée à l'emoji additionnel si applicable).
    """
    emojis = {emoji_chiffre(i): i for i in range(start, N + 1)}
    emojis.update(additional)
    return await wait_for_react_clic(
        message,
        emojis=emojis,
        process_text=True,
        text_filter=lambda s: s.isdigit() and start <= int(s) <= N,
        post_converter=int,
    )


async def sleep(chan: discord.abc.Messageable, tps: float) -> None:
    """Attend un temps donné en avertissant l'utilisateur.

    Pause l'exécution d'une commande en affichant l'indicateur *typing*
    ("*LGBot est en train d'écrire...*") sur un salon.

    Permet d'afficher plusieurs messages d'affilée en laissant le temps
    de lire, tout en indiquant que le bot n'a pas fini d'écrire.

    Args:
        chan: salon / contexte /... sur lequel attendre.
        tps: temps à attendre, en secondes.
    """
    async with chan.typing():
        await asyncio.sleep(tps)


# ---------------------------------------------------------------------------
# Utilitaires d'emojis
# ---------------------------------------------------------------------------


def montre(heure: str | None = None) -> str:
    """Renvoie l'emoji horloge le plus proche d'une heure donnée.

    Args:
        heure: heure à représenter, au format ``"XXh"`` ou ``"XXhMM"`` (défaut : heure actuelle).

    Returns:
       🕧, 🕓, 🕝...
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

    if 15 < minute < 45:  # Demi heure
        L = [
            "\N{CLOCK FACE TWELVE-THIRTY}",
            "\N{CLOCK FACE ONE-THIRTY}",
            "\N{CLOCK FACE TWO-THIRTY}",
            "\N{CLOCK FACE THREE-THIRTY}",
            "\N{CLOCK FACE FOUR-THIRTY}",
            "\N{CLOCK FACE FIVE-THIRTY}",
            "\N{CLOCK FACE SIX-THIRTY}",
            "\N{CLOCK FACE SEVEN-THIRTY}",
            "\N{CLOCK FACE EIGHT-THIRTY}",
            "\N{CLOCK FACE NINE-THIRTY}",
            "\N{CLOCK FACE TEN-THIRTY}",
            "\N{CLOCK FACE ELEVEN-THIRTY}",
        ]
    else:  # Heure pile
        L = [
            "\N{CLOCK FACE TWELVE OCLOCK}",
            "\N{CLOCK FACE ONE OCLOCK}",
            "\N{CLOCK FACE TWO OCLOCK}",
            "\N{CLOCK FACE THREE OCLOCK}",
            "\N{CLOCK FACE FOUR OCLOCK}",
            "\N{CLOCK FACE FIVE OCLOCK}",
            "\N{CLOCK FACE SIX OCLOCK}",
            "\N{CLOCK FACE SEVEN OCLOCK}",
            "\N{CLOCK FACE EIGHT OCLOCK}",
            "\N{CLOCK FACE NINE OCLOCK}",
            "\N{CLOCK FACE TEN OCLOCK}",
            "\N{CLOCK FACE ELEVEN OCLOCK}",
        ]
    return L[heure]


def emoji_chiffre(chiffre: int, multi: bool = False) -> str:
    """Renvoie l'emoji / les emojis chiffre correspondant à un chiffre/nombre.

    Args:
        chiffre: chiffre/nombre à représenter.
        multi: si ``True``, ``chiffre`` peut être n'importe quel entier positif, dont les chiffres seront convertis
            séparément ; sinon (par défaut), ``chiffre`` doit être un entier entre ``0`` et ``10``.

    Returns:
        0️⃣, 1️⃣, 2️⃣...
    """
    if isinstance(chiffre, int) and 0 <= chiffre <= 10:
        return ["0️⃣", "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][chiffre]
    elif multi and str(chiffre).isdigit():
        return "".join([emoji_chiffre(int(chr)) for chr in str(chiffre)])
    else:
        raise ValueError(
            "L'argument de tools.emoji_chiffre doit être un "
            "entier entre 0 et 10 OU un entier positif avec "
            "multi=True"
        )


def super_chiffre(chiffre: int, multi: bool = False) -> str:
    """Renvoie le(s) caractère(s) exposant correspondant à un chiffre/nombre.

    Args:
        chiffre: chiffre/nombre à représenter.
        multi: si ``True``, ``chiffre`` peut être n'importe quel entier positif, dont les chiffres seront convertis
            séparément ; sinon (par défaut), ``chiffre`` doit être un entier entre ``0`` et ``9``.

    Returns:
        ⁰, ¹, ²...
    """
    if isinstance(chiffre, int) and 0 <= chiffre <= 9:
        return ["⁰", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"][chiffre]
    elif multi and str(chiffre).isdigit():
        return "".join([super_chiffre(int(chr)) for chr in str(chiffre)])
    else:
        raise ValueError(
            "L'argument de tools.super_chiffre doit être un "
            "entier entre 0 et 9 OU un entier positif avec "
            "multi=True"
        )


def sub_chiffre(chiffre: int, multi: bool = False) -> str:
    """Renvoie le(s) caractère(s) indice correspondant à un chiffre/nombre.

    Args:
        chiffre: chiffre/nombre à représenter.
        multi: si ``True``, ``chiffre`` peut être n'importe quel entier positif, dont les chiffres seront convertis
            séparément ; sinon (par défaut), ``chiffre`` doit être un entier entre ``0`` et ``9``.

    Returns:
        ₀, ₁, ₂...
    """
    if isinstance(chiffre, int) and 0 <= chiffre <= 9:
        return ["₀", "₁", "₂", "₃", "₄", "₅", "₆", "₇", "₈", "₉"][chiffre]
    elif multi and str(chiffre).isdigit():
        return "".join([sub_chiffre(int(c)) for c in str(chiffre)])
    else:
        raise ValueError(
            "L'argument de tools.sub_chiffre doit être un "
            "entier entre 0 et 9 OU un entier positif avec "
            "multi=True"
        )


# ---------------------------------------------------------------------------
# Utilitaires de date / temps, notamment liées aux horaires de jeu
# ---------------------------------------------------------------------------


def heure_to_time(heure: str) -> datetime.time:
    """Convertit l'écriture d'une heure en objet :class:`datetime.time`.

    Args:
        heure: heure au format ``HHh``, ``HHhMM`` ou ``HH:MM``.

    Returns:
        Le datetime correspondant.

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
        raise ValueError(f'Valeur "{heure}" non convertible ' "en temps") from exc


def time_to_heure(tps: datetime.time, sep: str = "h", force_minutes: bool = False) -> str:
    """Convertit un objet :class:`datetime.time` en heure.

    (version maison de :meth:`datetime.time.strftime`)

    Args:
        tps: temps à convertir.
        sep: séparateur heures / minutes à utiliser (défaut ``"h"``).
        force_minutes: si ``False`` (défaut), les minutes ne sont indiquées que si différentes de ``0``.

    Returns:
        La description du temps fourni (``""`` si ``tps`` est ``None``)
    """
    if tps:
        if force_minutes or tps.minute > 0:
            return f"{tps.hour}{sep}{tps.minute:02}"
        else:
            return f"{tps.hour}{sep}"
    else:
        return ""


def next_occurrence(tps: datetime.time) -> datetime.datetime:
    """Renvoie la prochaine occurrence temporelle d'une heure donnée.

    Renvoie le prochain timestamp arrivant DANS LES HORAIRES DU JEU :
    entre :func:`.tools.fin_pause` et :func:`.tools.debut_pause`.

    Args:
        tps: heure dont on veut connaître la prochaine occurrence.

    Returns:
        Le datetime du prochain timestamp.
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


def debut_pause() -> datetime.datetime:
    """Datetime du prochain début de pause du jeu.

    Returns:
        Le timestamp correspondant au prochain vendredi 19h.
    """
    pause_time = datetime.time(hour=19)
    pause_wday = 4  # Vendredi

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


def fin_pause() -> datetime.datetime:
    """Datetime de la prochaine fin de pause du jeu.

    Returns:
       Le timestamp correspondant au prochain dimanche 19h.
    """
    reprise_time = datetime.time(hour=19)
    reprise_wday = 6  # Dimanche

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


def en_pause() -> bool:
    """Détermine si le jeu est actuellement en pause hebdomadaire.

    Si il n'y a pas de pause (:func:`.fin_pause` = :func:`.debut_pause`), renvoie toujours ``False``.

    Returns:
        Si le jeu est actuellement en pause hebdomadaire.
    """
    return fin_pause() < debut_pause()


# ---------------------------------------------------------------------------
# Split et log
# ---------------------------------------------------------------------------


def smooth_split(mess: str, N: int = 1990, sep: str = "\n", rep: str = "") -> list[str]:
    """Sépare un message en une blocs moins longs qu'une limite donnée.

    Très utile pour envoyer des messages de (potentiellement) plus de 2000 caractères (limitation Discord).

    Args:
        mess: message à découper.
        N: taille maximale des messages formés (défaut ``1990``, pour avoir un peu de marge par rapport
            à la limitation, et permettre d'entourer de ``````` par exemple)
        sep: caractères où séparer préférentiellement le texte (défaut : sauts de ligne).
            Si ``mess`` contient une sous-chaîne plus longue que ``N`` ne contenant pas ``sep``,
            le message sera tronqué à la limite.
        rep: chaîne ajoutée à la fin de chaque message formé (tronqué du séparateur final) (défaut : aucune).

    Returns:
        La liste des fractions du message.
    """
    mess = str(mess)
    LM = []  # Liste des messages
    psl = 0  # indice du Précédent Saut de Ligne
    L = len(mess)
    while psl + N < L:
        if mess.count(sep, psl, psl + N + len(sep)):
            # +len(sep) parce que si sep est à la fin, on le dégage
            i = psl + N - mess[psl : psl + N + len(sep)][::-1].find(sep)
            # un peu sombre mais vrai, tkt frère
            LM.append(mess[psl:i] + rep)
            psl = i + 1  # on élimine le \n
        else:
            LM.append(mess[psl : psl + N] + rep)
            psl += N

    if psl < L:
        LM.append(mess[psl:])  # ce qui reste
    return LM


async def send_blocs(
    messageable: discord.abc.Messageable, mess: str, *, N: int = 1990, sep: str = "\n", rep: str = ""
) -> list[discord.Message]:
    """Envoie un message en le coupant en blocs si nécessaire.

    Surcouche de :func:`.smooth_split` envoyant directement les messages formés.

    Args:
        messageable: objet où envoyer le message
            (:class:`~discord.ext.commands.Context` ou :class:`~discord.TextChannel`).
        mess: message à envoyer
        N, sep, rep: passé à :func:`.smooth_split`.

    Returns:
        La liste des messages envoyés.
    """
    messages = []
    for bloc in smooth_split(mess, N=N, sep=sep, rep=rep):
        messages.append(await messageable.send(bloc))

    return messages


async def send_code_blocs(
    messageable: discord.abc.Messageable,
    mess: str,
    *,
    N: int = 1990,
    sep: str = "\n",
    rep: str = "",
    prefixe: str = "",
    langage: str = "",
) -> list[discord.Message]:
    """Envoie un (potentiellement long) message sous forme de bloc(s) de code.

    Équivalent de :func:`.send_blocs` avec formatage de chaque bloc dans un bloc de code.

    Args:
        messageable, mess, N, sep, rep: voir :func:`.send_blocs`.
        prefixe: texte optionnel à mettre hors des code blocs, au début du premier message.
        language: voir :func:`.code_bloc`.

    Returns:
        La liste des messages envoyés.
    """
    mess = str(mess)

    if prefixe:
        prefixe = prefixe.rstrip() + "\n"

    blocs = smooth_split(prefixe + mess, N=N, sep=sep, rep=rep)

    messages = []
    for i, bloc in enumerate(blocs):
        if prefixe and i == 0:
            bloc = bloc[len(prefixe) :]
            message = await messageable.send(prefixe + code_bloc(bloc, langage=langage))
        else:
            message = await messageable.send(code_bloc(bloc, langage=langage))
        messages.append(message)

    return messages


async def log(
    message: str,
    *,
    code: bool = False,
    N: int = 1990,
    sep: str = "\n",
    rep: str = "",
    prefixe: str = "",
    langage: str = "",
) -> list[discord.Message]:
    """Envoie un message dans le channel :attr:`config.Channel.logs`.

    Surcouche de :func:`.send_blocs` / :func:`.send_code_blocs`.

    Args:
        message: message à log.
        code: si ``True``, log sous forme de bloc(s) de code (défaut ``False``).
        N, sep, rep: passé à :func:`.send_blocs` / :func:`.send_code_blocs`.
        prefixe: voir :func:`.send_code_blocs`, simplement ajouté avant ``message`` si ``code`` vaut ``False``.
        language: *identique à* :func:`.send_code_blocs`, ignoré si `code` vaut ``False``.

    Returns:
        La liste des messages envoyés.
    """
    logchan = config.Channel.logs
    if code:
        return await send_code_blocs(logchan, message, N=N, sep=sep, rep=rep, prefixe=prefixe, langage=langage)
    else:
        if prefixe:
            message = prefixe.rstrip() + "\n" + message
        return await send_blocs(logchan, message, N=N, sep=sep, rep=rep)


# ---------------------------------------------------------------------------
# Autres fonctions diverses
# ---------------------------------------------------------------------------


async def create_context(member: discord.Member, content: str) -> commands.Context:
    """Génère le contexte associé au message d'un membre dans son chan privé.

    Args:
        member (discord.Member): membre dont on veut simuler l'action.
            **Doit être inscrit en base** (pour avoir un chan privé).
        content: message à "faire envoyer" au joueur, généralement une commande.

    Utile notamment pour simuler des commandes à partir de clics sur des réactions.

    Returns:
        Le contexte "créé".
    """
    chan = Joueur.from_member(member).private_chan
    message = (await chan.history(limit=1).flatten())[0]
    # On a besoin de récupérer un message, ici le dernier de la conv privée
    message.author = member
    message.content = content
    ctx = await config.bot.get_context(message)
    return ctx


def remove_accents(text: str) -> str:
    """Enlève les accents d'un chaîne, mais conserve les caractères spéciaux.

    Version plus douce de ``unidecode.unidecode``, conservant notamment les emojis, ...

    Args:
        text: chaîne à désaccentuer.

    Returns:
        La chaîne désaccentuée.
    """
    p = re.compile("([À-ʲΆ-ת])")
    # Abracadabrax, c'est moche mais ça marche (source : tkt frère)
    return p.sub(lambda c: unidecode.unidecode(c.group()), text)


# Évaluation d'accolades
def eval_accols(rep: str, globals_: dict[str, Any] = None, locals_: dict[str, Any] = None, debug: bool = False) -> str:
    """Replace chaque bloc entouré par des ``{}`` par leur évaluation Python.

    Args:
        globals_: variables globales du contexte d'évaluation (passé à :func:`eval`).
        locals_: variables locales du contexte d'évaluation (passé à :func:`eval`).
        debug: si ``True``, insère le message d'erreur (type et texte de l'exception) dans le message
            à l'endroit où une exception est levée durant l'évaluation (défaut ``False``).

    Penser à passer les :func:`globals` et :func:`locals` si besoin.
    Généralement, il faut passer :func:`locals` qui contient ``ctx``, etc...
    mais pas :func:`globals` si on veut bénéficier de tous les modules importés dans ``tools.py``.
    """
    if globals_ is None:
        globals_ = globals()
        globals_.update(tools=__import__(__name__, fromlist=("tools")))
    if locals_ is None:
        locals_ = globals_

    if "{" not in rep:  # Si pas d'expressions, on renvoie direct
        return rep

    evrep = ""  # Réponse évaluée
    expr = ""  # Expression à évaluer
    noc = 0  # Nombre de { non appariés
    for car in rep:
        if car == "{":
            if noc:  # Expression en cours :
                expr += car  # on garde le {
            noc += 1
        elif car == "}":
            noc -= 1
            if noc:  # idem
                expr += car
            else:  # Fin d'une expression
                try:  # On essaie d'évaluer la chaîne
                    evrep += str(eval(expr, globals_, locals_))
                except Exception as e:
                    # Si erreur, on laisse {expr} non évaluée
                    evrep += "{" + expr + "}"
                    if debug:
                        evrep += code(f"->!!! {e} !!!")
                expr = ""
        elif noc:  # Expression en cours
            expr += car
        else:  # Pas d'expression en cours
            evrep += car
    if noc:  # Si expression jamais finie (nombre impair de {)
        evrep += "{" + expr
    return evrep


async def multicateg(base_name: str) -> discord.CategoryChannel:
    """Permet de gérer des groupes de catégories (plus de 50 salons).

    Renvoie la première catégorie pouvant accueillir un nouveau
    salon ; en crée une nouvelle si besoin.

    Args:
        base_name: le nom du groupe de catégorie (nom de la première catégorie, puis sera suivi de 2, 3...)

    Warning:
        Une catégorie appelée ``base_name`` doit exister au préalable dans le serveur (:attr:`config.guild`).

    Returns:
       La catégorie libre.
    """
    categ = channel(base_name)
    nb = 1
    while len(categ.channels) >= 50:
        # Limitation Discord : 50 channels par catégorie
        nb += 1
        next_name = f"{base_name} {nb}"
        next_categ = channel(next_name, must_be_found=False)
        if not next_categ:
            next_categ = await categ.clone(name=next_name)
        categ = next_categ

    return categ


def in_multicateg(categ: discord.CategoryChannel, base_name: str) -> bool:
    """Détecte si une catégorie appartient à un groupe de catégories.

    Args:
        categ: la catégorie à tester.
        base_name: le nom de base du groupe de catégories (voir :func:`.multicateg`).

    Returns:
        Si la catégorie fait partie du groupe.
    """
    stripped_name = categ.name.rstrip(string.digits + " ")
    return stripped_name == base_name


# ---------------------------------------------------------------------------
# Utilitaires de formatage de texte
# ---------------------------------------------------------------------------


def bold(text: str) -> str:
    """Formate une chaîne comme texte en **gras** dans Discord.

    Args:
        text: chaîne à formater.

    Returns:
        La chaîne formatée.
    """
    return f"**{text}**"


def ital(text: str) -> str:
    """Formate une chaîne comme texte en *italique* dans Discord.

    Args:
        text: chaîne à formater.

    Returns:
        La chaîne formatée.
    """
    return f"*{text}*"


def soul(text: str) -> str:
    """Formate une chaîne comme texte souligné dans Discord.

    Args:
        text: chaîne à formater.

    Returns:
        La chaîne formatée.
    """
    return f"__{text}__"


def strike(text: str) -> str:
    """Formate une chaîne comme texte barré dans Discord.

    Args:
        text: chaîne à formater.

    Returns:
        La chaîne formatée.
    """
    return f"~~{text}~~"


def code(text: str) -> str:
    """Formate une chaîne comme ``code`` (inline) dans Discord.

    Args:
        text: chaîne à formater.

    Returns:
        La chaîne formatée.
    """
    return f"`{text}`"


def code_bloc(text: str, langage: str = "") -> str:
    """Formate une chaîne comme un bloc de code dans Discord.

    Args:
        text: chaîne à formater.
        langage: langage du code, pour coloration syntaxique.

    Langages supportés (non exhaustif ?) : ``asciidoc``, ``autohotkey``,
    ``bash``, ``coffeescript``, ``cpp`` (C++), ``cs`` (C#), ``css``,
    ``diff``, ``fix``, ``glsl``, ``ini``, ``json``, ``md``, (markdown),
    ``ml``, ``prolog``, ``py``, ``tex``, ``xl``, ``xml``

    Returns:
        La chaîne formatée.
    """
    return f"```{langage}\n{text}```"


def quote(text: str) -> str:
    """Formate une chaîne comme citation (inline) dans Discord.

    Args:
        text: chaîne à formater.

    Returns:
        La chaîne formatée.
    """
    return f"> {text}"


def quote_bloc(text: str) -> str:
    """Formate une chaîne comme bloc de citation (multiline) dans Discord.

    Args:
        text: chaîne à formater.

    Returns:
        La chaîne formatée.
    """
    return f">>> {text}"


def spoiler(text: str) -> str:
    """Formate une chaîne comme spoiler (cliquer pour afficher) dans Discord.

    Args:
        text: chaîne à formater.

    Returns:
        La chaîne formatée.
    """
    return f"||{text}||"
