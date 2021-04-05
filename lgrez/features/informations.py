"""lg-rez / features / Commandes informatives

Commandes donnant aux joueurs des informations sur le jeu, leurs
actions, les joueurs en vie et morts...

"""

from discord.ext import commands

from lgrez import config
from lgrez.blocs import tools
from lgrez.bdd import Joueur, Role, Camp, ActionTrigger, Vote


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
            roles = Role.query.order_by(Role.nom).all()
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

                role = roles[0][0]
                await ctx.send(tools.code_bloc(
                    f"{role.prefixe}{role.nom} – {role.description_courte} "
                    f"(camp : {role.camp.nom})\n\n{role.description_longue}"
                ))
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
        def disponible(action):
            """Description des conditions de déclenchement d'<action>"""
            if action.base.trigger_debut == ActionTrigger.temporel:
                dispo = (f"De {tools.time_to_heure(action.base.heure_debut)} "
                         f"à {tools.time_to_heure(action.base.heure_fin)}")
            elif action.base.trigger_debut == ActionTrigger.perma:
                dispo = "N'importe quand"
            elif action.base.trigger_debut == ActionTrigger.start:
                dispo = "Au lancement de la partie"
            elif action.base.trigger_debut == ActionTrigger.mort:
                dispo = "S'active à ta mort"
            elif action.base.trigger_debut == ActionTrigger.mot_mjs:
                dispo = "S'active à l'annonce des résultats du vote"
            elif "_" in (name := action.base.trigger_debut.name):
                quoi, qui = name.split("_")
                d_quoi = {"open": "l'ouverture",
                          "close": "la fermeture"}
                d_qui = {"cond": "du vote condamné",
                         "maire": "du vote pour la mairie",
                         "loups": "du vote pour les loups"}
                try:
                    dispo = f"S'active à {d_quoi[quoi]} {d_qui[qui]}"
                except KeyError:
                    dispo = f"S'active à {quoi}_{qui}"
            else:
                dispo = action.base.trigger_debut.name

            return dispo


        member = ctx.author
        joueur = Joueur.from_member(member)
        r = ""

        r += f"Ton rôle actuel : {tools.bold(joueur.role.nom_complet)}\n"
        r += tools.ital(f"({tools.code(f'!roles {joueur.role.slug}')} "
                        "pour tout savoir sur ce rôle)")

        if joueur.actions_actives:
            r += "\n\nActions :"
            r += tools.code_bloc("\n".join([(
                f" - {action.base.slug.ljust(20)} "
                + (f"Cooldown : {action.cooldown}" if action.cooldown
                   else disponible(action)).ljust(22)
                + (f"   {action.charges} charge(s)"
                    + (" pour cette semaine"
                        if (action.refill and "weekends" in action.refill)
                        else "")
                    if isinstance(action.charges, int) else "Illimitée")
            ) for action in joueur.actions_actives]))
            # Vraiment désolé pour cette immondice j'ai la flemme
        else:
            r += "\n\nAucune action disponible."

        await ctx.send(
            f"{r}\n{tools.code('!menu')} pour voir les votes et "
            f"actions en cours, {tools.code('@MJ')} en cas de problème"
        )


    @commands.command()
    @tools.mjs_only
    async def actions(self, ctx, *, cible):
        """Affiche et modifie les actions d'un joueur (COMMANDE MJ)

        Args:
            cible: le joueur dont on veut voir ou modifier les actions

        Warning:
            Commande expérimentale, non testée.
        """
        joueur = await tools.boucle_query_joueur(ctx, cible, "Qui ?")
        actions = [ac for ac in joueur.actions if not ac.vote]

        r = f"Rôle : {joueur.role.nom_complet or joueur.role}\n"

        if not actions:
            r += "Aucune action pour ce joueur."
            await ctx.send(r)
            return

        r += "Actions :"
        r += tools.code_bloc(
            "#️⃣  id   active  action                   début"
            "     fin       cd   charges   refill     \n"
            "-----------------------------------------"
            "-----------------------------------------\n"
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
                + str(action.refill)
            ) for i, action in enumerate(actions)])
        )
        r += "Modifier/ajouter/stop :"
        message = await ctx.send(r)
        i = await tools.choice(message, len(actions),
                               additionnal={"⏺": -1, "⏹": 0})

        if i < 0:     # ajouter
            await ctx.send("Pas encore codé, pas de chance")
            return

        elif i == 0:
            await ctx.send("Au revoir.")
            return

        # Modifier
        action = actions[i - 1]
        stop = False
        while not stop:
            await ctx.send(
                "Modifier : (parmi "
                + tools.code("début, fin, cd, charges, refill")
                + f")\n{tools.code('valider')} pour finir\n"
                + f"(Utiliser {tools.code('!open id')}/"
                + f"{tools.code('!close id')} pour ouvrir/fermer)"
            )
            modif = (await tools.wait_for_message_here(ctx)).content.lower()

            if modif in ["début", "fin"]:
                trigs = ", ".join(at.name for at in ActionTrigger)
                await ctx.send(
                    f"Trigger (parmi {tools.code(trigs)}) ou heure direct "
                    f"si {tools.code(ActionTrigger.temporel.name)} :"
                )
                mess = await tools.wait_for_message_here(ctx)
                trigger = mess.content.lower()
                heure = None
                if ":" in trigger or "h" in trigger:
                    heure = trigger
                    trigger = ActionTrigger.temporel
                else:
                    try:
                        trigger = ActionTrigger(trigger)
                    except ValueError:
                        await ctx.send("Valeur incorrecte")

                if trigger in [ActionTrigger.temporel, ActionTrigger.delta]:
                    if not heure:
                        await ctx.send(
                            f"Heure / delta {tools.code('HHhMM ou HH:MM')} :"
                        )
                        mess = await tools.wait_for_message_here(ctx)
                        heure = mess.content
                    ts = tools.heure_to_time(heure)
                else:
                    ts = None

                if modif == "début":
                    action.base.trigger_debut = trigger
                    action.base.heure_debut = ts
                else:
                    action.base.trigger_fin = trigger
                    action.base.heure_fin = ts

            elif modif in ["cd", "cooldown"]:
                await ctx.send("Combien ?")
                cd = int((await tools.wait_for_message_here(ctx)).content)
                action.cooldown = cd

            elif modif == "charges":
                await ctx.send(
                    f"Combien ? ({tools.code('None')} pour illimité)"
                )
                entry = (await tools.wait_for_message_here(ctx)).content
                charges = None if entry.lower() == "none" else int(entry)
                action.charges = charges

            elif modif == "refill":
                await ctx.send(
                    f"Quoi ? ({tools.code('rebouteux / forgeron / weekends')} "
                    f"séparés par des {tools.code(', ')})"
                )
                mess = await tools.wait_for_message_here(ctx)
                refill = mess.content.lower()
                action.refill = refill

            elif modif == "valider":
                config.session.commit()
                await ctx.send("Fait.")

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
