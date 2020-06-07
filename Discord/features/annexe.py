import random
import traceback

from discord.ext import commands

import tools
from bdd_connect import db, Joueurs


class Annexe(commands.Cog):
    """Annexe : commandes annexes aux usages divers"""

    @commands.command()
    async def roll(self, ctx, *, arg):
        dices = arg.replace(' ','').replace('-','+-').split('+')        # "1d6 + 5 - 2" -> ["1d6", "5", "-2"]
        r = ""
        s = 0
        try:
            for dice in dices:
                if 'd' in dice:
                    nb, faces = dice.split('d', maxsplit=1)
                    for i in range(int(nb)):
                        v = random.randrange(int(faces)) + 1 
                        s += v
                        r += f" + {v}₍{tools.sub_chiffre(int(faces), True)}₎"
                else:
                    v = int(dice)
                    s += v
                    r += f" {'-' if v < 0 else '+'} {abs(v)}"
            r += f" = {tools.emoji_chiffre(s, True)}"
        except Exception:
            await ctx.send(tools.code("!role") + " : pattern non reconu"+traceback.format_exc())
        else:
            await ctx.send(r[3:])
            

    @commands.command(aliases=["cf", "pf"])
    async def coinflip(self, ctx):
        await ctx.send(random.choice(["Pile", "Face"]))


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
    async def testreact(self, ctx, *reacts):
        message = await ctx.send(tools.code_bloc(f"REACT TO THAT!\nReacts: {' - '.join(reacts)}"))
        react = await tools.wait_for_react_clic(ctx.bot, message, ["🔴", "🟠", "🟢"])
        await ctx.send(tools.code_bloc(f"REACTED : {react}"))


    @commands.command()
    @commands.has_role("MJ")
    async def testbdd(self, ctx):
        """Test BDD"""

        tous = Joueurs.query.all()
        ret = '\n - '.join([u.nom for u in tous])
        message = await ctx.send(tools.code_bloc(f"Liste des joueurs :\n - {ret}"))


    @commands.command()
    @commands.has_role("MJ")
    async def rename(self, ctx, id: int, nom: str):
        """Renommer quelqu'un à partir de son ID"""

        try:
            u = Joueurs.query.filter_by(discord_id=id).one()
        except:
            await ctx.send(tools.code_bloc(f"Cible {id} non trouvée\n{traceback.format_exc()}"))
        else:
            oldnom = u.nom
            u.nom = nom
            db.session.commit()
            await ctx.send(tools.code_bloc(f"Joueur {oldnom} renommé en {nom}."))


    @commands.command()
    @tools.private
    async def private_test(self, ctx, *, arg):
        """Test PRIVÉ"""

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
