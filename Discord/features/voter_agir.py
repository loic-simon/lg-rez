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
    
    def __init__(self, bot):
        self.bot = bot


    @commands.command()
    @tools.private
    async def vote(self, ctx, *, nom_cible=None):
        """Voter pour le condamné du jour"""

        joueur = Joueurs.query.get(ctx.author.id)

        # Vérification vote en cours
        if not joueur.votant_village:
            await ctx.send("Tu n'es pas autorisé à participer à ce vote.")
            return
        elif joueur._vote_condamne is None:
            await ctx.send("Pas de vote pour le condamné de jour en cours !")
            return

        # Choix de la cible
        def trigCheck(m):
            return (m.channel == ctx.channel and m.author != self.bot.user)
            
        if not nom_cible:                   # Si cible pas précisée à l'appel de la commande
            await ctx.send(f"Contre qui veux-tu voter ? (vote actuel : {joueur._vote_condamne})")
            message = await self.bot.wait_for('message', check=trigCheck)
            nom_cible = message.content
        while not (cible := Joueur.query.filter_by(nom=nom_cible).one_or_none()):    # Tant que nom_cible n'est pas le nom d'un joueur
            await ctx.send(f"Cible {tools.quote(nom_cible)} non trouvée : contre qui veux-tu voter ?")
            message = await self.bot.wait_for('message', check=trigCheck)
            nom_cible = message.content
            
        async with ctx.typing():
            bdd_tools.modif(joueur, "_vote_condamne", cible.nom)       # Modification en base
            db.session.commit()
            
            sheet = gsheets.connect(VOTECOND_SHEET_ID).sheet1                   # Écriture dans sheet Données brutes
            sheet.append_row([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), joueur.nom, joueur._vote_condamne], value_input_option="USER_ENTERED")
            
        await ctx.send(f"Votre contre {tools.quote(cible.nom)} bien pris en compte.")


    @commands.command()
    @tools.private
    async def votemaire(self, ctx, *, nom_cible=None):
        """Voter pour le nouveau maire"""

        joueur = Joueurs.query.get(ctx.author.id)

        # Vérification vote en cours
        if not joueur.votant_village:
            await ctx.send("Tu n'es pas autorisé à participer à ce vote.")
            return
        elif joueur._vote_maire is None:
            await ctx.send("Pas de vote pour le nouveau maire en cours !")
            return

        # Choix de la cible
        def trigCheck(m):
            return (m.channel == ctx.channel and m.author != self.bot.user)
            
        if not nom_cible:                   # Si cible pas précisée à l'appel de la commande
            await ctx.send(f"Pour qui veux-tu voter ? (vote actuel : {joueur._vote_maire})")
            message = await self.bot.wait_for('message', check=trigCheck)
            nom_cible = message.content
        while not (cible := Joueur.query.filter_by(nom=nom_cible).one_or_none()):     # Tant que nom_cible n'est pas le nom d'un joueur
            await ctx.send(f"Cible {tools.quote(nom_cible)} non trouvée : pour qui veux-tu voter ?")
            message = await self.bot.wait_for('message', check=trigCheck)
            nom_cible = message.content
            
        async with ctx.typing():
            bdd_tools.modif(joueur, "_vote_maire", cible.nom)       # Modification en base
            db.session.commit()
            
            sheet = gsheets.connect(VOTEMAIRE_SHEET_ID).sheet1                   # Écriture dans sheet Données brutes
            sheet.append_row([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), joueur.nom, joueur._vote_maire], value_input_option="USER_ENTERED")
            
        await ctx.send(f"Votre pour {tools.quote(cible.nom)} bien pris en compte.")
        

    @commands.command()
    @tools.private
    async def voteloups(self, ctx, *, nom_cible=None):
        """Voter pour la victime de l'attaque des loups"""

        joueur = Joueurs.query.get(ctx.author.id)

        # Vérification vote en cours
        if not joueur.votant_loups:
            await ctx.send("Tu n'es pas autorisé à participer à ce vote.")
            return
        elif joueur._vote_loups is None:
            await ctx.send("Pas de vote pour la victime des loups en cours !")
            return

        # Choix de la cible
        def trigCheck(m):
            return (m.channel == ctx.channel and m.author != self.bot.user)
            
        if not nom_cible:                   # Si cible pas précisée à l'appel de la commande
            await ctx.send(f"Qui veux-tu manger ? (vote actuel : {joueur._vote_loups})")
            message = await self.bot.wait_for('message', check=trigCheck)
            nom_cible = message.content
        while not (cible := Joueur.query.filter_by(nom=nom_cible).one_or_none()):     # Tant que nom_cible n'est pas le nom d'un joueur
            await ctx.send(f"Cible {tools.quote(nom_cible)} non trouvée : qui veux-tu manger ?")
            message = await self.bot.wait_for('message', check=trigCheck)
            nom_cible = message.content
            
        async with ctx.typing():
            bdd_tools.modif(joueur, "_vote_loups", cible.nom)       # Modification en base
            db.session.commit()
            
            sheet = gsheets.connect(VOTELOUPS_SHEET_ID).sheet1                   # Écriture dans sheet Données brutes
            sheet.append_row([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), joueur.nom, joueur.camp, joueur._vote_loups], value_input_option="USER_ENTERED")
            
        await ctx.send(f"Votre contre {tools.quote(cible.nom)} bien pris en compte.")
        

    @commands.command()
    @tools.private
    async def action(self, ctx, *, decision=None):
        """Utiliser l'action / une des actions assossiées """

        joueur = Joueurs.query.get(ctx.author.id)

        # Détermine la/les actions en cours pour le joueur
        def trigCheck(m):
            return (m.channel == ctx.channel and m.author != self.bot.user)
            
        actions = Actions.query.filter(Actions.player_id == joueur.discord_id, Actions._decision != None).all()
        if not actions:
            await ctx.send("Aucune action en cours pour toi.")
            return
        elif (N := len(actions)) > 1:
            txt = "Tu as plusieurs actions actuellement en cours :\n"
            for i in range(N):
                txt += f" {tools.emoji_chiffre(i+1)} - {actions[i].action}\n"
            message = await ctx.send(txt + "\nPour laquelle veux-tu agir ?")
            i = await tools.wait_for_react_clic(
                self.bot, message, {tools.emoji_chiffre(i+1):i for i in range(N)}, process_text=True, 
                text_filter=lambda s:s.isdigit() and 1 <= int(s) <= N, post_converter=lambda s:int(s) - 1)
            action = actions[i]
        else:
            action = actions[0]

        # Choix de la décision : très simple pour l'instant, car pas de résolution auto
        if not decision:                   # Si décision pas précisée à l'appel de la commande
            await ctx.send(f"Que veux-tu faire pour l'action {action.action} ? (action actuelle : {action._decision})")
            message = await self.bot.wait_for('message', check=trigCheck)
            decision = message.content
            
        # Avertissement si action a conséquence instantanée (barbier...)
        if action.instant:
            message = await ctx.send("Attention : cette action a une conséquence instantanée ! "
                                     "Si tu valides, tu ne pourras pas revenir en arrière.\n"
                                     "Ça part ?")
            if not await tools.yes_no(self.bot, message):
                await ctx.send("Mission aborted.")
                return
                
        async with ctx.typing():
            bdd_tools.modif(action, "_decision", decision)       # Modification en base
            
            sheet = gsheets.connect(ACTIONS_SHEET_ID).sheet1                   # Écriture dans sheet Données brutes
            sheet.append_row([datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), joueur.nom, joueur.role, joueur.camp, 
                              "\n+\n".join([f"{action.action} : {action._decision}" for action in actions])],
                             value_input_option="USER_ENTERED")
                             
            await ctx.send(f"Action « {action._decision} » bien prise en compte pour {action.action}.")
            
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
