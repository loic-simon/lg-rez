from discord.ext import commands
import tools
from bdd_connect import db, Joueurs
import traceback



class Informations(commands.Cog):
    """Informations : Commandes que les joueurs peuvent utilisés régulièrement"""

    @commands.command()
    async def roles(self, ctx, nom_camp = "all") :
        """Affiche la liste des rôles,
        L'option nom_camp permet de lister les rôles d'un camp spécifique
        Valeurs possibles pour nom_camp : all, Loups, Villageois, Solitaire, Nécros""" #création de la BDD role dans models.py
        if nom_camp == "all" :
            tous = Roles.query.all()
            ret = '\n - '.join([r.nom_du_role for r in tous])
        elif nom_camp == "Loups" :
            liste = Roles.query.filter_by(camp="Loups")
            ret = '\n - '.join([r.nom_du_role for r in liste])
        elif nom_camp == "Villageois" :
            liste = Roles.query.filter_by(camp="Villageois")
            ret = '\n - '.join([r.nom_du_role for r in liste])
        elif nom_camp == "Solitaire" :
            liste = Roles.query.filter_by(camp="Solitaire")
            ret = '\n - '.join([r.nom_du_role for r in liste])
        elif nom_camp == "Nécros" :
            liste = Roles.query.filter_by(camp="Nécros")
            ret = '\n - '.join([r.nom_du_role for r in liste])
        else :
            await ctx.send(tools.code_bloc(f"Cible {nom_camp} non trouvée\n{traceback.format_exc()}"))

        await ctx.send(tools.code_bloc(f"Liste des roles dans le camp {nom_camp}: \n - {ret}"))

    @commands.command()
    async def MonRole(self, ctx, Details = "court") :
        """Affiche les informations du rôle du joueur
        L'option Details permet d'avoir plus ou moins d'info
        Valeurs possibles pour Details : court, long, role"""
        nom_user = ctx.author.display_name
        try :
            u = Joueurs.query.filter_by(nom = nom_user).one()
        except :
            await ctx.send(tools.code_bloc(f"Le joueur {nom_user} n'a pas été trouvé\n{traceback.format_exc()}"))
        else :
            user_role = u.role
            if Details == "role" :
                await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role}"))
            else :
                try :
                    r = Roles.query.filter_by(role = user_role).one()
                except :
                    await ctx.send(tools.code_bloc(f"Votre rôle : {user_role} n'existe pas\n{traceback.format_exc()}"))
                else :
                    user_begin_time = r.horaire_debut
                    user_end_time = r.horaire_fin
                    user_side = r.camp
                    user_descript = r.description_longue
                    user_short = r.description_courte
                    if Details == "long" and user_begin_time != None:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role} dans le camp {user_side}\nTon action est entre : {user_begin_time} et {user_end_time}\nTon role consiste en :\n {user_descript}"))
                    elif Details == "court" and user_begin_time != None:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role} dans le camp {user_side}\nTon action est entre : {user_begin_time} et {user_end_time}\nTon role consiste en :\n {user_short}"))
                    elif Details == "long" and user_begin_time == None:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role} dans le camp {user_side}\nTon action n'a pas d'heure\nTon role consiste en :\n {user_descript}"))
                    elif Details == "court" and user_begin_time == None:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role} dans le camp {user_side}\nTon action n'a pas d'heure\nTon role consiste en :\n {user_short}"))
                    else :
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role}\nEt utilise les bons arguments (voir !help MonRole pour plus de détails)"))
