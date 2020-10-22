import datetime

from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_

from lgrez.blocs import tools, bdd, bdd_tools
from lgrez.features import gestion_actions, taches
from lgrez.blocs.bdd import Joueurs, Actions, BaseActions, BaseActionsRoles


async def recup_joueurs(quoi, qui, heure=None):
    """Renvoie les joueurs concernés par la tâche !quoi <qui> [heure]

    Ex : !open cond -> joueurs avec droit de vote, !close action 17h -> joueurs dont l'action se termine à 17h
    """
    criteres = {
        "cond": {
            "open": and_(Joueurs.votant_village == True,        # Objets spéciaux SQLAlchemy.BinaryExpression : ne PAS simplifier !!!
                         Joueurs._vote_condamne == None),
            "close": Joueurs._vote_condamne != None,
            "remind": Joueurs._vote_condamne == "non défini",
            },
        "maire": {
            "open": and_(Joueurs.votant_village == True,        # Objets spéciaux SQLAlchemy.BinaryExpression : ne PAS simplifier !!!
                         Joueurs._vote_maire == None),
            "close": Joueurs._vote_maire != None,
            "remind": Joueurs._vote_maire == "non défini",
            },
        "loups": {
            "open": and_(Joueurs.votant_loups == True,          # Objets spéciaux SQLAlchemy.BinaryExpression : ne PAS simplifier !!!
                         Joueurs._vote_loups == None),
            "close": Joueurs._vote_loups != None,
            "remind": Joueurs._vote_loups == "non défini",
            },
        }

    if qui in criteres:
        critere = criteres[qui][quoi]
        return Joueurs.query.filter(critere).all()      # Liste des joueurs répondant aux critères

    elif qui == "action":
        if heure and isinstance(heure, str):            # Si l'heure est précisée, on convertit str "HHhMM" -> datetime.time
            tps = tools.heure_to_time(heure)
        else:                                           # Si l'heure n'est pas précisée, on prend l'heure actuelle
            raise ValueError("[heure] doit être spécifiée lorque <qui> == \"action\"")
            # tps = datetime.datetime.now().time()
            # if quoi == "remind":
            #     tps += datetime.timedelta(hours=1)      # Si remind, on considère l'heure qui arrive

        actions = await gestion_actions.get_actions(quoi, "temporel", tps)

        dic = {}
        for action in actions:
            if (joueur := Joueurs.query.get(action.player_id)) in dic:
                dic[joueur].append(action)
            else:
                dic[joueur] = [action]

        return dic
        #Formerly :
        #{joueur.player_id:[action for action in actions if action.player_id == joueur.player_id] for joueur in [Joueurs.query.get(action.player_id) for action in actions]}

    elif qui.isdigit() and (action := Actions.query.get(int(qui))):     # Appel direct action par son numéro
        if ((quoi == "open" and not action._decision)       # Sécurité : ne pas lancer une action déjà lancer,
            or (quoi == "close" and action._decision)       #   ni fermer une déjà fermée
            or (quoi == "remind" and action._decision == "rien")):

            return {Joueurs.query.get(action.player_id):[action]}
        else:
            return {}

    else:
        raise ValueError(f"""Argument <qui> == \"{qui}" invalide""")



class OpenClose(commands.Cog):
    """OpenClose - Commandes de lancement, rappel et fermeture des votes et actions"""

    @commands.command()
    @tools.mjs_only
    async def open(self, ctx, qui, heure=None, heure_chain=None):
        """Lance un vote / des actions de rôle (COMMANDE BOT / MJ)

        <qui> prend les valeurs :
            cond        pour le vote du condamné
            maire       pour le vote du maire
            loups       pour le vote des loups
            action      pour les actions commençant à [heure]
            {id}        pour une action spécifique (paramètre Actions.id)

        [heure] a deux rôles différents :
            - si <qui> == "cond", "maire" ou "loup", programme en plus la fermeture à [heure] (et un rappel 10 minutes avant) ;
            - si <qui> == "action", il est obligatoire : heure des actions à lancer (cf plus haut). Pour les actions, la fermeture est de toute façon programmée le cas échéant (trigger_fin temporel ou delta).
        Dans tous les cas, format HHh ou HHhMM.

        [heure_chain] permet de chaîner des votes : lance le vote immédiatement et programme sa fermeture à [heure], en appellant !close de sorte à programmer une nouvelle ouverture le lendemain à [heure_chain], et ainsi de suite
        Format HHh ou HHhMM.

        Une sécurité empêche de lancer un vote ou une action déjà en cours.

        Cette commande a pour vocation première d'être exécutée automatiquement par des tâches planifiées.
        Elle peut être utilisée à la main, mais attention à ne pas faire n'importe quoi (penser à envoyer / planifier la fermeture des votes, par exemple).

        Ex. !open maire             lance un vote condamné maintenant
            !open cond 19h          lance un vote condamné maintenant et programme sa fermeture à 19h00 (ex. Juge Bègue)
            !open cond 18h 10h      lance un vote condamné maintenant, programme sa fermeture à 18h00, et une prochaine ouverture à 10h, etc
            !open action 19h        lance toutes les actions commençant à 19h00
            !open 122               lance l'action d'ID 122
        """
        joueurs = await recup_joueurs("open", qui, heure)        # Liste de joueurs (votes) ou dictionnaire joueur : action

        str_joueurs = "\n - ".join([joueur.nom for joueur in joueurs])
        await tools.send_code_blocs(ctx, f"Utilisateur(s) répondant aux critères ({len(joueurs)}) : \n - {str_joueurs}")

        for joueur in joueurs:
            chan = ctx.guild.get_channel(joueur._chan_id)
            assert chan, f"!open : chan privé de {joueur} introuvable"

            if qui == "cond":
                bdd_tools.modif(joueur, "_vote_condamne", "non défini")
                message = await chan.send(
                    f"""{tools.montre()}  Le vote pour le condamné du jour est ouvert !  {tools.emoji(ctx, "bucher")} \n"""
                    + (f"""Tu as jusqu'à {heure} pour voter. \n""" if heure else "")
                    + tools.ital(f"""Tape {tools.code('!vote <joueur>')} ou utilise la réaction pour voter."""))
                await message.add_reaction(tools.emoji(ctx, "bucher"))

            elif qui == "maire":
                bdd_tools.modif(joueur, "_vote_maire", "non défini")
                message = await chan.send(
                    f"""{tools.montre()}  Le vote pour l'élection du maire est ouvert !  {tools.emoji(ctx, "maire")} \n"""
                    + (f"""Tu as jusqu'à {heure} pour voter. \n""" if heure else "")
                    + tools.ital(f"""Tape {tools.code('!votemaire <joueur>')} ou utilise la réaction pour voter."""))
                await message.add_reaction(tools.emoji(ctx, "maire"))

            elif qui == "loups":
                bdd_tools.modif(joueur, "_vote_loups", "non défini")
                message = await chan.send(
                    f"""{tools.montre()}  Le vote pour la victime de cette nuit est ouvert !  {tools.emoji(ctx, "lune")} \n"""
                    + (f"""Tu as jusqu'à {heure} pour voter. \n""" if heure else "")
                    + tools.ital(f"""Tape {tools.code('!voteloups <joueur>')} ou utilise la réaction pour voter."""))
                await message.add_reaction(tools.emoji(ctx, "lune"))

            else:       # Action

                for action in joueurs[joueur]:
                    await gestion_actions.open_action(ctx, action, chan)

        bdd.session.commit()

        # Actions déclenchées par ouverture
        for action in Actions.query.filter_by(trigger_debut=f"open_{qui}"):
            await gestion_actions.open_action(ctx, action)

        # Programme fermeture
        if qui in ["cond", "maire", "loups"] and heure:
            ts = tools.next_occurence(tools.heure_to_time(heure))
            taches.add_task(ctx.bot, ts - datetime.timedelta(minutes=10), f"!remind {qui}")
            if heure_chain:
                taches.add_task(ctx.bot, ts, f"!close {qui} {heure_chain} {heure}")      # Programmera prochaine ouverture
            else:
                taches.add_task(ctx.bot, ts, f"!close {qui}")



    @commands.command()
    @tools.mjs_only
    async def close(self, ctx, qui, heure=None, heure_chain=None):
        """Ferme un vote / des actions de rôle (COMMANDE BOT / MJ)

        <qui> prend les valeurs :
            cond        pour le vote du condamné
            maire       pour le vote du maire
            loups       pour le vote des loups
            action      pour les actions se terminant à [heure]
            {id}        pour une action spécifique (paramètre Actions.id)

        [heure] a deux rôles différents :
            - si <qui> == "cond", "maire" ou "loup", programme en plus une prochaine ouverture à [heure] ;
            - si <qui> == "action", il est obligatoire : heure des actions à lancer (cf plus haut). Pour les actions, la prochaine est de toute façon programmée le cas échéant (cooldown à 0 et reste des charges).
        Dans tous les cas, format HHh ou HHhMM.

        [heure_chain] permet de chaîner des votes : ferme le vote immédiatement et programme une prochaine ouverture à [heure], en appellant !open de sorte à programmer une nouvelle fermeture le lendemain à [heure_chain], et ainsi de suite.
        Format HHh ou HHhMM.

        Une sécurité empêche de fermer un vote ou une action qui n'est pas en cours.

        Cette commande a pour vocation première d'être exécutée automatiquement par des tâches planifiées.
        Elle peut être utilisée à la main, mais attention à ne pas faire n'importe quoi (penser à envoyer / planifier la fermeture des votes, par exemple).

        Ex. !close maire            ferme le vote condamné maintenant
            !close cond 10h         ferme le vote condamné maintenant et programme une prochaine ouverture à 10h00
            !close cond 10h 18h     ferme le vote condamné maintenant, programme une prochaine ouverture à 10h00, qui sera fermé à 18h, etc
            !close action 22h       ferme toutes les actions se terminant à 22h00
            !close 122              ferme l'action d'ID 122
        """

        joueurs = await recup_joueurs("close", qui, heure)

        str_joueurs = "\n - ".join([joueur.nom for joueur in joueurs])
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(joueurs)}) : \n{str_joueurs}"))

        for joueur in joueurs:
            chan = ctx.guild.get_channel(joueur._chan_id)
            assert chan, f"!close : chan privé de {joueur} introuvable"

            if qui == "cond":
                await chan.send(f"""{tools.montre()}  Fin du vote pour le condamné du jour ! \n"""
                                f"""Vote définitif : {joueur._vote_condamne}\n"""
                                f"""Les résultats arrivent dans l'heure !\n""")
                bdd_tools.modif(joueur, "_vote_condamne", None)

            elif qui == "maire":
                await chan.send(f"""{tools.montre()}  Fin du vote pour le maire ! \n"""
                                f"""Vote définitif : {joueur._vote_maire}""")
                bdd_tools.modif(joueur, "_vote_maire", None)

            elif qui == "loups":
                await chan.send(f"""{tools.montre()}  Fin du vote pour la victime du soir ! \n"""
                                f"""Vote définitif : {joueur._vote_loups}""")
                bdd_tools.modif(joueur, "_vote_loups", None)

            else:       # Action
                for action in joueurs[joueur]:
                    await chan.send(f"""{tools.montre()}  Fin de la possiblité d'utiliser ton action {tools.code(action.action)} ! \n"""
                                    f"""Action définitive : {action._decision}""")
                    await gestion_actions.close_action(ctx, action, chan)

        bdd.session.commit()

        # Actions déclenchées par fermeture
        for action in Actions.query.filter_by(trigger_debut=f"close_{qui}"):
            await gestion_actions.open_action(ctx, action)

        # Programme prochaine ouverture
        if qui in ["cond", "maire", "loups"] and heure:
            ts = tools.next_occurence(tools.heure_to_time(heure))
            if heure_chain:
                taches.add_task(ctx.bot, ts, f"!open {qui} {heure_chain} {heure}")      # Programmera fermeture
            else:
                taches.add_task(ctx.bot, ts, f"!open {qui}")



    @commands.command()
    @tools.mjs_only
    async def remind(self, ctx, qui, heure=None):
        """Envoi un rappel de vote / actions de rôle (COMMANDE BOT / MJ)

        <qui> prend les valeurs :
            cond        pour le vote du condamné
            maire       pour le vote du maire
            loups       pour le vote des loups
            action      pour les actions se terminant à [heure]
            {id}        pour une action spécifique (paramètre Actions.id)

        [heure] ne sert que dans le cas où <qui> == "action" (il est alors obligatoire), contrairement à !open et !close.
        Format HHh ou HHhMM.

        Le bot n'envoie un message qu'aux joueurs n'ayant pas encore voté / agi, si le vote ou l'action est bien en cours.

        Cette commande a pour vocation première d'être exécutée automatiquement par des tâches planifiées.
        Elle peut être utilisée à la main, mais attention à ne pas faire n'importe quoi !.

        Ex. !remind maire           rappelle le vote condamné maintenant
            !remind action 22h      rappelle toutes les actions se terminant à 22h00
            !remind 122             rappelle l'action d'ID 122
        """

        joueurs = await recup_joueurs("remind", qui, heure)

        str_joueurs = "\n - ".join([joueur.nom for joueur in joueurs])
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(joueurs)}) : \n{str_joueurs}"))

        for joueur in joueurs:
            chan = ctx.guild.get_channel(joueur._chan_id)
            assert chan, f"!remind : chan privé de {joueur} introuvable"
            member = ctx.guild.get_member(joueur.discord_id)
            assert member, f"!remind : member {joueur} introuvable"

            if qui == "cond":
                message = await chan.send(f"""⏰ {member.mention} Plus que 10 minutes pour voter pour le condamné du jour ! 😱 \n""")
                await message.add_reaction(tools.emoji(ctx, "bucher"))

            elif qui == "maire":
                message = await chan.send(f"""⏰ {member.mention} Plus que 10 minutes pour élire le nouveau maire ! 😱 \n""")
                await message.add_reaction(tools.emoji(ctx, "maire"))

            elif qui == "loups":
                message = await chan.send(f"""⏰ {member.mention} Plus que 10 minutes voter pour la victime du soir ! 😱 \n""")
                await message.add_reaction(tools.emoji(ctx, "lune"))

            else:       # Action
                for action in joueurs[joueur]:
                    message = await chan.send(f"""⏰ {member.mention} Plus que 10 minutes pour utiliser ton action {tools.code(action.action)} ! 😱 \n""")
                    await message.add_reaction(tools.emoji(ctx, "action"))



    @commands.command()
    @tools.mjs_only
    async def refill(self, ctx, motif, cible = None):
        """Permet de recharger le/les pouvoirs rechargeables (COMMANDE BOT / MJ)

        <motif> doit être "weekends", "forgeron", "rebouteux" ou "divin" (forcer le refill car les MJs tout-puissants l'ont décidé)
        [cible] peut être 'all', sinon il faudra spécifier un joueur
        """
        if motif not in ["weekends", "forgeron", "rebouteux", "divin"]:
            await ctx.send(f"{motif} n'est pas un <motif> valide")
            return

        if motif == "divin":
            if cible != "all":
                target = await tools.boucle_query_joueur(ctx, cible=cible, message = "Qui veux-tu recharger ?")
                refillable = Actions.query.filter(Actions.player_id == target.discord_id, Actions.charges != None).all()
            else:
                m = await ctx.send("Tu as choisi de recharger le pouvoir de TOUS les joueurs actifs, en es-tu sûr ?")

                if await tools.yes_no(ctx.bot, m):
                    refillable = Actions.query.filter(Actions.charges != None).all()

                else:
                    await ctx.send("Mission aborted.")
                    return

        else: #refill WE, forgeron ou rebouteux
            if cible != "all":
                target = await tools.boucle_query_joueur(ctx, cible=cible, message = "Qui veux-tu recharger ?")
                refillable = Actions.query.filter(Actions.refill.contains(motif), Actions.player_id == target.discord_id).all()
            else:
                refillable = Actions.query.filter(Actions.refill.contains(motif)).all()

        await tools.log(ctx, refillable)

        txt = "Action(s) répondant aux critères :\n"
        for action in refillable:
            txt += f"- {action.action}, id = {action.id} \n"

        await tools.send_code_blocs(ctx, txt)

        if motif == "weekends":
            remplissage = {action: BaseActions.query.get(action.action).base_charges for action in refillable}
        else:
            remplissage = {action: action.charges + 1 for action in refillable}

        for action, charge in remplissage.items():
            bdd_tools.modif(action, "charges", charge)

            await tools.send_blocs(tools.private_chan(ctx.guild.get_member(action.player_id)),f"Ton action {action.action} vient d'être rechargée, tu as maintenant {charge} charge(s) disponible(s) !")

        bdd.session.commit()


    @commands.command()
    @tools.mjs_only
    async def cparti(self, ctx):
        """Lance le jeu (COMMANDE MJ)

        - Crée (et programme) les actions associées aux rôles de tous les joueurs     ==> EN FAIT NON, plus besoin vu que c'est fait à la synchro des rôles
        - Programme les votes condamnés quotidiens (avec chaînage) 10h-18h
        - Programme un vote maire 10h-18h
        - Programme les actions au lancement du jeu (choix de mentor...) et permanentes (forgeron)... à 19h

        À utiliser le jour du lancement après 10h (lance les premières actions le soir et les votes le lendemain)
        """

        message = await ctx.send("C'est parti ?\nLes rôles ont bien été attribués et synchronisés ? (si non, le faire AVANT de valider)\n\nOn est bien après 10h le jour du lancement ?\n\nTu es conscient que tous les joueurs reçevront à 18h55 un message en mode « happy Hunger Games » ? (codé en dur parce que flemme)")
        if await tools.yes_no(ctx.bot, message):
            async with ctx.typing():
                joueurs = Joueurs.query.all()
                r = "C'est parti !\n"

                # Ajout de toutes les actions en base
                # r += "\nChargement des actions :\n"
                # actions = []
                # cols = [col for col in bdd_tools.get_cols(BaseActions) if not col.startswith("base")]
                #
                # for joueur in joueurs:
                #     base_actions_roles = BaseActionsRoles.query.filter_by(role=joueur.role).all()
                #     base_actions = [BaseActions.query.get(bar.action) for bar in base_actions_roles]
                #     actions.extend([Actions(player_id=joueur.discord_id, **{col: getattr(ba, col) for col in cols},
                #                             cooldown=0, charges=ba.base_charges) for ba in base_actions])
                #
                # for action in actions:
                #     bdd.session.add(action)  # add_all marche pas, problème d'ids étou étou
                # bdd.session.commit()
                # for action in actions:      # Après le commit pour que action.id existe
                #     r += f" - {action.id} ({joueur.nom} > {action.action})\n"
                #
                # # Programmation des actions temporelles
                # r += "\nProgrammation des tâches :\n"
                # for action in actions:
                #     if action.trigger_debut == "temporel":
                #         taches.add_task(ctx.bot, tools.next_occurence(action.heure_debut), f"!open {action.id}")
                #         r += f" - !open {action.id}"

                r += "\n\nBon plus besoin de lancer les actions, c'est fait à la synchro des rôles mais les !open n'ont aucun impact tant que tout le monde est en role_actif == False, DU COUP passer tout le monde en True genre MAINTENANT (et en silencieux !) si on veut vraiment lancer\n\n"

                # Programmation votes condamnés chainés 10h-18h
                r += "\nProgrammation des votes :\n"
                taches.add_task(ctx.bot, tools.next_occurence(datetime.time(hour=10)), "!open cond 18h 10h")
                r += " - À 10h : !open cond 18h 10h\n"

                # Programmation votes loups chainés 19h-23h
                taches.add_task(ctx.bot, tools.next_occurence(datetime.time(hour=19)), "!open loups 23h 19h")
                r += " - À 19h : !open loups 23h 19h\n"

                # Programmation premier vote maire 10h-17h
                taches.add_task(ctx.bot, tools.next_occurence(datetime.time(hour=10)), "!open maire 17h")
                r += " - À 10h : !open maire 17h\n"

                # Programmation actions au lancement et actions permanentes
                r += "\nProgrammation des actions start / perma :\n"
                ts = tools.next_occurence(datetime.time(hour=19))
                for action in Actions.query.filter_by(trigger_debut="start").all() + Actions.query.filter_by(trigger_debut="perma").all():
                    r += f" - À 19h : !open {action.id} (trigger_debut == {action.trigger_debut})\n"
                    taches.add_task(ctx.bot, ts, f"!open {action.id}", action=action.id)

                # Programmation envoi d'un message aux connards
                r += f"\nEt, à 18h50 : !send all [message de hype oue oue c'est génial]\n"
                taches.add_task(ctx.bot, ts - datetime.timedelta(minutes=10), "!send all Ah {member.mention}... J'espère que tu es prêt, parce que la partie commence DANS 10 MINUTES !!! https://tenor.com/view/thehungergames-hungergames-thggifs-effie-gif-5114734")

                await tools.log(ctx, r, code=True)

            await ctx.send("C'est tout bon ! (normalement) (détails dans #logs)")
        else:
            await ctx.send("Mission aborted.")