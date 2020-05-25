from discord.ext import commands
import tools
from bdd_connect import db, Actions, BaseActions
import datetime
from datetime import time

from sqlalchemy.orm.attributes import flag_modified     # Permet de "signaler" les entrées modifiées, à commit en base

async def get_actions(quoi, trigger, heure=None):
    """
    Renvoie la liste des actions déclenchées par trigger, dans le cas ou c'est temporel, les actions possibles à heure_debut (objet de type time)
    """
    
    if trigger == "temporel":
        if not heure:
            raise ValueError("Merci de préciser une heure......\n Connard.")
            
        if quoi == "open":
            criteres = {"trigger_debut": trigger, "heure_debut": heure}
        else:
            criteres = {"trigger_fin": trigger, "heure_fin": heure}
    else:
        if quoi == "open":
            criteres = {"trigger_debut": trigger}
        else:
            criteres = {"trigger_fin": trigger}


    all_actions = BaseActions.query.filter_by(**criteres).all()

    if not all_actions:
        return []
    else:
        actions = [action.action for action in all_actions]
        act_dispo = Actions.query.filter(Actions.action.in_(actions)).filter_by(cooldown=0).all()
        act_decrement = Actions.query.filter(Actions.action.in_(actions)).filter(Actions.cooldown > 0).all()

        if act_decrement:
            for act in act_decrement:
                act.cooldown -= 1
                flag_modified(act, "cooldown")

            db.session.commit()

        return(act_dispo)
