from discord.ext import commands
import tools
from bdd_connect import db, cache_TDB

class Annexe(commands.Cog):
    """Annexe : commandes annexes aux usages divers"""

    @commands.command()
    @commands.has_role("MJ")
    async def test(self, ctx, *, arg):
        """Test : test !"""

        # arg = tools.command_arg(ctx)    # Arguments de la commande (sans le !test) --> en fait c'est faisable nativement, zrtYes
        auteur = ctx.author.display_name
        salon = ctx.channel.name if hasattr(ctx.channel, "name") else f"DMChannel de {ctx.channel.recipient.name}"
        serveur = ctx.guild.name if hasattr(ctx.guild, "name") else "(DM)"
        # pref = ctx.prefix
        # com = ctx.command
        # ivkw = ctx.invoked_with

        await tools.log(ctx, "Alors, ça log ?")

        await ctx.send(tools.code_bloc(
            f"arg = {arg}\n"
            f"auteur = {auteur}\n"
            f"salon = {salon}\n"
            f"serveur = {serveur}"
        ))


    @commands.command()
    @commands.has_role("MJ")
    async def testbdd(self, ctx):
        """Test BDD"""

        tous = cache_TDB.query.all()
        ret = '\n - '.join([u.nom for u in tous])
        await ctx.send(tools.code_bloc(f"Liste des joueurs :\n - {ret}"))


    @commands.command()
    @commands.has_role("MJ")
    async def rename(self, ctx, id: int, nom: str):
        """Renommer quelqu'un à partir de son ID"""

        try:
            u = cache_TDB.query.filter_by(messenger_user_id=id).one()
        except:
            await ctx.send(tools.code_bloc(f"Cible {id} non trouvée\n{traceback.format_exc()}"))
        else:
            oldnom = u.nom
            u.nom = nom
            db.session.commit()
            await ctx.send(tools.code_bloc(f"Joueur {oldnom} renommé en {nom}."))


    @commands.command()
    async def role(self, ctx) :
        """Affiche la liste des roles""" #création de la BDD role dans models.py
