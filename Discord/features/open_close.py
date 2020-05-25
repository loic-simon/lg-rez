from discord.ext import commands
import tools
from bdd_connect import db, Joueurs


def get_criteres(quoi, qui):
    if qui in ["cond", "maire"]:
        return {"votantVillage": True}
    elif qui == "loups":
        return {"votantLoups": True}
    elif qui == "action":
        if heure and heure.isdigit():
            heure = int(d["heure"]) % 24
        else:
            if quoi == "remind":
                heure = (int(time.strftime("%H")) + 1) % 24
            else:
                heure = int(time.strftime("%H"))
                if quoi == "open":
                    return {"roleActif": True, "debutRole": heure}
                else:
                    return {"roleActif": True, "finRole": heure}
    else:
        raise ValueError(f"""Cannot associate criteria to job {quoi}_{qui}""")


class OpenClose(commands.Cog):
    """OpenClose : lancement, rappel et fermetures de votes / actions"""

    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def open(self, ctx, qui, heure=None):
        """Lance un vote / des actions de rôle"""

        ### DÉTECTION TÂCHE À FAIRE ET CRITÈRES ASSOCIÉS

        if qui in ["cond", "maire", "loups", "action"]:         # jobs : défini en début de fichier, car utile dans admin
            criteres = get_criteres("open", qui)
            
            await ctx.send(tools.code_bloc(f"""Critères : {criteres}<br/>"""))
        else:
            raise ValueError(f"""Argument \"{qui}" invalide""")

        ### RÉCUPÉRATION UTILISATEURS CACHE

        users = Joueurs.query.filter_by(**criteres).all()     # Liste des joueurs répondant aux cirtères
        str_users = str(users).replace(', ', ',\n ')
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(users)}) : \n{str_users}"))


    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def close(self, ctx, qui, heure=None):
        """Ferme un vote / des actions de rôle"""

        ### DÉTECTION TÂCHE À FAIRE ET CRITÈRES ASSOCIÉS

        if qui in ["cond", "maire", "loups", "action"]:         # jobs : défini en début de fichier, car utile dans admin
            criteres = get_criteres("close", qui)
            
            await ctx.send(tools.code_bloc(f"""Critères : {criteres}<br/>"""))
        else:
            raise ValueError(f"""Argument \"{qui}" invalide""")

        ### RÉCUPÉRATION UTILISATEURS CACHE

        users = Joueurs.query.filter_by(**criteres).all()     # Liste des joueurs répondant aux cirtères
        str_users = str(users).replace(', ', ',\n ')
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(users)}) : \n{str_users}"))


    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_role("MJ"))
    async def remind(self, ctx, qui, heure=None):
        """Envoie un rappel un vote / des actions de rôle au(x) joueur(s) n'ayant pas voté/agi"""

        ### DÉTECTION TÂCHE À FAIRE ET CRITÈRES ASSOCIÉS

        if qui in ["cond", "maire", "loups", "action"]:         # jobs : défini en début de fichier, car utile dans admin
            criteres = get_criteres("remind", qui)
            
            await ctx.send(tools.code_bloc(f"""Critères : {criteres}<br/>"""))
        else:
            raise ValueError(f"""Argument \"{qui}" invalide""")

        ### RÉCUPÉRATION UTILISATEURS CACHE

        users = Joueurs.query.filter_by(**criteres).all()     # Liste des joueurs répondant aux cirtères
        str_users = str(users).replace(', ', ',\n ')
        await ctx.send(tools.code_bloc(f"Utilisateur(s) répondant aux critères ({len(users)}) : \n{str_users}"))
