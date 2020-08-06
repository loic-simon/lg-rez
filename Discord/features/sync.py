import json
import traceback

from discord.ext import commands
import tools
from bdd_connect import db, Joueurs, Actions, BaseActions, BaseActionsRoles, Taches
from blocs import bdd_tools
from features import gestion_actions


class Sync(commands.Cog):
    """Sync - Commandes de synchronisation des GSheets vers la BDD et les joueurs"""

    @commands.command()
    @tools.mjs_only
    async def sync(self, ctx, silent, *, serial):
        """Applique les modifications lors d'un appel du Tableau de bord (COMMANDE BOT)

        <silent> prend les valeurs "False" (les joueurs sont notifiés si leur statut est modifié) ou "True" (les joueurs ne sont pas notifiés)
        <serial> est un dictionnaire de dictionnaires contenant les données à modifier, sérialisé en JSON sous la forme {"discord_id": {"attribut_modifié":"valeur_attribut"}}

        Cette commande va modifier toutes les colonnes de la BDD Joueurs nécessaires, et appliquer les modificatons dans Discord le cas échéant : renommage des utilisateurs, modification des rôles...

        CETTE COMMANDE EST UTILISÉE POUR LA SYNCHRONISATION UNIQUEMENT (APPEL WEBHOOK)
        ELLE N'EST PAS CONÇUE POUR ÊTRE UTILISÉE À LA MAIN
        """
        try:
            dic = json.loads(serial)                # Désérialisation JSON en dictionnaire Python
            silent = (silent == "True")
            changelog = f"Synchronisation TDB (silencieux = {silent}) :"

            for joueur_id in dic:               # Joueurs dont au moins un attribut a été modifié
                joueur = Joueurs.query.get(int(joueur_id))
                assert joueur, f"!sync : joueur d'ID {joueur_id} introuvable"

                member = ctx.guild.get_member(joueur.discord_id)
                assert member, f"!sync : member {joueur} introuvable"

                chan = ctx.guild.get_channel(joueur._chan_id)
                assert chan, f"!sync : chan privé de {member} introuvable"

                changelog += f"\n- {member.display_name} (@{member.name}#{member.discriminator}) :\n"
                notif = ""

                for col, val in dic[joueur_id].items():
                    changelog += f"    - {col} : {val}\n"

                    if col == "nom":                            # Renommage joueur
                        await chan.edit(name=f"conv-bot-{val}")
                        await member.edit(nick=val)
                        if not silent:
                            notif += f":arrow_forward: Tu t'appelles maintenant {tools.bold(val)}.\n"

                    elif col == "chambre" and not silent:       # Modification chambre
                        notif += f":arrow_forward: Tu habites maintenant en chambre {tools.bold(val)}.\n"

                    elif col == "statut":
                        if val == "vivant":                     # Statut = vivant
                            await member.add_roles(tools.role(ctx, "Joueur en vie"))
                            await member.remove_roles(tools.role(ctx, "Joueur mort"))
                            if not silent:
                                notif += f":arrow_forward: Tu es maintenant en vie. EN VIE !!!\n"

                        elif val == "mort":                     # Statut = mort
                            await member.add_roles(tools.role(ctx, "Joueur mort"))
                            await member.remove_roles(tools.role(ctx, "Joueur en vie"))
                            if not silent:
                                notif += f":arrow_forward: Tu es malheureusement décédé(e) :cry:\nÇa arrive même aux meilleurs, en espérant que ta mort ait été belle !\n"
                            # Actions à la mort
                            for action in Actions.query.filter_by(player_id=joueur.discord_id, trigger_debut="mort"):
                                await gestion_actions.open_action(ctx, action, chan)

                        elif val == "MV":                       # Statut = MV
                            await member.add_roles(tools.role(ctx, "Joueur en vie"))
                            await member.remove_roles(tools.role(ctx, "Joueur mort"))
                            if not silent:
                                notif += f":arrow_forward: Te voilà maintenant réduit(e) au statut de mort-vivant... Un MJ viendra te voir très vite, si ce n'est déjà fait, mais retient que la partie n'est pas finie pour toi !\n"

                        elif not silent:                        # Statut = autre
                            notif += f":arrow_forward: Nouveau statut : {tools.bold(val)} !\n"

                    elif col == "role":                         # Modification rôle
                        old_bars = BaseActionsRoles.query.filter_by(role=joueur.role).all()
                        old_actions = []
                        for bar in old_bars:
                            old_actions.extend(Actions.query.filter_by(action=bar.action, player_id=joueur.discord_id).all())
                        for action in old_actions:
                            gestion_actions.delete_action(ctx, action)  # On supprime les anciennes actions de rôle (et les tâches si il y en a)

                        new_bars = BaseActionsRoles.query.filter_by(role=val).all()         # Actions associées au nouveau rôle
                        new_bas = [BaseActions.query.get(bar.action) for bar in new_bars]   # Nouvelles BaseActions
                        cols = [col for col in bdd_tools.get_cols(BaseActions) if not col.startswith("base")]
                        new_actions = [Actions(player_id=joueur.discord_id, **{col: getattr(ba, col) for col in cols},
                                               cooldown=0, charges=ba.base_charges) for ba in new_bas]
                        await tools.log(ctx, str(new_actions))

                        for action in new_actions:
                            gestion_actions.add_action(ctx, action)     # Ajout et création des tâches si trigger temporel

                        role = tools.nom_role(val)
                        if not role:        # role <val> pas en base : Error!
                            role = f"« {val} »"
                            await tools.log(ctx, f"{tools.mention_MJ(ctx)} ALED : rôle \"{val}\" attribué à {joueur.nom} inconnu en base !")
                        if not silent:
                            notif += f":arrow_forward: Ton nouveau rôle, si tu l'acceptes : {tools.bold(role)} !\nQue ce soit pour un jour ou pour le reste de la partie, renseigne toi en tapant {tools.code(f'!roles {val}')}.\n"

                    elif col == "camp" and not silent:          # Modification camp
                        notif += f":arrow_forward: Tu fais maintenant partie du camp « {tools.bold(val)} ».\n"

                    elif col == "votant_village" and not silent:
                        if val:                                 # votant_village = True
                            notif += f":arrow_forward: Tu peux maintenant participer aux votes du village !\n"
                        else:                                   # votant_village = False
                            notif += f":arrow_forward: Tu ne peux maintenant plus participer aux votes du village.\n"

                    elif col == "votant_loups" and not silent:
                        if val:                                 # votant_loups = True
                            notif += f":arrow_forward: Tu peux maintenant participer aux votes des loups ! Amuse-toi bien :wolf:\n"
                        else:                                   # votant_loups = False
                            notif += f":arrow_forward: Tu ne peux maintenant plus participer aux votes des loups.\n"

                    elif col == "role_actif" and not silent:
                        if val:                                 # role_actif = True
                            notif += f":arrow_forward: Tu peux maintenant utiliser tes pouvoirs !\n"
                        else:                                   # role_actif = False
                            notif += f":arrow_forward: Tu ne peux maintenant plus utiliser aucun pouvoir.\n"

                    bdd_tools.modif(joueur, col, val)           # Dans tous les cas, on modifie en base (après, pour pouvoir accéder aux vieux attribus plus haut)

                if not silent:
                    await chan.send(":zap: Une action divine vient de modifier ton existence ! :zap:\n"
                                    + f"\n{notif}\n"
                                    + tools.ital(":warning: Si tu penses qu'il y a erreur, appelle un MJ au plus vite !"))

            db.session.commit()

            await tools.log(ctx, changelog, code=True)

        except Exception:
            await tools.log(ctx, traceback.format_exc(), code=True)
