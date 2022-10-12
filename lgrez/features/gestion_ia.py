"""lg-rez / features / IA des réponses

Tout ce qui concerne la manière dont le bot réagit aux messages :
détermination de la meilleure réaction, gestion des réactions,
activation/désactivation des modes de chat

"""

import re
import random
from typing import Callable, Coroutine, Literal
import requests

import discord
from discord import app_commands

from lgrez import config
from lgrez.blocs import tools
from lgrez.blocs.journey import DiscordJourney, journey_command, journey_context_menu
from lgrez.bdd import Trigger, Reaction, Role


# Marqueurs de séparation du mini-langage des séquences-réactions
MARK_OR = " <||> "
MARK_THEN = " <&&> "
MARK_REACT = "<::>"
MARKS = [MARK_OR, MARK_THEN, MARK_REACT]


async def _build_sequence(journey: DiscordJourney) -> str:
    """Construction d'une séquence-réaction par l'utilisateur"""
    reponse = ""
    channel_id = journey.channel.id
    try:
        if channel_id not in config.bot.in_stfu:
            config.bot.in_stfu.append(channel_id)

        while True:
            message = await journey.channel.send(
                "Réaction du bot : prochain message/commande/média, ou réaction à ce message"
            )
            ret = await tools.wait_for_react_added(message, process_text=True)
            if isinstance(ret, str):
                reponse += ret
            else:  # React
                reponse += MARK_REACT + ret.name

            choix = await journey.buttons(
                "Et ensuite ?",
                {
                    MARK_THEN: discord.ui.Button(label="Puis", emoji="▶"),
                    MARK_OR: discord.ui.Button(label="Alternatif", emoji="🔀"),
                    False: discord.ui.Button(label="Fin", emoji="⏹"),
                },
            )

            if choix:
                # On ajoute la marque OR ou THEN à la séquence
                reponse += choix
            else:
                break

    finally:
        if channel_id in config.bot.in_stfu:
            config.bot.in_stfu.remove(channel_id)

    return reponse


def fetch_tenor(trigger):
    """Renvoie le GIF Tenor le plus "pertinent" pour un texte donné.

    Args:
        trigger (str): texte auquel réagir.

    Returns:
        :class:`str` (URL du GIF) ou ``None``
    """
    # API key module ternorpy (parce que la flemme de créer un compte Tenor)
    apikey = "J5UVWPVIM4A5"

    rep = requests.get(
        url="https://api.tenor.com/v1/search",
        params={
            "q": trigger,
            "key": apikey,
            "limit": 1,
            "locale": "fr_FR",
            "contentfilter": "off",
            "media_filter": "minimal",
            "ar_range": "all",
        },
    )

    if rep:
        gifs = rep.json()["results"]
        # Payload Tenor : {..., "results":[ ... ]}
        # (https://tenor.com/gifapi/documentation#responseobjects-gif)
        if gifs:
            return gifs[0]["itemurl"]

    return None  # Pas de GIF trouvé


DESCRIPTION = """Commandes relatives à l'IA (réponses automatiques du bot)"""


@app_commands.command()
@tools.private()
@journey_command
async def stfu(journey: DiscordJourney, *, force: Literal["on", "off"] = None):
    """Active/désactive la réponse automatique du bot sur ton channel privé.

    Args:
        force: Forcer l'activation / la désactivation (toggle par défaut).

    N'agit que sur les messages classiques envoyés dans le channel : les commandes restent reconnues.

    Si vous ne comprenez pas le nom de la commande, demandez à Google.
    """
    id = journey.channel.id

    if force in [None, "on"] and id not in config.bot.in_stfu:
        config.bot.in_stfu.append(id)
        await journey.send("Okay, je me tais ! Tape !stfu quand tu voudras de nouveau de moi :cry:")

    elif force in [None, "off"] and id in config.bot.in_stfu:
        config.bot.in_stfu.remove(id)
        await journey.send("Ahhh, ça fait plaisir de pouvoir reparler !")


@app_commands.command()
@journey_command
async def fals(journey: DiscordJourney, force: Literal["on", "off"] = None):
    """Active/désactive le mode « foire à la saucisse ».

    Args:
        force: Forcer l'activation / la désactivation (toggle par défaut).

    En mode « foire à la saucisse », le bot réagira à (presque) tous les messages,
    pas seulement sur les motifs qu'on lui a appris.

    À utiliser à vos risques et périls !
    """
    id = journey.channel.id

    if force in [None, "on"] and id not in config.bot.in_fals:
        config.bot.in_fals.append(id)
        await journey.send("https://tenor.com/view/saucisse-sausage-gif-5426973")

    elif force in [None, "off"] and id in config.bot.in_fals:
        config.bot.in_fals.remove(id)
        await journey.send("T'as raison, faut pas abuser des bonnes choses")


class _FakeMessage:
    def __init__(self, channel: discord.TextChannel, author: discord.Member, content: str) -> None:
        self.channel = channel
        self.author = author
        self.content = content

    async def add_reaction(emoji: discord.Emoji | str) -> None:
        pass


@app_commands.command()
@journey_command
async def react(journey: DiscordJourney, *, trigger: str):
    """Force le bot à réagir à un message (sur un chan public, en mode STFU...)

    Args:
        trigger: Texte auquel le bot doit réagir.

    Permet de faire appel à l'IA du bot même sur les chans publics,ou en mode STFU, etc.

    Si utilisée par un MJ, active aussi le mode débug des évaluations Python (messages d'erreur).
    """
    message = _FakeMessage(journey.channel, journey.member, trigger)
    debug = journey.member.top_role >= config.Role.mj
    await process_ia(message, journey.send, debug=debug)


@app_commands.command()
@journey_command
async def reactfals(journey: DiscordJourney, *, trigger: str):
    """Force le bot à réagir à un message comme en mode Foire à la saucisse.

    Args:
        trigger: Texte auquel le bot doit réagir.

    Permet de faire appel directement au mode Foire à la saucisse,
    même si il n'est pas activé / sur un chan public.
    """
    gif = fetch_tenor(trigger)
    await journey.send(gif or "Palaref")


async def _add_ia(journey: DiscordJourney, *, triggers: str, reponse: str | None):
    triggers = triggers.split(";")
    triggers = [tools.remove_accents(s).lower().strip() for s in triggers]
    triggers = list({trig for trig in triggers if trig})
    # filtre doublons (accents et non accents...) et triggers vides

    avoided = []
    for trigger in triggers.copy():
        if Trigger.query.filter_by(trigger=trigger).all():
            avoided.append(trigger)
            triggers.remove(trigger)

    avoided = f"Trigger(s) déjà associé(s) à une réaction et ignorés : {avoided}\n\n" if avoided else ""

    if not triggers:
        await journey.send(avoided + ":x: Aucun trigger valide, abort")
        return

    await journey.send(avoided + f":arrow_forward: Triggers : `{'` – `'.join(triggers)}`")

    if reponse:
        reponse = reponse.strip()
    else:
        reponse = await _build_sequence(journey)

    if not reponse:
        await journey.channel.send("Réponse textuelle vide interdite, abort.")
        return

    await journey.channel.send(f"Résumé de la séquence : {tools.code(reponse)}")
    async with journey.channel.typing():
        reac = Reaction(reponse=reponse)
        config.session.add(reac)

        trigs = [Trigger(trigger=trigger, reaction=reac) for trigger in triggers]
        config.session.add_all(trigs)

        config.session.commit()

    await journey.channel.send("Règle ajoutée en base.")


@app_commands.command()
@tools.mjs_et_redacteurs
@journey_command
async def add_ia(journey: DiscordJourney, *, triggers: str, reponse: str | None = None):
    """Ajoute une règle d'IA (COMMANDE MJ/RÉDACTEURS)

    Args:
        triggers: Mot(s), phrase(s) ou expression(s) séparées par des ";".
        reponse: Si réponse textuelle simple, pour ajout rapide.

    Une sécurité empêche d'ajouter un trigger déjà existant.

    Dans le cas où plusieurs expressions sont spécifiées, toutes déclencheront l'action demandée.
    """
    await _add_ia(journey, triggers=triggers, reponse=reponse)


@app_commands.context_menu(name="Nouvelle règle d'IA")
@tools.mjs_et_redacteurs
@journey_context_menu
async def add_ia_menu(journey: DiscordJourney, message: discord.Message):
    await _add_ia(journey, triggers=message.content, reponse=None)


@app_commands.command()
@tools.mjs_et_redacteurs
@journey_command
async def list_ia(journey: DiscordJourney, trigger: str | None = None, sensi: float = 0.5):
    """Liste les règles d'IA reconnues par le bot (COMMANDE MJ/RÉDACTEURS)

    Args
        trigger: Mot/expression permettant de filter et trier les résultats.
        sensi: Sensibilité de détection (ratio des caractères correspondants, entre 0 et 1), défaut 0.5.
    """
    if trigger:
        trigs = Trigger.find_nearest(trigger, col=Trigger.trigger, sensi=sensi, solo_si_parfait=False)
        if not trigs:
            await journey.send(f"Rien trouvé, pas de chance (sensi = {sensi})")
            return
    else:
        raw_trigs = Trigger.query.order_by(Trigger.id).all()
        # Trié par date de création
        trigs = list(zip(raw_trigs, [None] * len(raw_trigs)))
        # Mise au format (trig, score)

    reacts = []  # Réactions associées à notre liste de triggers
    for trig in trigs:
        if (reac := trig[0].reaction) not in reacts:
            # Pas de doublons, et reste ordonné
            reacts.append(reac)

    def nettoy(s):
        # Abrège la réponse si trop longue et neutralise les
        # sauts de ligne / rupture code_bloc, pour affichage
        s = s.replace("\r\n", "\\n").replace("\n", "\\n")
        s = s.replace("\r", "\\r").replace("```", "'''")
        if len(s) < 75:
            return s
        else:
            return s[:50] + " [...] " + s[-15:]

    rep = ""
    for reac in reacts:  # pour chaque réponse
        r = ""
        for (trig, score) in trigs:  # pour chaque trigger
            if trig.reaction == reac:
                sc = f"({float(score):.2}) " if score else ""
                r += f" - {sc}{trig.trigger}"
                # (score) trigger - (score) trigger ...

        rep += r.ljust(50) + f" ⇒ {nettoy(reac.reponse)}\n"
        # ⇒ réponse

    rep += "\nPour modifier une réaction, utiliser `/modif_ia <trigger>`."

    await journey.send(rep, code=True)


@app_commands.command()
@tools.mjs_et_redacteurs
@journey_command
async def modif_ia(journey: DiscordJourney, *, trigger: str):
    """Modifie/supprime une règle d'IA (COMMANDE MJ/RÉDACTEURS)

    Args:
        trigger: Mot/expression déclenchant la réaction à modifier/supprimer.

    Permet d'ajouter et supprimer des triggers, de modifier la réaction du bot
    (construction d'une  séquence de réponses successives ou aléatoires)
    ou de supprimer la réaction.
    """
    trigs = Trigger.find_nearest(trigger, col=Trigger.trigger)
    if not trigs:
        await journey.send("Rien trouvé.")
        return

    trig = trigs[0][0]
    reac = trig.reaction

    displ_seq = reac.reponse if reac.reponse.startswith("`") else tools.code(reac.reponse)  # Pour affichage
    trigs = list(reac.triggers)

    choix = await journey.buttons(
        f"Triggers : `{'` – `'.join([trig.trigger for trig in trigs])}`\nSéquence réponse : {displ_seq}\n\nModifier :",
        {
            "triggers": discord.ui.Button(label="Triggers", emoji="⏩"),
            "response": discord.ui.Button(label="Réponse", emoji="⏺"),
            "delete": discord.ui.Button(label="Supprimer", emoji="🚮"),
        },
    )

    if choix == "triggers":  # Modification des triggers
        while True:
            action = await journey.buttons(
                "Supprimer / ajouter un trigger :",
                {
                    index: discord.ui.Button(label=trigger.trigger, emoji="🚮", style=discord.ButtonStyle.danger)
                    for index, trigger in enumerate(trigs)
                }
                | {
                    "new": discord.ui.Button(label="Nouveau", emoji="🆕", style=discord.ButtonStyle.primary),
                    "stop": discord.ui.Button(label="Fini", emoji="⏹"),
                },
            )

            if action == "stop":
                break
            elif action == "new":
                (new_trigger,) = await journey.modal("Ajouter un trigger", "Nouveau déclencheur")
                new_trig = Trigger(trigger=new_trigger, reaction=reac)
                trigs.append(new_trig)
                config.session.add(new_trig)
                config.session.commit()
            else:
                config.session.delete(trigs.pop(action))
                config.session.commit()

        if not trigs:  # on a tout supprimé !
            await journey.send("Tous les triggers supprimés, suppression de la réaction")
            config.session.delete(reac)
            config.session.commit()
            return

    elif choix == "response":  # Modification de la réponse
        if any([mark in reac.reponse for mark in MARKS]):
            # Séquence compliquée
            await journey.send(
                "\nLa séquence-réponse peut être refaite manuellement "
                "ou modifiée rapidement en envoyant directement la "
                "séquence ci-dessus modifiée (avec les marqueurs : "
                f"OU = {tools.code(MARK_OR)}, "
                f"ET = {tools.code(MARK_THEN)}, "
                f"REACT = {tools.code(MARK_REACT)}"
            )

        reponse = await _build_sequence(journey)
        if not reponse:
            await journey.send("Réponse textuelle vide interdite, abort.")

        reac.reponse = reponse

    else:  # Suppression
        config.session.delete(reac)
        for trig in trigs:
            config.session.delete(trig)

    config.session.commit()

    await journey.send("Fini.")


async def trigger_at_mj(message: discord.Message, send_callable: Callable[[str], Coroutine]) -> bool:
    """Règle d'IA : réaction si le message mentionne les MJs.

    Args:
        message: Message auquel réagir.

    Returns:
        Si le message mentionne les MJ et qu'une réponse a été envoyée
    """
    if config.Role.mj.mention in message.content:
        await send_callable("Les MJs ont entendu ton appel, ils sont en route ! :superhero:")
        return True

    return False


async def trigger_roles(
    message: discord.Message, send_callable: Callable[[str], Coroutine], sensi: float = 0.8
) -> bool:
    """Règle d'IA : réaction si un nom de rôle est donné.

    Args:
        message: Message auquel réagir.
        sensi: Sensibilité de la recherche (voir :meth:`.bdd.base.TableMeta.find_nearest`).

    Trouve l'entrée la plus proche de ``message.content`` dans la table :class:`.bdd.Role`.

    Returns:
        Si un rôle a été trouvé (sensibilité ``> sensi``) et qu'une réponse a été envoyée.
    """
    roles = Role.find_nearest(message.content, col=Role.nom, filtre=(Role.actif.is_(True)), sensi=sensi)

    if roles:  # Au moins un trigger trouvé à cette sensi
        await send_callable(embed=roles[0][0].embed)
        return True

    return False


async def trigger_reactions(
    message: discord.Message,
    send_callable: Callable[[str], Coroutine],
    chain: str | None = None,
    sensi: float = 0.7,
    debug: bool = False,
) -> bool:
    """Règle d'IA : réaction à partir de la table :class:`.bdd.Reaction`.

    Args:
        message: Message auquel réagir.
        chain: Contenu auquel réagir (défaut : contenu de ``message``).
        sensi: Sensibilité de la recherche (cf :meth:`.bdd.base.TableMeta.find_nearest`).
        debug: Si ``True``, affiche les erreurs lors de l'évaluation des messages (voir :func:`.tools.eval_accols`).

    Trouve l'entrée la plus proche de ``chain`` dans la table :class:`.bdd.Reaction` ;
    si il contient des accolades, évalue le message selon le contexte de ``message``.

    Returns:
        Si une réaction a été trouvé (sensibilité ``> sensi``) et qu'une réponse a été envoyée.
    """
    if not chain:  # Si pas précisé,
        chain = message.content  # contenu de message
    trigs = Trigger.find_nearest(chain, col=Trigger.trigger, sensi=sensi)

    if trigs:  # Au moins un trigger trouvé à cette sensi
        trig = trigs[0][0]  # Meilleur trigger (score max)
        seq = trig.reaction.reponse  # Séquence-réponse associée

        for rep in seq.split(MARK_THEN):  # Pour chaque étape :
            if MARK_OR in rep:
                # Si plusieurs possibilités, on en choisit une random
                rep = random.choice(rep.split(MARK_OR))

            if rep.startswith(MARK_REACT):  # Réaction
                react = rep.lstrip(MARK_REACT)
                emoji = tools.emoji(react, must_be_found=False) or react
                await message.add_reaction(emoji)

            else:  # Sinon, texte / média
                # On remplace tous les "{expr}" par leur évaluation
                rep = tools.eval_accols(rep, locals_=locals(), debug=debug)
                await send_callable(rep)

        return True

    return False


async def trigger_sub_reactions(
    message: discord.Message, send_callable: Callable[[str], Coroutine], sensi: float = 0.9, debug: bool = False
) -> bool:
    """Règle d'IA : réaction à partir de la table, mais sur les mots

    Appelle :func:`trigger_reactions(bot, message, mot, sensi, debug) <.trigger_reactions>`
    pour tous les mots ``mot`` composant ``message.content`` (mots de plus de 4 lettres,
    testés des plus longs aux plus courts).

    Args:
        message: Message auquel réagir.
        sensi: Sensibilité de la recherche (cf :meth:`.bdd.base.TableMeta.find_nearest`).
        debug: Si ``True``, affiche les erreurs lors de l'évaluation des messages (voir :func:`.tools.eval_accols`).

    Returns:
        Si une réaction a été trouvé (sensibilité ``> sensi``) et qu'une réponse a été envoyée.
    """
    mots = message.content.split(" ")
    if len(mots) > 1:  # Si le message fait plus d'un mot
        for mot in sorted(mots, key=lambda m: -len(m)):
            # On parcourt les mots du plus long au plus court
            if len(mot) > 4:  # on élimine les mots de liaison
                if await trigger_reactions(message, send_callable, chain=mot, sensi=sensi, debug=debug):
                    # Si on trouve une sous-rect (à 0.9)
                    return True

    return False


async def trigger_di(message: discord.Message, send_callable: Callable[[str], Coroutine]) -> bool:
    """Règle d'IA : réaction aux messages en di... / cri...

    Args:
        message: Message auquel réagir.

    Returns:
        Si le message correspond et qu'une réponse a été envoyée.
    """
    c = message.content
    diprefs = ["di", "dy", "dis ", "dit ", "dis-", "dit-"]
    criprefs = ["cri", "cry", "kri", "kry"]
    pos_prefs = {c.lower().find(pref): pref for pref in diprefs + criprefs if pref in c[:-1].lower()}
    # On extrait les cas où le préfixe est à la fin du message

    if pos_prefs:  # Si on a trouvé au moins un préfixe
        i = min(pos_prefs)
        pref = pos_prefs[i]
        if pref in criprefs:
            mess = tools.bold(c[i + len(pref) :].upper())
        else:
            mess = c[i + len(pref) :]
        await send_callable(mess, tts=True)
        # On envoie le di.../cri... en mode TTS (oh si, c'est rigolo)
        return True

    return False


async def trigger_gif(message: discord.Message, send_callable: Callable[[str], Coroutine]) -> bool:
    """Règle d'IA : réaction par GIF en mode Foire à la saucisse.

    Args:
        message: Message auquel réagir.

    Returns:
        Si le message correspond et qu'une réponse a été envoyée.
    """
    if message.channel.id in config.bot.in_fals:
        # Chan en mode Foire à la saucisse
        async with message.channel.typing():
            gif = fetch_tenor(message.content)
            if gif:
                await send_callable(gif)
                return True

    return False


async def trigger_mot_unique(message: discord.Message, send_callable: Callable[[str], Coroutine]) -> bool:
    """Règle d'IA : réaction à un mot unique (le répète).

    Args:
        message: Message auquel réagir.

    Returns:
        Si le message correspond et qu'une réponse a été envoyée
    """
    if len(message.content.split()) == 1 and ":" not in message.content:
        # : pour ne pas trigger aux liens
        rep = f"{message.content.capitalize()} ?"
        await send_callable(rep)
        return True

    return False


async def trigger_a_ou_b(message: discord.Message, send_callable: Callable[[str], Coroutine]) -> bool:
    """Règle d'IA : réaction à un motif type « a ou b » (répond « b »).

    Args:
        message: Message auquel réagir.

    Returns:
        Si le message correspond et qu'une réponse a été envoyée.
    """
    if motif := re.fullmatch(r"(.+)\s+ou\s+(.+?)", message.content):
        rep = f"{motif.group(2).rstrip(' !?.,;')}.".capitalize()
        await send_callable(rep)
        return True

    return False


async def default(message: discord.Message, send_callable: Callable[[str], Coroutine]) -> bool:
    """Règle d'IA : réponse par défaut

    Args:
        message: Message auquel réagir.

    Returns:
        Si le message correspond et qu'une réponse a été envoyée.
    """
    mess = "Désolé, je n'ai pas compris :person_shrugging:"
    if random.random() < 0.05:
        mess += "\n(et toi, tu as perdu)"
    await send_callable(mess)
    return True


async def process_ia(message: discord.Message, send_callable: Callable[[str], Coroutine], debug: bool = False) -> None:
    """Exécute les règles d'IA.

    Args:
        message: Message auquel réagir.
        debug: Si ``True``, affiche les erreurs lors de l'évaluation des messages (voir :func:`.tools.eval_accols`).
    """
    (
        await trigger_at_mj(message, send_callable)  # @MJ (aled)
        or await trigger_gif(message, send_callable)  # Un petit GIF ? (si FALS)
        or await trigger_roles(message, send_callable)  # Rôles
        or await trigger_reactions(message, send_callable, debug=debug)  # Table Reaction ("IA")
        or await trigger_sub_reactions(message, send_callable, debug=debug)  # IA sur les mots
        or await trigger_a_ou_b(message, send_callable)  # "a ou b" ==> "b"
        or await trigger_di(message, send_callable)  # di... / cri...
        or await trigger_mot_unique(message, send_callable)  # Un seul mot ==> on répète
        or await default(message, send_callable)  # Réponse par défaut
    )
