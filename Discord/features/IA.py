import random

from discord.ext import commands

import tools
from blocs import bdd_tools
from bdd_connect import db, Triggers, Reactions, Roles


# Marqueurs de séparation du mini-langage des séquences-réactions
MARK_OR = ' <||> '
MARK_THEN = ' <&&> '
MARK_REACT = '<::>'
MARK_CMD = '<!!>'
MARKS = [MARK_OR, MARK_THEN, MARK_REACT, MARK_CMD]



async def build_sequence(ctx):
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



class GestionIA(commands.Cog):
    """GestionIA - Commandes relatives à l'IA (réponses automatiques du bot)"""

    @commands.command()
    @tools.private
    async def stfu(self, ctx, force=None):
        """Active/désactive la réponse automatique du bot sur ton channel privé

        [force=start/stop] permet de forcer l'activation / la désactivation.
        Sans argument, la commande agit comme un toggle (active les réactions si désactivées et vice-versa).

        N'agit que sur les messages classiques envoyés dans le channel : les commandes restent reconnues.
        Si vous ne comprenez pas le nom de la commande, demandez à Google.
        """
        id = ctx.channel.id

        if force in [None, "start"] and id not in ctx.bot.in_stfu:
            ctx.bot.in_stfu.append(id)
            await ctx.send("Okay, je me tais ! Tape !stfu quand tu voudras de nouveau de moi :cry:")

        elif force in [None, "stop"] and id in ctx.bot.in_stfu:
            ctx.bot.in_stfu.remove(id)
            await ctx.send("Ahhh, ça fait plaisir de pouvoir reparler !")

        else:       # Quelque chose d'autre que start/stop précisé après !stfu : bot discret
            if id in ctx.bot.in_stfu:
                ctx.bot.in_stfu.remove(id)
            else:
                ctx.bot.in_stfu.append(id)


    @commands.command(aliases=["r"])
    async def react(self, ctx, *, trigger):
        """Force le bot à réagir à un message

        <trigger> message auquel le bot doit réagir

        Permet de faire appel à l'IA du bot même sur les chans publics, ou en mode STFU, etc.
        Si utilisée par un MJ, active aussi le mode débug des évaluations Python (messages d'erreur).
        """
        oc = ctx.message.content
        ctx.message.content = trigger
        await process_IA(ctx.bot, ctx.message, debug=(ctx.author.top_role.name == "MJ"))
        ctx.message.content = oc        # On rétablit le message original pour ne pas qu'il trigger l'IA 2 fois, le cas échéant


    @commands.command()
    @tools.mjs_only
    async def addIA(self, ctx, *, triggers=None):
        """Ajoute au bot une règle d'IA : mots ou expressions déclenchant une réaction (COMMANDE MJ)

        [trigger] mot(s), phrase(s), ou expression(s) séparées par des points-virgules ou sauts de lignes
        Dans le cas où plusieurs expressions sont spécifiées, toutes déclencheront l'action demandée.
        """
        if not triggers:
            await ctx.send("Mots/expressions déclencheurs (non sensibles à la casse / accents), séparés par des points-virgules ou des sauts de ligne :")
            mess = await tools.wait_for_message_here(ctx)
            triggers = mess.content

        triggers = triggers.replace('\n', ';').split(';')
        triggers = [tools.remove_accents(s).lower().strip() for s in triggers]
        await ctx.send(f"Triggers : `{'` – `'.join(triggers)}`")

        reponse = await build_sequence(ctx)

        await ctx.send(f"Résumé de la séquence : {tools.code(reponse)}")
        async with ctx.typing():
            reac = Reactions(reponse=reponse)
            db.session.add(reac)
            db.session.flush()          # On "fait comme si" on commitait l'ajout de reac, ce qui calcule read.id (autoincrément)

            trigs = [Triggers(trigger=trigger, reac_id=reac.id) for trigger in triggers]
            db.session.add_all(trigs)
            db.session.commit()
        await ctx.send(f"Règle ajoutée en base.")


    @commands.command()
    @tools.mjs_only
    async def listIA(self, ctx, trigger=None, sensi=0.5):
        """Liste les règles d'IA actuellement reconnues par le bot (COMMANDE MJ)

        [trigger] (optionnel) mot/expression permettant de filter et trier les résultats. SI TRIGGER FAIT PLUS D'UN MOT, IL DOIT ÊTRE ENTOURÉ PAR DES GUILLEMETS !
        Si trigger est précisé, les triggers sont détectés avec une sensibilité [sensi] (ratio des caractères correspondants, entre 0 et 1).
        """
        async with ctx.typing():
            if trigger:
                trigs = await bdd_tools.find_nearest(trigger, table=Triggers, carac="trigger", sensi=sensi, solo_si_parfait=False)
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
    @tools.mjs_only
    async def modifIA(self, ctx, *, trigger=None):
        """Modifie/supprime une règle d'IA (COMMANDE MJ)

        [trigger] mot/expression déclenchant la réaction à modifier/supprimer

        Permet d'ajouter et supprimer des triggers, de modifier la réaction du bot (construction d'une séquence de réponses successives ou aléatoires) ou de supprimer la réaction.
        """
        if not trigger:
            await ctx.send("Mot/expression déclencheur de la réaction à modifier :")
            mess = await tools.wait_for_message_here(ctx)
            trigger = mess.content

        trigs = await bdd_tools.find_nearest(trigger, Triggers, carac="trigger")
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
                    db.session.delete(trigs[n-1])
                    db.session.commit()
                    del trigs[n-1]
                else:
                    trig = Triggers(trigger=r, reac_id=rep.id)
                    trigs.append(trig)
                    db.session.add(trig)
                    db.session.commit()

            if not trigs:        # on a tout supprimé !
                await ctx.send("Tous les triggers supprimés, suppression de la réaction")
                db.session.delete(rep)
                db.session.commit()
                return

        if MR:                  # Modification de la réponse
            r = ""
            if MT:      # Si ça fait longtemps, on remet la séquence
                r += f"Séquence actuelle : {displ_seq}"

            if any([mark in rep.reponse for mark in MARKS]):                    # Séquence compliquée
                r += f"\nLa séquence-réponse peut être refaite manuellement ou modifiée rapidement en envoyant directment la séquence ci-dessus modifiée (avec les marqueurs : OU = {tools.code(MARK_OR)}, ET = {tools.code(MARK_THEN)}, REACT = {tools.code(MARK_REACT)}, CMD = {tools.code(MARK_CMD)})"

            reponse = await build_sequence(ctx)
            bdd_tools.modif(rep, "reponse", reponse)

        if not (MT or MR):      # Suppression
            db.session.delete(rep)
            for trig in trigs:
                db.session.delete(trig)

        db.session.commit()

        await ctx.send("Fini.")



async def trigger_roles(message):
    """Réaction si un nom de rôle est donné"""
    roles = await bdd_tools.find_nearest(message.content, Roles, carac="nom", sensi=0.7)

    if roles:       # Au moins un trigger trouvé à cette sensi
        role = roles[0][0]                                  # Meilleur trigger (score max)
        await message.channel.send(tools.code_bloc(f"{role.prefixe}{role.nom} – {role.description_courte}\n\n{role.description_longue}"))                    # On envoie
        return True

    return False


async def trigger_reactions(bot, message, chain=None, sensi=0.7, debug=False):
    """Réaction à partir de la base Reactions"""
    if not chain:                   # Si pas précisé,
        chain = message.content         # contenu de message
    trigs = await bdd_tools.find_nearest(chain, Triggers, carac="trigger", sensi=sensi)

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
                emoji = tools.emoji(message, react) or react        # Si custom emoji : objet Emoji, sinon le codepoint de l'emoji direct
                await message.add_reaction(emoji)                   # Ajout de la réaction

            elif rep.startswith(MARK_CMD):                      # Si commande :
                message.content = rep.replace(MARK_CMD, bot.command_prefix)
                await bot.process_commands(message)                 # Exécution de la commande

            else:                                               # Sinon, texte / média :
                rep = tools.eval_accols(rep, locals=locals(), debug=debug)  # On remplace tous les "{expr}" par leur évaluation
                # Passer locals permet d'accéder à bot, message... depuis eval_accols
                await message.channel.send(rep)                     # On envoie

        return True

    return False


async def trigger_sub_reactions(bot, message, debug=False):
    """Réaction à partir de la base Reactions sur les mots"""
    mots = message.content.split(" ")
    if len(mots) > 1:       # Si le message fait plus d'un mot
        for mot in sorted(mots, key=lambda m:-len(m)):      # On parcourt les mots du plus long au plus court
            if len(mot) > 4:                                            # on élimine les mots de liaison
                if await trigger_reactions(bot, message, chain=mot, sensi=0.9, debug=debug):    # Si on trouve une sous-rect (à 0.9)
                    return True

    return False


async def trigger_di(message):
    """Réaction aux messages en di... / cri..."""
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


async def default(message):
    """Réponse par défaut"""
    mess = "Désolé, je n'ai pas compris 🤷‍♂️"
    if random.random() < 0.05:
        mess += "\n(et toi, tu as perdu)"
    await message.channel.send(mess)                    # On envoie le texte par défaut


async def process_IA(bot, message, debug=False):
    """Exécute les règles d'IA en réaction à <message> (par ordre de priorité)
    [debug] permet d'afficher des messages en cas d'erreur lors de l'évaluation des commandes.
    """
    (await trigger_roles(message)                                   # Rôles
        or await trigger_reactions(bot, message, debug=debug)       # Table Reactions (IA proprement dite)
        or await trigger_sub_reactions(bot, message, debug=debug)   # IA sur les mots
        or await trigger_di(message)                                # di... / cri...
        or await default(message)                                   # Réponse par défaut
    )
