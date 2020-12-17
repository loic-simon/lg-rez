"""lg-rez / features / Gestion des actions

Liste, création, suppression, ouverture, fermeture d'actions

"""

import datetime

from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_

from lgrez.blocs import tools, bdd, bdd_tools
from lgrez.blocs.bdd import Actions, BaseActions, Joueurs, Taches
from lgrez.features import taches


async def get_actions(quoi, trigger, heure=None):
    """Renvoie la liste des actions répondant à un déclencheur donné

    Args:
        quoi (:class:`str`): Type d'opération en cours :

            - ``"open"`` :     ouverture : ``Actions.decision_`` doit être None
            - ``"close"`` :    fermeture : ``Actions.decision_`` ne doit pas être None
            - ``"remind"`` :   rappel : ``Actions.decision_`` doit être "rien"

        trigger (:class:`str`): valeur de ``Actions.trigger_debut/fin`` à détecter
        heure (:class:`datetime.time`): si ``trigger == "temporel"``, ajoute la condition ``Actions.heure_debut/fin == heure``
    """
    if trigger == "temporel":
        if not heure:
            raise ValueError("Merci de préciser une heure......\n https://tenor.com/view/mr-bean-checking-time-waiting-gif-11570520")

        if quoi == "open":
            criteres = and_(Actions.trigger_debut == trigger, Actions.heure_debut == heure,
                            Actions.decision_ == None)      # Objets spéciaux SQLAlchemy : LAISSER le == !
        elif quoi == "close":
            criteres = and_(Actions.trigger_fin == trigger, Actions.heure_fin == heure,
                            Actions.decision_ != None)      # Objets spéciaux SQLAlchemy : LAISSER le == !
        elif quoi == "remind":
            criteres = and_(Actions.trigger_fin == trigger, Actions.heure_fin == heure,
                            Actions.decision_ == "rien")
    else:
        if quoi == "open":
            criteres = and_(Actions.trigger_debut == trigger, Actions.decision_ == None)
        elif quoi == "close":
            criteres = and_(Actions.trigger_fin == trigger, Actions.decision_ != None)
        elif quoi == "remind":
            criteres = and_(Actions.trigger_fin == trigger, Actions.decision_ == "rien")

    return Actions.query.filter(criteres).all()


async def open_action(ctx, action, chan=None):
    """Ouvre une action

    Args:
        ctx (:class:`~discord.ext.commands.Context`): contexte quelconque (de ``!open``, ``!sync``)
        action (:class:`.bdd.Actions`): action à ouvrir
        chan (:class:`~discord.TextChannel`): salon ou informer le joueur concerné, par défaut son chan privé

    Opérations réalisées :
        - Vérification des conditions (cooldown, charges...) et reprogrammation si nécessaire ;
        - Gestion des tâches planifiées (planifie remind/close si applicable) ;
        - Information joueur dans ``chan``.
    """
    joueur = Joueurs.query.get(action.player_id)
    assert joueur, f"!open_action : joueur de {action} introuvable"

    if not chan:        # chan non défini ==> chan perso du joueur
        chan = ctx.guild.get_channel(joueur.chan_id_)
        assert chan, f"!open_action : chan privé de {joueur} introuvable"

    # Vérification cooldown
    if action.cooldown > 0:                 # Action en cooldown
        bdd_tools.modif(action, "cooldown", action.cooldown - 1)
        bdd.session.commit()
        await ctx.send(f"Action {action} : en cooldown, exit (reprogrammation si temporel).")
        if action.trigger_debut == "temporel":      # Programmation action du lendemain
            ts = tools.next_occurence(action.heure_debut)
            taches.add_task(ctx.bot, ts, f"!open {action.id}", action=action.id)
        return

    # Vérification role_actif
    if not joueur.role_actif:    # role_actif == False : on reprogramme la tâche au lendemain, tanpis
        await ctx.send(f"Action {action} : role_actif == False, exit (reprogrammation si temporel).")
        if action.trigger_debut == "temporel":
            ts = tools.next_occurence(action.heure_debut)
            taches.add_task(ctx.bot, ts, f"!open {action.id}", action=action.id)
        return

    # Vérification charges
    if action.charges == 0:                 # Plus de charges, mais action maintenue en base car refill / ...
        await ctx.send(f"Action {action} : plus de charges, exit (reprogrammation si temporel).")
        return

    # Action "automatiques" (passives : notaire...) : lance la procédure de clôture / résolution
    if action.trigger_fin == "auto":
        if action.trigger_debut == "temporel":
            await ctx.send(f"Action {action.action} pour {Joueurs.query.get(action.player_id).nom} pas vraiment automatique, {tools.mention_MJ(ctx)} VENEZ M'AIDER JE PANIQUE 😱 (comme je suis vraiment sympa je vous file son chan, {tools.private_chan(ctx.guild.get_member(Joueurs.query.get(action.player_id).discord_id)).mention})")
        else:
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

    # Programmation remind / close
    if action.trigger_fin in ["temporel", "delta"]:
        taches.add_task(ctx.bot, ts - datetime.timedelta(minutes=30), f"!remind {action.id}", action=action.id)
        taches.add_task(ctx.bot, ts, f"!close {action.id}", action=action.id)
    elif action.trigger_fin == "perma":       # Action permanente : fermer pour le WE ou rappel / réinitialisation chaque jour
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
        bdd_tools.modif(action, "decision_", "rien")
        message = await chan.send(
            f"""{tools.montre()}  Tu peux maintenant utiliser ton action {tools.code(action.action)} !  {tools.emoji(ctx, "action")} \n"""
            + (f"""Tu as jusqu'à {heure_fin} pour le faire. \n""" if heure_fin else "")
            + tools.ital(f"""Tape {tools.code('!action (ce que tu veux faire)')} ou utilise la réaction pour agir."""))

    await message.add_reaction(tools.emoji(ctx, "action"))

    bdd.session.commit()



async def close_action(ctx, action, chan=None):
    """Ferme une action

    Args:
        ctx (:class:`discord.ext.commands.Context`): contexte quelconque, (de ``!open``, ``!sync``)...
        action (:class:`.bdd.Actions`): action à clôturer
        chan (:class:`discord.TextChannel`): salon ou informer le joueur concerné, par défaut son chan privé

    Opérations réalisées :
        - Suppression si nécessaire ;
        - Gestion des tâches planifiées (planifie prochaine ouverture si applicable) ;
        - Information joueur dans <chan>.
    """
    joueur = Joueurs.query.get(action.player_id)
    assert joueur, f"!open_action : joueur de {action} introuvable"

    if not chan:        # chan non défini ==> chan perso du joueur
        chan = ctx.guild.get_channel(joueur.chan_id_)
        assert chan, f"!open_action : chan privé de {joueur} introuvable"

    deleted = False
    if action.decision_ != "rien" and not action.instant:
        # Résolution de l'action (pour l'instant juste charge -= 1 et suppression le cas échéant)
        if action.charges:
            bdd_tools.modif(action, "charges", action.charges - 1)
            pcs = " pour cette semaine" if "weekends" in action.refill else ""
            await chan.send(f"Il te reste {action.charges} charge(s){pcs}.")

            if action.charges == 0 and not action.refill:
                bdd.session.delete(action)
                deleted = True

    if not deleted:
        bdd_tools.modif(action, "decision_", None)

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

    bdd.session.commit()


def add_action(ctx, action):
    """Enregistre et programme l'ouverture d'une action

    Args:
        ctx (:class:`~discord.ext.commands.Context`): contexte quelconque (de ``!open``, ``!sync``...)
        action (:class:`.bdd.Actions`): action à enregistrer
    """
    bdd.session.add(action)
    bdd.session.commit()
    # Ajout tâche ouverture
    if action.trigger_debut == "temporel":          # Temporel : on programme
        taches.add_task(ctx.bot, tools.next_occurence(action.heure_debut), f"!open {action.id}", action=action.id)
    if action.trigger_debut == "perma":             # Perma : ON LANCE DIRECT
        taches.add_task(ctx.bot, datetime.datetime.now(), f"!open {action.id}", action=action.id)


def delete_action(ctx, action):
    """Supprime une action et annule les tâches en cours liées

    Args:
        ctx (:class:`~discord.ext.commands.Context`): contexte quelconque (de ``!open``, ``!sync``...)
        action (:class:`.bdd.Actions`): action à supprimer
    """
    bdd.session.delete(action)
    bdd.session.commit()
    # Suppression tâches liées à l'action
    for tache in Taches.query.filter_by(action=action.id).all():
        taches.cancel_task(ctx.bot, tache)
