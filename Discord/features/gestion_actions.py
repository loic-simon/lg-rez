import datetime

from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_

from bdd_connect import db, Actions, BaseActions, Joueurs, Taches
import tools
from blocs import bdd_tools
from features import taches


async def get_actions(quoi, trigger, heure=None):
    """Renvoie la liste des actions répondant à un déclencheur donné

    <quoi>      Type d'opération en cours :
        "open"      Ouverture : Actions._decision doit être None
        "close"     Fermeture : Actions._decision ne doit pas être None
        "remind"    Rappel : Actions._decision doit être "rien"

    <trigger>   valeur de Actions.trigger_debut/fin à détecter
    [heure]     Si <trigger> = "temporel", ajoute la condition Actions.heure_debut/fin == <heure> (objet datetime.time)
    """
    if trigger == "temporel":
        if not heure:
            raise ValueError("Merci de préciser une heure......\n https://tenor.com/view/mr-bean-checking-time-waiting-gif-11570520")

        if quoi == "open":
            criteres = and_(Actions.trigger_debut == trigger, Actions.heure_debut == heure,
                            Actions._decision == None)       # Obhects spéciaux SQLAlchemy : LAISSER le == !
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


async def open_action(ctx, action, chan=None):
    """Ouvre l'action <action>

    Opérations réalisées :
        - Vérification des conditions (cooldown, charges...) et reprogrammation si nécessaire ;
        - Gestion des tâches planifiées (planifie remind/close si applicable) ;
        - Information joueur dans <chan>.

    <ctx> contexte où on log, i.e. contexte de !open, !sync...
    """
    joueur = Joueurs.query.get(action.player_id)
    assert joueur, f"!open_action : joueur de {action} introuvable"

    if not chan:        # chan non défini ==> chan perso du joueur
        chan = ctx.guild.get_channel(joueur._chan_id)
        assert chan, f"!open_action : chan privé de {joueur} introuvable"

    # Vérification cooldown
    if action.cooldown > 0:                 # Action en cooldown
        bdd_tools.modif(action, "cooldown", action.cooldown - 1)
        db.session.commit()
        await ctx.send(f"Action en cooldown, exit (reprogrammation si temporel).")
        if action.trigger_debut == "temporel":      # Programmation action du lendemain
            ts = tools.next_occurence(action.heure_debut)
            taches.add_task(ctx.bot, ts, f"!open {action.id}", action=action.id)
        return

    # Vérification role_actif
    if not joueur.role_actif:    # role_actif == False : on reprogramme la tâche au lendemain, tanpis
        await ctx.send(f"role_actif == False, exit (reprogrammation si temporel).")
        if action.trigger_debut == "temporel":
            ts = tools.next_occurence(action.heure_debut)
            taches.add_task(ctx.bot, ts, f"!open {action.id}", action=action.id)
        return

    # Vérification charges
    if action.charges == 0:                 # Plus de charges, mais action maintenue en base car refill / ...
        await ctx.send(f"Plus de charges, exit (reprogrammation si temporel).")
        return

    # Action "automatiques" (passives : notaire...) : lance la procédure de clôture / résolution
    if action.trigger_fin == "auto":
        await ctx.send(f"Action automatique, appel processus de clôture")
        await close_action(ctx, action, chan)
        return

    # Tous tests préliminaires n'ont pas return ==> Vraie action à lancer

    # Calcul heure de fin (si applicable)
    heure_fin = None
    if action.trigger_fin == "temporel":
        heure_fin = action.heure_fin
        ts = tools.next_occurence(heure_fin)
    elif action.trigger_fin == "delta":         # Si delta, on calcule la vraie heure de fin (pas modifié en base)
        delta = action.heure_fin
        ts = datetime.datetime.now() + datetime.timedelta(hours=delta.hour, minutes=delta.minute, seconds=delta.second)
        heure_fin = ts.time()

    # Information du joueur
    bdd_tools.modif(action, "_decision", "rien")
    message = await chan.send(
        f"""{tools.montre()}  Tu peux maintenant utiliser ton action {tools.code(action.action)} !  {tools.emoji(ctx, "action")} \n"""
        + (f"""Tu as jusqu'à {heure_fin} pour le faire. \n""" if heure_fin else "")
        + tools.ital(f"""Tape {tools.code('!action <phrase>')} ou utilise la réaction pour agir."""))
    await message.add_reaction(tools.emoji(ctx, "action"))

    # Programmation remind / close
    if action.trigger_fin in ["temporel", "delta"]:
        taches.add_task(ctx.bot, ts - datetime.timedelta(minutes=10), f"!remind {action.id}", action=action.id)
        taches.add_task(ctx.bot, ts, f"!close {action.id}", action=action.id)
    elif action.trigger_fin == "perma":       # Action permanente : fermer pour le WE
        ts = tools.debut_pause()
        taches.add_task(ctx.bot, ts, f"!close {action.id}", action=action.id)

    db.session.commit()


async def close_action(ctx, action, chan=None):
    """Ferme l'action <action>

    Opérations réalisées :
        - Suppression si nécessaire ;
        - Gestion des tâches planifiées (planifie prochaine ouverture si applicable) ;
        - Information joueur dans <chan>.

    <ctx> contexte où on log, i.e. contexte de !open, !sync...
        """
    joueur = Joueurs.query.get(action.player_id)
    assert joueur, f"!open_action : joueur de {action} introuvable"

    if not chan:        # chan non défini ==> chan perso du joueur
        chan = ctx.guild.get_channel(joueur._chan_id)
        assert chan, f"!open_action : chan privé de {joueur} introuvable"

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

        # Si l'action a un cooldown, on le met
        ba = BaseActions.query.get(action.action)
        if ba and ba.base_cooldown > 0:
            bdd_tools.modif(action, "cooldown", ba.base_cooldown)

        # Programmation prochaine ouverture
        if action.trigger_debut == "temporel":
            ts = tools.next_occurence(action.heure_debut)
            taches.add_task(ctx.bot, ts, f"!open {action.id}", action=action.id)
        elif action.trigger_debut == "perma":           # Action permanente : ouvrir après le WE
            ts = tools.fin_pause()
            taches.add_task(ctx.bot, ts, f"!open {action.id}", action=action.id)

    db.session.commit()


def add_action(ctx, action):
    """Ajoute et programme l'ouverture d'<action>"""
    db.session.add(action)
    db.session.commit()
    # Ajout tâche ouverture
    if action.trigger_debut == "temporel":          # Temporel : on programme
        taches.add_task(ctx.bot, tools.next_occurence(action.heure_debut), f"!open {action.id}", action=action.id)
    if action.trigger_debut == "perma":             # Perma : ON LANCE DIRECT
        taches.add_task(ctx.bot, datetime.datetime.now(), f"!open {action.id}", action=action.id)


def delete_action(ctx, action):
    """Supprime <action> de la bdd Actions"""
    db.session.delete(action)
    db.session.commit()
    # Suppression tâches liées à l'action
    tachesz = Taches.query.filter_by(action=action.id).all() ##tachesz pour pas faire doublon avec taches.py
    for tache in tachesz:
        taches.cancel_task(ctx.bot, tache)
