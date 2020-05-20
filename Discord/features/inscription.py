from discord.ext import commands
import tools
from bdd_connect import db, cache_TDB

trigYesNo = {"oui","non","o","n","yes","no","y","n"}

repOui = {"oui","o","yes","y"}
repNon =

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
    await member.edit(nick = f"{vraiNom.content}")

    def checkTrigChan(m): #Check que le message soit une reponse oui/non et qu'elle soit dans le bon channel et pas le bon auteur
        return checkChan(m) and tools.checkTrig(m,trigYesNo)

    await chan.send("Habite-tu à la rez ? (O/N)")
    rep = await bot.wait_for('message', check=checkTrigChan)

    if a_la_rez := rep.content.lower() in repOui:
        chambre = (await bot.wait_for('message', check=checkChan)).contient
    else:
        chambre = "XXX (chambre MJ)"

    await tools.log(member, f"A la rez = {a_la_rez} et chambre = {chambre}")
