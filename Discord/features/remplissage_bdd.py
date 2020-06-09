import os
import traceback

from dotenv import load_dotenv
from discord.ext import commands

import tools
from blocs import gsheets, bdd_tools
from bdd_connect import db, Tables


class RemplissageBDD(commands.Cog):
    """
    RemplissageBDD - Commandes pour remplir la base de données du bot à partir des GSheets
    """


    @commands.command()
    @commands.has_role("MJ")
    async def droptable(self, ctx, table):
        """
        Supprime la table <table>.

        ATTENTION À SAUVEGARDER AVANT !
        CECI N'EST PAS UN EXERCICE, LA TABLE SERA SUPPRIMEE DEFINITIVEMENT!!
        """

        if table in Tables:
            if await tools.yes_no(ctx.bot, await ctx.send("Sûr ?")):
                Tables[table].__table__.drop(db.engine)

                await ctx.send(f"Table {tools.code(table)} supprimée.")
                await tools.log(ctx, f"Table {tools.code(table)} supprimée.")

            else:
                await ctx.send("Mission aborted.")
        else:
            await ctx.send(f"Table {tools.code(table)} non trouvée")


    @commands.command()
    @commands.has_role("MJ")
    async def fillroles(self, ctx):
        """
        Remplit les table Roles, BaseActions et BaseActionsRoles depuis le GSheet ad hoc
        """

        load_dotenv()
        SHEET_ID = os.getenv("ROLES_SHEET_ID")
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

                cols_index = {col:values[0].index(col) for col in cols}    # Dictionnaire des indices des colonnes GSheet pour chaque colonne de la table

                existants = {getattr(item, primary_col):item for item in table.query.all()}

                for L in values[1:]:
                    args = {col:bdd_tools.transtype(L[cols_index[col]], col, SQL_types[col], SQL_nullable[col]) for col in cols}
                    id = args[primary_col]
                    if id in existants:
                        for col in cols:
                            if getattr(existants[id], col) != args[col]:
                                bdd_tools.modif(existants[id], col, args[col])
                    else:
                        db.session.add(table(**args))

                db.session.commit()

            await ctx.send(f"Table {tools.code(table_name)} remplie !")
            await tools.log(ctx, f"Table {tools.code(table_name)} remplie !")
