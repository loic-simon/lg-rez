from discord.ext import commands
import tools
from bdd_connect import db, Joueurs, Actions, Roles, BaseActions

async def getActions(heure_debut): #Renvoie les numéros d'entrée des actions dont l'horaire de départ est heure_debut
    actions = [i.action for i in BaseActions.query.filter_by(trigger_debut = heure_debut).all()]
    #entries = [i.entry_num for i in Actions.query.filter_by(action in actions).all()] #Clés primaires des actions qui commencent à heure_debut

    return [i.discord_id for i in Actions.query.filter_by(action in actions).all()] #!!!Temporaire, pour ne pas push un truc qui manifestement ne marche pas!!!
