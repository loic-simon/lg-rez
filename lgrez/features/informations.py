"""lg-rez / features / Commandes informatives

Commandes donnant aux joueurs des informations sur le jeu, leurs
actions, les joueurs en vie et morts...

"""

from discord.ext import commands

from lgrez import config
from lgrez.blocs import tools
from lgrez.bdd import (Joueur, Role, Camp, Action, BaseAction,
                       ActionTrigger, Vote)


class Informations(commands.Cog):
    """Commandes pour en savoir plus sur soi et les autres"""

    @commands.command(aliases=["role", "rôles", "rôle", "camp", "camps"])
    async def roles(self, ctx, *, filtre=None):
        """Affiche la liste des rôles / des informations sur un rôle

        Args:
            filtre: peut être

                - Le nom d'un camp pour les rôles le composant ;
                - Le nom d'un rôle pour les informations sur ce rôle.

        Sans argument liste tous les rôles existants.
        """
        if filtre:
            filtre = tools.remove_accents(filtre.lower())
            filtre = filtre.strip("<>[](){}")

        if not filtre:
            roles = Role.query.filter_by(actif=True).order_by(Role.nom).all()
        else:
            camps = Camp.find_nearest(
                filtre, col=Camp.nom,
                sensi=0.6, filtre=Camp.public.is_(True)
            )

            if camps:
                roles = camps[0][0].roles
            else:
                roles = Role.find_nearest(filtre, col=Role.nom)
                if not roles:
                    await ctx.send(f"Rôle / camp \"{filtre}\" non trouvé.")
                    return

                await ctx.send(embed=roles[0][0].embed)
                return

        await tools.send_blocs(
            ctx,
            "Rôles trouvés :\n"
            + "\n".join([
                str(role.camp.discord_emoji_or_none or "")
                + tools.code(f"{role.nom.ljust(25)} {role.description_courte}")
                for role in roles if not role.nom.startswith("(")
            ])
            + "\n" + tools.ital(f"({tools.code('!roles <role>')} "
                                "pour plus d'informations sur un rôle.)")
        )


    @commands.command()
    @tools.mjs_only
    async def rolede(self, ctx, *, cible=None):
        """Donne le rôle d'un joueur (COMMANDE MJ)

        Args:
            cible: le joueur dont on veut connaître le rôle
        """
        joueur = await tools.boucle_query_joueur(ctx, cible, "Qui ?")
        if joueur:
            await ctx.send(joueur.role.nom_complet)


    @commands.command()
    @tools.mjs_only
    async def quiest(self, ctx, *, nomrole):
        """Liste les joueurs ayant un rôle donné (COMMANDE MJ)

        Args:
            nomrole: le rôle qu'on cherche (doit être un slug ou un nom
                de rôle valide)
        """
        roles = Role.find_nearest(nomrole)
        if roles:
            role = roles[0][0]
        else:
            roles = Role.find_nearest(nomrole, col=Role.nom)
            if roles:
                role = roles[0][0]
            else:
                await ctx.send("Connais pas")
                return

        joueurs = Joueur.query.filter_by(role=role).\
                               filter(Joueur.est_vivant).all()
        await ctx.send(
            f"{role.nom_complet} : "
            + (", ".join(joueur.nom for joueur in joueurs)
               if joueurs else "Personne.")
        )


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def menu(self, ctx):
        """Affiche des informations et boutons sur les votes / actions en cours

        Le menu a une place beaucoup moins importante ici que sur
        Messenger, vu que tout est accessible par commandes.
        """
        member = ctx.author
        joueur = Joueur.from_member(member)

        reacts = []
        r = "––– MENU –––\n\n"

        vaction = joueur.action_vote(Vote.cond)
        if vaction.is_open:
            r += (f" - {config.Emoji.bucher}  Vote pour le bûcher en cours – "
                  f"vote actuel : {tools.code(vaction.decision)}\n")
            reacts.append(config.Emoji.bucher)

        vaction = joueur.action_vote(Vote.maire)
        if vaction.is_open:
            r += (f" - {config.Emoji.maire}  Vote pour le maire en cours – "
                  f"vote actuel : {tools.code(vaction.decision)}\n")
            reacts.append(config.Emoji.maire)

        vaction = joueur.action_vote(Vote.loups)
        if vaction.is_open:
            r += (f" - {config.Emoji.lune}  Vote des loups en cours – "
                  f"vote actuel : {tools.code(vaction.decision)}\n")
            reacts.append(config.Emoji.lune)

        if not reacts:
            r += "Aucun vote en cours.\n"

        actions = [ac for ac in joueur.actions_actives if ac.is_open]
        if actions:
            for action in actions:
                r += (f" - {config.Emoji.action}  Action en cours : "
                      f"{tools.code(action.base.slug)} (id {action.id}) – "
                      f"décision : {tools.code(action.decision)}\n")
            reacts.append(config.Emoji.action)
        else:
            r += "Aucune action en cours.\n"

        message = await ctx.send(
            r + f"\n{tools.code('!infos')} pour voir ton rôle et tes "
            f"actions, {tools.code('@MJ')} en cas de problème"
        )
        for react in reacts:
            await message.add_reaction(react)


    @commands.command()
    @tools.vivants_only
    @tools.private
    async def infos(self, ctx):
        """Affiche tes informations de rôle / actions

        Toutes les actions liées à ton rôle (et parfois d'autres) sont
        indiquées, même celles que tu ne peux pas utiliser pour
        l'instant (plus de charges, déclenchées automatiquement...)
        """
        member = ctx.author
        joueur = Joueur.from_member(member)
        r = ""

        r += f"Ton rôle actuel : {tools.bold(joueur.role.nom_complet)}\n"
        r += tools.ital(f"({tools.code(f'!roles {joueur.role.slug}')} "
                        "pour tout savoir sur ce rôle)")

        if joueur.actions_actives:
            r += "\n\nActions :"
            r += tools.code_bloc("\n".join((
                f" - {action.base.slug.ljust(20)} "
                + (f"Cooldown : {action.cooldown}" if action.cooldown
                   else action.base.temporalite).ljust(22)
                + (f"   {action.charges} charge(s)"
                    + (" pour cette semaine"
                        if (action.refill and "weekends" in action.refill)
                        else "")
                    if isinstance(action.charges, int) else "Illimitée")
            ) for action in joueur.actions_actives))
            # Vraiment désolé pour cette immondice j'ai la flemme
        else:
            r += "\n\nAucune action disponible."

        await ctx.send(
            f"{r}\n{tools.code('!menu')} pour voir les votes et "
            f"actions en cours, {tools.code('@MJ')} en cas de problème"
        )


    @commands.command()
    @tools.mjs_only
    async def actions(self, ctx, *, cible=None):
        """Affiche et modifie les actions d'un joueur (COMMANDE MJ)

        Args:
            cible: le joueur dont on veut voir ou modifier les actions

        Warning:
            Commande expérimentale, non testée.
        """
        joueur = await tools.boucle_query_joueur(ctx, cible, "Qui ?")
        actions = [ac for ac in joueur.actions if not ac.vote]

        r = f"Rôle : {joueur.role.nom_complet or joueur.role}\n"

        # if not actions:
        #     r += "Aucune action pour ce joueur."
        #     await ctx.send(r)
        #     return

        r += "Actions :"
        r += tools.code_bloc(
            "#️⃣  id   active  baseaction               début"
            "     fin       cd   charges   refill     \n"
            "---------------------------------------------"
            "---------------------------------------------\n"
            + "\n".join([(
                tools.emoji_chiffre(i + 1) + "  "
                + str(action.id).ljust(5)
                + str(action.active).ljust(8)
                + action.base.slug.ljust(25)
                + str(action.base.heure_debut
                      if action.base.trigger_debut == ActionTrigger.temporel
                      else action.base.trigger_debut).ljust(10)
                + str(action.base.heure_fin
                      if action.base.trigger_fin == ActionTrigger.temporel
                      else action.base.trigger_fin).ljust(10)
                + str(action.cooldown).ljust(5)
                + str(action.charges).ljust(10)
                + str(action.base.refill)
            ) for i, action in enumerate(actions)])
        )
        r += "Modifier/ajouter/stop :"
        message = await ctx.send(r)
        i = await tools.choice(message, len(actions),
                               additionnal={"🆕": -1, "⏹": 0})

        if i < 0:     # ajouter
            await ctx.send("Slug de la baseaction à ajouter ? "
                           "(voir Gsheet Rôles et actions)")
            base = await tools.boucle_query(ctx, BaseAction)

            await ctx.send("Cooldown ? (nombre entier)")
            mess = await tools.wait_for_message_here(ctx)
            cooldown = int(mess.content)

            await ctx.send(f"Charges ? ({tools.code('None')} pour illimité)")
            mess = await tools.wait_for_message_here(ctx)
            charges = int(mess.content) if mess.content.isdigit() else None

            action = Action(joueur=joueur, base=base, cooldown=cooldown,
                            charges=charges)
            action.add()
            await ctx.send(f"Action ajoutée (id {action.id}).")
            return

        elif i == 0:
            await ctx.send("Au revoir.")
            return

        # Modifier
        action = actions[i - 1]
        stop = False
        while not stop:
            await ctx.send(
                "Modifier : (parmi `active, cd, charges`}) ; `valider` pour "
                "finir ; `supprimer` pour supprimer l'action.\n(Pour modifier "
                "les attributs de la baseaction, modifier le Gsheet et "
                "utiliser `!fillroles` ; pour ouvrir/fermer l'action, "
                f"utiliser `!open {action.id}` / `!close {action.id}`.)"
            )
            mess = await tools.wait_for_message_here(ctx)
            modif = mess.content.lower()

            if modif == "active":
                mess = await ctx.send("Action active ?")
                action.active = await tools.yes_no(mess)

            elif modif in ["cd", "cooldown"]:
                await ctx.send("Combien ?")
                mess = await tools.wait_for_message_here(ctx)
                action.cooldown = int(mess.content)

            elif modif == "charges":
                await ctx.send("Combien ? (`None` pour illimité)")
                mess = await tools.wait_for_message_here(ctx)
                action.charges = (int(mess.content)
                                  if mess.content.isdigit() else None)

            elif modif == "valider":
                action.update()
                await ctx.send("Fait.")
                stop = True

            elif modif == "supprimer":
                mess = await ctx.send("Supprimer l'action ? (privilégier "
                                      "l'archivage  `active = False`)")
                if await tools.yes_no(mess):
                    action.delete()
                    await ctx.send("Fait.")
                    stop = True

            else:
                await ctx.send("Valeur incorrecte")


    @commands.command(aliases=["joueurs", "vivant"])
    async def vivants(self, ctx):
        """Affiche la liste des joueurs vivants

        Aussi dite : « liste des joueurs qui seront bientôt morts »
        """
        joueurs = Joueur.query.filter(Joueur.est_vivant).\
                               order_by(Joueur.nom).all()

        mess = " Joueur                     en chambre\n"
        mess += "––––––––––––––––––––––––––––––––––––––––––––––\n"
        if config.demande_chambre:
            for joueur in joueurs:
                mess += f" {joueur.nom.ljust(25)}  {joueur.chambre}\n"
        else:
            for joueur in joueurs:
                mess += f" {joueur.nom}\n"

        await tools.send_code_blocs(
            ctx, mess, prefixe=f"Les {len(joueurs)} joueurs vivants sont :"
        )


    @commands.command(aliases=["mort"])
    async def morts(self, ctx):
        """Affiche la liste des joueurs morts

        Aussi dite : « liste des joueurs qui mangent leurs morts »
        """
        joueurs = Joueur.query.filter(Joueur.est_mort).\
                               order_by(Joueur.nom).all()

        if joueurs:
            mess = ""
            for joueur in joueurs:
                mess += f" {joueur.nom}\n"
        else:
            mess = "Toi (mais tu ne le sais pas encore)"

        await tools.send_code_blocs(
            ctx, mess, prefixe=f"Les {len(joueurs) or ''} morts sont :"
        )
