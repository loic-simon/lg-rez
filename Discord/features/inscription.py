import os

from dotenv import load_dotenv
from discord.ext import commands

import tools
from bdd_connect import db, Joueurs
from blocs import gsheets, bdd_tools


async def main(bot, member):
    ### Vérification si le joueur est déjà inscrit / en cours et création chan privé si nécessaire

    if Joueurs.query.get(member.id):                                            # Joueur dans la bdd = déjà inscrit
        await tools.private_chan(member).send(f"Saloww ! {member.mention} tu es déjà inscrit, viens un peu ici enculé !")
        return
    elif chan := tools.get(member.guild.text_channels, topic=f"{member.id}"):   # Inscription en cours
        await chan.send(f"Tu as déjà un channel à ton nom, {member.mention}, par ici !")
    else:
        chan = await member.guild.create_text_channel(f"conv-bot-{member.name}", category=tools.channel(member, "CONVERSATION BOT"), topic=f"{member.id}") # Crée le channel "conv-bot-nom" avec le topic "member.id"
        await chan.set_permissions(member, read_messages=True, send_messages=True)


    ### Récupération nom et renommages

    await chan.send(f"Bienvenue {member.mention}, laisse moi t'aider à t'inscrire !\n Pour commencer, qui es-tu ?")

    def checkChan(m): #Check que le message soit envoyé par l'utilisateur et dans son channel perso
        return m.channel == chan and m.author == member and not m.content.startswith(bot.command_prefix)
    vraiNom = await tools.wait_for_message(bot, check=checkChan)

    await chan.edit(name=f"conv-bot-{vraiNom.content}")       # Renommage conv
    if not tools.role(member,"MJ") in member.roles:
        await member.edit(nick=f"{vraiNom.content}")          # Renommage joueur (ne peut pas renommer les MJ)


    ### Récupération chambre

    a_la_rez = await tools.yes_no(bot, await chan.send("Habite-tu à la rez ?"))

    def sortieNumRez(m):
        return len(m.content) < 200 #Longueur de chambre de rez maximale

    if a_la_rez:
        chambre = (await tools.boucleMessage(bot, chan, "Alors, quelle est ta chambre ?", sortieNumRez, checkChan, repMessage="Désolé, ce n'est pas un numéro de chambre valide, réessaie...")).content
    else:
        chambre = "XXX (chambre MJ)"

    await chan.send(f"A la rez = {a_la_rez} et chambre = {chambre}")


    async with chan.typing():     # Envoi indicateur d'écriture pour informer le joueur que le bot fait des trucs

        ### Ajout à la BDD

        joueur = Joueurs(discord_id=member.id, _chan_id=chan.id, nom=member.display_name,
                         chambre=chambre, statut="vivant", role="Non attribué", camp="Non attribué", 
                         votant_village=True, votant_loups=False, role_actif=True)
        db.session.add(joueur)
        db.session.commit()


        ### Ajout au TDB

        cols = [col for col in bdd_tools.get_cols(Joueurs) if not col.startswith('_')]    # On élimine les colonnes locales

        load_dotenv()
        SHEET_ID = os.getenv("TDB_SHEET_ID")

        workbook = gsheets.connect(SHEET_ID)    # Tableau de bord
        sheet = workbook.worksheet("Journée en cours")
        values = sheet.get_all_values()         # Liste de liste des valeurs des cellules
        NL = len(values)

        head = values[2]            # Ligne d'en-têtes (noms des colonnes) = 3e ligne du TDB
        TDB_index = {col:head.index(col) for col in cols}    # Dictionnaire des indices des colonnes GSheet pour chaque colonne de la table
        TDB_tampon_index = {col:head.index(f"tampon_{col}") for col in cols if col != 'discord_id'}    # Idem pour la partie « tampon »

        plv = 3        # Première ligne vide (si tableau vide, 4e ligne ==> l=3)
        for l in range(NL):
            if values[l][TDB_index["discord_id"]].isdigit():    # Si il y a un vrai ID dans la colonne ID, ligne l
                plv = l + 1

        Modifs = [(plv, TDB_index[col], getattr(joueur, col)) for col in TDB_index] + [(plv, TDB_tampon_index[col], getattr(joueur, col)) for col in TDB_tampon_index]   # Modifs : toutes les colonnes de la partie principale + du cache
        gsheets.update(sheet, Modifs)


        ### Grant accès aux channels joueurs et information

        await member.add_roles(tools.role(member, "Joueur en vie"))
        await chan.edit(topic="Ta conversation privée avec le bot, c'est ici que tout se passera !")
        
        
    # Conseiller d'ACTIVER TOUTES LES NOTIFS du chan (et mentions only pour le reste, en activant @everyone)
    await chan.send("Tu es maintenant inscrit, installe toi confortablement, la partie va bientôt commencer !")
