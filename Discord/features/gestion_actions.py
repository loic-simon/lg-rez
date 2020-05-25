from discord.ext import commands
import tools
from bdd_connect import db, Tables
import datetime
from datetime import time

from sqlalchemy.orm.attributes import flag_modified     # Permet de "signaler" les entrées modifiées, à commit en base

async def get_actions(trigger, heure_debut=None):
    """
    Renvoie la liste des actions déclenchées par trigger, dans le cas ou c'est temporel, les actions possibles à heure_debut (objet de type time)
    """

    if trigger == "temporel":
        if not heure_debut:
            raise ValueError("Merci de préciser une heure......\n Connard.")
        all_actions = Tables["BaseActions"].query.filter_by(heure_debut=heure_debut).all()

    else:
        all_actions = Tables["BaseActions"].query.filter_by(trigger_debut=trigger).all()

    if not all_actions:
        return []
    else:
        actions = [action.action for action in all_actions]
        act_dispo = Tables["Actions"].query.filter(Tables["BaseActions"].action.in_(actions)).filter_by(cooldown=0).all()
        act_decrement = Tables["Actions"].query.filter(Tables["BaseActions"].action.in_(actions)).filter(cooldown > 0).all()

        for act in act_decrement:
            act.cooldown -= 1
            flag_modified(act, "cooldown")

        db.commit()
        return(act_dispo)
