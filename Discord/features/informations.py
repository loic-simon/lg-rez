import traceback
import unidecode

from discord.ext import commands

from bdd_connect import db, Joueurs, Roles, Actions, BaseActions
from blocs import bdd_tools
import tools


def emoji_camp(arg, camp):
    d = {"village": "village",
         "loups": "lune",
         "nécro": "necro",
         "solitaire": "pion",
         "autre": "pion"}
    if camp in d:
        return str(tools.emoji(arg, d[camp]))
    else:
        return ""


class Informations(commands.Cog):
    """Informations - Commandes disponibles pour s'informer sur les rôles"""

    @commands.command(aliases=["role"])
    async def roles(self, ctx, *, filtre=None):
        """Affiche la liste des rôles / des informations sur un rôle

        [filtre] peut être
            - Villageois, Loups, Nécros, Autres pour les rôles d'un camp ;
            - Un nom de rôle pour les informations sur ce rôle.
        Si [filtre] n'est pas précisé, liste tous les rôles existants.
        """
        if filtre:
            filtre = tools.remove_accents(filtre.lower())

        if not filtre:
            roles = Roles.query.order_by(Roles.nom).all()
        elif "villag" in filtre:
            roles = Roles.query.filter_by(camp="village").all()
        elif "loup" in filtre:
            roles = Roles.query.filter_by(camp="loups").all()
        elif "necro" in filtre:
            roles = Roles.query.filter_by(camp="nécro").all()
        elif "autre" in filtre:
            roles = Roles.query.filter_by(camp="solitaire").all()
        elif filtre:
            if role := Roles.query.get(filtre):     # Slug du rôle trouvé direct
                pass
            else:                                   # Sinon, on cherche en base
                roles = await bdd_tools.find_nearest(filtre, Roles, carac="nom")
                if roles:
                    role = roles[0][0]
                else:
                    await ctx.send(f"Rôle / camp \"{filtre}\" non trouvé.")
                    return
            await ctx.send(tools.code_bloc(f"{role.prefixe}{role.nom} – {role.description_courte}\n\n{role.description_longue}"))
            return

        await tools.send_blocs(ctx,
            f"Rôles trouvés :\n"
            + "\n".join([emoji_camp(ctx, role.camp) + tools.code(f"{role.nom.ljust(25)} {role.description_courte}") for role in roles if not role.nom.startswith("(")])
            + "\n" + tools.ital(f"({tools.code('!roles <role>')} pour plus d'informations sur un rôle.)")
        )


    @commands.command()
    async def menu(self, ctx):
        """Affiche des informations et boutons sur les votes / actions en cours

        Le menu a une place beaucoup moins importante ici que sur Messenger, vu que tout est accessible par commandes.
        """
        member = ctx.author
        joueur = Joueurs.query.get(member.id)
        reacts = []
        r = "––– MENU –––\n\n"

        if joueur._vote_condamne:
            r += f" - {tools.emoji(ctx, 'bucher')}  Vote pour le bûcher en cours – vote actuel : {tools.code(joueur._vote_condamne)}\n"
            reacts.append(tools.emoji(ctx, 'bucher'))
        if joueur._vote_maire:
            r += f" - {tools.emoji(ctx, 'maire')}  Vote pour le maire en cours – vote actuel : {tools.code(joueur._vote_maire)}\n"
            reacts.append(tools.emoji(ctx, 'maire'))
        if joueur._vote_loups:
            r += f" - {tools.emoji(ctx, 'lune')}  Vote des loups en cours – vote actuel : {tools.code(joueur._vote_loups)}\n"
            reacts.append(tools.emoji(ctx, 'lune'))

        if not reacts:
            r += "Aucun vote en cours.\n"

        actions = Actions.query.filter_by(player_id=member.id).filter(Actions._decision != None).all()
        if actions:
            for action in actions:
                r += f" - {tools.emoji(ctx, 'action')}  Action en cours : {tools.code(action.action)} (id {action.id}) – décision : {tools.code(action._decision)}\n"
            reacts.append(tools.emoji(ctx, 'action'))
        else:
            r += "Aucune action en cours.\n"

        message = await ctx.send(r + f"\n{tools.code('!infos')} pour voir ton rôle et tes actions, {tools.code('@MJ')} en cas de problème")
        for react in reacts:
            await message.add_reaction(react)


    @commands.command()
    async def infos(self, ctx):
        """Affiche tes informations de rôle / actions

        Tout est dit, pas de vanne
        """
        member = ctx.author
        joueur = Joueurs.query.get(member.id)
        r = ""

        r += f"Ton rôle actuel : {tools.bold(tools.nom_role(joueur.role) or joueur.role)}\n"
        r += tools.ital(f"({tools.code(f'!roles {joueur.role}')} pour tout savoir sur ce rôle)")

        actions = Actions.query.filter_by(player_id=member.id).all()
        if actions:
            r += "\n\nActions :"
            r += tools.code_bloc("\n".join([
                f" - {str(action.action).ljust(20)} "
                + (f"Cooldown : {cooldown}  " if (cooldown := action.cooldown) else "Disponible     ")
                + (f"{charges} charge(s){' pour cette semaine' if 'weekends' in action.refill else ''}" if (charges := action.charges) else "Illimitée")
                for action in actions]
            ))
        else:
            r += "\n\nAucune action disponible."

        await ctx.send(r + f"\n{tools.code('!menu')} pour voir les votes et actions en cours, {tools.code('@MJ')} en cas de problème")


    @commands.command(enabled=False)
    async def monrole(self, ctx, details="court") :
        """Affiche les informations du rôle du joueur

        L'option details permet d'avoir plus ou moins d'infos, elle est facultative
        Valeurs possibles pour details : None, court, long, role
        """
        nom_user = ctx.author.display_name
        try:
            u = Joueurs.query.filter_by(nom = nom_user).one()
        except:
            await ctx.send(tools.code_bloc(f"Le joueur {nom_user} n'a pas été trouvé\n{traceback.format_exc()}"))
        else:
            user_role = u.role
            if details == "role" :
                await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role}"))
            else:
                try:
                    r = Roles.query.filter_by(role = user_role).one()
                except:
                    await ctx.send(tools.code_bloc(f"Votre rôle : {user_role} n'existe pas\n{traceback.format_exc()}"))
                else:
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
                    else:
                        await ctx.send(tools.code_bloc(f"Bonjour {nom_user} !\n Ton rôle : {user_role}\nEt utilise les bons arguments (voir !help MonRole pour plus de détails)"))
