"""lg-rez / features / Tâches planifiées

Planification, liste, annulation, exécution de tâches planifiées

"""

import datetime

from discord.ext import commands

from lgrez import config
from lgrez.blocs import env, gsheets, tools
from lgrez.bdd import (Joueur, Action, Role, Camp, Utilisation, Ciblage,
                       CandidHaro, CandidHaroType, UtilEtat, CibleType, Vote)
from lgrez.features import gestion_actions


def export_vote(vote, utilisation):
    """Enregistre un vote/les actions résolues dans le GSheet ad hoc.

    Écrit dans le GSheet ``LGREZ_DATA_SHEET_ID``. Peut être écrasé
    pour une autre implémentation.

    Args:
        vote (.bdd.Vote): le vote concerné, ou ``None`` pour une action.
        utilisation (.bdd.Utilisation): l'utilisation qui vient d'être
            effectuée. Doit être remplie (:attr:`.bdd.Utilisation.is_filled`).

    Raises:
        RuntimeError: si la variable d'environnement ``LGREZ_DATA_SHEET_ID``
            n'est pas définie.
    """
    if vote and not isinstance(vote, Vote):
        vote = Vote[vote]       # str -> Vote

    joueur = utilisation.action.joueur
    if vote == Vote.cond:
        sheet_name = config.db_votecond_sheet
        data = [joueur.nom, utilisation.cible.nom]
    elif vote == Vote.maire:
        sheet_name = config.db_votemaire_sheet
        data = [joueur.nom, utilisation.cible.nom]
    elif vote == Vote.loups:
        sheet_name = config.db_voteloups_sheet
        data = [joueur.nom, joueur.camp.slug, utilisation.cible.nom]
    else:
        sheet_name = config.db_actions_sheet
        recap = "\n+\n".join(
            f"{action.base.slug}({last_util.decision})"
            for action in joueur.actions_actives
            if ((last_util := action.derniere_utilisation)
                and last_util.is_filled         # action effectuée
                and last_util.ts_decision.date() == datetime.date.today())
                # Et dernière décision aujourd'hui ==> on met dans le TDB
        )
        data = [joueur.nom, joueur.role.slug, joueur.camp.slug, recap]

    LGREZ_DATA_SHEET_ID = env.load("LGREZ_DATA_SHEET_ID")
    sheet = gsheets.connect(LGREZ_DATA_SHEET_ID).worksheet(sheet_name)
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    sheet.append_row([timestamp, *data], value_input_option="USER_ENTERED")


async def get_cible(ctx, action, base_ciblage, first=None):
    """Demande une cible à l'utilisateur.

    Args:
        ctx (~discord.ext.commands.Context): le contexte de commande.
        action: (.bdd.Action): action pour laquelle on cherche une cible.
        base_ciblage (.bdd.BaseCiblage): ciblage à demander.
        first (str): proposition initale du joueur (passée comme argument
            d'une commande).

    Returns:
        Union[.bdd.Joueur, .bdd.Role, .bdd.Camp, bool, str]: La
        cible sélectionnée, selon le type de ciblage.

    Réalise les interactions adéquates en fonction du type du base_ciblage,
    vérifie le changement de cible le cas échéant.
    """
    phrase = base_ciblage.phrase.rstrip()

    # ou_vide = ("" if base_ciblage.obligatoire
    #            else ", ou :no_entry_sign: pour laisser vide")
    if not base_ciblage.obligatoire:
        await ctx.send("[Étape non obligatoire, caractère non pris en "
                       "compte (pour l'instant) par le bot, dommage]")

    stop = f"({tools.code(config.stop_keywords[0])} pour annuler)"

    if base_ciblage.type == CibleType.joueur:
        res = await tools.boucle_query_joueur(
            ctx, cible=first, message=(f"{phrase}\n\n*Écris simplement le "
                                       f"nom du joueur ci-dessous {stop} :*")
        )
    elif base_ciblage.type == CibleType.vivant:
        res = await tools.boucle_query_joueur(
            ctx, cible=first, filtre=Joueur.est_vivant,
            message=(f"{phrase}\n\n*Écris simplement le nom du joueur "
                     f"(vivant) ci-dessous {stop} :*")
        )
    elif base_ciblage.type == CibleType.mort:
        res = await tools.boucle_query_joueur(
            ctx, cible=first, filtre=Joueur.est_mort,
            message=(f"{phrase}\n\n*Écris simplement le nom du mort "
                     f"ci-dessous {stop} :*")
        )
    elif base_ciblage.type == CibleType.role:
        res = await tools.boucle_query(
            ctx, Role, Role.nom, cible=first,
            message=(f"{phrase}\n\n*Écris simplement le nom du rôle "
                     f"ci-dessous {stop} :*")
        )
    elif base_ciblage.type == CibleType.camp:
        res = await tools.boucle_query(
            ctx, Camp, Camp.nom, cible=first,
            message=(f"{phrase}\n\n*Écris simplement le nom du camp "
                     f"ci-dessous {stop} :*")
        )
    elif base_ciblage.type == CibleType.booleen:
        message = await ctx.send(f"{phrase}\n\n*{stop}*")
        if first:
            await ctx.send(quote_bloc(first))
        res = await tools.yes_no(message, first_text=first)
    elif base_ciblage.type == CibleType.texte:
        if first:
            res = first
        else:
            await ctx.send(
                f"{phrase}\n\n*Réponds simplement ci-dessous {stop} :*"
            )
            mess = await tools.wait_for_message_here(ctx)
            res = mess.content

    if base_ciblage.doit_changer:
        derniere_util = action.utilisations.filter(
            ~Utilisation.is_open).order_by(Utilisation.ts_close.desc()).first()
        if derniere_util and derniere_util.etat == UtilEtat.validee:
            # Dernière utilisation validée : comparaison avec ciblages
            # de même prio que le ciblage en cours de demande
            cibles = [cib.valeur for cib in derniere_util.ciblages
                      if cib.base.prio == base_ciblage.prio]

            if res in cibles:       # interdit !
                await ctx.send(
                    f":stop_sign: {res} déjà ciblé(e) lors de la "
                    "précédente utilisation, merci de changer :stop_sign:\n"
                    "*(`@MJ` si contestation)*\n——————————"
                )
                await tools.sleep(ctx, 2)
                # On re-demande (ptite réccurence)
                res = await get_cible(ctx, action, base_ciblage)

    return res


class _BaseCiblageForVote():
    """Mock un objet BaseCiblage pour représenter la cible d'un vote"""
    def __init__(self, phrase):
        self._id = 0
        self.base_action = None
        self.slug = "cible"
        self.type = CibleType.vivant
        self.prio = 1
        self.phrase = phrase
        self.obligatoire = True     # vote blanc non pris en compte
        self.doit_changer = False


class VoterAgir(commands.Cog):
    """Commandes de vote et d'action de rôle"""

    @commands.command()
    @tools.vivants_only
    @tools.private
    async def vote(self, ctx, *, cible=None):
        """Vote pour le condamné du jour

        Args:
            cible: nom du joueur contre qui tu veux diriger ton vote.

        Cette commande n'est utilisable que lorsqu'un vote pour le
        condamné est en cours, pour les joueurs ayant le droit de voter.

        Le bot t'enverra un message à l'ouverture de chaque vote.

        La commande peut être utilisée autant que voulu pour changer
        de cible tant que le vote est en cours.
        """
        joueur = Joueur.from_member(ctx.author)
        try:
            vaction = joueur.action_vote(Vote.cond)
        except RuntimeError:
            await ctx.send("Minute papillon, le jeu n'est pas encore lancé !")
            return

        # Vérification vote en cours
        if not joueur.votant_village:
            await ctx.send("Tu n'as pas le droit de participer à ce vote.")
            return
        if not vaction.is_open:
            await ctx.send("Pas de vote pour le condamné de jour en cours !")
            return

        util = vaction.derniere_utilisation

        # Choix de la cible
        haros = CandidHaro.query.filter_by(type=CandidHaroType.haro).all()
        harotes = [haro.joueur.nom for haro in haros]
        pseudo_bc = _BaseCiblageForVote(
            "Contre qui veux-tu voter ? (vote actuel : "
            f"{tools.bold(util.cible.nom if util.cible else 'aucun')})\n"
            f"(harotés : {', '.join(harotes) or 'aucun :pensive:'})"
        )
        cible = await get_cible(ctx, vaction, pseudo_bc, cible)

        # Test si la cible est sous le coup d'un haro
        cible_ds_haro = CandidHaro.query.filter_by(
            joueur=cible, type=CandidHaroType.haro).all()
        if not cible_ds_haro:
            mess = await ctx.send(
                f"{cible.nom} n'a pas (encore) subi ou posté de haro ! "
                "Si c'est toujours le cas à la fin du vote, ton vote sera "
                "compté comme blanc... \n Veux-tu continuer ?"
            )
            if not await tools.yes_no(mess):
                await ctx.send("Compris, mission aborted.")
                return

        if not vaction.is_open:
            # On revérifie, si ça a fermé entre temps !!
            await ctx.send("Le vote pour le condamné du jour a fermé "
                           "entre temps, pas de chance !")
            return

        # Modification en base
        if util.ciblages:       # ancien ciblage
            Ciblage.delete(*util.ciblages)
        Ciblage(utilisation=util, joueur=cible).add()
        util.ts_decision = datetime.datetime.now()
        util.etat = UtilEtat.remplie
        util.update()

        async with ctx.typing():
            # Écriture dans sheet Données brutes
            export_vote(Vote.cond, util)

        await ctx.send(
            f"Vote contre {tools.bold(cible.nom)} bien pris en compte.\n"
            + tools.ital("Tu peux modifier ton vote autant que nécessaire "
                         "avant sa fermeture.")
        )


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def votemaire(self, ctx, *, cible=None):
        """Vote pour le nouveau maire

        Args:
            cible: nom du joueur pour lequel tu souhaites voter.

        Cette commande n'est utilisable que lorsqu'une élection pour le
        maire est en cours, pour les joueurs ayant le droit de voter.

        Le bot t'enverra un message à l'ouverture de chaque vote.

        La commande peut être utilisée autant que voulu pour changer de
        cible tant que le vote est en cours.
        """
        joueur = Joueur.from_member(ctx.author)
        try:
            vaction = joueur.action_vote(Vote.maire)
        except RuntimeError:
            await ctx.send("Minute papillon, le jeu n'est pas encore lancé !")
            return

        # Vérification vote en cours
        if not joueur.votant_village:
            await ctx.send("Tu n'as pas le droit de participer à ce vote.")
            return
        if not vaction.is_open:
            await ctx.send("Pas de vote pour le nouveau maire en cours !")
            return

        util = vaction.derniere_utilisation

        # Choix de la cible
        candids = CandidHaro.query.filter_by(
            type=CandidHaroType.candidature).all()
        candidats = [candid.joueur.nom for candid in candids]
        pseudo_bc = _BaseCiblageForVote(
            "Pour qui veux-tu voter ? (vote actuel : "
            f"{tools.bold(util.cible.nom if util.cible else 'aucun')})\n"
            f"(candidats : {', '.join(candidats) or 'aucun :pensive:'})"
        )
        cible = await get_cible(ctx, vaction, pseudo_bc, cible)

        # Test si la cible s'est présentée
        cible_ds_candid = CandidHaro.query.filter_by(
            joueur=cible, type=CandidHaroType.candidature).all()
        if not cible_ds_candid:
            mess = await ctx.send(
                f"{cible.nom} ne s'est pas (encore) présenté(e) ! "
                "Si c'est toujours le cas à la fin de l'élection, ton vote "
                "sera compté comme blanc... \n Veux-tu continuer ?"
            )
            if not await tools.yes_no(mess):
                await ctx.send("Compris, mission aborted.")
                return

        if not vaction.is_open:
            # On revérifie, si ça a fermé entre temps !!
            await ctx.send("Le vote pour le nouveau maire a fermé "
                           "entre temps, pas de chance !")
            return

        # Modification en base
        if util.ciblages:       # ancien ciblage
            Ciblage.delete(*util.ciblages)
        Ciblage(utilisation=util, joueur=cible).add()
        util.ts_decision = datetime.datetime.now()
        util.etat = UtilEtat.remplie
        util.update()

        async with ctx.typing():
            # Écriture dans sheet Données brutes
            export_vote(Vote.maire, util)

        await ctx.send(
            f"Vote pour {tools.bold(cible.nom)} bien pris en compte.\n"
            + tools.ital("Tu peux modifier ton vote autant "
                         "que nécessaire avant sa fermeture.")
        )


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def voteloups(self, ctx, *, cible=None):
        """Vote pour la victime de l'attaque des loups

        Args:
            cible: nom du joueur que tu souhaites éliminer.

        Cette commande n'est utilisable que lorsqu'une vote pour la
        victime du soir est en cours, pour les joueurs concernés.

        Le bot t'enverra un message à l'ouverture de chaque vote.

        La commande peut être utilisée autant que voulu pour changer
        de cible tant que le vote est en cours.
        """
        joueur = Joueur.from_member(ctx.author)
        try:
            vaction = joueur.action_vote(Vote.loups)
        except RuntimeError:
            await ctx.send("Minute papillon, le jeu n'est pas encore lancé !")
            return

        # Vérification vote en cours
        if not joueur.votant_loups:
            await ctx.send("Tu n'as pas le droit de participer à ce vote.")
            return
        if not vaction.is_open:
            await ctx.send("Pas de vote pour le nouveau maire en cours !")
            return

        util = vaction.derniere_utilisation

        # Choix de la cible
        pseudo_bc = _BaseCiblageForVote(
            "Qui veux-tu manger ? (vote actuel : "
            f"{tools.bold(util.cible.nom if util.cible else 'aucun')})"
        )
        cible = await get_cible(ctx, vaction, pseudo_bc, cible)

        if not vaction.is_open:
            # On revérifie, si ça a fermé entre temps !!
            await ctx.send("Le vote pour la victime des loups a "
                           "fermé entre temps, pas de chance !")
            return

        # Modification en base
        if util.ciblages:       # ancien ciblage
            Ciblage.delete(*util.ciblages)
        Ciblage(utilisation=util, joueur=cible).add()
        util.ts_decision = datetime.datetime.now()
        util.etat = UtilEtat.remplie
        util.update()

        async with ctx.typing():
            # Écriture dans sheet Données brutes
            export_vote(Vote.loups, util)

        await ctx.send(
            f"Vote contre {tools.bold(cible.nom)} bien pris en compte."
        )


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def action(self, ctx, *, decision=None):
        """Utilise l'action de ton rôle / une des actions associées

        Args:
            decision: ce que tu souhaites faire.

                Dans le cas où tu as plusieurs actions disponibles,
                ce paramètre n'est pas pris en compte pour éviter
                toute ambiguïté.

        Cette commande n'est utilisable que si tu as au moins une action
        ouverte. Action = pouvoir associé à ton rôle, mais aussi
        pouvoirs ponctuels (Lame Vorpale, Chat d'argent...)
        Le bot t'enverra un message à l'ouverture de chaque action.

        La commande peut être utilisée autant que voulu pour changer
        d'action tant que la fenêtre d'action est en cours, SAUF pour
        certaines actions (dites "instantanées") ayant une conséquence
        immédiate (Barbier, Licorne...). Le bot mettra dans ce cas un
        message d'avertissement.
        """
        joueur = Joueur.from_member(ctx.author)

        # Vérification rôle actif
        if not joueur.role_actif:
            await ctx.send(
                "Tu ne peux pas utiliser tes pouvoirs pour le moment !"
            )
            return

        # Détermine la/les actions en cours pour le joueur
        actions = [ac for ac in joueur.actions_actives if ac.is_open]
        if not actions:
            await ctx.send("Aucune action en cours pour toi.")
            return

        elif (N := len(actions)) > 1:
            decision = None
            # Évite de lancer une décision en blind
            # si le joueur a plusieurs actions
            txt = "Tu as plusieurs actions actuellement ouvertes :\n"
            for i in range(N):
                txt += (f" {tools.emoji_chiffre(i+1)} - "
                        f"{tools.code(actions[i].base.slug)}\n")
            message = await ctx.send(txt + "\nPour laquelle veux-tu agir ?")
            i = await tools.choice(message, N)
            action = actions[i-1]

        else:
            action = actions[0]

        util = action.derniere_utilisation

        # Dernière décision et choix annulation/modification
        delete = False
        if util.ciblages and not decision:
            pencil, trash = "\N{PENCIL}", "\N{WASTEBASKET}"
            message = await ctx.send(
                f"Action actuelle : {tools.bold(action.decision)}\n\n"
                f"Souhaites-tu la modifier ({pencil}) ou l'annuler ({trash}) ?"
            )
            delete = await tools.wait_for_react_clic(
                message, emojis={pencil: False, trash: True}
            )

        # Choix de la décision
        cibles = {}
        if not delete:
            for bc in action.base.base_ciblages:        # Triés par priorité
                cibles[bc] = await get_cible(ctx, action, bc, decision)
                decision = None     # si plus de 1 ciblage, vaut pour le 1er

        if not action.is_open:
            # On revérifie, si ça a fermé entre temps !!
            await ctx.send("L'action a fermé entre temps, pas de chance !")
            return

        # Avertissement si action a conséquence instantanée (barbier...)
        if action.base.instant:
            message = await ctx.send(
                "Attention : cette action a une conséquence instantanée ! "
                "Si tu valides, tu ne pourras pas revenir en arrière.\n"
                "Ça part ?"
            )
            if not await tools.yes_no(message):
                await ctx.send("Mission aborted.")
                return

        # Modification en base
        if util.ciblages:     # ancien ciblages
            Ciblage.delete(*util.ciblages)
        for bc, cible in cibles.items():
            cib = Ciblage(utilisation=util, base=bc)
            cib.valeur = cible      # affecte le bon attribut selon le bc.type
        util.ts_decision = datetime.datetime.now()
        util.etat = UtilEtat.remplie
        util.update()

        async with ctx.typing():
            # Écriture dans sheet Données brutes
            export_vote(None, util)

        # Conséquences si action instantanée
        if action.base.instant:
            await gestion_actions.close_action(action)

            await ctx.send(tools.ital(
                f"[Allô {config.Role.mj.mention}, "
                "conséquence instantanée ici !]"
            ))

        else:
            await ctx.send(
                f"Action « {tools.bold(action.decision)} » bien prise "
                f"en compte pour {tools.code(action.base.slug)}.\n"
                + tools.ital("Tu peux modifier ta décision autant que "
                             "nécessaire avant la fin du créneau.")
            )
