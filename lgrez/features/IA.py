"""lg-rez / features / IA des réponses

Tout ce qui concerne la manière dont le bot réagit aux messages : détermination de la meilleure réaction, gestion des réactions, activation/désactivation des modes de chat

"""

import re
import random
import requests

from discord.ext import commands

from lgrez.blocs import bdd, tools, bdd_tools
from lgrez.blocs.bdd import Triggers, Reactions, Roles


# Marqueurs de séparation du mini-langage des séquences-réactions
MARK_OR = ' <||> '
MARK_THEN = ' <&&> '
MARK_REACT = '<::>'
MARK_CMD = '<!!>'
MARKS = [MARK_OR, MARK_THEN, MARK_REACT, MARK_CMD]



async def _build_sequence(ctx):
    """Construction d'une séquence-réaction par l'utilisateur"""
    reponse = ""
    fini = False
    while not fini:
        message = await ctx.send("Réaction du bot : prochain message/commande/média, ou réaction à ce message")
        ret = await tools.wait_for_react_clic(ctx.bot, message, process_text=True, trigger_all_reacts=True, trigger_on_commands=True)
        if isinstance(ret, str):
            if ret.startswith(ctx.bot.command_prefix):      # Commande
                reponse += MARK_CMD + ret.lstrip(ctx.bot.command_prefix)
            else:                                           # Texte / média
                reponse += ret
        else:                                               # React
            reponse += MARK_REACT + ret.name

        message = await ctx.send("▶ Puis / 🔀 Ou / ⏹ Fin ?")
        ret = await tools.wait_for_react_clic(ctx.bot, message, emojis={"▶": MARK_THEN, "🔀": MARK_OR, "⏹": False})
        if ret:
            reponse += ret          # On ajoute la marque OR ou THEN à la séquence
        else:
            fini = True

    return reponse


def fetch_tenor(trigger):
    """Renvoie le GIF Tenor le plus pertinent (d'après Tenor) pour un texte donnée

    Args:
        trigger (:class:`str`): texte auquel réagir

    Returns:
        ``str`` (URL du GIF) ou ``None``
    """
    apikey = "J5UVWPVIM4A5"  # API key module ternorpy (parce que la flemme de créer un compte Tenor)

    rep = requests.get(
        url="https://api.tenor.com/v1/search",
        params={
            "q": trigger, "key": apikey, "limit": 1, "locale": "fr_FR",
            "contentfilter": "off", "media_filter": "minimal", "ar_range": "all"
        }
    )

    if rep:
        gifs = rep.json()["results"]        # Payload Tenor : {..., "results":[ (https://tenor.com/gifapi/documentation#responseobjects-gif) ]}
        if gifs:
            return gifs[0]["itemurl"]

    return None     # Pas de GIF trouvé



class GestionIA(commands.Cog):
    """GestionIA - Commandes relatives à l'IA (réponses automatiques du bot)"""

    @commands.command()
    @tools.private
    async def stfu(self, ctx, force=None):
        """Active/désactive la réponse automatique du bot sur ton channel privé

        Args:
            force: ``"start"``/``"on"`` / ``"stop"``/``"off"`` permet de forcer l'activation / la désactivation.

        Sans argument, la commande agit comme un toggle (active les réactions si désactivées et vice-versa).

        N'agit que sur les messages classiques envoyés dans le channel : les commandes restent reconnues.

        Si vous ne comprenez pas le nom de la commande, demandez à Google.
        """
        id = ctx.channel.id

        if force in [None, "start", "on"] and id not in ctx.bot.in_stfu:
            ctx.bot.in_stfu.append(id)
            await ctx.send("Okay, je me tais ! Tape !stfu quand tu voudras de nouveau de moi :cry:")

        elif force in [None, "stop", "off"] and id in ctx.bot.in_stfu:
            ctx.bot.in_stfu.remove(id)
            await ctx.send("Ahhh, ça fait plaisir de pouvoir reparler !")

        else:       # Quelque chose d'autre que start/stop précisé après !stfu : bot discret
            if id in ctx.bot.in_stfu:
                ctx.bot.in_stfu.remove(id)
            else:
                ctx.bot.in_stfu.append(id)


    @commands.command(aliases=["cancer", "214"])
    async def fals(self, ctx, force=None):
        """Active/désactive le mode « foire à la saucisse »

        Args:
            force: ``"start"``/``"on"`` / ``"stop"``/``"off"`` permet de forcer l'activation / la désactivation.

        Sans argument, la commande agit comme un toggle (active le mode si désactivé et vice-versa).

        En mode « foire à la saucisse », le bot réagira à (presque) tous les messages, pas seulement sur les motifs qu'on lui a appris.

        À utiliser à vos risques et périls !
        """
        id = ctx.channel.id

        if force in [None, "start", "on"] and id not in ctx.bot.in_fals:
            ctx.bot.in_fals.append(id)
            await ctx.send("https://tenor.com/view/saucisse-sausage-gif-5426973")

        elif force in [None, "stop", "off"] and id in ctx.bot.in_fals:
            ctx.bot.in_fals.remove(id)
            await ctx.send("T'as raison, faut pas abuser des bonnes choses")

        else:       # Quelque chose d'autre que start/stop précisé après !fals : bot discret
            if id in ctx.bot.in_fals:
                ctx.bot.in_fals.remove(id)
            else:
                ctx.bot.in_fals.append(id)


    @commands.command(aliases=["r"])
    async def react(self, ctx, *, trigger):
        """Force le bot à réagir à un message

        Args:
            trigger: texte auquel le bot doit réagir

        Permet de faire appel à l'IA du bot même sur les chans publics, ou en mode STFU, etc.

        Si utilisée par un MJ, active aussi le mode débug des évaluations Python (messages d'erreur).
        """
        oc = ctx.message.content
        ctx.message.content = trigger
        await process_IA(ctx.bot, ctx.message, debug=(ctx.author.top_role.name == "MJ"))
        ctx.message.content = oc        # On rétablit le message original pour ne pas qu'il trigger l'IA 2 fois, le cas échéant


    @commands.command(aliases=["rf"])
    async def reactfals(self, ctx, *, trigger):
        """Force le bot à réagir à un message comme en mode Foire à la saucisse

        Args:
            trigger: texte auquel le bot doit réagir

        Permet de faire appel directement au mode Foire à la saucisse, même si il n'est pas activé / sur un chan public.
        """
        async with ctx.typing():
            gif = fetch_tenor(trigger)

        if gif:
            await ctx.send(gif)
        else:
            await ctx.send("Palaref")


    @commands.command()
    @tools.mjs_et_redacteurs
    async def addIA(self, ctx, *, triggers=None):
        """Ajoute au bot une règle d'IA : mots ou expressions déclenchant une réaction (COMMANDE MJ/RÉDACTEURS)

        Args:
            *triggers: mot(s), phrase(s), ou expression(s) séparées par des points-virgules ou sauts de lignes

        Dans le cas où plusieurs expressions sont spécifiées, toutes déclencheront l'action demandée.
        """
        if not triggers:
            await ctx.send("Mots/expressions déclencheurs (non sensibles à la casse / accents), séparés par des points-virgules ou des sauts de ligne :")
            mess = await tools.wait_for_message_here(ctx)
            triggers = mess.content

        triggers = triggers.replace('\n', ';').split(';')
        triggers = [tools.remove_accents(s).lower().strip() for s in triggers]
        await ctx.send(f"Triggers : `{'` – `'.join(triggers)}`")

        reponse = await _build_sequence(ctx)

        await ctx.send(f"Résumé de la séquence : {tools.code(reponse)}")
        async with ctx.typing():
            reac = Reactions(reponse=reponse)
            bdd.session.add(reac)
            bdd.session.commit()          # On "fait comme si" on commitait l'ajout de reac, ce qui calcule read.id (autoincrément)

            trigs = [Triggers(trigger=trigger, reac_id=reac.id) for trigger in triggers]
            bdd.session.add_all(trigs)
            bdd.session.commit()
        await ctx.send(f"Règle ajoutée en base.")


    @commands.command()
    @tools.mjs_et_redacteurs
    async def listIA(self, ctx, trigger=None, sensi=0.5):
        """Liste les règles d'IA actuellement reconnues par le bot (COMMANDE MJ/RÉDACTEURS)

        Args
            trigger (optionnel): mot/expression permettant de filter et trier les résultats. SI ``trigger`` FAIT PLUS D'UN MOT, IL DOIT ÊTRE ENTOURÉ PAR DES GUILLEMETS !
            sensi: sensibilité de détection (ratio des caractères correspondants, entre 0 et 1) si trigger est précisé.
        """
        async with ctx.typing():
            if trigger:
                trigs = bdd_tools.find_nearest(trigger, table=Triggers, carac="trigger", sensi=sensi, solo_si_parfait=False)
                if not trigs:
                    await ctx.send(f"Rien trouvé, pas de chance (sensi = {sensi})")
                    return
            else:
                raw_trigs = Triggers.query.order_by(Triggers.id).all()          # Trié par date de création
                trigs = list(zip(raw_trigs, [None]*len(raw_trigs)))             # Mise au format (trig, score)

            reacts_ids = []     # IDs des réactions associées à notre liste de triggers
            [reacts_ids.append(id) for trig in trigs if (id := trig[0].reac_id) not in reacts_ids]    # Pas de doublons, et reste ordonné

            def nettoy(s):      # Abrège la réponse si trop longue et neutralise les sauts de ligne / rupture code_bloc, pour affichage
                s = s.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '\\r').replace("```", "'''")
                if len(s) < 75:
                    return s
                else:
                    return s[:50] + " [...] " + s[-15:]

            L = ["- " + " – ".join([(f"({float(score):.2}) " if score else "") + trig.trigger       # (score) trigger - (score) trigger ...
                                    for (trig, score) in trigs if trig.reac_id == id]).ljust(50)        # pour chaque trigger
                 + f" ⇒ {nettoy(Reactions.query.get(id).reponse)}"                                 # ⇒ réponse
                 for id in reacts_ids]                                                                  # pour chaque réponse

            r = "\n".join(L) + "\n\nPour modifier une réaction, utiliser !modifIA <trigger>."

        await tools.send_code_blocs(ctx, r)       # On envoie, en séparant en blocs de 2000 caractères max


    @commands.command()
    @tools.mjs_et_redacteurs
    async def modifIA(self, ctx, *, trigger=None):
        """Modifie/supprime une règle d'IA (COMMANDE MJ/RÉDACTEURS)

        Args:
            trigger: mot/expression déclenchant la réaction à modifier/supprimer

        Permet d'ajouter et supprimer des triggers, de modifier la réaction du bot (construction d'une séquence de réponses successives ou aléatoires) ou de supprimer la réaction.
        """
        if not trigger:
            await ctx.send("Mot/expression déclencheur de la réaction à modifier :")
            mess = await tools.wait_for_message_here(ctx)
            trigger = mess.content

        trigs = bdd_tools.find_nearest(trigger, Triggers, carac="trigger")
        if not trigs:
            await ctx.send("Rien trouvé.")
            return

        trig = trigs[0][0]
        rep = Reactions.query.get(trig.reac_id)
        assert rep, f"!modifIA : réaction associée à {trig} introuvable"

        displ_seq = rep.reponse if rep.reponse.startswith('`') else tools.code(rep.reponse)     # Pour affichage
        trigs = Triggers.query.filter_by(reac_id=trig.reac_id).all()

        await ctx.send(f"Triggers : `{'` – `'.join([trig.trigger for trig in trigs])}`\n"
                       f"Séquence réponse : {displ_seq}")

        message = await ctx.send("Modifier : ⏩ triggers / ⏺ Réponse / ⏸ Les deux / 🚮 Supprimer ?")
        MT, MR = await tools.wait_for_react_clic(ctx.bot, message, emojis={"⏩": (True, False), "⏺": (False, True),
                                                                           "⏸": (True, True),  "🚮": (False, False)})

        if MT:                      # Modification des triggers
            fini = False
            while not fini:
                s = "Supprimer un trigger : \n"
                for i, t in enumerate(trigs[:10]):
                    s += f"{tools.emoji_chiffre(i+1)}. {t.trigger} \n"
                mess = await ctx.send(s + "Ou entrer un mot / une expression pour l'ajouter en trigger.\n⏹ pour finir")
                r = await tools.wait_for_react_clic(ctx.bot, mess, emojis={(tools.emoji_chiffre(i) if i else "⏹"): str(i) for i in range(len(trigs)+1)}, process_text=True)

                if r == "0":
                    fini = True
                elif r.isdigit() and (n := int(r)) <= len(trigs):
                    bdd.session.delete(trigs[n-1])
                    bdd.session.commit()
                    del trigs[n-1]
                else:
                    trig = Triggers(trigger=r, reac_id=rep.id)
                    trigs.append(trig)
                    bdd.session.add(trig)
                    bdd.session.commit()

            if not trigs:        # on a tout supprimé !
                await ctx.send("Tous les triggers supprimés, suppression de la réaction")
                bdd.session.delete(rep)
                bdd.session.commit()
                return

        if MR:                  # Modification de la réponse
            r = ""
            if MT:      # Si ça fait longtemps, on remet la séquence
                r += f"Séquence actuelle : {displ_seq}"

            if any([mark in rep.reponse for mark in MARKS]):                    # Séquence compliquée
                r += f"\nLa séquence-réponse peut être refaite manuellement ou modifiée rapidement en envoyant directment la séquence ci-dessus modifiée (avec les marqueurs : OU = {tools.code(MARK_OR)}, ET = {tools.code(MARK_THEN)}, REACT = {tools.code(MARK_REACT)}, CMD = {tools.code(MARK_CMD)})"

            reponse = await _build_sequence(ctx)
            bdd_tools.modif(rep, "reponse", reponse)

        if not (MT or MR):      # Suppression
            bdd.session.delete(rep)
            for trig in trigs:
                bdd.session.delete(trig)

        bdd.session.commit()

        await ctx.send("Fini.")



async def trigger_at_mj(message):
    """Réaction si le message mentionne les MJs

    Args:
        message (:class:`~discord.Message`): message auquel réagir

    Returns:
        ``True`` si le message mentionne les MJ et qu'une réponse a été envoyée, ``False`` sinon
    """
    if message.role_mentions:           # Au moins un rôle mentionné
        if tools.role(message, "MJ") in message.role_mentions:      # MJs mentionnés (pas check direct pour des raisons de performance)
            await message.channel.send("Les MJs ont entenu ton appel, ils sont en route ! :superhero:")
            return True

    return False


async def trigger_roles(message, sensi=0.8):
    """Réaction si un nom de rôle est donné

    Args:
        message (:class:`~discord.Message`): message auquel réagir
        sensi (:class:`float`): sensibilité de la recherche (voir :func:`.bdd_tools.find_nearest`)

    Trouve l'entrée la plus proche de ``message.content`` dans la table :class:`.bdd.Roles`.

    Returns:
        ``True`` si un rôle a été trouvé (sensibilité ``> sensi``) et qu'une réponse a été envoyée, ``False`` sinon
    """
    roles = bdd_tools.find_nearest(message.content, Roles, carac="nom", sensi=sensi)

    if roles:       # Au moins un trigger trouvé à cette sensi
        role = roles[0][0]                                  # Meilleur trigger (score max)
        await message.channel.send(tools.code_bloc(f"{role.prefixe}{role.nom} – {role.description_courte} (camp : {role.camp})\n\n{role.description_longue}"))                    # On envoie
        return True

    return False


async def trigger_reactions(bot, message, chain=None, sensi=0.7, debug=False):
    """Réaction à partir de la base Reactions

    Args:
        bot (:class:`.LGBot`): bot
        message (:class:`~discord.Message`): message auquel réagir
        chain (:class:`str`): contenu auquel réagir (défaut : contenu de ``message``)
        sensi (:class:`float`): sensibilité de la recherche (voir :func:`.bdd_tools.find_nearest`)
        debug (:class:`bool`): si ``True``, affiche les erreurs lors de l'évaluation des messages (voir :func:`.tools.eval_accols`)

    Trouve l'entrée la plus proche de ``chain`` dans la table :class:`.bdd.Reactions` ; si il contient des accolades, évalue le message selon le contexte de ``message``.

    Returns:
        ``True`` si une réaction a été trouvée (sensibilité ``> sensi``) et qu'une réponse a été envoyée, ``False`` sinon
    """
    if not chain:                   # Si pas précisé,
        chain = message.content         # contenu de message
    trigs = bdd_tools.find_nearest(chain, Triggers, carac="trigger", sensi=sensi)

    if trigs:       # Au moins un trigger trouvé à cette sensi
        trig = trigs[0][0]                                  # Meilleur trigger (score max)
        rep = Reactions.query.get(trig.reac_id)
        assert rep, f"trigger_reactions : Réaction associée à {trig} introuvable"
        seq = rep.reponse                                   # Séquence-réponse associée

        for rep in seq.split(MARK_THEN):                    # Pour chaque étape :
            if MARK_OR in rep:                                  # Si plusieurs possiblités :
                rep = random.choice(rep.split(MARK_OR))             # On en choisit une random

            if rep.startswith(MARK_REACT):                      # Si réaction :
                react = rep.lstrip(MARK_REACT)
                emoji = tools.emoji(message, react, must_be_found=False) or react        # Si custom emoji : objet Emoji, sinon le codepoint de l'emoji direct
                await message.add_reaction(emoji)                   # Ajout de la réaction

            elif rep.startswith(MARK_CMD):                      # Si commande :
                message.content = rep.replace(MARK_CMD, bot.command_prefix)
                await bot.process_commands(message)                 # Exécution de la commande

            else:                                               # Sinon, texte / média :
                rep = tools.eval_accols(rep, locals_=locals(), debug=debug)  # On remplace tous les "{expr}" par leur évaluation
                # Passer locals permet d'accéder à bot, message... depuis eval_accols
                await message.channel.send(rep)                     # On envoie

        return True

    return False


async def trigger_sub_reactions(bot, message, sensi=0.9, debug=False):
    """Réaction à partir de la base Reactions sur les mots

    Appelle :func:`trigger_reactions(bot, message, mot, sensi, debug) <.trigger_reactions>` pour tous les mots ``mot`` composant ``message.content`` (mots de plus de 4 lettres, essayés des plus longs aux plus courts).

    Returns:
        ``True`` si une réaction a été trouvée (sensibilité ``> sensi``) et qu'une réponse a été envoyée, ``False`` sinon
    """
    mots = message.content.split(" ")
    if len(mots) > 1:       # Si le message fait plus d'un mot
        for mot in sorted(mots, key=lambda m:-len(m)):      # On parcourt les mots du plus long au plus court
            if len(mot) > 4:                                            # on élimine les mots de liaison
                if await trigger_reactions(bot, message, chain=mot, sensi=sensi, debug=debug):    # Si on trouve une sous-rect (à 0.9)
                    return True

    return False


async def trigger_di(message):
    """Réaction aux messages en di... / cri...

    Args:
        message (:class:`~discord.Message`): message auquel réagir

    Returns:
        ``True`` si le message correspond et qu'une réponse a été envoyée, ``False`` sinon
    """
    c = message.content
    diprefs = ["di", "dy", "dis ", "dit ", "dis-", "dit-"]
    criprefs = ["cri", "cry", "kri", "kry"]
    pos_prefs = {c.lower().find(pref): pref for pref in diprefs + criprefs
                if pref in c[:-1].lower()}                      # On extrait les cas où le préfixe est à la fin du message

    if pos_prefs:                                       # Si on a trouvé au moins un préfixe
        i = min(pos_prefs)
        pref = pos_prefs[i]
        if pref in criprefs:
            mess = tools.bold(c[i+len(pref):].upper())
        else:
            mess = c[i+len(pref):]
        await message.channel.send(mess, tts=True)          # On envoie le di.../cri... en mode TTS
        return True

    return False


async def trigger_gif(bot, message):
    """Réaction par GIF en mode Foire à la saucisse

    Args:
        message (:class:`~discord.Message`): message auquel réagir

    Returns:
        ``True`` si le message correspond et qu'une réponse a été envoyée, ``False`` sinon
    """
    if message.channel.id in bot.in_fals:       # Chan en mode Foire à la saucisse
        async with message.channel.typing():
            gif = fetch_tenor(message.content)
            if gif:
                await message.channel.send(gif)
                return True

    return False


async def trigger_mot_unique(message):
    """Réaction à un mot unique : le répète

    Args:
        message (:class:`~discord.Message`): message auquel réagir

    Returns:
        ``True`` si le message correspond et qu'une réponse a été envoyée, ``False`` sinon
    """
    if len(message.content.split()) == 1 and not ":" in message.content:
        rep = f"{message.content.capitalize()} ?"
        await message.channel.send(rep)
        return True

    return False


async def trigger_a_ou_b(message):
    """Réaction à un motif type « a ou b » : répond « b »

    Args:
        message (:class:`~discord.Message`): message auquel réagir

    Returns:
        ``True`` si le message correspond et qu'une réponse a été envoyée, ``False`` sinon
    """
    if (motif := re.fullmatch(r"(.+)\s+ou\s+(.+?)", message.content)):
        rep = f"{motif.group(2).rstrip(' !?.,;')}.".capitalize()
        await message.channel.send(rep)
        return True

    return False


async def default(message):
    """Réponse par défaut

    Returns:
        ``True`` (réponse par défaut envoyée)
    """
    mess = "Désolé, je n'ai pas compris :person_shrugging:"
    if random.random() < 0.05:
        mess += "\n(et toi, tu as perdu)"
    await message.channel.send(mess)                    # On envoie le texte par défaut
    return True



async def process_IA(bot, message, debug=False):
    """Exécute les règles d'IA

    Args:
        bot (:class:`.LGBot`): bot
        message (:class:`~discord.Message`): message auquel réagir
        debug (:class:`bool`): si ``True``, affiche les erreurs lors de l'évaluation des messages (voir :func:`.tools.eval_accols`)
    """
    (await trigger_at_mj(message)                                   # @MJ (aled)
        or await trigger_gif(bot, message)                          # Un petit GIF ? (en mode FALS uniquement)
        or await trigger_roles(message)                             # Rôles
        or await trigger_reactions(bot, message, debug=debug)       # Table Reactions (IA proprement dite)
        or await trigger_sub_reactions(bot, message, debug=debug)   # IA sur les mots
        or await trigger_a_ou_b(message)                                # di... / cri...
        or await trigger_di(message)                                # di... / cri...
        or await trigger_mot_unique(message)                        # Un seul mot ==> on répète
        or await default(message)                                   # Réponse par défaut
    )
