"""lg-rez / features / Commandes informatives

Commandes donnant aux joueurs des informations sur le jeu, leurs actions, les joueurs en vie et morts...

"""

import traceback
import unidecode

from discord.ext import commands

from lgrez.blocs import bdd, bdd_tools, tools
from lgrez.blocs.bdd import session, Joueurs, Roles, Actions, BaseActions


class Informations(commands.Cog):
    """Informations - Commandes disponibles pour en savoir plus sur soi et les autres"""

    @commands.command(aliases=["role", "rôles", "rôle", "camp", "camps"])
    async def roles(self, ctx, *, filtre=None):
        """Affiche la liste des rôles / des informations sur un rôle

        Args:
            filtre: peut être

                - "Villageois", "Loups", "Nécros", "Autres" pour les rôles d'un camp ;
                - Un nom de rôle pour les informations sur ce rôle.

        Sans argument liste tous les rôles existants.
        """
        if filtre:
            filtre = tools.remove_accents(filtre.lower())

        if not filtre:
            roles = Roles.query.order_by(Roles.nom).all()
        elif filtre in ("villageois", "village", "<villageois>", "<village>"):
            roles = Roles.query.filter_by(camp="village").all()
        elif filtre in ("loups", "<loups>"):
            roles = Roles.query.filter_by(camp="loups").all()
        elif filtre in ("necros", "<necros>"):
            roles = Roles.query.filter_by(camp="nécro").all()
        elif filtre in ("autres", "solitaires", "<autres>", "<solitaires>"):
            roles = Roles.query.filter_by(camp="solitaire").all()
        elif filtre:
            if role := Roles.query.get(filtre):     # Slug du rôle trouvé direct
                pass
            else:                                   # Sinon, on cherche en base
                roles = bdd_tools.find_nearest(filtre, Roles, carac="nom")
                if roles:
                    role = roles[0][0]
                else:
                    await ctx.send(f"Rôle / camp \"{filtre}\" non trouvé.")
                    return
            await ctx.send(tools.code_bloc(f"{role.prefixe}{role.nom} – {role.description_courte} (camp : {role.camp})\n\n{role.description_longue}"))
            return

        await tools.send_blocs(ctx,
            f"Rôles trouvés :\n"
            + "\n".join([str(tools.emoji_camp(ctx, role.camp)) + tools.code(f"{role.nom.ljust(25)} {role.description_courte}") for role in roles if not role.nom.startswith("(")])
            + "\n" + tools.ital(f"({tools.code('!roles <role>')} pour plus d'informations sur un rôle.)")
        )


    @commands.command()
    @tools.mjs_only
    async def rolede(self, ctx, *, cible):
        """Donne le rôle d'un joueur (COMMANDE MJ)

        Args:
            cible: le joueur dont on veut connaître le rôle
        """
        joueur = await tools.boucle_query_joueur(ctx, cible, "Qui ?")
        if joueur:
            await ctx.send(tools.nom_role(joueur.role, prefixe=True))


    @commands.command()
    @tools.mjs_only
    async def quiest(self, ctx, *, nomrole):
        """Liste les joueurs ayant un rôle donné (COMMANDE MJ)

        Args:
            nomrole: le rôle qu'on cherche (doit être un slug ou nom de rôle valide)
        """
        roles = bdd_tools.find_nearest(tools.remove_accents(nomrole), Roles, carac="slug")
        if roles:
            role = roles[0][0]
        else:
            roles = await bdd_tools.find_nearest(tools.remove_accents(nomrole).capitalize(), Roles, carac="nom")
            if roles:
                role = roles[0][0]
            else:
                await ctx.send("Connais pas")

        joueurs = Joueurs.query.filter_by(role=role.slug).filter(Joueurs.statut.in_(["vivant", "MV"])).all()
        await ctx.send(f"{tools.nom_role(role.slug)} : " + (", ".join(joueur.nom for joueur in joueurs) if joueurs else "Personne."))


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

        if joueur.vote_condamne_:
            r += f" - {tools.emoji(ctx, 'bucher')}  Vote pour le bûcher en cours – vote actuel : {tools.code(joueur.vote_condamne_)}\n"
            reacts.append(tools.emoji(ctx, 'bucher'))
        if joueur.vote_maire_:
            r += f" - {tools.emoji(ctx, 'maire')}  Vote pour le maire en cours – vote actuel : {tools.code(joueur.vote_maire_)}\n"
            reacts.append(tools.emoji(ctx, 'maire'))
        if joueur.vote_loups_:
            r += f" - {tools.emoji(ctx, 'lune')}  Vote des loups en cours – vote actuel : {tools.code(joueur.vote_loups_)}\n"
            reacts.append(tools.emoji(ctx, 'lune'))

        if not reacts:
            r += "Aucun vote en cours.\n"

        actions = Actions.query.filter_by(player_id=member.id).filter(Actions.decision_ != None).all()
        if actions:
            for action in actions:
                r += f" - {tools.emoji(ctx, 'action')}  Action en cours : {tools.code(action.action)} (id {action.id}) – décision : {tools.code(action.decision_)}\n"
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
        assert joueur, f"!infos : joueur {member} introuvable"
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
    @tools.mjs_only
    async def actions(self, ctx, *, cible):
        """Affiche et modifie les actions d'un joueur (COMMANDE MJ)

        Args:
            cible: le joueur dont on veut voir ou modifier les actions
        """
        joueur = await tools.boucle_query_joueur(ctx, cible, "Qui ?")
        if joueur:

            member = ctx.guild.get_member(joueur.discord_id)
            assert member, f"!actions : membre {joueur} introuvable"
            r = ""

            r += f"Rôle : {tools.nom_role(joueur.role) or joueur.role}\n"

            actions = Actions.query.filter_by(player_id=joueur.discord_id).all()

            if actions:
                r += "Actions :"
                r += tools.code_bloc(
                    f"#️⃣  id   action                   début     fin       cd   charges   refill\n"
                    "----------------------------------------------------------------------------------\n"
                    + "\n".join([(tools.emoji_chiffre(i+1) + "  "
                        + str(action.id).ljust(5)
                        + str(action.action).ljust(25)
                        + str(action.heure_debut if action.trigger_debut == "temporel" else action.trigger_debut).ljust(10)
                        + str(action.heure_fin if action.trigger_fin == "temporel" else action.trigger_fin).ljust(10)
                        + str(action.cooldown).ljust(5)
                        + str(action.charges).ljust(10)
                        + str(action.refill)
                    ) for i, action in enumerate(actions)]
                ))
                r += "Modifier/ajouter/stop :"
                message = await ctx.send(r)
                i = await tools.choice(ctx.bot, message, len(actions), additionnal={"⏺": -1, "⏹": 0})
                if i > 0:       # modifier
                    action = actions[i-1]
                    stop = False
                    while not stop:
                        await ctx.send(f"Modifier : (parmis {tools.code('début, fin, cd, charges, refill')})\n{tools.code('valider')} pour finir\n(Utiliser {tools.code('!open id')}/{tools.code('!close id')} pour ouvrir/fermer)")
                        modif = (await tools.wait_for_message_here(ctx)).content.lower()

                        if modif in ["début", "fin"]:
                            await ctx.send(f"Trigger (parmis {tools.code('temporel, delta, perma, start, auto, mort, mot_mjs, {open|close|remind}_{cond|maire|loups}')}) ou heure direct si {tools.code('temporel')} :")
                            trigger = (await tools.wait_for_message_here(ctx)).content.lower()
                            heure = None
                            if ":" in trigger or "h" in trigger:
                                heure = trigger
                                trigger = "temporel"

                            if trigger in ["temporel", "delta"]:
                                if not heure:
                                    await ctx.send(f"Heure / delta {tools.code('HHhMM ou HH:MM')} :")
                                    heure = (await tools.wait_for_message_here(ctx)).content
                                ts = tools.heure_to_time(heure)
                                bdd_tools.modif(action, "trigger_debut" if modif == "début" else "trigger_fin", trigger)
                                bdd_tools.modif(action, "heure_debut" if modif == "début" else "heure_fin", ts)
                            elif trigger in ["perma", "start", "auto", "mot_mjs", "mort"] + [f"{quoi}_{qui}" for quoi in ["open", "close", "remind"] for qui in ["cond", "maire", "loups"]]:
                                bdd_tools.modif(action, "trigger_debut" if modif == "début" else "trigger_fin", trigger)
                                bdd_tools.modif(action, "heure_debut" if modif == "début" else "heure_fin", None)
                            else:
                                await ctx.send("Valeur incorrecte")

                        elif modif in ["cd", "cooldown"]:
                            await ctx.send(f"Combien ?")
                            cd = int((await tools.wait_for_message_here(ctx)).content)
                            bdd_tools.modif(action, "cooldown", cd)

                        elif modif == "charges":
                            await ctx.send(f"Combien ? ({tools.code('None')} pour illimité)")
                            entry = (await tools.wait_for_message_here(ctx)).content
                            charges = None if entry.lower() == "none" else int(entry)
                            bdd_tools.modif(action, "charges", charges)

                        elif modif == "refill":
                            await ctx.send(f"Quoi ? ({tools.code('rebouteux / forgeron / weekends')} séparés par des {tools.code(', ')})")
                            refill = (await tools.wait_for_message_here(ctx)).content.lower()
                            bdd_tools.modif(action, "refill", refill)

                        elif modif == "valider":
                            bdd.session.commit()
                            await ctx.send("Fait.")

                        else:
                            await ctx.send("Valeur incorrecte")

                elif i < 0:     # ajouter
                    await ctx.send("Pas encore codé, pas de chance")

            else:
                r += "Aucune action pour ce joueur."
                await ctx.send(r)



    @commands.command(aliases=["joueurs", "vivant"])
    async def vivants(self, ctx):
        """Affiche la liste des joueurs vivants

        Aussi dite : « liste des joueurs qui seront bientôt morts »
        """
        joueurs = [joueur for joueur in Joueurs.query.filter(Joueurs.statut != "mort").order_by(Joueurs.nom)]

        mess = f" Joueur                     en chambre\n"
        mess += f"––––––––––––––––––––––––––––––––––––––––––––––\n"
        if ctx.bot.config.get("demande_chambre", True):
            for joueur in joueurs:
                mess += f" {joueur.nom.ljust(25)}  {joueur.chambre}\n"
        else:
            for joueur in joueurs:
                mess += f" {joueur.nom}\n"

        await tools.send_code_blocs(ctx, mess, prefixe=f"Les {len(joueurs)} joueurs vivants sont :")


    @commands.command(aliases=["mort"])
    async def morts(self, ctx):
        """Affiche la liste des joueurs morts

        Aussi dite : « liste des joueurs qui mangent leurs morts »
        """
        joueurs = [joueur for joueur in Joueurs.query.filter_by(statut="mort").order_by(Joueurs.nom)]

        if joueurs:
            mess = ""
            for joueur in joueurs:
                mess += f" {joueur.nom}\n"
        else:
            mess = "Toi (mais tu ne le sais pas encore)"

        await tools.send_code_blocs(ctx, mess, prefixe=f"Les {len(joueurs) or ''} morts sont :")
