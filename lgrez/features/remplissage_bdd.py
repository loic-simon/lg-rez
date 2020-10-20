import traceback
import time

from discord import Embed
from discord.ext import commands

from lgrez.blocs import tools, bdd, env, gsheets, bdd_tools
from lgrez.blocs.bdd import session, engine, Tables, Roles
from lgrez.features import informations


class RemplissageBDD(commands.Cog):
    """ RemplissageBDD - Commandes pour remplir la base de données du bot à partir des GSheets"""

    @commands.command(disabled=True)
    @tools.mjs_only
    async def droptable(self, ctx, *, table):
        """Supprime sans ménagement une table de données (COMMANDE MJ)

        <table> table à supprimer (doit exister)

        ATTENTION À SAUVEGARDER AVANT !
        CECI N'EST PAS UN EXERCICE, LA TABLE SERA SUPPRIMÉE DÉFINITIVEMENT !!!

        Cette commande ne devrait certainement pas exister, mais bon...
        """

        if table in Tables:
            if await tools.yes_no(ctx.bot, await ctx.send("Sûr ?")):
                Tables[table].__table__.drop(engine)

                await ctx.send(f"Table {tools.code(table)} supprimée.")
                await tools.log(ctx, f"Table {tools.code(table)} supprimée.")

            else:
                await ctx.send("Mission aborted.")
        else:
            await ctx.send(f"Table {tools.code(table)} non trouvée")


    @commands.command()
    @tools.mjs_only
    async def fillroles(self, ctx):
        """Remplit les tables des rôles / actions et #roles depuis le GSheet ad hoc (COMMANDE MJ)

        - Remplit les tables Roles, BaseActions et BaseActionsRoles avec les informations du Google Sheets "Rôles et actions" (https://docs.google.com/spreadsheets/d/1Mfs22B_HtqSejaN0lX_Q555JW4KTYW5Pj-D-1ywoEIg) ;
        - Vide le chan #roles puis le remplit avec les descriptifs de chaque rôle.

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
                    await chan_roles.send(embed=Embed(title=f"Camp : {camp}").set_image(url=informations.emoji_camp(ctx, camp).url))
                    await chan_roles.send(f"——————————————————————————")
                    for role in roles_camp:
                        await chan_roles.send(f"{informations.emoji_camp(ctx, role.camp)} {tools.bold(role.prefixe + role.nom)} – {role.description_courte} (camp : {role.camp})\n\n{role.description_longue}\n\n——————————————————————————")

        await ctx.send(f"{chan_roles.mention} rempli ! (en {(time.time() - t0):.4} secondes)")
