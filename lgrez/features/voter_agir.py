"""lg-rez / features / Tâches planifiées

Planification, liste, annulation, exécution de tâches planifiées

"""

import datetime

from discord.ext import commands

from lgrez import config
from lgrez.blocs import env, gsheets, tools
from lgrez.bdd import Joueur, Action, CandidHaro, CandidHaroType
from lgrez.features import gestion_actions


def export_vote(vote, joueur):
    """Enregistre un vote/les actions résolues dans le GSheet ad hoc.

    Écrit dans le GSheet ``LGREZ_DATA_SHEET_ID``. Peut être écrasé
    pour une autre implémentation.

    Args:
        vote (str): ```"cond"``, ```"maire"``, ```"loups"`` ou
            ``"action"``.
        joueur (.bdd.Joueur): le joueur ayant voté/agi.

    Raises:
        ValueError: si ``vote`` vaut une autre valeur.
        RuntimeError: si la variable d'environnement ``LGREZ_DATA_SHEET_ID``
            n'est pas définie.
    """
    if vote == "cond":
        sheet_name = "votecond_brut"
        data = [joueur.nom, joueur.vote_condamne_]
    elif vote == "maire":
        sheet_name = "votemaire_brut"
        data = [joueur.nom, joueur.vote_maire_]
    elif vote == "loups":
        sheet_name = "voteloups_brut"
        data = [joueur.nom, joueur.camp.slug, joueur.vote_loups_]
    elif vote == "action":
        sheet_name = "actions_brut"
        recap = "\n+\n".join(f"{action.base.slug} : {action.decision_}"
                             for action in joueur.actions
                             if action.decision_ is not None)
        data = [joueur.nom, joueur.role.slug, joueur.camp.slug, recap]
    else:
        raise ValueError(f"export_vote: valeur '{vote}' invalide pour 'vote'")

    LGREZ_DATA_SHEET_ID = env.load("LGREZ_DATA_SHEET_ID")
    sheet = gsheets.connect(LGREZ_DATA_SHEET_ID).worksheet(sheet_name)
    sheet.append_row([
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        *data
    ], value_input_option="USER_ENTERED")



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

        # Vérification vote en cours
        if not joueur.votant_village:
            await ctx.send("Tu n'es pas autorisé à participer à ce vote.")
            return
        elif joueur.vote_condamne_ is None:
            await ctx.send("Pas de vote pour le condamné de jour en cours !")
            return

        # Choix de la cible
        haros = CandidHaro.query.filter_by(type=CandidHaroType.haro).all()
        harotes = [haro.joueur.nom for haro in haros]
        cible = await tools.boucle_query_joueur(ctx, cible=cible, message=(
            f"Contre qui veux-tu voter ? (vote actuel : "
            f"{tools.bold(joueur.vote_condamne_)})\n"
            f"(harotés : {', '.join(harotes) or 'aucun :pensive:'})\n"
            "*Écris simplement le nom du joueur ci-dessous "
            f"({tools.code('stop')} pour annuler) :*"
        ))

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

        if joueur.vote_condamne_ is None:
            # On revérifie, si ça a fermé entre temps !!
            await ctx.send("Le vote pour le condamné du jour a fermé "
                           "entre temps, pas de chance !")
            return

        async with ctx.typing():
            # Modification en base
            joueur.vote_condamne_ = cible.nom
            joueur.update()

            # Écriture dans sheet Données brutes
            export_vote("cond", joueur)

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

        # Vérification vote en cours
        if not joueur.votant_village:
            await ctx.send("Tu n'es pas autorisé à participer à ce vote.")
            return
        elif joueur.vote_maire_ is None:
            await ctx.send("Pas de vote pour le nouveau maire en cours !")
            return


        # Choix de la cible
        candids = CandidHaro.query.filter_by(
            type=CandidHaroType.candidature).all()
        candidats = [candid.joueur.nom for candid in candids]
        cible = await tools.boucle_query_joueur(ctx, cible=cible, message=(
            "Pour qui veux-tu voter ? (vote actuel : "
            f"{tools.bold(joueur.vote_maire_)})\n"
            f"(candidats : {', '.join(candidats) or 'aucun :pensive:'})\n"
            f"*Écris simplement le nom du joueur ci-dessous "
            "({tools.code('stop')} pour annuler) :*"
        ))

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

        if joueur.vote_maire_ is None:
            # On revérifie, si ça a fermé entre temps !!
            await ctx.send("Le vote pour le nouveau maire a fermé "
                           "entre temps, pas de chance !")
            return

        async with ctx.typing():
            # Modification en base
            joueur.vote_maire_ = cible.nom
            joueur.update()

            # Écriture dans sheet Données brutes
            export_vote("maire", joueur)

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

        # Vérification vote en cours
        if not joueur.votant_loups:
            await ctx.send("Tu n'es pas autorisé à participer à ce vote.")
            return
        elif joueur.vote_loups_ is None:
            await ctx.send("Pas de vote pour la victime des loups en cours !")
            return

        # Choix de la cible
        cible = await tools.boucle_query_joueur(ctx, cible=cible, message=(
            "Qui veux-tu manger ? (vote actuel : "
            f"{tools.bold(joueur.vote_loups_)})"
            "\n*Écris simplement le nom du joueur ci-dessous "
            f"({tools.code('stop')} pour annuler) :*"
        ))

        if joueur.vote_loups_ is None:
            # On revérifie, si ça a fermé entre temps !!
            await ctx.send("Le vote pour la victime des loups a "
                           "fermé entre temps, pas de chance !")
            return

        async with ctx.typing():
            # Modification en base
            joueur.vote_loups_ = cible.nom
            joueur.update()

            # Écriture dans sheet Données brutes
            export_vote("loups", joueur)

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
        actions = Action.query.filter_by(joueur=joueur).filter(
            Action.decision_.isnot(None)).all()
        if not actions:
            await ctx.send("Aucune action en cours pour toi.")
            return

        elif (N := len(actions)) > 1:
            txt = "Tu as plusieurs actions actuellement en cours :\n"
            decision = None
            # Évite de lancer une décision en blind
            # si le joueur a plusieurs actions
            for i in range(N):
                txt += (f" {tools.emoji_chiffre(i+1)} - "
                        f"{tools.code(actions[i].base.slug)}\n")
            message = await ctx.send(txt + "\nPour laquelle veux-tu agir ?")
            i = await tools.choice(message, N)
            action = actions[i-1]

        else:
            action = actions[0]

        # Choix de la décision : très simple pour l'instant,
        # car pas de résolution auto
        if not decision:
            await ctx.send(
                "Que veux-tu faire pour l'action "
                f"{tools.code(action.base.slug)} ? (action actuelle : "
                f"{tools.bold(action.decision_)})"
            )
            message = await tools.wait_for_message_here(ctx)
            decision = message.content

        if action.decision_ is None:
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

        async with ctx.typing():
            # Modification en base
            action.decision_ = decision

            # Écriture dans sheet Données brutes
            export_vote("action", joueur)

        # Conséquences si action instantanée
        if action.base.instant:
            await gestion_actions.close_action(action)

            await ctx.send(tools.ital(
                f"[Allô {config.Role.mj.mention}, "
                "conséquence instantanée ici !]"
            ))

        else:
            await ctx.send(
                f"Action « {tools.bold(action.decision_)} » bien prise "
                f"en compte pour {tools.code(action.base.slug)}.\n"
                + tools.ital("Tu peux modifier ta décision autant que "
                             "nécessaire avant la fin du créneau.")
            )
