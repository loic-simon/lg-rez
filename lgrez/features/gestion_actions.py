"""lg-rez / features / Gestion des actions

Liste, création, suppression, ouverture, fermeture d'actions

"""

import datetime

from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_

from lgrez import config
from lgrez.blocs import tools, bdd
from lgrez.blocs.bdd import Action, BaseAction, Joueur, Tache, ActionTrigger
from lgrez.features import taches


async def get_actions(quoi, trigger, heure=None):
    """Renvoie la liste des actions répondant à un déclencheur donné

    Args:
        quoi (:class:`str`): Type d'opération en cours :

            - ``"open"`` :     ouverture : ``Action.decision_`` doit être None
            - ``"close"`` :    fermeture : ``Action.decision_`` ne doit pas être None
            - ``"remind"`` :   rappel : ``Action.decision_`` doit être "rien"

        trigger (:class:`bdd.ActionTrigger`): valeur de ``Action.trigger_debut/fin`` à détecter
        heure (:class:`datetime.time`): si ``trigger == "temporel"``, ajoute la condition ``Action.heure_debut/fin == heure``
    """
    if trigger == "temporel":
        if not heure:
            raise ValueError("Merci de préciser une heure......\n https://tenor.com/view/mr-bean-checking-time-waiting-gif-11570520")

        if quoi == "open":
            criteres = and_(Action.trigger_debut == trigger, Action.heure_debut == heure,
                            Action.decision_ == None)      # Objets spéciaux SQLAlchemy : LAISSER le == !
        elif quoi == "close":
            criteres = and_(Action.trigger_fin == trigger, Action.heure_fin == heure,
                            Action.decision_ != None)      # Objets spéciaux SQLAlchemy : LAISSER le == !
        elif quoi == "remind":
            criteres = and_(Action.trigger_fin == trigger, Action.heure_fin == heure,
                            Action.decision_ == "rien")
    else:
        if quoi == "open":
            criteres = and_(Action.trigger_debut == trigger, Action.decision_ == None)
        elif quoi == "close":
            criteres = and_(Action.trigger_fin == trigger, Action.decision_ != None)
        elif quoi == "remind":
            criteres = and_(Action.trigger_fin == trigger, Action.decision_ == "rien")

    return Action.query.filter(criteres).all()


async def open_action(ctx, action, chan=None):
    """Ouvre une action

    Args:
        ctx (:class:`~discord.ext.commands.Context`): contexte quelconque (de ``!open``, ``!sync``)
        action (:class:`.bdd.Action`): action à ouvrir
        chan (:class:`~discord.TextChannel`): salon ou informer le joueur concerné, par défaut son chan privé

    Opérations réalisées :
        - Vérification des conditions (cooldown, charges...) et reprogrammation si nécessaire ;
        - Gestion des tâches planifiées (planifie remind/close si applicable) ;
        - Information joueur dans ``chan``.
    """
    joueur = action.joueur

    if not chan:        # chan non défini ==> chan perso du joueur
        chan = joueur.private_chan

    # Vérification cooldown
    if action.cooldown > 0:                 # Action en cooldown
        action.cooldown = action.cooldown - 1
        config.session.commit()
        await ctx.send(f"Action {action} : en cooldown, exit (reprogrammation si temporel).")
        if action.trigger_debut == ActionTrigger.temporel:      # Programmation action du lendemain
            ts = tools.next_occurence(action.heure_debut)
            taches.add_task(ctx.bot, ts, f"!open {action.id}", action=action.id)
        return

    # Vérification role_actif
    if not joueur.role_actif:    # role_actif == False : on reprogramme la tâche au lendemain, tanpis
        await ctx.send(f"Action {action} : role_actif == False, exit (reprogrammation si temporel).")
        if action.trigger_debut == ActionTrigger.temporel:
            ts = tools.next_occurence(action.heure_debut)
            taches.add_task(ctx.bot, ts, f"!open {action.id}", action=action.id)
        return

    # Vérification charges
    if action.charges == 0:                 # Plus de charges, mais action maintenue en base car refill / ...
        await ctx.send(f"Action {action} : plus de charges, exit (reprogrammation si temporel).")
        return

    # Action "automatiques" (passives : notaire...) : lance la procédure de clôture / résolution
    if action.trigger_fin == ActionTrigger.auto:
        if action.trigger_debut == ActionTrigger.temporel:
            await ctx.send(f"Action {action.action} pour {joueur.nom} pas vraiment automatique, {tools.mention_MJ(ctx)} VENEZ M'AIDER JE PANIQUE 😱 (comme je suis vraiment sympa je vous file son chan, {joueur.private_chan.mention})")
        else:
            await ctx.send(f"Action automatique, appel processus de clôture")

        await close_action(ctx, action, chan)
        return

    # Tous tests préliminaires n'ont pas return ==> Vraie action à lancer

    # Calcul heure de fin (si applicable)
    heure_fin = None
    if action.trigger_fin == ActionTrigger.temporel:
        heure_fin = action.heure_fin
        ts = tools.next_occurence(heure_fin)
    elif action.trigger_fin == ActionTrigger.delta:     # Si delta, on calcule la vraie heure de fin (pas modifié en base)
        delta = action.heure_fin
        ts = datetime.datetime.now() + datetime.timedelta(hours=delta.hour, minutes=delta.minute, seconds=delta.second)
        heure_fin = ts.time()

    # Programmation remind / close
    if action.trigger_fin in [ActionTrigger.temporel, ActionTrigger.delta]:
        taches.add_task(ctx.bot, ts - datetime.timedelta(minutes=30), f"!remind {action.id}", action=action.id)
        taches.add_task(ctx.bot, ts, f"!close {action.id}", action=action.id)
    elif action.trigger_fin == ActionTrigger.perma:     # Action permanente : fermer pour le WE ou rappel / réinitialisation chaque jour
        ts_matin = tools.next_occurence(datetime.time(hour=7))
        ts_pause = tools.debut_pause()
        if ts_matin < ts_pause:
            taches.add_task(ctx.bot, ts_matin, f"!open {action.id}", action=action.id)      # Réopen le lendamain
        else:
            taches.add_task(ctx.bot, ts_pause, f"!close {action.id}", action=action.id)     # Sauf si pause d'ici là

    # Information du joueur
    if action.decision_ == "rien":      # déjà ouverte
        message = await chan.send(
            f"""{tools.montre()}  Rappel : tu peux utiliser quand tu le souhaites ton action {tools.code(action.action)} !  {tools.emoji(ctx, "action")} \n"""
            + (f"""Tu as jusqu'à {heure_fin} pour le faire. \n""" if heure_fin else "")
            + tools.ital(f"""Tape {tools.code('!action (ce que tu veux faire)')} ou utilise la réaction pour agir."""))
    else:
        action.decision_ = "rien"
        message = await chan.send(
            f"""{tools.montre()}  Tu peux maintenant utiliser ton action {tools.code(action.action)} !  {tools.emoji(ctx, "action")} \n"""
            + (f"""Tu as jusqu'à {heure_fin} pour le faire. \n""" if heure_fin else "")
            + tools.ital(f"""Tape {tools.code('!action (ce que tu veux faire)')} ou utilise la réaction pour agir."""))

    await message.add_reaction(tools.emoji(ctx, "action"))

    config.session.commit()



async def close_action(ctx, action, chan=None):
    """Ferme une action

    Args:
        ctx (:class:`discord.ext.commands.Context`): contexte quelconque, (de ``!open``, ``!sync``)...
        action (:class:`.bdd.Action`): action à clôturer
        chan (:class:`discord.TextChannel`): salon ou informer le joueur concerné, par défaut son chan privé

    Opérations réalisées :
        - Suppression si nécessaire ;
        - Gestion des tâches planifiées (planifie prochaine ouverture si applicable) ;
        - Information joueur dans <chan>.
    """
    joueur = action.joueur

    if not chan:        # chan non défini ==> chan perso du joueur
        chan = joueur.private_chan

    deleted = False
    if action.decision_ != "rien" and not action.instant:
        # Résolution de l'action (pour l'instant juste charge -= 1 et suppression le cas échéant)
        if action.charges:
            action.charges = action.charges - 1
            pcs = " pour cette semaine" if "weekends" in action.refill else ""
            await chan.send(f"Il te reste {action.charges} charge(s){pcs}.")

            if action.charges == 0 and not action.refill:
                config.session.delete(action)
                deleted = True

    if not deleted:
        action.decision_ = None

        # Si l'action a un cooldown, on le met
        ba = action.base
        if ba and ba.base_cooldown > 0:
            action.cooldown = ba.base_cooldown

        # Programmation prochaine ouverture
        if action.trigger_debut == ActionTrigger.temporel:
            ts = tools.next_occurence(action.heure_debut)
            taches.add_task(ctx.bot, ts, f"!open {action.id}", action=action.id)
        elif action.trigger_debut == ActionTrigger.perma:       # Action permanente : ouvrir après le WE
            ts = tools.fin_pause()
            taches.add_task(ctx.bot, ts, f"!open {action.id}", action=action.id)

    config.session.commit()


def add_action(ctx, action):
    """Enregistre et programme l'ouverture d'une action

    Args:
        ctx (:class:`~discord.ext.commands.Context`): contexte quelconque (de ``!open``, ``!sync``...)
        action (:class:`.bdd.Action`): action à enregistrer
    """
    config.session.add(action)
    config.session.commit()
    # Ajout tâche ouverture
    if action.trigger_debut == ActionTrigger.temporel:          # Temporel : on programme
        taches.add_task(ctx.bot, tools.next_occurence(action.heure_debut), f"!open {action.id}", action=action.id)
    if action.trigger_debut == ActionTrigger.perma:             # Perma : ON LANCE DIRECT
        taches.add_task(ctx.bot, datetime.datetime.now(), f"!open {action.id}", action=action.id)


def delete_action(ctx, action):
    """Supprime une action et annule les tâches en cours liées

    Args:
        ctx (:class:`~discord.ext.commands.Context`): contexte quelconque (de ``!open``, ``!sync``...)
        action (:class:`.bdd.Action`): action à supprimer
    """
    # Suppression tâches liées à l'action
    for tache in action.taches:
        taches.cancel_task(ctx.bot, tache)

    config.session.delete(action)
    config.session.commit()
