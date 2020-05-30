import datetime

from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_

from bdd_connect import db, Joueurs
from features import gestion_actions
import tools


async def retrieve_users(quoi, qui, heure=None):
    """Renvoie les joueurs concernés par la tâche !quoi qui <heure>
        Ex : !open cond -> joueurs avec droit de vote, !close action 17h -> joueurs dont l'action se termine à 17h"""
        
    criteres = {
        "cond": {
            "open": Joueurs.votant_village == True,     # Objets spéciaux SQLAlchemy.BinaryExpression : ne PAS simplifier !!!
            "close": Joueurs._vote_village != None,
            "remind": Joueurs._vote_village == "non défini",
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
    """OpenClose : lancement, rappel et fermetures de votes / actions"""

    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def open(self, ctx, qui, heure=None):
        """Lance un vote / des actions de rôle"""

        users = await retrieve_users("open", qui, heure)        # Liste de joueurs ou dictionnaire joueur : action

        str_users = "\n - ".join([user.nom for user in users])
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(users)}) : \n - {str_users}"))
        
        for user in users:
            chan = ctx.guild.get_channel(user._chan_id)
            if qui == "cond":
                message = await chan.send(
                    f"""{tools.montre()}  Le vote pour le condamné du jour est ouvert !  {tools.emoji(ctx, "bucher")} \n"""
                    f"""Tape {tools.code('!vote <joueur>')} ou utilise la réaction pour voter.""")
                await message.add_reaction(tools.emoji(ctx, "bucher"))
                    
            elif qui == "maire":
                message = await chan.send(
                    f"""{tools.montre()}  Le vote pour l'élection du maire est ouvert !  {tools.emoji(ctx, "maire")} \n"""
                    f"""Tape {tools.code('!votemaire <joueur>')} ou utilise la réaction pour voter.""")
                await message.add_reaction(tools.emoji(ctx, "maire"))
                    
            elif qui == "loups":
                message = await chan.send(
                    f"""{tools.montre()}  Le vote pour la victime de cette nuit est ouvert !  {tools.emoji(ctx, "lune")} \n"""
                    f"""Tape {tools.code('!voteloups <joueur>')} ou utilise la réaction pour voter.""")
                await message.add_reaction(tools.emoji(ctx, "lune"))
                    
            elif qui == "action":
                action = users[user]
                if action.trigger_fin != "auto":
                    message = await chan.send(
                        f"""{tools.montre()}  Tu peux maintenant utiliser ton action de {user.role} !  {tools.emoji(ctx, "foudra")} \n"""
                        f"""Tape {tools.code('!action <phrase>')} ou utilise la réaction pour voter.""")
                    await message.add_reaction(tools.emoji(ctx, "foudra"))
                
                
                
    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def close(self, ctx, qui, heure=None):
        """Ferme un vote / des actions de rôle"""

        users = await retrieve_users("close", qui, heure)

        str_users = str(users).replace(', ', ',\n ')
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(users)}) : \n{str_users}"))
        
        for user in users:
            chan = ctx.guild.get_channel(user._chan_id)
            if qui == "cond":
                await chan.send(f"""{tools.montre()}  Fin du vote pour le condamné du jour ! \n"""
                                f"""Vote définitif : {user._vote_village}""")
                    
            elif qui == "maire":
                await chan.send(f"""{tools.montre()}  Fin du vote pour le maire ! \n"""
                                f"""Vote définitif : {user._vote_maire}""")
                    
            elif qui == "loups":
                await chan.send(f"""{tools.montre()}  Fin du vote pour la victime du soir ! \n"""
                                f"""Vote définitif : {user._vote_loups}""")
                    
            elif qui == "action":
                action = users[user]
                await chan.send(f"""{tools.montre()}  Fin de la possiblité d'utiliser ton action de {user.role} ! \n"""
                                f"""Action définitive : {action._decision}""")
                                
                                
                                
    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def remind(self, ctx, qui, heure=None):
        """Envoie un rappel un vote / des actions de rôle au(x) joueur(s) n'ayant pas voté/agi"""

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
