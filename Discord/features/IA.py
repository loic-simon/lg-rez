import tools
from discord.ext import commands

#Commandes de STFU
async def stfu_on(ctx):
    topic = "Ta conversation privée avec le bot, c'est ici que tout se passera !"
    if ctx.channel.id not in ctx.bot.in_stfu:
        await ctx.channel.send("STFU activé")
        ctx.bot.in_stfu.append(ctx.channel.id)
        await ctx.channel.edit(topic = f"{topic} (STFU ON)")
    else:
        await ctx.channel.send("Le STFU est déjà activé")

async def stfu_off(ctx):
    topic = "Ta conversation privée avec le bot, c'est ici que tout se passera !"
    if ctx.channel.id in ctx.bot.in_stfu:
        await ctx.channel.send("STFU désactivé")
        ctx.bot.in_stfu.remove(ctx.channel.id)
        await ctx.channel.edit(topic = topic)
    else:
        await ctx.channel.send("Le STFU est déjà désactivé")

class GestionIA(commands.Cog):
    """
    Commandes relatives à l'IA (arrêter l'IA, les réactions ud bot, etc)
    """
    @commands.command()
    @tools.private
    async def stfu(self, ctx, force=None): #stfu le channel de la personne mise en arguments
        """Toggle l'IA sur le channel courant"""
        topic = ctx.channel.topic
        if force == "start":
            await stfu_on(ctx)
            ctx.channel.send("started")
        elif force == "stop":
            await stfu_off(ctx)
        else:
            if ctx.channel.id not in ctx.bot.in_stfu:
                await stfu_on(ctx)
            else:
                await stfu_off(ctx)
        ctx.channel.send("yousk2")


async def main(message):
    if 'lange' in message.content.lower():
        rep = "LE LANGE !!!!!"
    elif message.content.lower() == "stop":     # Si on a quitté une commande. Laisser tel quel.
        return
    else:
        rep = "Désolé, je n'ai pas compris 🤷‍♂️"

    await message.channel.send(rep)
