import traceback
import unidecode

from discord.ext import commands

from bdd_connect import db, Joueurs, Roles, Actions, BaseActions
from blocs import bdd_tools
import tools
from blocs import bdd_tools

def emoji_camp(arg, camp):
    """Renvoie l'emoji associé à <camp>

    <arg> peut être de type Context, Guild, User/Member, Channel
    """
    d = {"village": "village",
         "loups": "lune",
         "nécro": "necro",
         "solitaire": "pion",
         "autre": "pion"}
    if camp in d:
        return tools.emoji(arg, d[camp])
    else:
        return ""


class Informations(commands.Cog):
    """Informations - Commandes disponibles pour en savoir plus sur soi et les autres"""

    @commands.command(aliases=["role", "rôles", "rôle"])
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
            await ctx.send(tools.code_bloc(f"{role.prefixe}{role.nom} – {role.description_courte} (camp : {role.camp})\n\n{role.description_longue}"))
            return

        await tools.send_blocs(ctx,
            f"Rôles trouvés :\n"
            + "\n".join([str(emoji_camp(ctx, role.camp)) + tools.code(f"{role.nom.ljust(25)} {role.description_courte}") for role in roles if not role.nom.startswith("(")])
            + "\n" + tools.ital(f"({tools.code('!roles <role>')} pour plus d'informations sur un rôle.)")
        )


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def menu(self, ctx):
        """Affiche des informations et boutons sur les votes / actions en cours

        Le menu a une place beaucoup moins importante ici que sur Messenger, vu que tout est accessible par commandes.
        """
        member = ctx.author
        joueur = Joueurs.query.get(member.id)
        assert joueur, f"!menu : joueur {member} introuvable"

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
    @tools.vivants_only
    @tools.private
    async def infos(self, ctx):
        """Affiche tes informations de rôle / actions

        Tout est dit, pas de vanne
        """
        member = ctx.author
        joueur = Joueurs.query.get(member.id)
        assert joueur, f"!menu : joueur {member} introuvable"
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


    @commands.command()
    async def vivants(self, ctx):
        """Affiche la liste des joueurs vivants"""

        mess = "Les joueurs vivants sont : \n"
        joueurs = [joueur.nom for joueur in Joueurs.query.filter(Joueurs.statut != "mort").order_by(Joueurs.nom)]
        for joueur in joueurs:
            mess += f" - {joueur} \n"
        await tools.send_code_blocs(ctx, mess)


    @commands.command()
    async def morts(self, ctx):
        """Affiche la liste des joueurs morts"""

        mess = "Les morts sont :\n"
        joueurs = [joueur.nom for joueur in Joueurs.query.filter_by(statut = "mort").order_by(Joueurs.nom)]
        if not joueurs:
            mess += "Toi (mais tu ne le sais pas encore)"
        else:
            for joueur in joueurs:
                mess += f" - {joueur} \n"
        await tools.send_code_blocs(ctx, mess)
