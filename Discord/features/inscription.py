from discord.ext import commands
import tools
from bdd_connect import db, Joueurs

trigYesNo = {"oui","non","o","n","yes","no","y","n"}
repOui = {"oui","o","yes","y"}

async def main(bot, member):
    if chan := tools.get(member.guild.text_channels, topic=f"{member.id}"):
        await chan.send(f"Tu as déjà un channel à ton nom, {member.mention}, par ici !")
    elif len(Joueurs.query.filter_by(discord_id=member.id).all())>0:
        await tools.private_chan(member).send(f"Saloww ! {member.mention} tu es déjà inscrit, viens un peu ici enculé !")
        return
    else:
        chan = await member.guild.create_text_channel(f"conv-bot-{member.name}", category = tools.channel(member, "CONVERSATION BOT"), topic=f"{member.id}") # Crée le channel "perso-nom" avec le topic "member.id"

    await chan.set_permissions(member, read_messages=True, send_messages=True)

    await chan.send(f"Bienvenue {member.mention}, laisse moi t'aider à t'inscrire !\n Pour commencer, qui es-tu ?")

    def checkChan(m): #Check que le message soit envoyé par l'utilisateur et dans son channel perso
        return m.channel == chan and m.author == member and not m.content.startswith(bot.command_prefix)

    vraiNom = await bot.wait_for('message', check=checkChan)

    ##await tools.log(member,vraiNom.content)

    await chan.edit(name = f"conv-bot-{vraiNom.content}")
    if not tools.role(member,"MJ") in member.roles:
        await member.edit(nick = f"{vraiNom.content}")


    message = await chan.send("Habite-tu à la rez ? (O/N)")

    # def checkTrigChan(m): #Check que le message soit une reponse oui/non et qu'elle soit dans le bon channel et pas le bon auteur
    #     return checkChan(m) and tools.checkTrig(m,trigYesNo)

    #rep = await bot.wait_for('message', check=checkTrigChan) #Utile avant l'arrivée des reacts
    #a_la_rez = rep.content.lower() in repOui

    rep = await tools.wait_for_react_clic(bot, message, text_filter=lambda s:s.lower() in trigYesNo)
    a_la_rez = (rep is True) or (isinstance(rep, str) and rep.lower() in repOui)

    def sortieNumRez(m):
        return len(m.content) < 200 #Longueur de chambre de rez maximale

    if a_la_rez:
        chambre = (await tools.boucleMessage(bot, chan, "Alors, quelle est ta chambre ?", sortieNumRez, checkChan, repMessage="Désolé, ce n'est pas un numéro de chambre valide, réessaie...")).content
    else:
        chambre = "XXX (chambre MJ)"

    await chan.send(f"A la rez = {a_la_rez} et chambre = {chambre}")
    
    db.session.add(Joueurs(member.id, chan.id, member.display_name, chambre, "vivant", "Non attribué", "Non attribué", True, False))
    db.session.commit()

    await member.add_roles(tools.role(member, "Joueur en vie"))

    await chan.edit(topic="Ta conversation privée avec le bot, c'est ici que tout se passera !")
    await chan.send("Tu es maintenant inscrit, installe toi confortablement, la partie va bientôt commencer !")
