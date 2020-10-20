import traceback

from discord.ext import commands

from lgrez.blocs import tools, bdd, bdd_tools, env, gsheets
from lgrez.blocs.bdd import Joueurs, Actions, BaseActions, BaseActionsRoles, Taches
from lgrez.features import gestion_actions


async def get_sync():
    """Récupère les modifications en attente sur le TDB"""

    cols = [col for col in bdd_tools.get_cols(Joueurs) if not col.startswith('_')]    # On élimine les colonnes locales
    cols_SQL_types = bdd_tools.get_SQL_types(Joueurs)
    cols_SQL_nullable = bdd_tools.get_SQL_nullable(Joueurs)

    ### RÉCUPÉRATION INFOS GSHEET

    SHEET_ID = env.load("LGREZ_TDB_SHEET_ID")

    workbook = gsheets.connect(SHEET_ID)    # Tableau de bord
    sheet = workbook.worksheet("Journée en cours")
    values = sheet.get_all_values()         # Liste de liste des valeurs des cellules
    (NL, NC) = (len(values), len(values[0]))

    head = values[2]            # Ligne d'en-têtes (noms des colonnes) = 3e ligne du TDB
    TDB_index = {col: head.index(col) for col in cols}    # Dictionnaire des indices des colonnes GSheet pour chaque colonne de la table
    TDB_tampon_index = {col: head.index(f"tampon_{col}") for col in cols if col != 'discord_id'}    # Idem pour la partie « tampon »

    # CONVERSION INFOS GSHEET EN UTILISATEURS

    joueurs_TDB = []            # Liste des joueurs tels qu'actuellement dans le TDB
    ids_TDB = []                # discord_ids des différents joueurs du TDB
    rows_TDB = {}               # Indices des lignes ou sont les différents joueurs du TDB

    for l in range(NL):
        L = values[l]           # On parcourt les lignes du TDB
        id_cell = L[TDB_index["discord_id"]]
        if id_cell.isdigit():        # Si la cellule contient bien un ID (que des chiffres, et pas vide)
            id = int(id_cell)
            joueur_TDB = {col: bdd_tools.transtype(L[TDB_index[col]], col, cols_SQL_types[col], cols_SQL_nullable[col]) for col in cols}
                # Dictionnaire correspondant à l'utilisateur
            joueurs_TDB.append(joueur_TDB)
            ids_TDB.append(id)
            rows_TDB[id] = l

    ### RÉCUPÉRATION UTILISATEURS CACHE

    joueurs_BDD = Joueurs.query.all()     # Liste des joueurs tels qu'actuellement en cache
    ids_BDD = [joueur_BDD.discord_id for joueur_BDD in joueurs_BDD]

    ### COMPARAISON

    modifs = []         # modifs à porter au TDB : tuple (id - colonne (nom) - valeur)
    modified_ids = []

    for joueur_BDD in joueurs_BDD.copy():                   ## Joueurs dans le cache supprimés du TDB
        if joueur_BDD.discord_id not in ids_TDB:
            joueurs_BDD.remove(joueur_BDD)
            bdd.session.delete(joueur_BDD)

    for joueur_TDB in joueurs_TDB:                              ## Différences
        id = joueur_TDB["discord_id"]

        if id not in ids_BDD:             # Si joueur dans le cache pas dans le TDB
            raise ValueError(f"Joueur {joueur_TDB['nom']} hors BDD : vérifier processus d'inscription")

        joueur_BDD = [joueur for joueur in joueurs_BDD if joueur.discord_id == id][0]     # joueur correspondant dans le cache

        for col in cols:
            if getattr(joueur_BDD, col) != joueur_TDB[col]:   # Si <col> diffère entre TDB et cache

                modifs.append( (id, col, joueur_TDB[col]) )   # On ajoute les modifs
                if id not in modified_ids:
                    modified_ids.append(id)

    ### APPLICATION DES MODIFICATIONS SUR LE TDB

    if modifs:
        modifs_lc = [(rows_TDB[id], TDB_tampon_index[col], v) for (id, col, v) in modifs]
            # On transforme les infos en coordonnées dans le TDB : ID -> ligne et col -> colonne,
        gsheets.update(sheet, modifs_lc)


    ### RETOURNAGE DES RÉSULTATS

    return {id: {col: v for (idM, col, v) in modifs if idM == id} for id in modified_ids}



async def modif_joueur(ctx, joueur_id, modifs, silent):
    """Attribue les modifications demandées au joueur

    modifs : dictionnaire {colonne BDD: nouvelle valeur}
    """
    joueur = Joueurs.query.get(int(joueur_id))
    assert joueur, f"!sync : joueur d'ID {joueur_id} introuvable"

    member = ctx.guild.get_member(joueur.discord_id)
    assert member, f"!sync : member {joueur} introuvable"

    chan = ctx.guild.get_channel(joueur._chan_id)
    assert chan, f"!sync : chan privé de {member} introuvable"

    changelog = f"\n- {member.display_name} (@{member.name}#{member.discriminator}) :\n"
    notif = ""

    for col, val in modifs.items():
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
                for action in Joueurs.query.filter_by(player_id=joueur.discord_id, trigger_debut="mort"):
                    await gestion_actions.open_action(ctx, action, chan)

            elif val == "MV":                       # Statut = MV
                await member.add_roles(tools.role(ctx, "Joueur en vie"))
                await member.remove_roles(tools.role(ctx, "Joueur mort"))
                if not silent:
                    notif += f":arrow_forward: Te voilà maintenant réduit(e) au statut de mort-vivant... Un MJ viendra te voir très vite, si ce n'est déjà fait, mais retient que la partie n'est pas finie pour toi !\n"

            elif not silent:                        # Statut = autre
                notif += f":arrow_forward: Nouveau statut : {tools.bold(val)} !\n"

        elif col == "role":                         # Modification rôle
            old_bars = Joueurs.query.filter_by(role=joueur.role).all()
            old_actions = []
            for bar in old_bars:
                old_actions.extend(Joueurs.query.filter_by(action=bar.action, player_id=joueur.discord_id).all())
            for action in old_actions:
                gestion_actions.delete_action(ctx, action)  # On supprime les anciennes actions de rôle (et les tâches si il y en a)

            new_bars = Joueurs.query.filter_by(role=val).all()         # Actions associées au nouveau rôle
            new_bas = [Joueurs.query.get(bar.action) for bar in new_bars]   # Nouvelles BaseActions
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

    return changelog


class Sync(commands.Cog):
    """Sync - Commandes de synchronisation des GSheets vers la BDD et les joueurs"""

    @commands.command()
    @tools.mjs_only
    async def sync(self, ctx, silent=False):
        """Applique les modifications lors d'un appel du Tableau de bord (COMMANDE MJ)

        <silent> peut valoir
            False / 0       les joueurs sont notifiés si leur statut est modifié (défaut)
            True  / 1       les joueurs ne sont pas notifiés

        Cette commande va récupérer les modifications en attente sur le Tableau de bord (lignes en rouge), modifer la BDD Joueurs, et appliquer les modificatons dans Discord le cas échéant : renommage des utilisateurs, modification des rôles...
        """
        try:
            await ctx.send("Récupération des modifications...")
            async with ctx.typing():
                dic = await get_sync()                  # Récupération du dictionnaire {joueur_id: modified_attrs}
                silent = (silent == "True")
                changelog = f"Synchronisation TDB (silencieux = {silent}) :"

            if dic:
                nb_modifs = sum(len(modifs) for modifs in dic.values())
                await ctx.send(f"{nb_modifs} modification(s) trouvée(s) pour {len(dic)} joueur(s), application...")
                async with ctx.typing():
                    for joueur_id, modifs in dic.items():               # Joueurs dont au moins un attribut a été modifié
                        try:
                            changelog += await modif_joueur(ctx, joueur_id, modifs, silent)
                        except Exception as e:
                            changelog += traceback.format_exc()
                            await ctx.send(f"Erreur joueur {joueur_id}, passage au suivant, voir logs pour les détails")

                    bdd.session.commit()

                    await tools.log(ctx, changelog, code=True)

                await ctx.send(f"Fait (voir {tools.channel(ctx, 'logs')} pour le détail)")

            else:
                await ctx.send("Pas de nouvelles modificatons.")

        except Exception:
            await tools.log(ctx, traceback.format_exc(), code=True)
