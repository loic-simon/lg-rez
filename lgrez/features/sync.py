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


class TDBModif():
    """Modification flag sur le Tableau de bord, à appliquer"""

    def __init__(self, id, col, val, row, column):
        """Initializes self."""
        #: :class:`int`: ID Discord du joueur concerné
        self.id = id
        #: :class:`str`: Colonne de Joueurs à modifier
        self.col = col
        #: :class:`object`: Nouvelle valeur
        self.val = val

        #: :class:`int`: Numéro de la ligne sur le TDB
        self.row = row
        #: :class:`int`: Numéro de la colonne TAMPON sur le TDB
        self.column = column

    def __repr__(self):
        """Returns repr(self)"""
        return f"<TDBModif id {self.id}: {self.col} = {self.val}>"


def get_sync():
    """Récupère les modifications en attente sur le TDB

    Charge les données du Tableau de bord (variable d'environment ``LGREZ_TDB_SHEET_ID``), compare les informations qui y figurent avec celles de la base de données (:class:`.bdd.Joueurs`)

    Returns:
        :class:`list`\[:class:`.TDBModif`\]: liste des modifications à apporter
    """

    all_cols = bdd_tools.get_cols(Joueurs)
    cols = [col for col in all_cols if not col.endswith('_')]    # On élimine les colonnes locales
    cols_SQL_types = bdd_tools.get_SQL_types(Joueurs)
    cols_SQL_nullable = bdd_tools.get_SQL_nullable(Joueurs)
    primary_col = bdd_tools.get_primary_col(Joueurs)

    ### RÉCUPÉRATION INFOS GSHEET

    SHEET_ID = env.load("LGREZ_TDB_SHEET_ID")

    workbook = gsheets.connect(SHEET_ID)    # Tableau de bord
    sheet = workbook.worksheet("Journée en cours")
    values = sheet.get_all_values()         # Liste de liste des valeurs des cellules

    head = values[2]            # Ligne d'en-têtes (noms des colonnes) = 3e ligne du TDB
    TDB_index = {col: head.index(col) for col in cols}    # Dictionnaire des indices des colonnes GSheet pour chaque colonne de la table
    TDB_tampon_index = {col: head.index(f"tampon_{col}") for col in cols if col != 'discord_id'}    # Idem pour la partie « tampon »

    # CONVERSION INFOS GSHEET EN UTILISATEURS

    joueurs_TDB = []            # Liste des joueurs tels qu'actuellement dans le TDB
    ids_TDB = []                # discord_ids des différents joueurs du TDB
    rows_TDB = {}               # Indices des lignes ou sont les différents joueurs du TDB

    for i_row in range(len(values)):
        L = values[i_row]           # On parcourt les lignes du TDB
        id_cell = L[TDB_index[primary_col]]
        if id_cell.isdigit():        # Si la cellule contient bien un ID (que des chiffres, et pas vide)
            id = int(id_cell)
            joueur_TDB = {col: bdd_tools.transtype(L[TDB_index[col]], col, cols_SQL_types[col], cols_SQL_nullable[col]) for col in cols}    # Dictionnaire correspondant à l'utilisateur
            joueurs_TDB.append(joueur_TDB)
            ids_TDB.append(id)
            rows_TDB[id] = i_row

    ### RÉCUPÉRATION UTILISATEURS CACHE

    joueurs_BDD = Joueurs.query.all()     # Liste des joueurs tels qu'actuellement en cache
    ids_BDD = [joueur_BDD.discord_id for joueur_BDD in joueurs_BDD]

    ### COMPARAISON

    modifs = []         # modifs à porter au TDB (liste de TDBModifs)

    for joueur_BDD in joueurs_BDD.copy():           # Joueurs dans le cache supprimés du TDB
        if joueur_BDD.discord_id not in ids_TDB:
            joueurs_BDD.remove(joueur_BDD)
            bdd.session.delete(joueur_BDD)

    for joueur_TDB in joueurs_TDB:                  # Différences
        id = joueur_TDB["discord_id"]

        if id not in ids_BDD:             # Si joueur dans le cache pas dans le TDB
            raise ValueError(f"Joueur {joueur_TDB['nom']} hors BDD : vérifier processus d'inscription")

        joueur_BDD = [joueur for joueur in joueurs_BDD if joueur.discord_id == id][0]     # joueur correspondant dans le cache

        for col in cols:
            if getattr(joueur_BDD, col) != joueur_TDB[col]:     # Si <col> diffère entre TDB et cache
                modif = TDBModif(id, col, joueur_TDB[col],
                                 rows_TDB[id], TDB_tampon_index[col])
                modifs.append(modif)   # On ajoute les modifs

    ### RETOURNAGE DES RÉSULTATS

    return modifs


def validate_sync(modifs):
    """Valide des modificatons sur le Tableau de bord (case plus en rouge)

    Args:
        modifs (:class:`list`\[:class:`.TDBModif`\]): liste des modifications à apporter

    Modifie sur le Tableau de bord (variable d'environment ``LGREZ_TDB_SHEET_ID``) et applique les modifications contenues dans modifs
    """

    ### APPLICATION DES MODIFICATIONS SUR LE TDB

    SHEET_ID = env.load("LGREZ_TDB_SHEET_ID")

    workbook = gsheets.connect(SHEET_ID)    # Tableau de bord
    sheet = workbook.worksheet("Journée en cours")

    modifs_lc = [(modif.row, modif.column, modif.val) for modif in modifs]
        # On transforme les infos en coordonnées dans le TDB : ID -> ligne et col -> colonne,
    gsheets.update(sheet, modifs_lc)


async def modif_joueur(ctx, joueur_id, modifs, silent=False):
    """Attribue les modifications demandées au joueur

    Args:
        ctx (:class:`~discord.ext.commands.Context`): contexte quelconque du bot
        joueur_id (:class:`int`): id Discord du joueur concerné
        modifs (:class:`list`\[:class:`.TDBModif`\]): liste des modifications à apporter
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

    for modif in modifs:
        changelog += f"    - {modif.col} : {modif.val}\n"

        if modif.col == "nom":                            # Renommage joueur
            await chan.edit(name=f"conv-bot-{modif.val}")
            await member.edit(nick=modif.val)
            if not silent:
                notif += f":arrow_forward: Tu t'appelles maintenant {tools.bold(modif.val)}.\n"

        elif modif.col == "chambre" and not silent:       # Modification chambre
            notif += f":arrow_forward: Tu habites maintenant en chambre {tools.bold(modif.val)}.\n"

        elif modif.col == "statut":
            if modif.val == "vivant":                     # Statut = vivant
                await member.add_roles(tools.role(ctx, "Joueur en vie"))
                await member.remove_roles(tools.role(ctx, "Joueur mort"))
                if not silent:
                    notif += f":arrow_forward: Tu es maintenant en vie. EN VIE !!!\n"

            elif modif.val == "mort":                     # Statut = mort
                await member.add_roles(tools.role(ctx, "Joueur mort"))
                await member.remove_roles(tools.role(ctx, "Joueur en vie"))
                if not silent:
                    notif += f":arrow_forward: Tu es malheureusement décédé(e) :cry:\nÇa arrive même aux meilleurs, en espérant que ta mort ait été belle !\n"
                # Actions à la mort
                for action in Actions.query.filter_by(player_id=joueur.discord_id, trigger_debut="mort"):
                    await gestion_actions.open_action(ctx, action, chan)

            elif modif.val == "MV":                       # Statut = MV
                await member.add_roles(tools.role(ctx, "Joueur en vie"))
                await member.remove_roles(tools.role(ctx, "Joueur mort"))
                if not silent:
                    notif += f":arrow_forward: Te voilà maintenant réduit(e) au statut de mort-vivant... Un MJ viendra te voir très vite, si ce n'est déjà fait, mais retient que la partie n'est pas finie pour toi !\n"

            elif not silent:                        # Statut = autre
                notif += f":arrow_forward: Nouveau statut : {tools.bold(modif.val)} !\n"

        elif modif.col == "role":                         # Modification rôle
            old_bars = BaseActionsRoles.query.filter_by(role=joueur.role).all()
            old_actions = []
            for bar in old_bars:
                old_actions.extend(Actions.query.filter_by(action=bar.action, player_id=joueur.discord_id).all())
            for action in old_actions:
                gestion_actions.delete_action(ctx, action)  # On supprime les anciennes actions de rôle (et les tâches si il y en a)

            new_bars = BaseActionsRoles.query.filter_by(role=modif.val).all()         # Actions associées au nouveau rôle
            new_bas = [BaseActions.query.get(bar.action) for bar in new_bars]   # Nouvelles BaseActions
            cols = [col for col in bdd_tools.get_cols(BaseActions) if not col.startswith("base")]
            new_actions = [Actions(player_id=joueur.discord_id, **{col: getattr(ba, col) for col in cols},
                                   cooldown=0, charges=ba.base_charges) for ba in new_bas]
            await tools.log(ctx, str(new_actions))

            for action in new_actions:
                gestion_actions.add_action(ctx, action)     # Ajout et création des tâches si trigger temporel

            role = tools.nom_role(modif.val)
            if not role:        # role <modif.val> pas en base : Error!
                role = f"« {modif.val} »"
                await tools.log(ctx, f"{tools.mention_MJ(ctx)} ALED : rôle \"{modif.val}\" attribué à {joueur.nom} inconnu en base !")
            if not silent:
                notif += f":arrow_forward: Ton nouveau rôle, si tu l'acceptes : {tools.bold(role)} !\nQue ce soit pour un jour ou pour le reste de la partie, renseigne toi en tapant {tools.code(f'!roles {modif.val}')}.\n"

        elif modif.col == "camp" and not silent:          # Modification camp
            notif += f":arrow_forward: Tu fais maintenant partie du camp « {tools.bold(modif.val)} ».\n"

        elif modif.col == "votant_village" and not silent:
            if modif.val:                                 # votant_village = True
                notif += f":arrow_forward: Tu peux maintenant participer aux votes du village !\n"
            else:                                   # votant_village = False
                notif += f":arrow_forward: Tu ne peux maintenant plus participer aux votes du village.\n"

        elif modif.col == "votant_loups" and not silent:
            if modif.val:                                 # votant_loups = True
                notif += f":arrow_forward: Tu peux maintenant participer aux votes des loups ! Amuse-toi bien :wolf:\n"
            else:                                   # votant_loups = False
                notif += f":arrow_forward: Tu ne peux maintenant plus participer aux votes des loups.\n"

        elif modif.col == "role_actif" and not silent:
            if modif.val:                                 # role_actif = True
                notif += f":arrow_forward: Tu peux maintenant utiliser tes pouvoirs !\n"
            else:                                   # role_actif = False
                notif += f":arrow_forward: Tu ne peux maintenant plus utiliser aucun pouvoir.\n"

        bdd_tools.modif(joueur, modif.col, modif.val)           # Dans tous les cas, on modifie en base (après, pour pouvoir accéder aux vieux attribus plus haut)

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
        await ctx.send("Récupération des modifications...")
        async with ctx.typing():
            modifs = get_sync()                 # Récupération du dictionnaire {joueur_id: modified_attrs}
            silent = bool(silent)
            changelog = f"Synchronisation TDB (silencieux = {silent}) :"

        if not modifs:
            await ctx.send("Pas de nouvelles modificatons.")
            return

        dic = {}
        for modif in modifs:
            if modif.id not in dic:
                dic[modif.id] = []
            dic[modif.id].append(modif)

        message = await ctx.send(f"{len(modifs)} modification(s) trouvée(s) pour {len(dic)} joueur(s), go ?")
        if not await tools.yes_no(ctx.bot, message):
            await ctx.send("Mission aborted.")
            return

        # Go sync
        done = []
        async with ctx.typing():
            for joueur_id, modifs in dic.items():        # Joueurs dont au moins un attribut a été modifié
                try:
                    changelog += await modif_joueur(ctx, joueur_id, modifs, silent)
                except Exception:
                    changelog += traceback.format_exc()
                    await ctx.send(f"Erreur joueur {joueur_id}, passage au suivant, voir logs pour les détails")
                else:
                    done.extend(modifs)

            bdd.session.commit()

            if done:
                validate_sync(done)

            await tools.log(ctx, changelog, code=True)

        await ctx.send(f"Fait (voir {tools.channel(ctx, 'logs').mention} pour le détail)")


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
