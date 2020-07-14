import datetime
import discord
from discord.ext import commands
from sqlalchemy.sql.expression import and_, or_, not_

from bdd_connect import db, Joueurs, Actions, BaseActions, BaseActionsRoles, CandidHaro
from features import gestion_actions, taches
from blocs import bdd_tools
import tools

class ActionsPubliques(commands.Cog):
    """ActionsPubliques - Gestion des actions publiques comme haros, candidatures à la mairie, etc..."""


    @commands.command()
    async def haro(self, ctx, target=None):
        """Lance un haro contre [cible]
        """
        auteur = ctx.author
        cible = await tools.boucle_query_joueur(ctx, target, 'Contre qui souhaite-tu déverser ta haine ?')
        await tools.send_blocs(ctx, "Et quel est la raison de cette haine, d'ailleurs ?")
        motif = await ctx.bot.wait_for('message', check = lambda m: m.channel == ctx.channel and m.author != ctx.bot.user)

        if not CandidHaro.query.filter_by(player_id = cible.discord_id):
            haroted = CandidHaro(id = None, player_id = cible.discord_id, type = "haro")
            db.session.add(haroted)

        if not CandidHaro.query.filter_by(player_id = ctx.author.id):
            haroteur = CandidHaro(id=None, player_id = ctx.author.id, type="haro")
            db.session.add(haroteur)

        db.session.commit()

        emb = discord.Embed(title = f"{tools.emoji(ctx, 'ha')}{tools.emoji(ctx, 'ro')} contre {cible.nom} !",
                            description = f"**« {motif.content} »**\n \n" + f"{ctx.author.display_name} en a gros     :rage: :rage:", color=0xff0000 )
        await ctx.send(f"{ctx.guild.get_member(cible.discord_id).mention}", embed=emb)
