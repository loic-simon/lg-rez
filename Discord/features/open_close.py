import datetime

from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_

from bdd_connect import db, Joueurs, Actions, BaseActions, BaseActionsRoles
from features import gestion_actions, taches
from blocs import bdd_tools
import tools


async def retrieve_users(quoi, qui, heure=None):
    # Renvoie les joueurs concernés par la tâche !quoi qui <heure>
    # Ex : !open cond -> joueurs avec droit de vote, !close action 17h -> joueurs dont l'action se termine à 17h

    criteres = {
        "cond": {
            "open": and_(Joueurs.votant_village == True,        # Objets spéciaux SQLAlchemy.BinaryExpression : ne PAS simplifier !!!
                         Joueurs._vote_condamne == None),
            "close": Joueurs._vote_condamne != None,
            "remind": Joueurs._vote_condamne == "non défini",
            },
        "maire": {
            "open": and_(Joueurs.votant_village == True,        # Objets spéciaux SQLAlchemy.BinaryExpression : ne PAS simplifier !!!
                         Joueurs._vote_condamne == None),
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
        return {Joueurs.query.get(action.player_id):action for action in actions}

    elif qui.isdigit() and (action := Actions.query.get(int(qui))):     # Appel direct action par son numéro
        if ((quoi == "open" and not action._decision)       # Sécurité : ne pas lancer une action déjà lancer,
            or (quoi == "close" and action._decision)       #   ni fermer une déjà fermée
            or (quoi == "remind" and action._decision == "rien")):

            return {Joueurs.query.get(action.player_id):action}
        else:
            return {}

    else:
        raise ValueError(f"""Argument <qui> == \"{qui}" invalide""")



class OpenClose(commands.Cog):
    """OpenClose - lancement, rappel et fermetures des votes ou des actions"""

    @commands.command()
    @commands.check_any(commands.check(lambda ctx: ctx.message.webhook_id), commands.has_any_role("MJ", "Bot"))
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
        users = await retrieve_users("open", qui, heure)        # Liste de joueurs (votes) ou dictionnaire joueur : action

        str_users = "\n - ".join([user.nom for user in users])
        await tools.send_code_blocs(ctx, f"Utilisateur(s) répondant aux critères ({len(users)}) : \n - {str_users}")

        for user in users:
            chan = ctx.guild.get_channel(user._chan_id)
            if qui == "cond":
                bdd_tools.modif(user, "_vote_condamne", "non défini")
                message = await chan.send(
                    f"""{tools.montre()}  Le vote pour le condamné du jour est ouvert !  {tools.emoji(ctx, "bucher")} \n"""
                    + (f"""Tu as jusqu'à {heure} pour voter. \n""" if heure else "")
                    + tools.ital(f"""Tape {tools.code('!vote <joueur>')} ou utilise la réaction pour voter."""))
                await message.add_reaction(tools.emoji(ctx, "bucher"))

            elif qui == "maire":
                bdd_tools.modif(user, "_vote_maire", "non défini")
                message = await chan.send(
                    f"""{tools.montre()}  Le vote pour l'élection du maire est ouvert !  {tools.emoji(ctx, "maire")} \n"""
                    + (f"""Tu as jusqu'à {heure} pour voter. \n""" if heure else "")
                    + tools.ital(f"""Tape {tools.code('!votemaire <joueur>')} ou utilise la réaction pour voter."""))
                await message.add_reaction(tools.emoji(ctx, "maire"))

            elif qui == "loups":
                bdd_tools.modif(user, "_vote_loups", "non défini")
                message = await chan.send(
                    f"""{tools.montre()}  Le vote pour la victime de cette nuit est ouvert !  {tools.emoji(ctx, "lune")} \n"""
                    + (f"""Tu as jusqu'à {heure} pour voter. \n""" if heure else "")
                    + tools.ital(f"""Tape {tools.code('!voteloups <joueur>')} ou utilise la réaction pour voter."""))
                await message.add_reaction(tools.emoji(ctx, "lune"))

            else:       # Action
                action = users[user]
                await gestion_actions.open_action(ctx, action, chan)

        db.session.commit()

        if qui in ["cond", "maire", "loups"] and heure:             # Programme fermeture
            ts = tools.next_occurence(tools.heure_to_time(heure))
            taches.add_task(ctx.bot, ts - datetime.timedelta(minutes=10), f"!remind {qui}")
            if heure_chain:
                taches.add_task(ctx.bot, ts, f"!close {qui} {heure_chain} {heure}")      # Programmera prochaine ouverture
            else:
                taches.add_task(ctx.bot, ts, f"!close {qui}")



    @commands.command()
    @commands.check_any(commands.check(lambda ctx: ctx.message.webhook_id), commands.has_any_role("MJ", "Bot"))
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

        users = await retrieve_users("close", qui, heure)

        str_users = "\n - ".join([user.nom for user in users])
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(users)}) : \n{str_users}"))

        for user in users:
            chan = ctx.guild.get_channel(user._chan_id)
            if qui == "cond":
                await chan.send(f"""{tools.montre()}  Fin du vote pour le condamné du jour ! \n"""
                                f"""Vote définitif : {user._vote_condamne}""")
                bdd_tools.modif(user, "_vote_condamne", None)

            elif qui == "maire":
                await chan.send(f"""{tools.montre()}  Fin du vote pour le maire ! \n"""
                                f"""Vote définitif : {user._vote_maire}""")
                bdd_tools.modif(user, "_vote_maire", None)

            elif qui == "loups":
                await chan.send(f"""{tools.montre()}  Fin du vote pour la victime du soir ! \n"""
                                f"""Vote définitif : {user._vote_loups}""")
                bdd_tools.modif(user, "_vote_loups", None)

            else:       # Action
                action = users[user]
                await chan.send(f"""{tools.montre()}  Fin de la possiblité d'utiliser ton action {action.action} ! \n"""
                                f"""Action définitive : {action._decision}""")
                await gestion_actions.close_action(ctx, action, chan)

        db.session.commit()

        if qui in ["cond", "maire", "loups"] and heure:             # Programme prochaine ouverture
            ts = tools.next_occurence(tools.heure_to_time(heure))
            if heure_chain:
                taches.add_task(ctx.bot, ts, f"!open {qui} {heure_chain} {heure}")      # Programmera fermeture
            else:
                taches.add_task(ctx.bot, ts, f"!open {qui}")



    @commands.command()
    @commands.check_any(commands.check(lambda ctx: ctx.message.webhook_id), commands.has_any_role("MJ", "Bot"))
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

        users = await retrieve_users("remind", qui, heure)

        str_users = "\n - ".join([user.nom for user in users])
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(users)}) : \n{str_users}"))

        for user in users:
            chan = ctx.guild.get_channel(user._chan_id)
            if qui == "cond":
                await chan.send(f"""⏰ {ctx.guild.get_member(user.discord_id).mention} Plus que 10 minutes pour voter pour le condamné du jour ! 😱 \n""")

            elif qui == "maire":
                await chan.send(f"""⏰ {ctx.guild.get_member(user.discord_id).mention} Plus que 10 minutes pour élire le nouveau maire ! 😱 \n""")

            elif qui == "loups":
                await chan.send(f"""⏰ {ctx.guild.get_member(user.discord_id).mention} Plus que 10 minutes voter pour la victime du soir ! 😱 \n""")

            else:       # Action
                action = users[user]
                await chan.send(f"""⏰ {ctx.guild.get_member(user.discord_id).mention} Plus que 10 minutes pour utiliser ton action {action.action} ! 😱 \n""")



    @commands.command()
    @commands.check_any(commands.check(lambda ctx: ctx.message.webhook_id), commands.has_any_role("MJ", "Bot"))
    async def cparti(self, ctx):
        """Lance le jeu (COMMANDE MJ)

        Crée (et programme) les actions associées aux rôles de tous les joueurs     ==> EN FAIT NON, plus besoin vu que c'est fait à la synchro des rôles
        Programme les votes condamnés quotidiens (avec chaînage) 10h-18h
        Programme un vote maire 10h-18h

        À utiliser le jour du lancement après 10h (lance les premières actions le soir et les votes le lendemain)
        """

        message = await ctx.send("C'est parti ?")
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
                #     db.session.add(action)  # add_all marche pas, problème d'ids étou étou
                # db.session.commit()
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

                # Programmation votes condamnés chainés
                r += "\nProgrammation des votes :\n"
                taches.add_task(ctx.bot, tools.next_occurence(datetime.time(hour=10)), "!open cond 18h 10h")
                r += " - !open cond 18h 10h\n"

                # Programmation premier vote maire
                taches.add_task(ctx.bot, tools.next_occurence(datetime.time(hour=10)), "!open maire 17h")
                r += " - !open maire 17h\n"

                await tools.log(ctx, r, code=True)

            await ctx.send("C'est tout bon ! (normalement) (détails dans #logs)")
        else:
            await ctx.send("Mission aborted.")
