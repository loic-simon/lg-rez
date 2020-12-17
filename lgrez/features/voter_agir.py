"""lg-rez / features / Tâches planifiées

Planification, liste, annulation, exécution de tâches planifiées

"""

import datetime

from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_

from lgrez.blocs import env, bdd, bdd_tools, gsheets, tools
from lgrez.blocs.bdd import Joueurs, Actions, CandidHaro
from lgrez.features import gestion_actions



class VoterAgir(commands.Cog):
    """VoterAgir - Commandes de vote et d'action de rôle"""

    @commands.command()
    @tools.vivants_only
    @tools.private
    async def vote(self, ctx, *, cible=None):
        """Vote pour le condamné du jour

        Args:
            cible: nom du joueur contre qui tu veux diriger ton vote.

        Cette commande n'est utilisable que lorsqu'un vote pour le condamné est en cours, pour les joueurs ayant le droit de voter.

        Le bot t'enverra un message à l'ouverture de chaque vote.

        La commande peut être utilisée autant que voulu pour changer de cible tant que le vote est en cours.
        """
        joueur = Joueurs.query.get(ctx.author.id)
        assert joueur, f"!vote : joueur {ctx.author} introuvable"

        # Vérification vote en cours
        if not joueur.votant_village:
            await ctx.send("Tu n'es pas autorisé à participer à ce vote.")
            return
        elif joueur.vote_condamne_ is None:
            await ctx.send("Pas de vote pour le condamné de jour en cours !")
            return

        # Choix de la cible
        haros = CandidHaro.query.filter_by(type="haro").all()
        harotes = [Joueurs.query.get(haro.player_id).nom for haro in haros]
        cible = await tools.boucle_query_joueur(ctx, cible=cible,
            message=f"Contre qui veux-tu voter ? (vote actuel : {tools.bold(joueur.vote_condamne_)})"
                    f"\n(harotés : {', '.join(harotes) or 'aucun :pensive:'})"
                    f"\n*Écris simplement le nom du joueur ci-dessous ({tools.code('stop')} pour annuler) :*"
        )

        # Test si la cible est sous le coup d'un haro
        cible_ds_haro = CandidHaro.query.filter_by(player_id=cible.discord_id, type='haro').all()
        if not cible_ds_haro:
            mess = await ctx.send(f"{cible.nom} n'a pas (encore) subi ou posté de haro ! Si c'est toujours le cas à la fin du vote, ton vote sera compté comme blanc... \n Veux-tu continuer ?")
            if not await tools.yes_no(ctx.bot, mess):
                await ctx.send("Compris, mission aborted.")
                return

        if joueur.vote_condamne_ is None:      # On revérifie, si ça a fermé entre temps !!
            await ctx.send("Le vote pour le condamné du jour a fermé entre temps, pas de chance !")
            return

        async with ctx.typing():
            # Modification en base
            bdd_tools.modif(joueur, "vote_condamne_", cible.nom)
            bdd.session.commit()

            # Écriture dans sheet Données brutes
            LGREZ_DATA_SHEET_ID = env.load("LGREZ_DATA_SHEET_ID")
            sheet = gsheets.connect(LGREZ_DATA_SHEET_ID).worksheet("votecond_brut")
            sheet.append_row([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), joueur.nom, joueur.vote_condamne_], value_input_option="USER_ENTERED")

        await ctx.send(f"Vote contre {tools.bold(cible.nom)} bien pris en compte.\n"
                       + tools.ital("Tu peux modifier ton vote autant que nécessaire avant sa fermeture."))


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def votemaire(self, ctx, *, cible=None):
        """Vote pour le nouveau maire

        Args:
            cible: nom du joueur pour lequel tu souhaites voter.

        Cette commande n'est utilisable que lorsqu'une élection pour le maire est en cours, pour les joueurs ayant le droit de voter.

        Le bot t'enverra un message à l'ouverture de chaque vote.

        La commande peut être utilisée autant que voulu pour changer de cible tant que le vote est en cours.
        """
        joueur = Joueurs.query.get(ctx.author.id)
        assert joueur, f"!vote : joueur {ctx.author} introuvable"

        # Vérification vote en cours
        if not joueur.votant_village:
            await ctx.send("Tu n'es pas autorisé à participer à ce vote.")
            return
        elif joueur.vote_maire_ is None:
            await ctx.send("Pas de vote pour le nouveau maire en cours !")
            return


        # Choix de la cible
        candids = CandidHaro.query.filter_by(type="candidature").all()
        candidats = [Joueurs.query.get(candid.player_id).nom for candid in candids]
        cible = await tools.boucle_query_joueur(ctx, cible=cible,
            message=f"Pour qui veux-tu voter ? (vote actuel : {tools.bold(joueur.vote_maire_)})"
                    f"\n(candidats : {', '.join(candidats) or 'aucun :pensive:'})"
                    f"\n*Écris simplement le nom du joueur ci-dessous ({tools.code('stop')} pour annuler) :*"
        )

        # Test si la cible s'est présentée
        cible_ds_candid = CandidHaro.query.filter_by(player_id=cible.discord_id, type='candidature').all()
        if not cible_ds_candid:
            mess = await ctx.send(f"{cible.nom} ne s'est pas (encore) présenté(e) ! Si c'est toujours le cas à la fin de l'élection, ton vote sera compté comme blanc... \n Veux-tu continuer ?")
            if not await tools.yes_no(ctx.bot, mess):
                await ctx.send("Compris, mission aborted.")
                return

        if joueur.vote_maire_ is None:          # On revérifie, si ça a fermé entre temps !!
            await ctx.send("Le vote pour le nouveau maire a fermé entre temps, pas de chance !")
            return

        async with ctx.typing():
            # Modification en base
            bdd_tools.modif(joueur, "vote_maire_", cible.nom)
            bdd.session.commit()

            # Écriture dans sheet Données brutes
            LGREZ_DATA_SHEET_ID = env.load("LGREZ_DATA_SHEET_ID")
            sheet = gsheets.connect(LGREZ_DATA_SHEET_ID).worksheet("votemaire_brut")
            sheet.append_row([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), joueur.nom, joueur.vote_maire_], value_input_option="USER_ENTERED")

        await ctx.send(f"Vote pour {tools.bold(cible.nom)} bien pris en compte.\n"
                       + tools.ital("Tu peux modifier ton vote autant que nécessaire avant sa fermeture."))


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def voteloups(self, ctx, *, cible=None):
        """Vote pour la victime de l'attaque des loups

        Args:
            cible: nom du joueur que tu souhaites éliminer.

        Cette commande n'est utilisable que lorsqu'une vote pour la victime du soir est en cours, pour les joueurs concernés.

        Le bot t'enverra un message à l'ouverture de chaque vote.

        La commande peut être utilisée autant que voulu pour changer de cible tant que le vote est en cours.
        """
        joueur = Joueurs.query.get(ctx.author.id)
        assert joueur, f"!vote : joueur {ctx.author} introuvable"

        # Vérification vote en cours
        if not joueur.votant_loups:
            await ctx.send("Tu n'es pas autorisé à participer à ce vote.")
            return
        elif joueur.vote_loups_ is None:
            await ctx.send("Pas de vote pour la victime des loups en cours !")
            return

        # Choix de la cible
        cible = await tools.boucle_query_joueur(ctx, cible=cible,
                                                message=f"Qui veux-tu manger ? (vote actuel : {tools.bold(joueur.vote_loups_)})"
                                                f"\n*Écris simplement le nom du joueur ci-dessous ({tools.code('stop')} pour annuler) :*")

        if joueur.vote_loups_ is None:          # On revérifie, si ça a fermé entre temps !!
            await ctx.send("Le vote pour la victime des loups a fermé entre temps, pas de chance !")
            return

        async with ctx.typing():
            # Modification en base
            bdd_tools.modif(joueur, "vote_loups_", cible.nom)
            bdd.session.commit()

            # Écriture dans sheet Données brutes
            LGREZ_DATA_SHEET_ID = env.load("LGREZ_DATA_SHEET_ID")
            sheet = gsheets.connect(LGREZ_DATA_SHEET_ID).worksheet("voteloups_brut")
            sheet.append_row([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), joueur.nom, joueur.camp, joueur.vote_loups_], value_input_option="USER_ENTERED")

        await ctx.send(f"Vote contre {tools.bold(cible.nom)} bien pris en compte.")


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def action(self, ctx, *, decision=None):
        """Utilise l'action de ton rôle / une des actions associées

        Args:
            decision: ce que tu souhaites faire.

                Dans le cas où tu as plusieurs actions disponibles, ce paramètre n'est pas pris en compte pour éviter toute ambiguïté.

        Cette commande n'est utilisable que si tu as au moins une action ouverte. Action = pouvoir associé à ton rôle, mais aussi pouvoirs ponctuels (Lame Vorpale, Chat d'argent...)
        Le bot t'enverra un message à l'ouverture de chaque action.

        La commande peut être utilisée autant que voulu pour changer d'action tant que la fenêtre d'action est en cours, SAUF pour certaines actions (dites "instantanées") ayant une conséquence immédiate (Barbier, Licorne...). Le bot mettra dans ce cas un message d'avertissement.
        """
        joueur = Joueurs.query.get(ctx.author.id)
        assert joueur, f"!vote : joueur {ctx.author} introuvable"

        # Détermine la/les actions en cours pour le joueur
        actions = Actions.query.filter(Actions.player_id == joueur.discord_id, Actions.decision_ != None).all()
        if not actions:
            await ctx.send("Aucune action en cours pour toi.")
            return
        elif (N := len(actions)) > 1:
            txt = "Tu as plusieurs actions actuellement en cours :\n"
            decision = None #Evite de lancer une décision en blind si le joueur a plusieurs actions
            for i in range(N):
                txt += f" {tools.emoji_chiffre(i+1)} - {tools.code(actions[i].action)}\n"
            message = await ctx.send(txt + "\nPour laquelle veux-tu agir ?")
            i = await tools.choice(ctx.bot, message, N)
            action = actions[i-1]
        else:
            action = actions[0]

        # Choix de la décision : très simple pour l'instant, car pas de résolution auto
        if not decision:                    # Si décision pas précisée à l'appel de la commande
            await ctx.send(f"Que veux-tu faire pour l'action {tools.code(action.action)} ? (action actuelle : {tools.bold(action.decision_)})")
            message = await tools.wait_for_message_here(ctx)
            decision = message.content

        if action.decision_ is None:        # On revérifie, si ça a fermé entre temps !!
            await ctx.send("L'action a fermé entre temps, pas de chance !")
            return

        # Avertissement si action a conséquence instantanée (barbier...)
        if action.instant:
            message = await ctx.send("Attention : cette action a une conséquence instantanée ! "
                                     "Si tu valides, tu ne pourras pas revenir en arrière.\n"
                                     "Ça part ?")
            if not await tools.yes_no(ctx.bot, message):
                await ctx.send("Mission aborted.")
                return

        async with ctx.typing():
            # Modification en base
            bdd_tools.modif(action, "decision_", decision)

            # Écriture dans sheet Données brutes
            LGREZ_DATA_SHEET_ID = env.load("LGREZ_DATA_SHEET_ID")
            sheet = gsheets.connect(LGREZ_DATA_SHEET_ID).worksheet("actions_brut")
            sheet.append_row([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), joueur.nom, joueur.role, joueur.camp,
                              "\n+\n".join([f"{action.action} : {action.decision_}" for action in actions])],
                             value_input_option="USER_ENTERED")

        # Conséquences si action instantanée
        if action.instant:
            async with ctx.typing():
                deleted = False
                if action.charges:
                    bdd_tools.modif(action, "charges", action.charges - 1)
                    pcs = " pour cette semaine" if "weekends" in (action.refill or "").split() else ""
                    await ctx.send(f"Il te reste {action.charges} charge(s){pcs}.")
                    if action.charges == 0 and not action.refill:
                        gestion_actions.delete_action(ctx, action)
                        deleted = True
                if not deleted:
                    bdd_tools.modif(action, "decision_", None)

            await ctx.send(tools.ital(f"[Allo {tools.role(ctx, 'MJ').mention}, conséquence instantanée ici !]"))

        else:
            await ctx.send(f"Action « {tools.bold(action.decision_)} » bien prise en compte pour {tools.code(action.action)}.\n"
                           + tools.ital("Tu peux modifier ta décision autant que nécessaire avant la fin du créneau."))
