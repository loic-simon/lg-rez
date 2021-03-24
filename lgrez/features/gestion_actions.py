"""lg-rez / features / Gestion des actions

Liste, création, suppression, ouverture, fermeture d'actions

"""

import datetime

from discord.ext import commands

from lgrez import config
from lgrez.blocs import tools
from lgrez.bdd import Action, BaseAction, Tache, ActionTrigger


def add_action(action):
    """Enregistre une action et programme son ouverture le cas échéant.

    Args:
        action (.bdd.Action): l'action à enregistrer
    """
    action.add()

    # Ajout tâche ouverture
    if action.base.trigger_debut == ActionTrigger.temporel:
        # Temporel : on programme
        Tache(timestamp=tools.next_occurence(action.base.heure_debut),
              commande=f"!open {action.id}",
              action=action).add()

    elif action.base.trigger_debut == ActionTrigger.perma:
        # Perma : ON LANCE DIRECT
        Tache(timestamp=datetime.datetime.now(),
              commande=f"!open {action.id}",
              action=action).add()


def delete_action(action):
    """Supprime une action et annule les tâches en cours liées.

    Args:
        action (.bdd.Action): l'action à supprimer
    """
    # Suppression tâches liées à l'action
    if action.taches:
        Tache.delete(*action.taches)
    action.delete()


async def open_action(action):
    """Ouvre l'action.

    Args:
        action (.bdd.Action): l'action à ouvir

    Opérations réalisées :
        - Vérification des conditions (cooldown, charges...) et
          reprogrammation si nécessaire ;
        - Gestion des tâches planifiées (planifie remind/close si
          applicable) ;
        - Information du joueur.
    """
    joueur = action.joueur
    chan = joueur.private_chan

    # Vérification cooldown
    if action.cooldown > 0:                 # Action en cooldown
        action.cooldown = action.cooldown - 1
        config.session.commit()
        await tools.log(
            f"Action {action} : en cooldown, exit "
            "(reprogrammation si temporel)."
        )
        if action.base.trigger_debut == ActionTrigger.temporel:
            # Programmation action du lendemain
            ts = tools.next_occurence(action.base.heure_debut)
            Tache(timestamp=ts,
                  commande=f"!open {action.id}",
                  action=action).add()
        return

    # Vérification role_actif
    if not joueur.role_actif:
        # role_actif == False : on reprogramme la tâche au lendemain tanpis
        await tools.log(
            f"Action {action} : role_actif == False, exit "
            "(reprogrammation si temporel)."
        )
        if action.base.trigger_debut == ActionTrigger.temporel:
            ts = tools.next_occurence(action.base.heure_debut)
            Tache(timestamp=ts,
                  commande=f"!open {action.id}",
                  action=action).add()
        return

    # Vérification charges
    if action.charges == 0:
        # Plus de charges, mais action maintenue en base car refill / ...
        await tools.log(
            f"Action {action} : plus de charges, exit "
            "(reprogrammation si temporel)."
        )
        return

    # Action "automatiques" (passives : notaire...) :
    # lance la procédure de clôture / résolution
    if action.base.trigger_fin == ActionTrigger.auto:
        if action.base.trigger_debut == ActionTrigger.temporel:
            await tools.log(
                f"Action {action.base.slug} pour {joueur.nom} pas vraiment "
                f"automatique, {config.Role.mj.mention} VENEZ M'AIDER "
                "JE PANIQUE 😱 (comme je suis vraiment sympa je vous "
                f"file son chan, {chan.mention})"
            )
        else:
            await tools.log(
                f"Action {action} : automatique, appel processus de clôture"
            )

        await close_action(action)
        return

    # Tous tests préliminaires n'ont pas return ==> Vraie action à lancer

    # Calcul heure de fin (si applicable)
    heure_fin = None
    if action.base.trigger_fin == ActionTrigger.temporel:
        heure_fin = action.base.heure_fin
        ts = tools.next_occurence(heure_fin)
    elif action.base.trigger_fin == ActionTrigger.delta:
        # Si delta, on calcule la vraie heure de fin (pas modifié en base)
        delta = action.base.heure_fin
        ts = (datetime.datetime.now()
              + datetime.timedelta(hours=delta.hour,
                                   minutes=delta.minute,
                                   seconds=delta.second))
        heure_fin = ts.time()

    # Programmation remind / close
    if action.base.trigger_fin in [ActionTrigger.temporel,
                                   ActionTrigger.delta]:
        Tache(timestamp=ts - datetime.timedelta(minutes=30),
              commande=f"!remind {action.id}",
              action=action).add()
        Tache(timestamp=ts,
              commande=f"!close {action.id}",
              action=action).add()
    elif action.base.trigger_fin == ActionTrigger.perma:
        # Action permanente : fermer pour le WE
        # ou rappel / réinitialisation chaque jour
        ts_matin = tools.next_occurence(datetime.time(hour=7))
        ts_pause = tools.debut_pause()
        if ts_matin < ts_pause:
            # Réopen le lendamain
            Tache(timestamp=ts_matin,
                  commande=f"!open {action.id}",
                  action=action).add()
        else:
            # Sauf si pause d'ici là
            Tache(timestamp=ts_pause,
                  commande=f"!close {action.id}",
                  action=action).add()

    # Information du joueur
    if action.decision_ == "rien":      # déjà ouverte
        message = await chan.send(
            f"{tools.montre()}  Rappel : tu peux utiliser quand tu le "
            f"souhaites ton action {tools.code(action.base.slug)} ! "
            f" {config.Emoji.action} \n"
            + (f"Tu as jusqu'à {heure_fin} pour le faire. \n"
               if heure_fin else "")
            + tools.ital(
                f"Tape {tools.code('!action (ce que tu veux faire)')}"
                " ou utilise la réaction pour agir."
            )
        )
    else:
        action.decision_ = "rien"
        message = await chan.send(
            f"{tools.montre()}  Tu peux maintenant utiliser ton action "
            f"{tools.code(action.base.slug)} !  {config.Emoji.action} \n"
            + (f"Tu as jusqu'à {heure_fin} pour le faire. \n"
               if heure_fin else "")
            + tools.ital(
                f"Tape {tools.code('!action (ce que tu veux faire)')}"
                " ou utilise la réaction pour agir."
            )
        )

    await message.add_reaction(config.Emoji.action)

    config.session.commit()


async def close_action(action):
    """Ferme l'action.

    Args:
        action (.bdd.Action): l'action à enregistrer

    Opérations réalisées :
        - Suppression si nécessaire ;
        - Gestion des tâches planifiées (planifie prochaine ouverture
          si applicable) ;
        - Information du joueur (si charge-- seulement).
    """
    joueur = action.joueur
    chan = joueur.private_chan

    deleted = False
    if action.decision_ != "rien":
        # Résolution de l'action
        # (pour l'instant juste charge -= 1 et suppression le cas échéant)
        if action.charges:
            action.charges = action.charges - 1
            pcs = (" pour cette semaine"
                   if "weekends" in action.base.refill else "")
            await chan.send(f"Il te reste {action.charges} charge(s){pcs}.")

            if action.charges == 0 and not action.base.refill:
                delete_action(action)
                deleted = True

    if not deleted:
        action.decision_ = None

        # Si l'action a un cooldown, on le met
        if action.base.base_cooldown > 0:
            action.cooldown = action.base.base_cooldown

        # Programmation prochaine ouverture
        if action.base.trigger_debut == ActionTrigger.temporel:
            ts = tools.next_occurence(action.base.heure_debut)
            Tache(timestamp=ts,
                  commande=f"!open {action.id}",
                  action=action).add()
        elif action.base.trigger_debut == ActionTrigger.perma:
            # Action permanente : ouvrir après le WE
            ts = tools.fin_pause()
            Tache(timestamp=ts,
                  commande=f"!open {action.id}",
                  action=action).add()

    config.session.commit()


def get_actions(quoi, trigger, heure=None):
    """Renvoie les actions répondant à un déclencheur donné.

    Args:
        quoi (str): Type d'opération en cours :

          - ``"open"`` : ouverture, ``Action.decision_`` doit être
            ``None``;
          - ``"close"`` :  fermeture, ``Action.decision_`` ne doit pas
            être None;
          - ``"remind"`` : rappel, ``Action.decision_`` doit être
            ``"rien"``

        trigger (bdd.ActionTrigger): valeur de ``Action.trigger_debut/fin``
            à détecter.
        heure (datetime.time): si ``trigger == "temporel"``, ajoute la
            condition ``Action.heure_debut/fin == heure``.

    Returns:
        Sequence[.bdd.Action]: La liste des actions correspondantes.
    """
    if trigger == ActionTrigger.temporel:
        if not heure:
            raise commands.UserInputError("merci de préciser une heure")

        if quoi == "open":
            criteres = (Action.base.has(BaseAction.trigger_debut == trigger)
                        & Action.base.has(BaseAction.heure_debut == heure)
                        & Action.decision_.is_(None))
        elif quoi == "close":
            criteres = (Action.base.has(BaseAction.trigger_fin == trigger)
                        & Action.base.has(BaseAction.heure_fin == heure)
                        & Action.decision_.isnot(None))
        elif quoi == "remind":
            criteres = (Action.base.has(BaseAction.trigger_fin == trigger)
                        & Action.base.has(BaseAction.heure_fin == heure)
                        & (Action.decision_ == "rien"))
        else:
            raise commands.UserInputError(f"bad value for quoi: '{quoi}'")
    else:
        if quoi == "open":
            criteres = (Action.base.has(BaseAction.trigger_debut == trigger)
                        & Action.decision_.is_(None))
        elif quoi == "close":
            criteres = (Action.base.has(BaseAction.trigger_fin == trigger)
                        & Action.decision_.isnot(None))
        elif quoi == "remind":
            criteres = (Action.base.has(BaseAction.trigger_fin == trigger)
                        & (Action.decision_ == "rien"))
        else:
            raise commands.UserInputError(f"bad value for quoi: '{quoi}'")

    return Action.query.filter(criteres).all()
