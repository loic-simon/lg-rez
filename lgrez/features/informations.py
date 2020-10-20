import traceback
import unidecode

from discord.ext import commands

from lgrez.blocs import bdd_tools, tools
from lgrez.blocs.bdd import session, Joueurs, Roles, Actions, BaseActions


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

    @commands.command(aliases=["role", "rôles", "rôle", "camp", "camps"])
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
        elif filtre.startswith("villag"):
            roles = Roles.query.filter_by(camp="village").all()
        elif filtre.startswith("loup"):
            roles = Roles.query.filter_by(camp="loups").all()
        elif filtre.startswith("necro"):
            roles = Roles.query.filter_by(camp="nécro").all()
        elif filtre.startswith("autre") or filtre.startswith("solitaire"):
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

        Toutes les actions liées à ton rôle (et parfois d'autres) sont indiquées, même celles que tu ne peux pas utiliser pour l'instant (plus de charges, déclenchées automatiquement...)
        """
        def disponible(action):
            """Renvoie une description human readible des conditions de déclenchement d'<action>"""
            if action.trigger_debut == "temporel":
                dispo = f"De {tools.time_to_heure(action.heure_debut)} à {tools.time_to_heure(action.heure_fin)}"
            elif action.trigger_debut == "perma":
                dispo = f"N'importe quand"
            elif action.trigger_debut == "start":
                dispo = f"Au lancement de la partie"
            elif action.trigger_debut == "mort":
                dispo = f"S'active à ta mort"
            elif action.trigger_debut == "mot_mjs":
                dispo = f"S'active à l'annonce des résultats du vote"
            elif "_" in action.trigger_debut:
                quoi, qui = action.trigger_debut.split("_")
                d_quoi = {"open": "l'ouverture",
                          "close": "la fermeture",
                          "remind": "personne utilise ça",
                }
                d_qui = {"cond": "du vote condamné",
                         "maire": "du vote pour la mairie",
                         "loups": "du vote pour les loups",
                         "action": "personne utilise ça",
                }
                try:
                    dispo = f"S'active à {d_quoi[quoi]} {d_qui[qui]}"
                except KeyError:
                    dispo = f"S'active à {quoi}_{qui}"
            else:
                dispo = action.trigger_debut

            return dispo


        member = ctx.author
        joueur = Joueurs.query.get(member.id)
        assert joueur, f"!menu : joueur {member} introuvable"
        r = ""

        r += f"Ton rôle actuel : {tools.bold(tools.nom_role(joueur.role) or joueur.role)}\n"
        r += tools.ital(f"({tools.code(f'!roles {joueur.role}')} pour tout savoir sur ce rôle)")

        actions = Actions.query.filter_by(player_id=member.id).all()

        if actions:
            r += "\n\nActions :"
            r += tools.code_bloc("\n".join([(
                f" - {str(action.action).ljust(20)} "
                + (f"Cooldown : {cooldown}" if (cooldown := action.cooldown) else disponible(action)).ljust(22)
                + (f"   {action.charges} charge(s){' pour cette semaine' if (action.refill and 'weekends' in action.refill) else ''}" if isinstance(action.charges, int) else "Illimitée")     # Vraiment désolé pour cette immondice
                ) for action in actions]
            ))
        else:
            r += "\n\nAucune action disponible."

        await ctx.send(r + f"\n{tools.code('!menu')} pour voir les votes et actions en cours, {tools.code('@MJ')} en cas de problème")



    @commands.command()
    async def vivants(self, ctx):
        """Affiche la liste des joueurs vivants

        Aussi dite : « liste des joueurs qui seront bientôt morts »
        """
        mess = "Les joueurs vivants sont : \n"
        joueurs = [joueur for joueur in Joueurs.query.filter(Joueurs.statut != "mort").order_by(Joueurs.nom)]
        for joueur in joueurs:
            mess += f" - {joueur.nom.ljust(15)} en chambre {joueur.chambre}\n"
        await tools.send_code_blocs(ctx, mess)


    @commands.command()
    async def morts(self, ctx):
        """Affiche la liste des joueurs morts

        Aussi dite : « liste des joueurs qui mangent leurs morts »
        """
        mess = "Les morts sont :\n"
        joueurs = [joueur.nom for joueur in Joueurs.query.filter_by(statut = "mort").order_by(Joueurs.nom)]
        if not joueurs:
            mess += "Toi (mais tu ne le sais pas encore)"
        else:
            for joueur in joueurs:
                mess += f" - {joueur} \n"
        await tools.send_code_blocs(ctx, mess)
