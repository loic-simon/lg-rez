from discord.ext import commands
import unidecode
import tools
from bdd_connect import db, Joueurs, Roles
import traceback



class Informations(commands.Cog):
    """Informations - Commandes disponibles pour être s'informer sur les rôles"""

    @commands.command()
    async def roles(self, ctx, nom_camp="all") :
        """
        !roles [camp] - Affiche la liste des rôles

        L'option nom_camp permet de lister les rôles d'un camp spécifique, elle est facultative
        Valeurs possibles pour nom_camp : all, None, Loups, Villageois, Solitaire, Nécros
        """ #création de la BDD role dans models.py
        nom_camp = unidecode.unidecode(nom_camp.lower())
        if nom_camp == "all":
            tous = Roles.query.all()
            ret = '\n - '.join([r.nom for r in tous])
        elif "loup" in nom_camp:
            liste = Roles.query.filter_by(camp="loups")
            ret = '\n - '.join([r.nom for r in liste])
        elif "villag" in nom_camp:
            liste = Roles.query.filter_by(camp="village")
            ret = '\n - '.join([r.nom for r in liste])
        elif "solit" in nom_camp:
            liste = Roles.query.filter_by(camp="solitaire")
            ret = '\n - '.join([r.nom for r in liste])
        elif "necro" in nom_camp:
            liste = Roles.query.filter_by(camp="nécro")
            ret = '\n - '.join([r.nom for r in liste])
        else :
            await ctx.send(tools.code_bloc(f"Cible {nom_camp} non trouvée\n{traceback.format_exc()}"))
            return

        await ctx.send(tools.code_bloc(f"Liste des rôles dans le camp {nom_camp} : \n - {ret}"))


    @commands.command()
    async def monrole(self, ctx, details="court") :
        """
        !monrole [details] - Affiche les informations du rôle du joueur

        L'option details permet d'avoir plus ou moins d'infos, elle est facultative
        Valeurs possibles pour details : None, court, long, role
        """
        nom_user = ctx.author.display_name
        try :
            u = Joueurs.query.filter_by(nom = nom_user).one()
        except :
            await ctx.send(tools.code_bloc(f"Le joueur {nom_user} n'a pas été trouvé\n{traceback.format_exc()}"))
        else :
            user_role = u.role
            if details == "role" :
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
                    if details == "long" and user_begin_time != None:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role} dans le camp {user_side}\nTon action est entre : {user_begin_time} et {user_end_time}\nTon role consiste en :\n {user_descript}"))
                    elif details == "court" and user_begin_time != None:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role} dans le camp {user_side}\nTon action est entre : {user_begin_time} et {user_end_time}\nTon role consiste en :\n {user_short}"))
                    elif details == "long" and user_begin_time == None:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role} dans le camp {user_side}\nTon action n'a pas d'heure\nTon role consiste en :\n {user_descript}"))
                    elif details == "court" and user_begin_time == None:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role} dans le camp {user_side}\nTon action n'a pas d'heure\nTon role consiste en :\n {user_short}"))
                    else :
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role}\nEt utilise les bons arguments (voir !help MonRole pour plus de détails)"))
