"""lg-rez / features / Gestion des votes et actions

Ouverture / fermeture / rappels des votes et actions (+ refill)

"""

import datetime

from discord.ext import commands

from lgrez import config
from lgrez.blocs import tools
from lgrez.features import gestion_actions
from lgrez.bdd import (Joueur, Action, Tache, CandidHaro,
                       CandidHaroType, ActionTrigger)


async def recup_joueurs(quoi, qui, heure=None):
    """Renvoie les joueurs concernés par la tâche !quoi <qui> [heure].

    Args:
        quoi (str): évènement, ``"open" / "close" / "remind"``.
        qui (str): cible, ``"cond" / "maire" / "loups" / "action"``.
        heure (str): si ``qui == "action"``, heure associée
            (au format ``HHhMM``).

    Returns:
        :class:`list`\[:class:`.bdd.Joueur`\]

    Examples:
        ``!open cond`` -> joueurs avec droit de vote
        ``!close action 17h`` -> joueurs dont l'action se termine à 17h
    """
    criteres = {
        "cond": {
            "open": (Joueur.votant_village.is_(True)
                     & Joueur.vote_condamne_.is_(None)),
            "close": Joueur.vote_condamne_.is_not(None),
            "remind": Joueur.vote_condamne_ == "non défini",
        },
        "maire": {
            "open": (Joueur.votant_village.is_(True)
                     & Joueur.vote_maire_.is_(None)),
            "close": Joueur.vote_maire_.is_not(None),
            "remind": Joueur.vote_maire_ == "non défini",
        },
        "loups": {
            "open": (Joueur.votant_loups.is_(True)
                     & Joueur.vote_loups_.is_(None)),
            "close": Joueur.vote_loups_.is_not(None),
            "remind": Joueur.vote_loups_ == "non défini",
        },
    }

    if qui in criteres:
        critere = criteres[qui][quoi]
        return Joueur.query.filter(critere).all()
        # Liste des joueurs répondant aux critères

    elif qui == "action":
        if heure and isinstance(heure, str):
            # Si l'heure est précisée, on convertit "HHhMM" -> datetime.time
            tps = tools.heure_to_time(heure)
        else:
            # Si l'heure n'est pas précisée, on prend l'heure actuelle
            raise ValueError(
                "[heure] doit être spécifiée lorque <qui> == \"action\""
            )

        actions = await gestion_actions.get_actions(
            quoi, ActionTrigger.temporel, tps
        )

        dic = {}
        for action in actions:
            if (joueur := action.joueur) in dic:
                dic[joueur].append(action)
            else:
                dic[joueur] = [action]

        return dic
        # Formerly :
        # {joueur.player_id:[action for action in actions if
        # action.player_id == joueur.player_id] for joueur in
        # [Joueur.query.get(action.player_id) for action in actions]}

    elif qui.isdigit() and (action := Action.query.get(int(qui))):
        # Appel direct action par son numéro
        if ((quoi == "open" and (action.trigger_debut == ActionTrigger.perma
                                 or not action.decision_))
            or (quoi == "close" and action.decision_)
            or (quoi == "remind" and action.decision_ == "rien")):
            # Action lançable
            return {action.joueur: [action]}
        else:
            return {}

    else:
        raise ValueError(f"""Argument <qui> == \"{qui}" invalide""")


class OpenClose(commands.Cog):
    """Commandes de gestion des votes et actions"""

    @commands.command()
    @tools.mjs_only
    async def open(self, ctx, qui, heure=None, heure_chain=None):
        """Lance un vote / des actions de rôle (COMMANDE BOT / MJ)

        Args:
            qui:
                ===========     ===========
                ``cond``        pour le vote du condamné
                ``maire``       pour le vote du maire
                ``loups``       pour le vote des loups
                ``action``      pour les actions commençant à ``heure``
                ``{id}``        pour une action spécifique
                ===========     ===========

            heure:
                - si ``qui == "cond"``, ``"maire"`` ou ``"loup"``,
                  programme en plus la fermeture à ``heure``
                  (et un rappel 30 minutes avant) ;
                - si ``qui == "action"``, il est obligatoire : heure des
                  actions à lancer (cf plus haut). Pour les actions, la
                  fermeture est de toute façon programmée le cas échéant
                  (``trigger_fin`` ``temporel`` ou ``delta``).

                Dans tous les cas, format ``HHh`` ou ``HHhMM``.

            heure_chain:
                permet de chaîner des votes : lance le vote immédiatement
                et programme sa fermeture à ``heure``, en appellant ``!close``
                de sorte à programmer une nouvelle ouverture le lendemain à
                ``heure_chain``, et ainsi de suite.
                Format ``HHh`` ou ``HHhMM``.

        Une sécurité empêche de lancer un vote ou une action déjà en cours.

        Cette commande a pour vocation première d'être exécutée
        automatiquement par des tâches planifiées.
        Elle peut être utilisée à la main, mais attention à ne pas
        faire n'importe quoi (penser à envoyer / planifier la fermeture
        des votes, par exemple).

        Examples:
            - ``!open maire`` :        lance un vote condamné maintenant
            - ``!open cond 19h`` :     lance un vote condamné maintenant
              et programme sa fermeture à 19h00 (ex. Juge Bègue)
            - ``!open cond 18h 10h`` : lance un vote condamné maintenant,
              programme sa fermeture à 18h00, et une prochaine ouverture
              à 10h qui se fermera à 18h, et ainsi de suite
            - ``!open action 19h`` :   lance toutes les actions
              commençant à 19h00
            - ``!open 122`` :          lance l'action d'ID 122

        """
        joueurs = await recup_joueurs("open", qui, heure)
        # Liste de joueurs (votes) ou dictionnaire joueur : action

        str_joueurs = "\n - ".join([joueur.nom for joueur in joueurs])
        await tools.send_code_blocs(
            ctx,
            f"Utilisateur(s) répondant aux critères ({len(joueurs)}) : \n"
            f" - {str_joueurs}"
        )

        for joueur in joueurs:
            chan = ctx.guild.get_channel(joueur.chan_id_)
            assert chan, f"!open : chan privé de {joueur} introuvable"

            if qui == "cond":
                joueur.vote_condamne_ = "non défini"
                message = await chan.send(
                    f"{tools.montre()}  Le vote pour le condamné du "
                    f"jour est ouvert !  {config.Emoji.bucher} \n"
                    + (f"Tu as jusqu'à {heure} pour voter. \n"
                       if heure else "")
                    + tools.ital(f"Tape {tools.code('!vote (nom du joueur)')}"
                                 " ou utilise la réaction pour voter.")
                )
                await message.add_reaction(config.Emoji.bucher)

            elif qui == "maire":
                joueur.vote_maire_ = "non défini"
                message = await chan.send(
                    f"{tools.montre()}  Le vote pour l'élection du "
                    f"maire est ouvert !  {config.Emoji.maire} \n"
                    + (f"Tu as jusqu'à {heure} pour voter. \n"
                       if heure else "")
                    + tools.ital(
                        f"Tape {tools.code('!votemaire (nom du joueur)')} "
                        "ou utilise la réaction pour voter."
                    )
                )
                await message.add_reaction(config.Emoji.maire)

            elif qui == "loups":
                joueur.vote_loups_ = "non défini"
                message = await chan.send(
                    f"{tools.montre()}  Le vote pour la victime de "
                    f"cette nuit est ouvert !  {config.Emoji.lune} \n"
                    + (f"Tu as jusqu'à {heure} pour voter. \n"
                       if heure else "")
                    + tools.ital(
                        f"Tape {tools.code('!voteloups (nom du joueur)')} "
                        "ou utilise la réaction pour voter."
                    )
                )
                await message.add_reaction(config.Emoji.lune)

            else:       # Action
                for action in joueurs[joueur]:
                    await gestion_actions.open_action(action)

        config.session.commit()

        # Actions déclenchées par ouverture
        for action in Action.query.filter_by(
                trigger_debut=ActionTrigger(f"open_{qui}")):
            await gestion_actions.open_action(action)

        # Réinitialise haros/candids
        items = []
        if qui == "cond":
            items = CandidHaro.query.filter_by(
                type=CandidHaroType.haro).all()
        elif qui == "maire":
            items = CandidHaro.query.filter_by(
                type=CandidHaroType.candidature).all()
        if items:
            CandidHaro.delete(*items)
            await tools.log(f"!open {qui} : haros/candids wiped")
            await config.Channel.haros.send(
                f"{config.Emoji.void}\n" * 30
                + "Nouveau vote, nouveaux haros !\n"
                + tools.ital(
                    "Les posts ci-dessus sont invalides pour le vote actuel. "
                    f"Utilisez {tools.code('!haro')} pour en relancer."
                )
            )

        # Programme fermeture
        if qui in ["cond", "maire", "loups"] and heure:
            ts = tools.next_occurence(tools.heure_to_time(heure))
            Tache(timestamp=ts - datetime.timedelta(minutes=30),
                  commande=f"!remind {qui}").add()
            if heure_chain:
                Tache(timestamp=ts,
                      commande=f"!close {qui} {heure_chain} {heure}").add()
                # Programmera prochaine ouverture
            else:
                Tache(timestamp=ts, commande=f"!close {qui}").add()


    @commands.command()
    @tools.mjs_only
    async def close(self, ctx, qui, heure=None, heure_chain=None):
        """Ferme un vote / des actions de rôle (COMMANDE BOT / MJ)

        Args:
            qui:
                ===========     ===========
                ``cond``        pour le vote du condamné
                ``maire``       pour le vote du maire
                ``loups``       pour le vote des loups
                ``action``      pour les actions se terminant à ``heure``
                ``{id}``        pour une action spécifique
                ===========     ===========

            heure:
                - si ``qui == "cond"``, ``"maire"`` ou ``"loup"``,
                  programme en plus une prochaine ouverture à ``heure``
                  (et un rappel 30 minutes avant) ;
                - si ``qui == "action"``, il est obligatoire : heure des
                  actions à lancer (cf plus haut). Pour les actions, la
                  prochaine est de toute façon programmée le cas échéant
                  (cooldown à 0 et reste des charges).

                Dans tous les cas, format ``HHh`` ou ``HHhMM``.

            heure_chain:
                permet de chaîner des votes : ferme le vote immédiatement
                et programme une prochaine ouverture à ``heure``, en
                appellant ``!close`` de sorte à programmer une nouvelle
                fermeture le lendemain à ``heure_chain``, et ainsi de suite.
                Format ``HHh`` ou ``HHhMM``.

        Une sécurité empêche de fermer un vote ou une action
        qui n'est pas en cours.

        Cette commande a pour vocation première d'être exécutée
        automatiquement par des tâches planifiées.
        Elle peut être utilisée à la main, mais attention à ne pas
        faire n'importe quoi (penser à envoyer / planifier la fermeture
        des votes, par exemple).

        Examples:
            - ``!close maire`` :        ferme le vote condamné maintenant
            - ``!close cond 10h`` :     ferme le vote condamné maintenant
              et programme une prochaine ouverture à 10h00
            - ``!close cond 10h 18h`` : ferme le vote condamné maintenant,
              programme une prochaine ouverture à 10h00, qui sera fermé à
              18h, puis une nouvelle ouverture à 10h, etc
            - ``!close action 22h`` :   ferme toutes les actions
              se terminant à 22h00
            - ``!close 122`` :          ferme l'action d'ID 122
        """

        joueurs = await recup_joueurs("close", qui, heure)

        str_joueurs = "\n - ".join([joueur.nom for joueur in joueurs])
        await ctx.send(tools.code_bloc(
            f"Utilisateur(s) répondant aux critères ({len(joueurs)}) : \n"
            + str_joueurs
        ))

        for joueur in joueurs:
            chan = ctx.guild.get_channel(joueur.chan_id_)
            assert chan, f"!close : chan privé de {joueur} introuvable"

            if qui == "cond":
                await chan.send(
                    f"{tools.montre()}  Fin du vote pour le condamné du jour !"
                    f"\nVote définitif : {joueur.vote_condamne_}\n"
                    f"Les résultats arrivent dans l'heure !\n"
                )
                joueur.vote_condamne_ = None

            elif qui == "maire":
                await chan.send(
                    f"{tools.montre()}  Fin du vote pour le maire ! \n"
                    f"Vote définitif : {joueur.vote_maire_}"
                )
                joueur.vote_maire_ = None

            elif qui == "loups":
                await chan.send(
                    f"{tools.montre()}  Fin du vote pour la victime du soir !"
                    f"\nVote définitif : {joueur.vote_loups_}"
                )
                joueur.vote_loups_ = None

            else:       # Action
                for action in joueurs[joueur]:
                    await chan.send(
                        f"{tools.montre()}  Fin de la possiblité d'utiliser "
                        f"ton action {tools.code(action.action)} ! \n"
                        f"Action définitive : {action.decision_}"
                    )
                    await gestion_actions.close_action(action)

        config.session.commit()

        # Actions déclenchées par fermeture
        for action in Action.query.filter_by(trigger_debut=f"close_{qui}"):
            await gestion_actions.open_action(action)

        # Programme prochaine ouverture
        if qui in ["cond", "maire", "loups"] and heure:
            ts = tools.next_occurence(tools.heure_to_time(heure))
            if heure_chain:
                Tache(timestamp=ts,
                      commande=f"!open {qui} {heure_chain} {heure}").add()
                # Programmera prochaine fermeture
            else:
                Tache(timestamp=ts, commande=f"!open {qui}").add()


    @commands.command()
    @tools.mjs_only
    async def remind(self, ctx, qui, heure=None):
        """Envoi un rappel de vote / actions de rôle (COMMANDE BOT / MJ)

        Args:
            qui:
                ===========     ===========
                ``cond``        pour le vote du condamné
                ``maire``       pour le vote du maire
                ``loups``       pour le vote des loups
                ``action``      pour les actions se terminant à ``heure``
                ``{id}``        pour une action spécifique
                ===========     ===========

            heure: ne sert que dans le cas où <qui> == "action"
                (il est alors obligatoire), contrairement à !open et
                !close.
                Format HHh ou HHhMM.

        Le bot n'envoie un message qu'aux joueurs n'ayant pas encore
        voté / agi, si le vote ou l'action est bien en cours.

        Cette commande a pour vocation première d'être exécutée
        automatiquement par des tâches planifiées.
        Elle peut être utilisée à la main, mais attention à ne pas
        faire n'importe quoi !.

        Examples:
            - ``!remind maire`` :      rappelle le vote maire maintenant
            - ``!remind action 22h`` : rappelle toutes les actions
              se terminant à 22h00
            - ``!remind 122`` :        rappelle l'action d'ID 122
        """

        joueurs = await recup_joueurs("remind", qui, heure)

        str_joueurs = "\n - ".join([joueur.nom for joueur in joueurs])
        await ctx.send(tools.code_bloc(
            f"Utilisateur(s) répondant aux critères ({len(joueurs)}) : \n"
            + str_joueurs
        ))

        for joueur in joueurs:
            chan = ctx.guild.get_channel(joueur.chan_id_)
            assert chan, f"!remind : chan privé de {joueur} introuvable"
            member = ctx.guild.get_member(joueur.discord_id)
            assert member, f"!remind : member {joueur} introuvable"

            if qui == "cond":
                message = await chan.send(
                    f"⏰ {member.mention} Plus que 30 minutes pour voter "
                    "pour le condamné du jour ! 😱 \n"
                )
                await message.add_reaction(config.Emoji.bucher)

            elif qui == "maire":
                message = await chan.send(
                    f"⏰ {member.mention} Plus que 30 minutes pour élire "
                    "le nouveau maire ! 😱 \n"
                )
                await message.add_reaction(config.Emoji.maire)

            elif qui == "loups":
                message = await chan.send(
                    f"⏰ {member.mention} Plus que 30 minutes voter "
                    "pour la victime du soir ! 😱 \n"
                )
                await message.add_reaction(config.Emoji.lune)

            else:       # Action
                for action in joueurs[joueur]:
                    message = await chan.send(
                        f"⏰ {member.mention} Plus que 30 minutes pour "
                        f"utiliser ton action {tools.code(action.base.slug)}"
                        " ! 😱 \n"
                    )
                    await message.add_reaction(config.Emoji.action)


    @commands.command()
    @tools.mjs_only
    async def refill(self, ctx, motif, *, cible=None):
        """Recharger un/des pouvoirs rechargeables (COMMANDE BOT / MJ)

        Args:
            motif: ``"weekends"``, ``"forgeron"``, ``"rebouteux"``
                ou ``"divin"`` (forcer le refill car les MJs
                tout-puissants l'ont décidé)
            cible: ``"all"`` ou le nom d'un joueur
        """
        if motif not in ["weekends", "forgeron", "rebouteux", "divin"]:
            await ctx.send(f"{motif} n'est pas un <motif> valide")
            return

        if motif == "divin":
            if cible != "all":
                target = await tools.boucle_query_joueur(
                    cible=cible, message="Qui veux-tu recharger ?"
                )
                refillable = Action.query.filter(
                    Action.charges.is_not(None)).filter_by(joueur=target).all()
            else:
                m = await ctx.send(
                    "Tu as choisi de recharger le pouvoir de "
                    "TOUS les joueurs actifs, en es-tu sûr ?"
                )
                if await tools.yes_no(m):
                    refillable = Action.query.filter(
                        Action.charges.is_not(None)).all()

                else:
                    await ctx.send("Mission aborted.")
                    return

        else:       # refill WE, forgeron ou rebouteux
            if cible != "all":
                target = await tools.boucle_query_joueur(
                    cible=cible, message="Qui veux-tu recharger ?"
                )
                refillable = Action.query.filter(
                    Action.refill.contains(motif)).filter_by(
                    joueur=target).all()
            else:
                refillable = Action.query.filter(
                    Action.refill.contains(motif)).all()

        await tools.log(refillable)

        txt = "Action(s) répondant aux critères :\n"
        for action in refillable:
            txt += f"- {action.base.slug}, id = {action.id} \n"

        await tools.send_code_blocs(ctx, txt)

        # Détermination nouveau nombre de charges
        if motif == "weekends":
            remplissage = {action: action.base.base_charges
                           for action in refillable}
        else:
            remplissage = {action: action.charges + 1
                           for action in refillable}

        # Refill proprement dit
        for action, charge in remplissage.items():
            if charge > action.charges:
                if not action.charges and action.trigger_debut == "perma":
                    # Action permanente : on ré-ouvre !
                    if motif == "weekends":
                        ts = tools.fin_pause()
                    else:
                        ts = (datetime.datetime.now()
                              + datetime.timedelta(seconds=10))
                    Tache(timestamp=ts,
                          commande=f"!open {action.id}",
                          action=action).add()

                action.charges = charge

                await tools.send_blocs(
                    action.joueur.private_chan,
                    f"Ton action {action.base.slug} vient d'être rechargée, "
                    f"tu as maintenant {charge} charge(s) disponible(s) !"
                )

        config.session.commit()


    @commands.command()
    @tools.mjs_only
    async def cparti(self, ctx):
        """Lance le jeu (COMMANDE MJ)

        - Crée (et programme) les actions associées aux rôles de
          tous les joueurs     ==> EN FAIT NON, plus besoin vu que
          c'est fait à la synchro des rôles
        - Programme les votes condamnés quotidiens (avec chaînage) 10h-18h
        - Programme un vote maire 10h-18h
        - Programme les actions au lancement du jeu (choix de mentor...)
          et permanentes (forgeron)... à 19h

        À utiliser le jour du lancement après 10h (lance les premières
        actions le soir et les votes le lendemain)
        """

        message = await ctx.send(
            "C'est parti ?\n"
            "Les rôles ont bien été attribués et synchronisés ?"
            " (si non, le faire AVANT de valider)\n\n"
            "On est bien après 10h le jour du lancement ?\n\n"
            "Tu es conscient que tous les joueurs reçevront à 18h55 un message"
            " en mode « happy Hunger Games » ? (codé en dur parce que flemme)"
        )
        if not await tools.yes_no(message):
            await ctx.send("Mission aborted.")

        taches = []
        r = "C'est parti !\n\n"

        r += ("Bon plus besoin de lancer les actions, c'est fait "
              "à la synchro des rôles mais les !open n'ont aucun "
              "impact tant que tout le monde est en role_actif == "
              "False, DU COUP passer tout le monde en True genre "
              "MAINTENANT (et en silencieux !) si on veut vraiment "
              "lancer\n\n")

        n10 = tools.next_occurence(datetime.time(hour=10))
        n19 = tools.next_occurence(datetime.time(hour=19))

        # Programmation votes condamnés chainés 10h-18h
        r += "\nProgrammation des votes :\n"
        taches.append(Tache(timestamp=n10, commande="!open cond 18h 10h"))
        r += " - À 10h : !open cond 18h 10h\n"

        # Programmation votes loups chainés 19h-23h
        taches.append(Tache(timestamp=n19, commande="!open loups 23h 19h"))
        r += " - À 19h : !open loups 23h 19h\n"

        # Programmation premier vote maire 10h-17h
        taches.append(Tache(timestamp=n10, commande="!open maire 17h"))
        r += " - À 10h : !open maire 17h\n"

        # Programmation actions au lancement et actions permanentes
        r += "\nProgrammation des actions start / perma :\n"
        start_perma = Action.query.filter(Action.trigger_debut.in_(
            [ActionTrigger.start, ActionTrigger.perma]
        )).all()
        for action in start_perma:
            r += (f" - À 19h : !open {action.id} "
                  f"(trigger_debut == {action.trigger_debut})\n")
            taches.append(Tache(timestamp=n19,
                                commande=f"!open {action.id}",
                                action=action))

        # Programmation refill weekends
        # r += "\nProgrammation des refills weekends :\n"
        # ts = tools.fin_pause() - datetime.timedelta(minutes=5)
        # taches.append(Tache(timestamp=ts,
        #                     commande=f"!refill weekends all"))
        # r += " - Dimanche à 18h55 : !refill weekends all\n"

        # Programmation envoi d'un message aux connards
        r += ("\nEt, à 18h50 : !send all [message de hype oue oue "
              "c'est génial]\n")
        taches.append(Tache(
            timestamp=(n19 - datetime.timedelta(minutes=10)),
            commande=(
                "!send all Ah {member.mention}... J'espère que tu "
                "es prêt(e), parce que la partie commence DANS 10 "
                " MINUTES !!! https://tenor.com/view/thehungergames-"
                "hungergames-thggifs-effie-gif-5114734"
            )
        ))
        await tools.log(r, code=True)

        Tache.add(*taches)      # On enregistre et programme le tout !

        await ctx.send("C'est tout bon ! (normalement) (détails dans #logs)")
