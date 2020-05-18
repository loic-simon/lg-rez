from discord.ext import commands
import tools
from bdd_connect import db, cache_TDB

class Annexe(commands.Cog):
    """Annexe : commandes annexes aux usages divers"""

    @commands.command()
    @commands.has_role("MJ")
    async def test(self, ctx, *, arg):
        """Test : test !"""

        # arg = tools.command_arg(ctx)    # Arguments de la commande (sans le !test) --> en fait c'est faisable nativement, zrtYes
        auteur = ctx.author.display_name
        salon = ctx.channel.name if hasattr(ctx.channel, "name") else f"DMChannel de {ctx.channel.recipient.name}"
        serveur = ctx.guild.name if hasattr(ctx.guild, "name") else "(DM)"
        # pref = ctx.prefix
        # com = ctx.command
        # ivkw = ctx.invoked_with

        await tools.log(ctx, "Alors, ça log ?")

        await ctx.send(tools.code_bloc(
            f"arg = {arg}\n"
            f"auteur = {auteur}\n"
            f"salon = {salon}\n"
            f"serveur = {serveur}"
        ))


    @commands.command()
    @commands.has_role("MJ")
    async def testbdd(self, ctx):
        """Test BDD"""

        tous = cache_TDB.query.all()
        ret = '\n - '.join([u.nom for u in tous])
        await ctx.send(tools.code_bloc(f"Liste des joueurs :\n - {ret}"))


    @commands.command()
    @commands.has_role("MJ")
    async def rename(self, ctx, id: int, nom: str):
        """Renommer quelqu'un à partir de son ID"""

        try:
            u = cache_TDB.query.filter_by(messenger_user_id=id).one()
        except:
            await ctx.send(tools.code_bloc(f"Cible {id} non trouvée\n{traceback.format_exc()}"))
        else:
            oldnom = u.nom
            u.nom = nom
            db.session.commit()
            await ctx.send(tools.code_bloc(f"Joueur {oldnom} renommé en {nom}."))


    @commands.command()
    async def roles(self, ctx, nom_camp = "all") :
        """Affiche la liste des rôles,
        L'option nom_camp permet de lister les rôles d'un camp spécifique
        Valeurs possibles pour nom_camp : all, Loups, Villageois, Solitaire, Nécros""" #création de la BDD role dans models.py
        if nom_camp == "all" :
            tous = role_BDD.query.all()
            ret = '\n - '.join([r.nom_du_role for r in tous])
        elif nom_camp == "Loups" :
            liste = role_BDD.query.filter_by(camp="Loups")
            ret = '\n - '.join([r.nom_du_role for r in liste])
        elif nom_camp == "Villageois" :
            liste = role_BDD.query.filter_by(camp="Villageois")
            ret = '\n - '.join([r.nom_du_role for r in liste])
        elif nom_camp == "Solitaire" :
            liste = role_BDD.query.filter_by(camp="Solitaire")
            ret = '\n - '.join([r.nom_du_role for r in liste])
        elif nom_camp == "Nécros" :
            liste = role_BDD.query.filter_by(camp="Nécros")
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
            u = cache_TDB.query.filter_by(nom = nom_user).one()
        except :
            await ctx.send(tools.code_bloc(f"Le joueur {nom_user} n'a pas été trouvé\n{traceback.format_exc()}"))
        else :
            user_role = u.role
            if Details == "role" :
                await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role}"))
            else :
                try :
                    r = role_BDD.query.filter_by(role = user_role).one()
                except :
                    await ctx.send(tools.code_bloc(f"Votre rôle : {user_role} n'existe pas\n{traceback.format_exc()}"))
                else :
                    user_begin_time = r.horaire_debut
                    user_end_time = r.horaire_fin
                    user_side = r.camp
                    user_descript = r.description_longue
                    user_short = r.description_courte
                    if Details == "long" AND user_begin_time != None:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role} dans le camp {user_side}\nTon action est entre : {user_begin_time} et {user_end_time}\nTon role consiste en :\n {user_descript}"))
                    elif Details == "court" AND user_begin_time != None:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role} dans le camp {user_side}\nTon action est entre : {user_begin_time} et {user_end_time}\nTon role consiste en :\n {user_short}"))
                    elif Details == "long" AND user_begin_time == None:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role} dans le camp {user_side}\nTon action n'a pas d'heure\nTon role consiste en :\n {user_descript}"))
                    elif Details == "court" AND user_begin_time == None:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role} dans le camp {user_side}\nTon action n'a pas d'heure\nTon role consiste en :\n {user_short}"))
                    else :
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role}\nEt utilise les bons arguments (voir !help MonRole pour plus de détails)"))
