from discord.ext import commands
import tools
from bdd_connect import db, Joueurs
import datetime
from datetime import time

from . import gestion_actions

def get_criteres(quoi, qui, heure):
    if qui in ["cond", "maire"]:
        return {"votant_village": True}
    elif qui == "loups":
        return {"votant_loups": True}
    elif qui == "action":
        if heure and isinstance(heure, str):
            heure, minute = heure.split("h")
            heure = int(heure)
            minute = int(minute) if minute != "" else 0
        else:
            tps = datetime.datetime.now().time()
            if quoi == "remind":
                tps += datetime.timedelta(hours=1)
            else:
                if quoi == "open":
                    return {"role_actif": True, "heure_debut": tps}
                else:
                    return {"role_actif": True, "fin_role": tps}
    else:
        raise ValueError(f"""Cannot associate criteria to job {quoi}_{qui}""")

def get_actions(quoi, heure = None):
    if heure and isinstance(heure, str):
        heure, minute = heure.split("h")
        heure = int(heure)
        minute = int(minute) if minute != "" else 0
    else:
        tps = datetime.datetime.now().time()
        if quoi == "remind":
            tps += datetime.timedelta(hours=1)
    return gestion_actions.get_actions("temporel", tps)

class OpenClose(commands.Cog):
    """OpenClose : lancement, rappel et fermetures de votes / actions"""

    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def open(self, ctx, qui, heure=None):
        """Lance un vote / des actions de rôle"""

        if qui in ["cond", "maire", "loups"]:
            criteres = get_criteres("open", qui, heure)
            users = Joueurs.query.filter_by(**criteres).all()     # Liste des joueurs répondant aux critères
            await ctx.send(tools.code_bloc(f"""Critères : {criteres}<br/>"""))
        elif qui == "action":
            actions = await get_actions("temporel", heure)
            users = [action.player_id for action in actions]
        else:
            raise ValueError(f"""Argument \"{qui}" invalide""")

        str_users = str(users).replace(', ', ',\n ')
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(users)}) : \n{str_users}"))


    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def close(self, ctx, qui, heure=None):
        """Ferme un vote / des actions de rôle"""

        if qui in ["cond", "maire", "loups"]:
            criteres = get_criteres("open", qui, heure)
            users = Joueurs.query.filter_by(**criteres).all()     # Liste des joueurs répondant aux critères
            await ctx.send(tools.code_bloc(f"""Critères : {criteres}<br/>"""))
        elif qui == "action":
            actions = await get_actions("temporel", heure)
            users = [action.player_id for action in actions]
        else:
            raise ValueError(f"""Argument \"{qui}" invalide""")

        str_users = str(users).replace(', ', ',\n ')
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(users)}) : \n{str_users}"))


    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def remind(self, ctx, qui, heure=None):
        """Envoie un rappel un vote / des actions de rôle au(x) joueur(s) n'ayant pas voté/agi"""

        if qui in ["cond", "maire", "loups"]:
            criteres = get_criteres("open", qui, heure)
            users = Joueurs.query.filter_by(**criteres).all()     # Liste des joueurs répondant aux critères
            await ctx.send(tools.code_bloc(f"""Critères : {criteres}<br/>"""))
        elif qui == "action":
            actions = await get_actions("temporel", heure)
            users = [action.player_id for action in actions]
        else:
            raise ValueError(f"""Argument \"{qui}" invalide""")

        str_users = str(users).replace(', ', ',\n ')
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(users)}) : \n{str_users}"))
