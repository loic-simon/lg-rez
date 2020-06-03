import tools
from discord.ext import commands

#Commandes de STFU
async def stfu_on(ctx):
    if ctx.channel.id not in ctx.bot.in_stfu:
        await ctx.send("Okay, je me tais ! Tape !stfu quand tu voudras de nouveau de moi :cry:")
        ctx.bot.in_stfu.append(ctx.channel.id)
        #await ctx.channel.edit(topic = "Ta conversation privée avec le bot, c'est ici que tout se passera ! (STFU ON)")
    else:
        await ctx.send("Arrête de t'acharner, tu m'as déja dit de me taire...")

async def stfu_off(ctx):
    if ctx.channel.id in ctx.bot.in_stfu:
        await ctx.send("Ahhh, ça fait plaisir de pouvoir reparler !")
        ctx.bot.in_stfu.remove(ctx.channel.id)
        #await ctx.channel.edit(topic = "Ta conversation privée avec le bot, c'est ici que tout se passera !")
    else:
        await ctx.send("Ça mon p'tit pote, tu l'as déjà dit !")

class GestionIA(commands.Cog):
    """
    Commandes relatives à l'IA (arrêter l'IA, les réactions ud bot, etc)
    """
    @commands.command()
    @tools.private
    async def stfu(self, ctx, force=None): #stfu le channel de la personne mise en arguments
        """Toggle l'IA sur le channel courant"""
        if force == "start":
            await stfu_on(ctx)
        elif force == "stop":
            await stfu_off(ctx)
        else:
            if ctx.channel.id not in ctx.bot.in_stfu:
                await stfu_on(ctx)
            else:
                await stfu_off(ctx)


async def main(message):
    if 'lange' in message.content.lower():
        rep = "LE LANGE !!!!!"
    elif message.content.lower() == "crash":
        bonsoir
    elif message.content.lower() == "stop":     # Si on a quitté une commande. Laisser tel quel.
        return
    else:
        rep = "Désolé, je n'ai pas compris 🤷‍♂️"

    await message.channel.send(rep)
