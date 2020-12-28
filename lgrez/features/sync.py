"""lg-rez / features / Synchronisation GSheets

Récupération et application des données des GSheets : modifications décidées via le Tableau de bord et rôles

"""

import datetime
import time
import traceback

from discord import Embed
from discord.ext import commands

from lgrez import config
from lgrez.blocs import tools, bdd, env, gsheets
from lgrez.blocs.bdd import tables, Joueur, Action, Role, Statut, ActionTrigger
from lgrez.features import gestion_actions


class TDBModif():
    """Modification flag sur le Tableau de bord, à appliquer"""

    def __init__(self, id, col, val, row, column):
        """Initializes self."""
        #: :class:`int`: ID Discord du joueur concerné
        self.id = id
        #: :class:`str`: Colonne de :class:`~blocs.bdd.Joueur` à modifier
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



def transtype(value, col):
    """Utilitaire : caste une donnée brute d'un GSheet selon la colonne correspondante

    Args:
        value (:class:`object`): valeur à transtyper
        col (:class:`sqlalchemy.Column`): colonne associée. Types pris en charge :
            - :class:`sqlalchemy.String` et dérivés (``Text``, ``Varchar``...)
            - :class:`sqlalchemy.Integer` et dérivés (``BigInteger``...)
            - :class:`sqlalchemy.Boolean`
            - :class:`sqlalchemy.Time`

    Returns:
        L'objet Python correspondant au type de la colonne (:class:`str`, :class:`int`, :class:`bool`, :class:`datetime.time`) ou ``None``

    Raises:
        ``ValueError``: la conversion n'est pas possible (ou ``value`` est évaluée ``None`` et la colonne n'est pas *nullable*)
        ``KeyError``: type de colonne non pris en compte
    """
    try:
        if value in (None, '', 'None', 'none', 'Null', 'null'):
            if not col.nullable:
                raise ValueError
            return None
        elif isinstance(col.type, sqlalchemy.String):
            return str(value)
        elif isinstance(col.type, sqlalchemy.Integer):
            return int(value)
        elif isinstance(col.type, sqlalchemy.Boolean):
            if value in {True, 1} or (isinstance(value, str) and value.lower() in {'true', 'vrai'}):
                return True
            elif value in {False, 0} or (isinstance(value, str) and value.lower() in {'false', 'faux'}):
                return False
            else:
                raise ValueError
        elif isinstance(col.type, sqlalchemy.Time):                # hh:mm
            try:
                h, m, _ = value.split(':')
            except ValueError:
                h, m = value.split(':')
            return datetime.time(hour=int(h), minute=int(m))
        else:
            raise KeyError(f"unhandled type for column '{col.key}': '{col.type}'")

    except (ValueError, TypeError):
        raise ValueError(f"Valeur '{value}' incorrecte pour la colonne '{col.key}' (type '{col.type}'/{'NOT NULL' if not column.nullable else ''})") from None



def get_sync():
    """Récupère les modifications en attente sur le TDB

    Charge les données du Tableau de bord (variable d'environment ``LGREZ_TDB_SHEET_ID``), compare les informations qui y figurent avec celles de la base de données (:class:`.bdd.Joueur`)

    Returns:
        :class:`list`\[:class:`.TDBModif`\]: liste des modifications à apporter
    """

    cols = [col for col in Joueur.columns if not col.key.endswith('_')]    # On élimine les colonnes locales

    ### RÉCUPÉRATION INFOS GSHEET

    SHEET_ID = env.load("LGREZ_TDB_SHEET_ID")

    workbook = gsheets.connect(SHEET_ID)    # Tableau de bord
    sheet = workbook.worksheet("Journée en cours")
    values = sheet.get_all_values()         # Liste de liste des valeurs des cellules

    head = values[2]            # Ligne d'en-têtes (noms des colonnes) = 3e ligne du TDB
    TDB_index = {col: head.index(col.key) for col in cols}    # Dictionnaire des indices des colonnes GSheet pour chaque colonne de la table
    TDB_tampon_index = {col: head.index(f"tampon_{col.key}") for col in cols if not col.primary_key}    # Idem pour la partie « tampon » (sauf la clé primaire, pas reprise en double)

    # CONVERSION INFOS GSHEET EN UTILISATEURS

    joueurs_TDB = []            # Liste des joueurs tels qu'actuellement dans le TDB
    ids_TDB = []                # discord_ids des différents joueurs du TDB
    rows_TDB = {}               # Indices des lignes ou sont les différents joueurs du TDB

    for i_row in range(len(values)):
        L = values[i_row]           # On parcourt les lignes du TDB
        id_cell = L[TDB_index[Joueur.primary_col]]
        if id_cell.isdigit():        # Si la cellule contient bien un ID (que des chiffres, et pas vide)
            id = int(id_cell)
            joueur_TDB = {col: transtype(L[TDB_index[col]], col) for col in cols}    # Dictionnaire correspondant à l'utilisateur
            joueurs_TDB.append(joueur_TDB)
            ids_TDB.append(id)
            rows_TDB[id] = i_row

    ### RÉCUPÉRATION UTILISATEURS CACHE

    joueurs_BDD = Joueur.query.all()    # Liste des joueurs tels qu'actuellement en cache
    ids_BDD = [joueur_BDD.discord_id for joueur_BDD in joueurs_BDD]

    ### COMPARAISON

    modifs = []         # modifs à porter au TDB (liste de TDBModifs)

    for joueur_BDD in joueurs_BDD.copy():           # Joueurs dans le cache supprimés du TDB
        if joueur_BDD.discord_id not in ids_TDB:
            joueurs_BDD.remove(joueur_BDD)
            config.session.delete(joueur_BDD)

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
    joueur = Joueur.query.get(joueur_id)
    assert joueur, f"!sync : joueur d'ID {joueur_id} introuvable"

    member = joueur.member
    chan = joueur.private_chan

    changelog = f"\n- {member.display_name} (@{member.name}#{member.discriminator}) :\n"
    notif = ""

    done = []
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
            if modif.val == Statut.vivant.name:         # Statut = vivant
                await member.add_roles(tools.role(ctx, "Joueur en vie"))
                await member.remove_roles(tools.role(ctx, "Joueur mort"))
                if not silent:
                    notif += f":arrow_forward: Tu es maintenant en vie. EN VIE !!!\n"

            elif modif.val == Statut.mort.name:         # Statut = mort
                await member.add_roles(tools.role(ctx, "Joueur mort"))
                await member.remove_roles(tools.role(ctx, "Joueur en vie"))
                if not silent:
                    notif += f":arrow_forward: Tu es malheureusement décédé(e) :cry:\nÇa arrive même aux meilleurs, en espérant que ta mort ait été belle !\n"
                # Actions à la mort
                for action in joueur.actions:
                    if action.trigger_debut == ActionTrigger.mort:
                        await gestion_actions.open_action(ctx, action, chan)

            elif modif.val == Statut.MV.name:           # Statut = MV
                await member.add_roles(tools.role(ctx, "Joueur en vie"))
                await member.remove_roles(tools.role(ctx, "Joueur mort"))
                if not silent:
                    notif += f":arrow_forward: Te voilà maintenant réduit(e) au statut de mort-vivant... Un MJ viendra te voir très vite, si ce n'est déjà fait, mais retient que la partie n'est pas finie pour toi !\n"

            elif not silent:                        # Statut = autre
                notif += f":arrow_forward: Nouveau statut : {tools.bold(modif.val)} !\n"

        elif modif.col == "role":                         # Modification rôle
            for action in joueur.actions:
                if action.base in joueur.role.base_actions:
                    gestion_actions.delete_action(ctx, action)  # On supprime les anciennes actions de rôle (et les tâches si il y en a)

            new_role = Role.query.get(modif.val)
            if not new_role:
                changelog += f"!!!! Rôle `{modif.val}` inconnu pour `{joueur}`, passé !!!!\n"
                continue

            for base in new_role.base_actions:
                action = Action(joueur=joueur, base=base, cooldown=0, charges=base.base_charges)
                gestion_actions.add_action(ctx, action)     # Ajout et création des tâches si trigger temporel

            if not silent:
                notif += f":arrow_forward: Ton nouveau rôle, si tu l'acceptes : {tools.bold(new_role.nom_complet)} !\nQue ce soit pour un jour ou pour le reste de la partie, renseigne toi en tapant {tools.code(f'!roles {new_role.slug}')}.\n"

        elif modif.col == "camp" and not silent:    # Modification camp
            notif += f":arrow_forward: Tu fais maintenant partie du camp « {tools.bold(modif.val)} ».\n"

        elif modif.col == "votant_village" and not silent:
            if modif.val:                           # votant_village = True
                notif += f":arrow_forward: Tu peux maintenant participer aux votes du village !\n"
            else:                                   # votant_village = False
                notif += f":arrow_forward: Tu ne peux maintenant plus participer aux votes du village.\n"

        elif modif.col == "votant_loups" and not silent:
            if modif.val:                           # votant_loups = True
                notif += f":arrow_forward: Tu peux maintenant participer aux votes des loups ! Amuse-toi bien :wolf:\n"
            else:                                   # votant_loups = False
                notif += f":arrow_forward: Tu ne peux maintenant plus participer aux votes des loups.\n"

        elif modif.col == "role_actif" and not silent:
            if modif.val:                           # role_actif = True
                notif += f":arrow_forward: Tu peux maintenant utiliser tes pouvoirs !\n"
            else:                                   # role_actif = False
                notif += f":arrow_forward: Tu ne peux maintenant plus utiliser aucun pouvoir.\n"

        setattr(joueur, modif.col, modif.val)       # Dans tous les cas, on modifie en base (après, pour pouvoir accéder aux vieux attribus plus haut)
        done.append(modif)

    if not silent:
        await chan.send(f":zap: {member.mention} Une action divine vient de modifier ton existence ! :zap:\n"
                        + f"\n{notif}\n"
                        + tools.ital(":warning: Si tu penses qu'il y a erreur, appelle un MJ au plus vite !"))

    return done, changelog


class Sync(commands.Cog):
    """Sync - Commandes de synchronisation des GSheets vers la BDD et les joueurs"""

    @commands.command()
    @tools.mjs_only
    async def sync(self, ctx, silent=False):
        """Récupère et applique les modifications du Tableau de bord (COMMANDE MJ)

        Args:
            silent: si spécifié (quelque soit sa valeur), les joueurs ne sont pas notifiés des modifications.

        Cette commande va récupérer les modifications en attente sur le Tableau de bord (lignes en rouge), modifer la BDD, et appliquer les modificatons dans Discord le cas échéant : renommage des utilisateurs, modification des rôles...
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
                    done, cgl = await modif_joueur(ctx, int(joueur_id), modifs, silent)
                    changelog += cgl
                except Exception:
                    changelog += traceback.format_exc()
                    await ctx.send(f"Erreur joueur {joueur_id}, passage au suivant, voir logs pour les détails")
                else:
                    done.extend(modifs)

            config.session.commit()

            if done:
                validate_sync(done)

            await tools.log(ctx, changelog, code=True)

        await ctx.send(f"Fait (voir {tools.channel(ctx, 'logs').mention} pour le détail)")


    @commands.command()
    @tools.mjs_only
    async def fillroles(self, ctx):
        """Remplit les tables des rôles / actions et #roles depuis le GSheet ad hoc (COMMANDE MJ)

        - Remplit les tables :class:`.bdd.Role` et :class:`.bdd.BaseAction` avec les informations du Google Sheets "Rôles et actions" (variable d'environnement ``LGREZ_ROLES_SHEET_ID``) ;
        - Vide le chan ``#roles`` puis le remplit avec les descriptifs de chaque rôle.

        Utile à chaque début de saison / changement dans les rôles/actions. Écrase toutes les entrées déjà en base, mais ne supprime pas celles obsolètes.
        """

        SHEET_ID = env.load("LGREZ_ROLES_SHEET_ID")
        workbook = gsheets.connect(SHEET_ID)    # Tableau de bord

        for table_name in ["Role", "BaseAction"]:
            await ctx.send(f"Remplissage de la table {tools.code(table_name)}...")
            async with ctx.typing():

                sheet = workbook.worksheet(table_name)
                values = sheet.get_all_values()         # Liste de liste des valeurs des cellules

                table = tables[table_name]
                cols = table.columns
                primary_col = table.primary_col

                cols_index = {col: values[0].index(col) for col in cols}    # Dictionnaire des indices des colonnes GSheet pour chaque colonne de la table

                existants = {getattr(item, primary_col): item for item in table.query.all()}

                for L in values[1:]:
                    args = {col: transtype(L[cols_index[col]], col) for col in cols}
                    id = args[primary_col]
                    if id in existants:
                        for col in cols:
                            if getattr(existants[id], col) != args[col]:
                                setattr(existants[id], col, args[col])
                    else:
                        config.session.add(table(**args))

                config.session.commit()

            await ctx.send(f"Table {tools.code(table_name)} remplie !")
            await tools.log(ctx, f"Table {tools.code(table_name)} remplie !")

        chan_roles = tools.channel(ctx, "rôles")

        await ctx.send(f"Vidage de {chan_roles.mention}...")
        async with ctx.typing():
            await chan_roles.purge(limit=1000)

        camps = Camp.query.filter_by(visible=True).all()
        await ctx.send(f"Remplissage... (temps estimé : {sum(len(camp.roles) + 2 for camp in camps) + 2} secondes)")

        t0 = time.time()
        await chan_roles.send(f"Voici la liste des rôles : (accessible en faisant {tools.code('!roles')}, mais on l'a mis là parce que pourquoi pas)\n\n——————————————————————————")
        async with ctx.typing():
            for camp in camps:
                if camp.roles:
                    emoji = camp.emoji.discord_emoji_or_none
                    await chan_roles.send(embed=Embed(title=f"Camp : {camp}").set_image(url=emoji.url if emoji else None))
                    await chan_roles.send(f"——————————————————————————")
                    for role in camp.roles:
                        await chan_roles.send(f"{emoji or ''} {tools.bold(role.prefixe + role.nom)} – {role.description_courte} (camp : {role.camp})\n\n{role.description_longue}\n\n——————————————————————————")

        await ctx.send(f"{chan_roles.mention} rempli ! (en {(time.time() - t0):.4} secondes)")
