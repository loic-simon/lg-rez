import json
import traceback

from discord.ext import commands
import tools
from bdd_connect import db, Joueurs
from blocs import bdd_tools


class Sync(commands.Cog):
    """Sync - synchronisation du GSheets vers les tables SQL et les joueurs"""

    @commands.command()
    @commands.check_any(commands.check(lambda ctx:ctx.message.webhook_id), commands.has_any_role("MJ", "Bot"))
    async def sync(self, ctx, silent, *, serial):
        """Applique les modifications lors d'un appel du tableau de bord (COMMANDE BOT)

        <silent> prend les valeurs "False" (les joueurs sont notifiés si leur statut est modifié) ou "True" (les joueurs ne sont pas notifiés)
        <serial> est un dictionnaire de dictionnaires contenant les données à modifier, sérialisé en JSON sous la forme {"discord_id":{"attribut_modifié":"valeur_attribut"}}
        
        Cette commande va modifier toutes les colonnes de la BDD Joueurs nécessaires, et appliquer les modificatons dans Discord le cas échéant : renommage des utilisateurs, modification des rôles...

        CETTE COMMANDE EST UTILISÉE POUR LA SYNCHRONISATION UNIQUEMENT (APPEL WEBHOOK)
        ELLE N'EST PAS CONÇUE POUR ETRE UTILISÉE À LA MAIN
        """
        try:
            dic = json.loads(serial)                # Désérialisation JSON en dictionnaire Python
            silent = (silent == "True")
            changelog = f"Synchronisation TDB (silencieux = {silent}) :"

            for joueur_id in dic:               # Joueurs dont au moins un attribut a été modifié
                joueur = Joueurs.query.get(int(joueur_id))
                joueur_Discord = ctx.guild.get_member(joueur.discord_id)
                chan = ctx.guild.get_channel(joueur._chan_id)
                changelog += f"\n- {joueur_Discord.display_name} (@{joueur_Discord.discriminator}) :\n"
                notif = ""
                
                for col, val in dic[joueur_id].items():
                    changelog += f"    - {col} : {val}\n"
                    bdd_tools.modif(joueur, col, val)           # Dans tous les cas, on modifie en base
                    
                    if col == "nom":                            # Renommage joueur
                        await chan.edit(name=f"conv-bot-{val}")
                        await joueur_Discord.edit(nick=val)  
                        if not silent:
                            notif += f":arrow_forward: Tu t'appelles maintenant {tools.bold(val)}.\n"
                            
                    elif col == "chambre" and not silent:       # Modification chambre
                        notif += f":arrow_forward: Tu habites maintenant en chambre {tools.bold(val)}.\n"
                        
                    elif col == "statut":
                        if val == "vivant":                     # Statut = vivant
                            await joueur_Discord.add_roles(tools.role(ctx, "Joueur en vie"))
                            await joueur_Discord.remove_roles(tools.role(ctx, "Joueur mort"))
                            if not silent:
                                notif += f":arrow_forward: Tu es maintenant en vie. EN VIE !!!\n"
                                
                        elif val == "mort":                     # Statut = mort                   
                            await joueur_Discord.add_roles(tools.role(ctx, "Joueur mort"))
                            await joueur_Discord.remove_roles(tools.role(ctx, "Joueur en vie"))
                            if not silent:
                                notif += f":arrow_forward: Tu es malheureusement décédé(e) :cry:\nÇa arrive même aux meilleurs, en espérant que ta mort ait été belle !\n"
                                
                        elif val == "MV":                       # Statut = MV
                            await joueur_Discord.add_roles(tools.role(ctx, "Joueur en vie"))
                            await joueur_Discord.remove_roles(tools.role(ctx, "Joueur mort"))
                            if not silent:
                                notif += f":arrow_forward: Te voilà maintenant réduit(e) au statut de mort-vivant... Un MJ viendra te voir très vite, si ce n'est déjà fait, mais retient que la partie n'est pas finie pour toi !\n"
                            
                        elif not silent:                        # Statut = autre
                            notif += f":arrow_forward: Nouveau statut : {tools.bold(val)} !\n"
                            
                    elif col == "role" and not silent:          # Modification rôle
                        notif += f":arrow_forward: Ton nouveau rôle, si tu l'acceptes : {tools.bold(val)} !\nQue ce soit pour un jour ou pour le reste de la partie, renseigne toi en écrivant « {tools.bold(val)} » en texte libre.\n"
                        
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
                            notif += f":arrow_forward: Tu peux maintenant utiliser ton pouvoir de {joueur.role} !\n"
                        else:                                   # role_actif = False
                            notif += f":arrow_forward: Tu ne peux maintenant plus utiliser ton pouvoir de {joueur.role}.\n"
                            
                if not silent:
                    await chan.send(":zap: Une action divine vient de modifier ton existence ! :zap:\n" + notif)

            db.session.commit()

            await tools.log(ctx, changelog, code=True)
        
        except Exception:
            await tools.log(ctx, traceback.format_exc(), code=True)
