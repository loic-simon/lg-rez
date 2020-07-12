import datetime

from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_

from bdd_connect import db, Actions, BaseActions
import tools
from blocs import bdd_tools
from features import taches


async def get_actions(quoi, trigger, heure=None):
    # Renvoie la liste des actions déclenchées par trigger, dans le cas ou c'est temporel, les actions possibles à heure (objet de type time)

    if trigger == "temporel":
        if not heure:
            raise ValueError("Merci de préciser une heure......\n https://tenor.com/view/mr-bean-checking-time-waiting-gif-11570520")

        if quoi == "open":
            criteres = and_(Actions.trigger_debut == trigger, Actions.heure_debut == heure,
                            Action._decision == None)       # Obhects spéciaux SQLAlchemy : LAISSER le == !
        elif quoi == "close":
            criteres = and_(Actions.trigger_fin == trigger, Actions.heure_fin == heure,
                            Actions._decision != None)      # Obhects spéciaux SQLAlchemy : LAISSER le == !
        elif quoi == "remind":
            criteres = and_(Actions.trigger_fin == trigger, Actions.heure_fin == heure,
                            Actions._decision == "rien")
    else:
        if quoi == "open":
            criteres = and_(Actions.trigger_debut == trigger, Actions._decision == None)
        elif quoi == "close":
            criteres = and_(Actions.trigger_fin == trigger, Actions._decision != None)
        elif quoi == "remind":
            criteres = and_(Actions.trigger_fin == trigger, Actions._decision == "rien")

    return Actions.query.filter(criteres).all()


async def open_action(ctx, action, chan):
    if action.cooldown > 0:                 # Action en cooldown
        bdd_tools.modif(act, "cooldown", act.cooldown - 1)
        db.session.commit()
        if action.trigger_debut == "temporel":      # Programmation action du lendemain
            ts = tools.next_occurence(action.heure_debut)
            taches.add_task(ctx.bot, ts, f"!open {action.id}")
        return

    if not Joueurs.get(action.player_id).role_actif:    # role_actif == False : on reprogramme la tâche au lendemain, tanpis
        if action.trigger_debut == "temporel":
            ts = tools.next_occurence(action.heure_debut)
            taches.add_task(ctx.bot, ts, f"!open {action.id}")
        return

    if action.charges == 0:                 # Plus de charges, mais action maintenue en base car refill / ...
        return

    if action.trigger_fin == "auto":        # Action "automatiques" (passives : notaire...) : lance la procédure de clôture / résolution
        await close_action(ctx, action, chan)
        return

    # Tous tests préliminaires n'ont pas return ==> Vraie action à lancer
    heure_fin = None
    if action.trigger_fin == "temporel":
        heure_fin = action.heure_fin
        ts = tools.next_occurence(heure_fin)
    if action.trigger_fin == "delta":           # Si delta, on calcule la vraie heure de fin (pas modifié en base)
        delta = action.heure_fin
        ts = datetime.datetime.now() + datetime.timedelta(hours=delta.hour, minutes=delta.minute, seconds=delta.second)
        heure_fin = ts.time()

    bdd_tools.modif(action, "_decision", "rien")
    message = await chan.send(
        f"""{tools.montre()}  Tu peux maintenant utiliser ton action {action.action} !  {tools.emoji(ctx, "foudra")} \n"""
        + (f"""Tu as jusqu'à {heure_fin} pour le faire. \n""" if heure_fin else "")
        + tools.ital(f"""Tape {tools.code('!action <phrase>')} ou utilise la réaction pour voter."""))
    await message.add_reaction(tools.emoji(ctx, "foudra"))

    if action.trigger_fin in ["temporel", "delta"]:        # Programmation remind / close
        taches.add_task(ctx.bot, ts - datetime.timedelta(minutes=10), f"!remind {action.id}")
        taches.add_task(ctx.bot, ts, f"!close {action.id}")

    db.session.commit()


async def close_action(ctx, action, chan):
    deleted = False
    if action._decision != "rien" and not action.instant:
        # Résolution de l'action (pour l'instant juste charge -= 1 et suppression le cas échéant)
        if action.charges:
            bdd_tools.modif(action, "charges", action.charges - 1)
            pcs = " pour cette semaine" if "weekends" in action.refill else ""
            await chan.send(f"Il te reste {action.charges} charge(s){pcs}.")
            if action.charges == 0 and not action.refill:
                db.session.delete(action)
                deleted = True

    if not deleted:
        bdd_tools.modif(action, "_decision", None)

        ba = BaseActions.query.get(action.action)       # Si l'action a un cooldown, on le met
        if ba and ba.base_cooldown > 0:
            bdd_tools.modif(action, "cooldown", ba.base_cooldown)

        if action.trigger_debut == "temporel":          # Programmation action du lendemain
            ts = tools.next_occurence(action.heure_debut)
            taches.add_task(ctx.bot, ts, f"!open {action.id}")

    db.session.commit()
