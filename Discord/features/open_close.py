import datetime

from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_

from bdd_connect import db, Joueurs
from features import gestion_actions
from blocs import bdd_tools
import tools


async def retrieve_users(quoi, qui, heure=None):
    """Renvoie les joueurs concernés par la tâche !quoi qui <heure>
        Ex : !open cond -> joueurs avec droit de vote, !close action 17h -> joueurs dont l'action se termine à 17h"""

    criteres = {
        "cond": {
            "open": Joueurs.votant_village == True,     # Objets spéciaux SQLAlchemy.BinaryExpression : ne PAS simplifier !!!
            "close": Joueurs._vote_condamne != None,
            "remind": Joueurs._vote_condamne == "non défini",
            },
        "maire": {
            "open": Joueurs.votant_village == True,
            "close": Joueurs._vote_maire != None,
            "remind": Joueurs._vote_maire == "non défini",
            },
        "loups": {
            "open": Joueurs.votant_loups == True,
            "close": Joueurs._vote_loups != None,
            "remind": Joueurs._vote_loups == "non défini",
            },
        }

    if qui in criteres:
        critere = criteres[qui][quoi]
        return Joueurs.query.filter(critere).all()      # Liste des joueurs répondant aux critères
    elif qui == "action":
        if heure and isinstance(heure, str):            # Si l'heure est précisée, on convertit str "HHhMM" -> datetime.time
            heure, minute = heure.split("h")
            heure = int(heure)
            minute = int(minute) if minute else 0
            tps = datetime.time(heure, minute)
        else:                                           # Si l'heure n'est pas précisée, on prend l'heure actuelle
            tps = datetime.datetime.now().time()
            if quoi == "remind":
                tps += datetime.timedelta(hours=1)      # Si remind, on considère l'heure qui arrive

        actions = await gestion_actions.get_actions(quoi, "temporel", tps)
        return {Joueurs.query.get(action.player_id):action for action in actions}
    else:
        raise ValueError(f"""Argument \"{qui}" invalide""")



class OpenClose(commands.Cog):
    """
    OpenClose - lancement, rappel et fermetures des votes ou des actions
    """

    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_any_role("MJ", "Bot"))
    async def open(self, ctx, qui, heure=None):
        """
        Lance un vote / des actions de rôle pour <qui>

        <qui> prend les valeurs :
            -cond         Pour le vote du condamné
            -maire        Pour le vote du maire
            -loups        Pour le vote des loups
            -action       Pour lancer les actions commençant à [heure] (heure d'envoi du message si non spécifié)
        """

        users = await retrieve_users("open", qui, heure)        # Liste de joueurs ou dictionnaire joueur : action

        str_users = "\n - ".join([user.nom for user in users])
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(users)}) : \n - {str_users}"))

        for user in users:
            chan = ctx.guild.get_channel(user._chan_id)
            if qui == "cond":
                bdd_tools.modif(user, "_vote_condamne", "non défini")
                message = await chan.send(
                    f"""{tools.montre()}  Le vote pour le condamné du jour est ouvert !  {tools.emoji(ctx, "bucher")} \n"""
                    f"""Tape {tools.code('!vote <joueur>')} ou utilise la réaction pour voter.""")
                await message.add_reaction(tools.emoji(ctx, "bucher"))

            elif qui == "maire":
                bdd_tools.modif(user, "_vote_maire", "non défini")
                message = await chan.send(
                    f"""{tools.montre()}  Le vote pour l'élection du maire est ouvert !  {tools.emoji(ctx, "maire")} \n"""
                    f"""Tape {tools.code('!votemaire <joueur>')} ou utilise la réaction pour voter.""")
                await message.add_reaction(tools.emoji(ctx, "maire"))

            elif qui == "loups":
                bdd_tools.modif(user, "_vote_loups", "non défini")
                message = await chan.send(
                    f"""{tools.montre()}  Le vote pour la victime de cette nuit est ouvert !  {tools.emoji(ctx, "lune")} \n"""
                    f"""Tape {tools.code('!voteloups <joueur>')} ou utilise la réaction pour voter.""")
                await message.add_reaction(tools.emoji(ctx, "lune"))

            elif qui == "action":
                action = users[user]
                if action.trigger_fin != "auto":
                    bdd_tools.modif(action, "_decision", "rien")
                    message = await chan.send(
                        f"""{tools.montre()}  Tu peux maintenant utiliser ton action de {user.role} !  {tools.emoji(ctx, "foudra")} \n"""
                        f"""Tape {tools.code('!action <phrase>')} ou utilise la réaction pour voter. (avant {action.heure_fin})""")
                    await message.add_reaction(tools.emoji(ctx, "foudra"))

        db.session.commit()


    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_any_role("MJ", "Bot"))
    async def close(self, ctx, qui, heure=None):
        """
        Lance un vote / des actions de rôle pour <qui>

        <qui> prend les valeurs :
            -cond         Pour le vote du condamné
            -maire        Pour le vote du maire
            -loups        Pour le vote des loups
            -action       Pour fermer les actions commençant à [heure] (heure d'envoi du message si non spécifié)
        """

        users = await retrieve_users("close", qui, heure)

        str_users = str(users).replace(', ', ',\n ')
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

            elif qui == "action":
                action = users[user]
                await chan.send(f"""{tools.montre()}  Fin de la possiblité d'utiliser ton action de {user.role} ! \n"""
                                f"""Action définitive : {action._decision}""")

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

        db.session.commit()


    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_any_role("MJ", "Bot"))
    async def remind(self, ctx, qui, heure=None):
        """
        Rappelle un vote / des actions de rôle pour <qui> (message de rappel)

        <qui> prend les valeurs :
            -cond         Pour le vote du condamné
            -maire        Pour le vote du maire
            -loups        Pour le vote des loups
            -action       Pour rappeler les actions commençant à [heure] (heure d'envoi du message si non spécifié)
        """

        users = await retrieve_users("remind", qui, heure)

        str_users = str(users).replace(', ', ',\n ')
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(users)}) : \n{str_users}"))

        for user in users:
            chan = ctx.guild.get_channel(user._chan_id)
            if qui == "cond":
                await chan.send(f"""⏰ Plus que 10 minutes pour voter pour le condamné du jour ! 😱 \n""")

            elif qui == "maire":
                await chan.send(f"""⏰ Plus que 10 minutes pour élire le nouveau maire ! 😱 \n""")

            elif qui == "loups":
                await chan.send(f"""⏰ Plus que 10 minutes voter pour la victime du soir ! 😱 \n""")

            elif qui == "action":
                await chan.send(f"""⏰ Plus que 10 minutes pour utiliser ton action de {user.role} ! 😱 \n""")
