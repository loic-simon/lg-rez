import os
import datetime

from dotenv import load_dotenv
from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_

from bdd_connect import db, Joueurs, Actions
from features import gestion_actions
from blocs import bdd_tools, gsheets
import tools

load_dotenv()
VOTECOND_SHEET_ID = os.getenv("VOTECOND_SHEET_ID")
VOTEMAIRE_SHEET_ID = os.getenv("VOTEMAIRE_SHEET_ID")
VOTELOUPS_SHEET_ID = os.getenv("VOTELOUPS_SHEET_ID")
ACTIONS_SHEET_ID = os.getenv("ACTIONS_SHEET_ID")



class VoterAgir(commands.Cog):
    """VoterAgir : voter (aux votes) et agir (les actions) #yes"""

    @commands.command()
    @tools.private
    async def vote(self, ctx, *, nom_cible=None):
        """!vote [cible] - Vote pour le condamné du jour

        [cible] est la cible de ton vote"""

        joueur = Joueurs.query.get(ctx.author.id)

        # Vérification vote en cours
        if not joueur.votant_village:
            await ctx.send("Tu n'es pas autorisé à participer à ce vote.")
            return
        elif joueur._vote_condamne is None:
            await ctx.send("Pas de vote pour le condamné de jour en cours !")
            return

        # Choix de la cible
        cible = await tools.boucle_query_joueur(ctx, cible=nom_cible,
                                                message=f"Contre qui veux-tu voter ? (vote actuel : {joueur._vote_condamne})")

        async with ctx.typing():
            # Modification en base
            bdd_tools.modif(joueur, "_vote_condamne", cible.nom)
            db.session.commit()

            # Écriture dans sheet Données brutes
            sheet = gsheets.connect(VOTECOND_SHEET_ID).sheet1
            sheet.append_row([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), joueur.nom, joueur._vote_condamne], value_input_option="USER_ENTERED")

        await ctx.send(f"Votre contre {tools.code(cible.nom)} bien pris en compte.")


    @commands.command()
    @tools.private
    async def votemaire(self, ctx, *, nom_cible=None):
        """!votemaire [cible] - Vote pour le nouveau maire

        [cible] est la cible de ton vote"""

        joueur = Joueurs.query.get(ctx.author.id)

        # Vérification vote en cours
        if not joueur.votant_village:
            await ctx.send("Tu n'es pas autorisé à participer à ce vote.")
            return
        elif joueur._vote_maire is None:
            await ctx.send("Pas de vote pour le nouveau maire en cours !")
            return

        # Choix de la cible
        cible = await tools.boucle_query_joueur(ctx, cible=nom_cible,
                                                message=f"Pour qui veux-tu voter ? (vote actuel : {joueur._vote_maire})")

        async with ctx.typing():
            # Modification en base
            bdd_tools.modif(joueur, "_vote_maire", cible.nom)
            db.session.commit()

            # Écriture dans sheet Données brutes
            sheet = gsheets.connect(VOTEMAIRE_SHEET_ID).sheet1
            sheet.append_row([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), joueur.nom, joueur._vote_maire], value_input_option="USER_ENTERED")

        await ctx.send(f"Votre pour {tools.code(cible.nom)} bien pris en compte.")


    @commands.command()
    @tools.private
    async def voteloups(self, ctx, *, nom_cible=None):
        """!voteloups [cible] - Voter pour la victime de l'attaque des loups

        [cible] est la cible de ton vote"""

        joueur = Joueurs.query.get(ctx.author.id)

        # Vérification vote en cours
        if not joueur.votant_loups:
            await ctx.send("Tu n'es pas autorisé à participer à ce vote.")
            return
        elif joueur._vote_loups is None:
            await ctx.send("Pas de vote pour la victime des loups en cours !")
            return

        # Choix de la cible
        cible = await tools.boucle_query_joueur(ctx, cible=nom_cible,
                                                message=f"Qui veux-tu manger ? (vote actuel : {joueur._vote_loups})")

        async with ctx.typing():
            # Modification en base
            bdd_tools.modif(joueur, "_vote_loups", cible.nom)
            db.session.commit()

            # Écriture dans sheet Données brutes
            sheet = gsheets.connect(VOTELOUPS_SHEET_ID).sheet1
            sheet.append_row([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), joueur.nom, joueur.camp, joueur._vote_loups], value_input_option="USER_ENTERED")

        await ctx.send(f"Votre contre {tools.code(cible.nom)} bien pris en compte.")


    @commands.command()
    @tools.private
    async def action(self, ctx, *, decision=None):
        """!action [decision] - Utiliser l'action de ton rôle / une des actions associées

        [decision] correspond à comment tu utiliseras ton action
        Note: ce paramètre est facultatif, et il sera désactivé dans le cas où tu as plusieurs actions disponibles"""

        joueur = Joueurs.query.get(ctx.author.id)

        # Détermine la/les actions en cours pour le joueur
        def trigCheck(m):
            return (m.channel == ctx.channel and m.author != ctx.bot.user)

        actions = Actions.query.filter(Actions.player_id == joueur.discord_id, Actions._decision != None).all()
        if not actions:
            await ctx.send("Aucune action en cours pour toi.")
            return
        elif (N := len(actions)) > 1:
            txt = "Tu as plusieurs actions actuellement en cours :\n"
            decision = None #Evite de lancer une décision en blind si le joueur a plusieurs actions
            for i in range(N):
                txt += f" {tools.emoji_chiffre(i+1)} - {actions[i].action}\n"
            message = await ctx.send(txt + "\nPour laquelle veux-tu agir ?")
            i = await tools.choice(ctx.bot, message, N)
            action = actions[i-1]
        else:
            action = actions[0]

        # Choix de la décision : très simple pour l'instant, car pas de résolution auto
        if not decision:                   # Si décision pas précisée à l'appel de la commande
            await ctx.send(f"Que veux-tu faire pour l'action {action.action} ? (action actuelle : {action._decision})")
            message = await tools.wait_for_message(ctx.bot, check=trigCheck)
            decision = message.content

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
            bdd_tools.modif(action, "_decision", decision)

            # Écriture dans sheet Données brutes
            sheet = gsheets.connect(ACTIONS_SHEET_ID).sheet1
            sheet.append_row([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), joueur.nom, joueur.role, joueur.camp,
                              "\n+\n".join([f"{action.action} : {action._decision}" for action in actions])],
                             value_input_option="USER_ENTERED")

            await ctx.send(f"Action « {action._decision} » bien prise en compte pour {action.action}.")

            # Conséquences si action instantanée
            if action.instant:
                deleted = False
                if action.charges:
                    bdd_tools.modif(action, "charges", action.charges - 1)
                    pcs = " pour cette semaine" if "weekends" in action.refill else ""
                    await ctx.send(f"Il te reste {action.charges} charge(s){pcs}.")
                    if action.charges == 0 and not action.refill:
                        db.session.delete(action)
                        deleted = True
                if not deleted:
                    bdd_tools.modif(action, "_decision", None)

                await ctx.send(f"[Allo {tools.role(ctx, 'MJ').mention}, conséquance instantanée ici !]")

            db.session.commit()
