from discord.ext import commands
import tools
from bdd_connect import db, cache_TDB

trigYesNo = {"oui","non","o","n","yes","no","y","n"}

repOui = {"oui","o","yes","y"}

async def main(bot, member):
    if chan := tools.get(member.guild.text_channels, topic=f"{member.id}"):
        await chan.send(f"Tu as déjà un channel à ton nom, {member.mention}")
        return

    #print(f"{member.id}")

    chan = await member.guild.create_text_channel(f"conv-bot-{member.name}", category = tools.channel(member, "CONVERSATION BOT"), topic=f"{member.id}") # Crée le channel "perso-nom" avec le topic "member.id"

    await chan.set_permissions(member, read_messages=True, send_messages=True)

    await chan.send(f"Bienvenue {member.mention}, laisse moi t'aider à t'inscrire !\n Pour commencer, qui es-tu ?")

    def checkChan(m): #Check que le message soit envoyé par l'utilisateur et dans son channel perso
        return m.channel == chan and m.author == member

    vraiNom = await bot.wait_for('message', check=checkChan)

    ##await tools.log(member,vraiNom.content)

    await chan.edit(name = f"conv-bot-{vraiNom.content}")
    if not member.has_role("MJ"):
        await member.edit(nick = f"{vraiNom.content}")

    await chan.send("Habite-tu à la rez ? (O/N)")

    def checkTrigChan(m): #Check que le message soit une reponse oui/non et qu'elle soit dans le bon channel et pas le bon auteur
        return checkChan(m) and tools.checkTrig(m,trigYesNo)

    rep = await bot.wait_for('message', check=checkChan)

    if a_la_rez := rep.content.lower() in repOui:
        await chan.send("Alors quelle est ta chambre ?")
        chambre = (await bot.wait_for('message', check=checkChan)).content
    else:
        chambre = "XXX (chambre MJ)"

    await chan.send(f"A la rez = {a_la_rez} et chambre = {chambre}")
