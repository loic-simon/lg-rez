"""lg-rez / features / Synchronisation GSheets

Récupération et application des données des GSheets : modifications décidées via le Tableau de bord et rôles

"""

import traceback
import time

from discord import Embed
from discord.ext import commands

from lgrez.blocs import tools, bdd, bdd_tools, env, gsheets
from lgrez.blocs.bdd import engine, Tables, Joueurs, Actions, BaseActions, BaseActionsRoles, Roles, Taches
from lgrez.features import gestion_actions


async def get_sync():
    """Récupère les modifications en attente sur le TDB

    Charge les données du Tableau de bord (variable d'environment ``LGREZ_TDB_SHEET_ID``), compare les informations qui y figurent avec celles de la base de données (:class:`.bdd.Joueurs`)

    Pour les informations différant, met à jour le Tableau de bord (ligne plus en rouge)

    Returns:
        :class:`dict`\[:attr:`.bdd.Joueurs.id`, :class:`dict`\[:class:`str`, :class:`object`\]\]: Le dictionnaire des modifications pour chaque joueur (repéré par son ID Discord)
    """

    cols = [col for col in bdd_tools.get_cols(Joueurs) if not col.endswith('_')]    # On élimine les colonnes locales
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



async def modif_joueur(ctx, joueur_id, modifs, silent=False):
    """Attribue les modifications demandées au joueur

    Args:
        ctx (:class:`~discord.ext.commands.Context`): contexte quelconque du bot
        modifs (:class:`dict`\[:class:`str`, :class:`object`\]\]): dictionnaire {colonne BDD: nouvelle valeur}
        silent (:class:`bool`): si ``True``, no notifie pas le joueur des modifications

    Pour chaque modifications de ``modif``, applique les conséquences adéquates (rôles, nouvelles actions, tâches planifiées...) et informe le joueur si ``silent`` vaut ``False``.
    """
    joueur = Joueurs.query.get(int(joueur_id))
    assert joueur, f"!sync : joueur d'ID {joueur_id} introuvable"

    member = ctx.guild.get_member(joueur.discord_id)
    assert member, f"!sync : member {joueur} introuvable"

    chan = ctx.guild.get_channel(joueur.chan_id_)
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
        await chan.send(f":zap: {member.mention} Une action divine vient de modifier ton existence ! :zap:\n"
                        + f"\n{notif}\n"
                        + tools.ital(":warning: Si tu penses qu'il y a erreur, appelle un MJ au plus vite !"))

    return changelog


class Sync(commands.Cog):
    """Sync - Commandes de synchronisation des GSheets vers la BDD et les joueurs"""

    @commands.command()
    @tools.mjs_only
    async def sync(self, ctx, silent=False):
        """Récupère et applique les modifications du Tableau de bord (COMMANDE MJ)

        Args:
            silent: si spécifié (quelque soit sa valeur), les joueurs ne sont pas notifiés des modifications.

        Cette commande va récupérer les modifications en attente sur le Tableau de bord (lignes en rouge), modifer la BDD Joueurs, et appliquer les modificatons dans Discord le cas échéant : renommage des utilisateurs, modification des rôles...
        """
        try:
            await ctx.send("Récupération des modifications...")
            async with ctx.typing():
                dic = await get_sync()                  # Récupération du dictionnaire {joueur_id: modified_attrs}
                silent = bool(silent)
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


    @commands.command()
    @tools.mjs_only
    async def fillroles(self, ctx):
        """Remplit les tables des rôles / actions et #roles depuis le GSheet ad hoc (COMMANDE MJ)

        - Remplit les tables :class:`.bdd.Roles`, :class:`.bdd.BaseActions` et :class:`.bdd.BaseActionsRoles` avec les informations du Google Sheets "Rôles et actions" (variable d'environnement ``LGREZ_ROLES_SHEET_ID``) ;
        - Vide le chan ``#roles`` puis le remplit avec les descriptifs de chaque rôle.

        Utile à chaque début de saison / changement dans les rôles/actions. Écrase toutes les entrées déjà en base, mais ne supprime pas celles obsolètes.
        """

        SHEET_ID = env.load("LGREZ_ROLES_SHEET_ID")
        workbook = gsheets.connect(SHEET_ID)    # Tableau de bord

        for table_name in ["Roles", "BaseActions", "BaseActionsRoles"]:
            await ctx.send(f"Remplissage de la table {tools.code(table_name)}...")
            async with ctx.typing():

                sheet = workbook.worksheet(table_name)
                values = sheet.get_all_values()         # Liste de liste des valeurs des cellules

                table = Tables[table_name]
                cols = bdd_tools.get_cols(table)
                SQL_types = bdd_tools.get_SQL_types(table)
                SQL_nullable = bdd_tools.get_SQL_nullable(table)
                primary_col = bdd_tools.get_primary_col(table)

                cols_index = {col: values[0].index(col) for col in cols}    # Dictionnaire des indices des colonnes GSheet pour chaque colonne de la table

                existants = {getattr(item, primary_col):item for item in table.query.all()}

                for L in values[1:]:
                    args = {col: bdd_tools.transtype(L[cols_index[col]], col, SQL_types[col], SQL_nullable[col]) for col in cols}
                    id = args[primary_col]
                    if id in existants:
                        for col in cols:
                            if getattr(existants[id], col) != args[col]:
                                bdd_tools.modif(existants[id], col, args[col])
                    else:
                        bdd.session.add(table(**args))

                bdd.session.commit()

            await ctx.send(f"Table {tools.code(table_name)} remplie !")
            await tools.log(ctx, f"Table {tools.code(table_name)} remplie !")

        chan_roles = tools.channel(ctx, "rôles")

        await ctx.send(f"Vidage de {chan_roles.mention}...")
        async with ctx.typing():
            await chan_roles.purge(limit=1000)

        roles = {camp: Roles.query.filter_by(camp=camp).all() for camp in ["village", "loups", "nécro", "solitaire", "autre"]}
        await ctx.send(f"Remplissage... (temps estimé : {sum([len(v) + 2 for v in roles.values()]) + 1} secondes)")

        t0 = time.time()
        await chan_roles.send(f"Voici la liste des rôles : (accessible en faisant {tools.code('!roles')}, mais on l'a mis là parce que pourquoi pas)\n\n——————————————————————————")
        async with ctx.typing():
            for camp, roles_camp in roles.items():
                if roles_camp:
                    await chan_roles.send(embed=Embed(title=f"Camp : {camp}").set_image(url=tools.emoji_camp(ctx, camp).url))
                    await chan_roles.send(f"——————————————————————————")
                    for role in roles_camp:
                        await chan_roles.send(f"{tools.emoji_camp(ctx, role.camp)} {tools.bold(role.prefixe + role.nom)} – {role.description_courte} (camp : {role.camp})\n\n{role.description_longue}\n\n——————————————————————————")

        await ctx.send(f"{chan_roles.mention} rempli ! (en {(time.time() - t0):.4} secondes)")
